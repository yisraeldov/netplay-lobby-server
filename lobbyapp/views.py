from django.shortcuts import render, render_to_response
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.template import RequestContext
from django.utils.timezone import localtime, now
from django.core import serializers
from datetime import timedelta
from models import *
import json

ENTRY_TIMEOUT = 120
THROTTLE = True
THROTTLE_SECS = 10

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
      'mitm_port': 0,
      'ip': ip,
      'port': port,
      'host_method': host_method,
      'has_password': has_password,
      'has_spectate_password': has_spectate_password,
    }

    if update:
      entries = Entry.objects.filter(pk=update)
      entries.update(**kwargs)

      for entry in entries:
        entry.save()
    else:
      delete_old_entries()

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
  entries = Entry.objects.filter()

  delete_old_entries()

  return render_to_response("index.html", {
    'entries': entries
  })

@csrf_exempt
def list_entries(request):
  entries = Entry.objects.filter()

  if len(entries) == 0:
    data = '[]'
  else:
    data = serializers.serialize("json", entries, indent=2)

  return HttpResponse(data, content_type='text/plain')
