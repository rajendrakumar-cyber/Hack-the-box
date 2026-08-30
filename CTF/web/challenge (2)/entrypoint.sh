#!/bin/sh
set -eu

cd /app/app
node /app/entrypoint.js

/usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
