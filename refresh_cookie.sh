#!/bin/bash
# Floatbase — Steam Cookie Auto-Refresh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

source <(grep -E "^TELEGRAM_BOT_TOKEN=|^TELEGRAM_CHAT_ID=" .env)

telegram() {
    if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -H "Content-Type: application/json" \
            -d "{\"chat_id\":\"${TELEGRAM_CHAT_ID}\",\"text\":\"$1\",\"parse_mode\":\"HTML\"}" > /dev/null
    fi
}

echo "[$(date)] Starting Steam cookie refresh..."

if ! curl -s http://localhost:9222/json > /dev/null 2>&1; then
    telegram "🔴 <b>Floatbase — Cookie refresh failed</b>%0AChrome not running on port 9222."
    echo "Chrome not running"
    exit 1
fi

COOKIE=$(python3 - << 'EOF'
import json, urllib.request, asyncio, websockets, sys

async def get_cookie():
    try:
        pages = json.loads(urllib.request.urlopen('http://localhost:9222/json').read())
        if not pages:
            print("NO_PAGES")
            return
        page_ws = pages[0]['webSocketDebuggerUrl']
        async with websockets.connect(page_ws) as ws:
            # Get cookies directly — no navigation, avoids response ordering issues
            await ws.send(json.dumps({'id':1,'method':'Network.getAllCookies','params':{}}))
            # Drain responses until we get our id:1 response
            for _ in range(10):
                resp = json.loads(await ws.recv())
                if resp.get('id') == 1:
                    break
            cookies = resp.get('result',{}).get('cookies',[])
            steam = [c for c in cookies if c.get('name') == 'steamLoginSecure']
            if steam:
                best = max(steam, key=lambda c: len(c.get('value','')))
                print(best['value'])
            else:
                print("NOT_FOUND")
    except Exception as e:
        print(f"ERROR:{e}", file=sys.stderr)
        print("NOT_FOUND")

asyncio.run(get_cookie())
EOF
)

if [[ "$COOKIE" == "NOT_FOUND" || "$COOKIE" == "NO_PAGES" || "$COOKIE" == ERROR* || -z "$COOKIE" ]]; then
    telegram "🔴 <b>Floatbase — Cookie refresh failed</b>%0ACould not extract steamLoginSecure.%0ALog into Steam via VNC on port 5900."
    echo "Failed to extract cookie: $COOKIE"
    exit 1
fi

echo "Cookie extracted, length: ${#COOKIE}"

python3 - << PYEOF
import re
cookie = """$COOKIE"""
with open('.env', 'r') as f:
    env = f.read()
env = re.sub(r'^STEAM_LOGIN_SECURE=.*$', f'STEAM_LOGIN_SECURE={cookie}', env, flags=re.MULTILINE)
with open('.env', 'w') as f:
    f.write(env)
print("Updated .env")
PYEOF

docker compose up --build -d backend
echo "Backend restarted"

telegram "🟢 <b>Floatbase — Steam cookie refreshed</b>%0ACookie updated and backend restarted."
echo "[$(date)] Cookie refresh complete"
