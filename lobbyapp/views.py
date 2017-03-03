from django.shortcuts import render, render_to_response
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.template import RequestContext
from django.utils.timezone import localtime, now
from datetime import timedelta
from models import *

ENTRY_TIMEOUT = 120
THROTTLE = True
THROTTLE_SECS = 10

@csrf_exempt
def add_entry(request):
  if request.method != 'POST' or \
    not request.POST.has_key('username') or \
    not request.POST.has_key('corename') or \
    not request.POST.has_key('gamename') or \
    not request.POST.has_key('gamecrc') or \
    not request.POST.has_key('coreversion'):
      raise Http404

  username = request.POST['username']
  ip = None
  port = None
  update = None

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

  if len(request.POST['corename']) == 0 or \
    len(request.POST['gamename']) == 0 or \
    len(request.POST['gamecrc']) == 0 or \
    len(request.POST['coreversion']) == 0:
      raise Http404

  t = localtime(now())

  entries = Entry.objects.filter().all()

  for entry in entries:
    if THROTTLE:
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
      'core_name': request.POST['corename'],
      'game_name': request.POST['gamename'],
      'game_crc': request.POST['gamecrc'],
      'core_version': request.POST['coreversion'],
      'mitm_port': 0,
      'ip': ip,
      'port': port,
      'host_method': 0,
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
  entries = Entry.objects.filter(updated__lt=t).all()

  for entry in entries:
    entry.delete()

@csrf_exempt
def index(request):
  entries = Entry.objects.filter().all()

  delete_old_entries()

  return render_to_response("index.html", {
    'entries': entries
  })
