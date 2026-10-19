#!/bin/bash
# Room screen on kellerkind: the host's web page (Home view) full screen in Chromium.
# Started by the desktop (labwc): ~/.config/labwc/autostart → /home/pi/easteregged/kiosk.sh &
# Waits until the host answers, so the screen never shows an error page after a cold start.
URL="${KIOSK_URL:-http://dexy.local:8080/static/clock.html}"   # the room clock (home object); main page: /?kiosk=1#home
until curl -s -m 3 -o /dev/null "${URL%%#*}"; do sleep 5; done
exec chromium --ozone-platform=wayland --kiosk --noerrdialogs --disable-infobars --no-first-run --password-store=basic \
  --disable-features=TranslateUI --check-for-update-interval=31536000 "$URL"
