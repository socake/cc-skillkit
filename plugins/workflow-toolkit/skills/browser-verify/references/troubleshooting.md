# browser-verify troubleshooting

By symptom; copy-paste the commands. Container name `browser-verify`, CDP port 9222
assumed — adjust to your setup.

## Container layer

### `docker ps` doesn't show the container

- Directory exists but the container is stopped: `cd "$BROWSER_DIR" && docker compose up -d`
- Directory missing (new host): see [cold-start.md](cold-start.md)
- "Cannot connect to the Docker daemon": `sudo systemctl start docker`

### Container is Restarting / Exited

```bash
docker logs browser-verify --tail 80
docker exec browser-verify supervisorctl -c /etc/supervisor/conf.d/browser-verify.conf status
```

Common causes:
- **Stale `/profile/SingletonLock`** → inside the container
  `rm -f /profile/Singleton{Lock,Cookie,Socket}`, then `docker compose restart`.
  (entrypoint.sh clears these on start, but a hard-killed Chromium can leave them.)
- **`x11vnc` can't find `.vncpasswd`** → the cold-start step 3 was skipped; redo it.
- **Not enough shared memory, Chrome dies** → check `shm_size: 2gb` is still in
  docker-compose.yml.

## CDP layer

### `curl http://127.0.0.1:9222/json/version` fails

```bash
# 1. is the chrome process up?
docker exec browser-verify ps -ef | grep -i chrome
# 2. is the socat bridge up? (Chrome binds only 127.0.0.1; socat forwards it)
docker exec browser-verify ps -ef | grep socat
# expect socat TCP-LISTEN:9222 ... TCP:127.0.0.1:9223
# 3. can the container reach it internally?
docker exec browser-verify curl -sf http://127.0.0.1:9223/json/version | head -2
# 4. port mapping
docker port browser-verify 9222
```

Any failing step → `docker compose restart`.

### `connect_over_cdp` hangs / times out

- Too many tabs (>20) → `python3 scripts/gc.py`
- Chrome OOM-restarted → `docker logs` for "out of memory", then restart
- **Remote host calling local 9222** → won't work; Chrome advertises a 127.0.0.1 ws
  address. SSH into the host and run there.

## Playwright MCP layer

### `claude mcp list` has no playwright

```bash
claude mcp add playwright -s user -- npx -y @playwright/mcp@latest --cdp-endpoint=http://127.0.0.1:9222
# takes effect in a new session
```

### MCP tool reports `No browser is open`

The old session's MCP server lost the freshly restarted Chromium. Start a new session.

## Login-state layer

### Redirected to login / 401 / token expired

The container Chromium's login state expired.

```bash
xdg-open "http://127.0.0.1:6080/vnc.html?autoconnect=true"
# log in once inside the container's Chrome via noVNC; the VNC password is the one
# set during cold start
```

Cookies land in `./profile/` and are reused next run.

## Performance / resource layer

### Container memory spikes past 2GB

```bash
docker stats browser-verify --no-stream
docker exec browser-verify ps -ef | grep -c chrome
```

- >6 chrome processes: too many tabs → `python3 scripts/gc.py --keep-url <url-to-keep>`
- still high: confirm the launch flags are present in supervisord.conf
  (`--renderer-process-limit=4`, `--js-flags=--max-old-space-size=512`,
  `--disk-cache-size=52428800`, `--process-per-site`), then `docker compose restart`
  (flags are volume-mounted, no rebuild needed).

### Captured console / network is always incomplete

- Register `page.on("response", ...)` **before** `page.goto`.
- After a navigation, listeners on the same context keep working, but confirm the page
  is still alive.
- MCP `browser_network_requests` returns only the current page's traffic; history is
  lost across navigations, so pull it at each step.

## Log-query layer

### The log-query tool isn't installed

Install your environment's client (Loki `logcli`, the cloud CLI, etc.). Keep the exact
command and any auth in your own runbook.

### Grep finds nothing

- The id may use a different field name (`trace_id` / `traceId` / `request_id` / `rid`).
  Grep the bare id string first.
- Window too small: widen `5m` → `30m`.
- Wrong environment selected: confirm the environment name maps to the target you
  think it does (display name ≠ underlying target is a classic trap).
