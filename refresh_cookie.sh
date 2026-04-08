#!/bin/bash
# Floatbase — Steam Cookie Auto-Refresh
# Extracts steamLoginSecure from running Chromium via CDP,
# updates .env, restarts backend, notifies Telegram.

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Load env vars for Telegram
source <(grep -E "^TELEGRAM_BOT_TOKEN=|^TELEGRAM_CHAT_ID=" .env)

telegram() {
    if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -H "Content-Type: application/json" \
            -d "{\"chat_id\":\"${TELEGRAM_CHAT_ID}\",\"text\":\"$1\",\"parse_mode\":\"HTML\"}" > /dev/null
    fi
}

echo "[$(date)] Starting Steam cookie refresh..."

# Check Chromium is running with debug port
if ! curl -s http://localhost:9222/json/version > /dev/null 2>&1; then
    echo "Chromium not running — starting it..."
    DISPLAY=:100 chromium-browser \
        --no-sandbox \
        --user-data-dir=/home/ratul/snap/chromium/common/steam-profile \
        --remote-debugging-port=9222 \
        --remote-debugging-address=127.0.0.1 \
        https://steamcommunity.com/market/ &
    sleep 10
fi

# Extract cookie via CDP
COOKIE=$(python3 - << 'PYEOF'
import json, urllib.request, asyncio, websockets, sys

async def get_cookie():
    try:
        pages = json.loads(urllib.request.urlopen('http://localhost:9222/json', timeout=10).read())
        if not pages:
            print("", end="")
            return
        page_ws = pages[0]['webSocketDebuggerUrl']
        async with websockets.connect(page_ws) as ws:
            await ws.send(json.dumps({'id':1,'method':'Network.getAllCookies','params':{}}))
            resp = json.loads(await ws.recv())
            cookies = resp.get('result',{}).get('cookies',[])
            steam = [c for c in cookies if c.get('name') == 'steamLoginSecure']
            if steam:
                best = max(steam, key=lambda c: len(c.get('value','')))
                print(best['value'], end="")
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        print("", end="")

asyncio.run(get_cookie())
PYEOF
)

if [ -z "$COOKIE" ] || [ ${#COOKIE} -lt 100 ]; then
    echo "[$(date)] ERROR: Failed to extract cookie (length: ${#COOKIE})"
    telegram "❌ <b>Floatbase — Cookie refresh FAILED</b>%0A%0AChromium running but cookie not found. Steam session may have expired — log in again via VNC."
    exit 1
fi

echo "[$(date)] Cookie extracted (length: ${#COOKIE})"

# Update .env
sed -i "s|^STEAM_LOGIN_SECURE=.*|STEAM_LOGIN_SECURE=${COOKIE}|" .env
echo "[$(date)] Updated .env"

# Restart backend
docker compose up --build -d backend
echo "[$(date)] Backend restarted"

telegram "🔄 <b>Floatbase — Steam cookie refreshed</b>%0A%0AAutomatic refresh successful. $(date '+%Y-%m-%d %H:%M')"
echo "[$(date)] Done!"
