#!/bin/bash
# Floatbase — Steam Cookie Auto-Refresh
# Navigates Chrome to Steam Market, waits for fresh cookie, updates .env, restarts backend.

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

# Check Chrome debug port is up
if ! curl -s http://localhost:9222/json > /dev/null 2>&1; then
    telegram "🔴 <b>Floatbase — Cookie refresh failed</b>%0AChrome not running on port 9222. Check steam-chromium service."
    echo "Chrome not running"
    exit 1
fi

# Navigate to Steam Market, wait for page load, extract fresh cookie
COOKIE=$(python3 - << 'EOF'
import json, urllib.request, asyncio, websockets, sys

async def get_cookie():
    try:
        pages = json.loads(urllib.request.urlopen('http://localhost:9222/json').read())
        if not pages:
            print("NO_PAGES")
            return

        page_ws = pages[0]['webSocketDebuggerUrl']
        print(f"Connecting to: {page_ws}", file=sys.stderr)

        async with websockets.connect(page_ws) as ws:
            # Step 1: Navigate to Steam Market to force a fresh cookie
            print("Navigating to Steam Market...", file=sys.stderr)
            await ws.send(json.dumps({
                'id': 1,
                'method': 'Page.navigate',
                'params': {'url': 'https://steamcommunity.com/market/'}
            }))

            # Step 2: Wait generously for page to fully load and cookie to be issued
            print("Waiting 10s for page load...", file=sys.stderr)
            await asyncio.sleep(10)

            # Step 3: Drain any pending messages from navigation
            print("Draining pending messages...", file=sys.stderr)
            try:
                while True:
                    msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    data = json.loads(msg)
                    print(f"  Drained: {data.get('method', data.get('id', '?'))}", file=sys.stderr)
            except asyncio.TimeoutError:
                pass

            # Step 4: Request all cookies
            print("Requesting cookies...", file=sys.stderr)
            await ws.send(json.dumps({
                'id': 2,
                'method': 'Network.getAllCookies',
                'params': {}
            }))

            # Step 5: Wait for the cookies response
            resp = None
            for _ in range(15):
                msg = json.loads(await ws.recv())
                if msg.get('id') == 2:
                    resp = msg
                    break

            if not resp:
                print("NO_RESPONSE")
                return

            cookies = resp.get('result', {}).get('cookies', [])
            steam = [c for c in cookies if c.get('name') == 'steamLoginSecure']
            print(f"Found {len(steam)} steamLoginSecure cookies", file=sys.stderr)

            if steam:
                best = max(steam, key=lambda c: len(c.get('value', '')))
                print(f"Best cookie length: {len(best['value'])}", file=sys.stderr)
                print(best['value'])
            else:
                print("NOT_FOUND")

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        print("NOT_FOUND")

asyncio.run(get_cookie())
EOF
)

if [[ "$COOKIE" == "NOT_FOUND" || "$COOKIE" == "NO_PAGES" || "$COOKIE" == "NO_RESPONSE" || "$COOKIE" == ERROR* || -z "$COOKIE" ]]; then
    telegram "🔴 <b>Floatbase — Cookie refresh failed</b>%0ACould not extract steamLoginSecure: $COOKIE%0ALog into Steam via VNC on port 5900."
    echo "Failed to extract cookie: $COOKIE"
    exit 1
fi

echo "Cookie extracted, length: ${#COOKIE}"

# Update .env with fresh cookie
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

# Rebuild and restart backend to pick up new env var
echo "Rebuilding backend..."
docker compose up --build -d backend

echo "Backend restarted"
telegram "🟢 <b>Floatbase — Steam cookie refreshed</b>%0ACookie updated and backend restarted successfully."
echo "[$(date)] Cookie refresh complete"
