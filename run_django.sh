#!/bin/bash

#!/bin/bash

#source ~/venv/bin/activate

killall -9 uwsgi &>/dev/null

sleep 1

uwsgi --chdir=/home/lobby/lobby \
    --plugins python \
    --module=lobby.wsgi:application \
    --env DJANGO_SETTINGS_MODULE=lobby.settings \
    --master --pidfile=/tmp/lobby-master.pid \
    --fastcgi-socket=127.0.0.1:3035 \
    --processes=5 \
    --uid=1003 --gid=1003 \
    --harakiri=120 \
    --max-requests=5000 \
    --vacuum \
    --pp=/usr/lib/python2.7 \
    --daemonize=/tmp/lobby.log
#    --daemonize=/dev/null
#    --log-syslog \
