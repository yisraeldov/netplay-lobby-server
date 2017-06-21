#!/bin/bash

USER_ID=`id -u`
GROUP_ID=`id -g`

ps ax|grep uwsgi|grep lobby|awk '{print $1}'|xargs kill -9

sleep 1

uwsgi --chdir=/home/lobby/lobby \
    --plugins python \
    --module=lobby.wsgi:application \
    --env DJANGO_SETTINGS_MODULE=lobby.settings \
    --master --pidfile=/tmp/lobby-master.pid \
    --fastcgi-socket=127.0.0.1:3035 \
    --processes=5 \
    --uid=$USER_ID --gid=$GROUP_ID \
    --harakiri=120 \
    --max-requests=5000 \
    --vacuum \
    --touch-reload=/tmp/lobby-reload \
    --pp=/usr/lib/python2.7 \
    --daemonize=/tmp/lobby.log
#    --daemonize=/dev/null
#    --log-syslog \
