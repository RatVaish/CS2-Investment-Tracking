#!/bin/bash
# Floatbase — Start persistent Steam browser session
# Run on boot via crontab @reboot

# Kill any existing instances
pkill -f "chromium.*steam-profile" 2>/dev/null || true
pkill Xvfb 2>/dev/null || true
sleep 2

# Start virtual display on :100
Xvfb :100 -screen 0 1280x800x24 &
sleep 3

# Start Chromium with saved Steam session + remote debug port
DISPLAY=:100 chromium-browser \
    --no-sandbox \
    --user-data-dir=/home/ratul/snap/chromium/common/steam-profile \
    --remote-debugging-port=9222 \
    --remote-debugging-address=127.0.0.1 \
    --disable-background-mode \
    --no-first-run \
    https://steamcommunity.com/market/ &

sleep 8

# Verify it's up
if curl -s http://localhost:9222/json/version > /dev/null 2>&1; then
    echo "Steam browser started successfully"
else
    echo "ERROR: Steam browser failed to start"
    exit 1
fi
