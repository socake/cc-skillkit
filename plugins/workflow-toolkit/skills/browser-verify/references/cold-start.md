# Cold start: bring up the browser container on a fresh host

For when the container directory doesn't exist yet, or you're moving to another Linux
host and starting from zero.

## Prerequisites

- Linux (tested on Ubuntu/Debian; other distros work the same way)
- Docker + docker compose v2 (`docker compose version` works)
- Disk > 3GB (the Playwright/Python base image is ~2.5GB)
- Memory > 2GB (idle Chromium ~280MB; many tabs push past 2GB)

## Steps

```bash
# 1. Pick a directory
TARGET="${BROWSER_DIR:-$HOME/browser-verify}"
mkdir -p "$TARGET" && cd "$TARGET"

# 2. Copy the assets shipped with this skill (adjust the source path to where the
#    skill is installed)
SKILL_ASSETS="<path-to>/workflow-toolkit/skills/browser-verify/assets"
cp "$SKILL_ASSETS"/{Dockerfile,docker-compose.yml,supervisord.conf,entrypoint.sh} .
cp -r "$SKILL_ASSETS/scripts" .
chmod +x entrypoint.sh

# 3. Init the profile dir + a VNC password
mkdir -p profile
docker run --rm -v "$(pwd)/profile":/profile -it ubuntu:22.04 bash -c '
  apt-get update -qq && apt-get install -y -qq x11vnc &&
  x11vnc -storepasswd "change-me-$(date +%s)" /profile/.vncpasswd
'
# Replace the password above with your own and note it down (needed for noVNC login)

# 4. Build + start
docker compose up -d --build

# 5. Wait ~30s for the first Chromium launch, then verify
docker exec browser-verify supervisorctl -c /etc/supervisor/conf.d/browser-verify.conf status
# expect xvfb / fluxbox / x11vnc / novnc / chromium / cdp-bridge all RUNNING

curl -s http://127.0.0.1:9222/json/version | head -3
# expect {"Browser":"Chrome/...","Protocol-Version":"1.3", ...}
```

## Wire up Playwright

If you drive the browser through the Playwright MCP server, point it at the CDP
endpoint once (user scope, picked up by new sessions):

```bash
claude mcp add playwright -s user -- npx -y @playwright/mcp@latest --cdp-endpoint=http://127.0.0.1:9222
claude mcp list | grep playwright   # expect ✓ Connected
```

New sessions can then call the `mcp__playwright__browser_*` tools directly instead of
hand-writing Python. If you don't use the MCP, the scripts in `assets/scripts/` drive
CDP directly with `playwright.sync_api`.

## First login to the target system

```bash
# host has a display:
xdg-open "http://127.0.0.1:6080/vnc.html?autoconnect=true&password=<your-vnc-password>"

# headless host: tunnel noVNC over SSH
ssh -L 6080:127.0.0.1:6080 <host>
# then open http://127.0.0.1:6080/ locally
```

Log in to the target system inside the container's Chromium through noVNC. The login
state lands in `./profile/` and is reused by every subsequent run.

## Capacity & resource limits

- Chromium launch flags in `supervisord.conf` cap memory:
  `--renderer-process-limit=4` + `--js-flags=--max-old-space-size=512` +
  `--disk-cache-size=52428800` + `--process-per-site`.
- When tabs pile up, run `python3 scripts/gc.py --keep-url <url-to-keep>` to reclaim.

## Known boundaries (read before moving hosts)

- **CDP binds to `127.0.0.1`.** Recent Chrome forces `--remote-debugging-port` onto
  loopback; `supervisord.conf` uses `socat` to forward the container's external
  9222 → internal 9223, but a *remote* host calling `connect_over_cdp("http://host:9222")`
  still won't connect (Chrome advertises a 127.0.0.1 ws address). To drive it from
  another machine, SSH in first.
- **Don't share the profile across concurrent drivers.** It's a single Chromium
  instance; two sessions driving the same Chrome interrupt each other's tabs. For
  parallelism, run a second container with its own profile on different ports.
- **noVNC is bare VNC.** Keep it on localhost / a private network — don't expose it
  publicly.
