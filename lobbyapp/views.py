from django.shortcuts import render, render_to_response
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.template import RequestContext
from django.utils.timezone import localtime, now
from django.core import serializers
from datetime import timedelta
from models import *
import json, socket, struct

ENTRY_TIMEOUT = 120
THROTTLE = True
THROTTLE_SECS = 10
MITM_HOST = 'newlobby.libretro.com'
MITM_PORT = 55435
MITM_SOCKET_TIMEOUT = 10

def request_new_mitm_port():
  try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(MITM_SOCKET_TIMEOUT)
    s.connect((MITM_HOST, MITM_PORT))

    # CMD_REQ_PORT
    s.sendall('\x00\x00\x46\x49\x00\x00\x00\x00')

    data = ''

    while len(data) < 12:
      data += s.recv(12)

    s.close()

    # CMD_NEW_PORT
    if data[0:8] == '\x00\x00\x46\x4a\x00\x00\x00\x04':
      port_unpack = struct.unpack('!I', data[8:12])

      if len(port_unpack) > 0:
        port = port_unpack[0]

        return port
  except Exception, e:
    f = open('/tmp/entry_mitm_error', 'wb')
    f.write(str(e) + '\n')
    f.close()
    #pass

  return 0

@csrf_exempt
def add_entry(request):
  if request.method != 'POST' or \
    not request.POST.has_key('username') or \
    not request.POST.has_key('core_name') or \
    not request.POST.has_key('game_name') or \
    not request.POST.has_key('game_crc') or \
    not request.POST.has_key('core_version'):
      raise Http404

  username = request.POST['username']
  ip = None
  port = None
  update = None
  host_method = HOST_METHOD_UNKNOWN
  has_password = False
  has_spectate_password = False

  if request.POST.has_key('has_password') and request.POST['has_password'] == 1:
    has_password = True

  if request.POST.has_key('has_spectate_password') and request.POST['has_spectate_password'] == 1:
    has_spectate_password = True

  if request.POST.has_key('force_mitm') and int(request.POST['force_mitm']) == 1:
    host_method = HOST_METHOD_MITM

  if request.POST.has_key('port'):
    port = int(request.POST['port'])

  if not port:
    port = 55435

  if port <= 0 or port > 65535:
    raise Http404

  if request.META.has_key('REMOTE_ADDR'):
    ip = request.META['REMOTE_ADDR']

  if not ip or len(ip) == 0:
    ip = '127.0.0.1'

  if len(username) == 0:
    username = ip

  if len(request.POST['core_name']) == 0 or \
    len(request.POST['game_name']) == 0 or \
    len(request.POST['game_crc']) == 0 or \
    len(request.POST['core_version']) == 0:
      raise Http404

  t = localtime(now())

  entries = Entry.objects.filter()

  for entry in entries:
    if THROTTLE and ip != '127.0.0.1':
      if entry.ip == ip and (t - entry.updated).seconds < THROTTLE_SECS:
        # only one new/updated entry allowed per IP every X seconds
        raise Http404

    if entry.username == username and \
      entry.ip == ip and \
      entry.port == port:
        update = entry.id
        break

  try:
    connection.close()

    kwargs = {
      'username': username,
      'core_name': request.POST['core_name'],
      'game_name': request.POST['game_name'],
      'game_crc': request.POST['game_crc'].upper(),
      'core_version': request.POST['core_version'],
      'ip': ip,
      'port': port,
      'host_method': host_method,
      'has_password': has_password,
      'has_spectate_password': has_spectate_password,
    }

    if request.POST.has_key('mitm_ip') and len(request.POST['mitm_ip']) > 0:
      kwargs['mitm_ip'] = request.POST['mitm_ip']

      if request.POST.has_key('mitm_port') and int(request.POST['mitm_port']) > 0:
        kwargs['mitm_port'] = int(request.POST['mitm_port'])
      else:
        kwargs['mitm_port'] = MITM_PORT

    if update:
      entries = Entry.objects.filter(pk=update)

      entries.update(**kwargs)

      for entry in entries:
        if entry.host_method != HOST_METHOD_MITM and host_method == HOST_METHOD_MITM and 'mitm_ip' not in kwargs:
          new_mitm_port = request_new_mitm_port()

          if new_mitm_port > 0:
            entry.mitm_ip = MITM_HOST
            entry.mitm_port = new_mitm_port

        entry.save()
    else:
      delete_old_entries()

      if host_method == HOST_METHOD_MITM and 'mitm_ip' not in kwargs:
        new_mitm_port = request_new_mitm_port()

        if new_mitm_port > 0:
          kwargs['mitm_ip'] = MITM_HOST
          kwargs['mitm_port'] = new_mitm_port

      entry = Entry.objects.create(**kwargs)
      entry.save()

      log = LogEntry.objects.create(**kwargs)
      log.save()

    response = HttpResponse("OK")

    return response
  except Exception, e:
    f = open('/tmp/entry_error', 'wb')
    f.write(str(e) + '\n')
    f.close()
    #pass

  raise Http404

def delete_old_entries():
  t = localtime(now()) - timedelta(seconds=ENTRY_TIMEOUT)
  entries = Entry.objects.filter(fixed=False, updated__lt=t)

  for entry in entries:
    entry.delete()

@csrf_exempt
def index(request):
  delete_old_entries()

  entries = Entry.objects.filter()

  return render_to_response("index.html", {
    'entries': entries
  })

@csrf_exempt
def list_entries(request):
  delete_old_entries()

  entries = Entry.objects.filter()

  if len(entries) == 0:
    data = '[]'
  else:
    data = serializers.serialize("json", entries, indent=2)

  return HttpResponse(data, content_type='text/plain')
