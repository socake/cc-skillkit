#!/bin/bash
set -e

# /profile is mounted from the host; ensure it exists
mkdir -p /profile
# Clear stale lock files so chromium can start (common after a hard kill)
rm -f /profile/SingletonLock /profile/SingletonCookie /profile/SingletonSocket

exec /usr/bin/supervisord -c /etc/supervisor/conf.d/browser-verify.conf
