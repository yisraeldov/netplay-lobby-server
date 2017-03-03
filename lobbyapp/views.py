from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from models import *

@csrf_exempt
def add_entry(request):
  if request.method != 'POST' or \
    not request.POST.has_key('username') or \
    not request.POST.has_key('corename') or \
    not request.POST.has_key('gamename') or \
    not request.POST.has_key('gamecrc') or \
    not request.POST.has_key('coreversion') or \
    not request.POST.has_key('port'):
      raise Http404

  username = request.POST['username']

  if len(username) == 0:
    username = request.META['REMOTE_ADDR']

  if len(request.POST['corename']) == 0 or \
    len(request.POST['gamename']) == 0 or \
    len(request.POST['gamecrc']) == 0 or \
    len(request.POST['coreversion']) == 0 or \
    len(request.POST['port']) == 0:
      raise Http404

  port = int(request.POST['port'])

  if port <= 0 or port > 65535:
    raise Http404

  try:
    connection.close()

    kwargs = {
      'username': username,
      'core_name': request.POST['corename'],
      'game_name': request.POST['gamename'],
      'game_crc': request.POST['gamecrc'],
      'core_version': request.POST['coreversion'],
      'mitm_port': 0,
      'ip': request.META['REMOTE_ADDR'],
      'port': port,
      'host_method': 0,
    }

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

@csrf_exempt
def index(request):
  return HttpResponse('index')
