# Dockerfile audit checklist

Full per-item checklist. For each: what to look for, why it matters, the fix. Grouped
by axis. Severity in brackets is the default — adjust for context (a root-running
public web server is more severe than a root-running batch job in a private network).

---

## Security

### Runs as root [High → Critical if network-facing]
- **Look for:** no `USER` directive anywhere, or the last `USER` is `root`/`0`.
- **Why:** a compromised process runs as root inside the container; combined with a
  kernel/runtime escape that's host root. Defense in depth says drop privileges.
- **Fix:** create and switch to a non-root user before `CMD`:
  ```dockerfile
  RUN useradd --uid 10001 --create-home appuser
  USER 10001
  ```
  Use a numeric UID so Kubernetes `runAsNonRoot` can enforce it.

### Secrets baked into layers [Critical]
- **Look for:** `ARG`/`ENV` named `*TOKEN*`/`*PASSWORD*`/`*KEY*`/`*SECRET*`; `COPY`
  of `.env`, `id_rsa`, `.npmrc`, `.netrc`, a service-account JSON; `RUN` with an
  inline credential (`curl -H "Authorization: Bearer …"`, `git clone https://user:pass@…`).
- **Why:** every layer is stored and shippable. `docker history` / unpacking the
  image recovers it **even if a later `RUN` deletes the file** — the deleting layer
  sits on top of the layer that still contains it. `ARG` values are also visible in
  image metadata.
- **Fix:** BuildKit build secrets, never persisted to a layer:
  ```dockerfile
  RUN --mount=type=secret,id=npm_token \
      NPM_TOKEN=$(cat /run/secrets/npm_token) npm ci
  ```
  Build with `docker build --secret id=npm_token,src=./token`. For private git, use
  `--mount=type=ssh`. Rotate any secret that was ever committed to a layer.

### Unpinned or untrusted base image [High]
- **Look for:** `FROM something:latest`, a bare `FROM ubuntu`, or a mutable tag with
  no digest.
- **Why:** `latest` moves; today's reproducible build silently differs tomorrow, and
  you can't audit exactly what shipped. Untrusted/oversized bases widen attack
  surface.
- **Fix:** pin tag **and** digest, prefer minimal trusted images:
  ```dockerfile
  FROM node:20.11-slim@sha256:<digest>
  ```
  Consider distroless / `-slim` / `alpine` (mind musl vs glibc). Smaller base = fewer
  CVEs to patch.

### Over-broad COPY [Medium → High if secrets in context]
- **Look for:** `COPY . .` / `ADD . /app` early in the file with no `.dockerignore`.
- **Why:** pulls `.git`, `.env`, local creds, CI config, test fixtures into the
  image — bloat and potential secret leak.
- **Fix:** copy only what's needed (`COPY src/ ./src/`), and add a `.dockerignore`
  (see Maintainability).

### Installing from untrusted sources / `curl | sh` [Medium]
- **Look for:** `RUN curl … | sh`, `wget … | bash`, adding unverified apt repos/keys.
- **Why:** unauthenticated remote code execution at build time; supply-chain risk.
- **Fix:** download to a file, verify checksum/signature, then run. Pin the version.

---

## Size

### No multi-stage build [Medium]
- **Look for:** compilers, `build-essential`, `-dev` packages, `go`/`node`/`maven`
  toolchains present in the only/final stage.
- **Why:** build-time tooling ships to production — bigger image, larger attack
  surface, slower pulls.
- **Fix:** build in one stage, copy only the artifact into a clean runtime stage:
  ```dockerfile
  FROM golang:1.22 AS build
  WORKDIR /src
  COPY . .
  RUN go build -o /app ./cmd/server

  FROM gcr.io/distroless/static
  COPY --from=build /app /app
  USER 10001
  ENTRYPOINT ["/app"]
  ```

### Package-manager cache left in the layer [Medium]
- **Look for:** `apt-get install` with no `rm -rf /var/lib/apt/lists/*` **in the same
  `RUN`**; `pip` without `--no-cache-dir`; `npm install` leaving `~/.npm`.
- **Why:** caches add tens to hundreds of MB. Cleaning in a *later* `RUN` doesn't
  help — the bytes are already committed in the earlier layer.
- **Fix:** clean in the same `RUN`:
  ```dockerfile
  RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
      && rm -rf /var/lib/apt/lists/*
  ```
  `pip install --no-cache-dir`, `npm ci && npm cache clean --force`.

### Excessive layers [Low]
- **Look for:** many small sequential `RUN` lines.
- **Why:** each `RUN` is a layer; more layers, marginally bigger image, slower pulls.
- **Fix:** chain related commands with `&&` and line continuations. (Don't over-merge
  — keep the dependency-install layer separate from source copy for cache reasons.)

---

## Reproducibility

### Unpinned dependencies [High]
- **Look for:** `pip install requests`, `npm install` (no lockfile / not `npm ci`),
  `apt-get install foo` with no version, `go get` without a pinned module.
- **Why:** the same Dockerfile produces different images over time; "works on my
  build" diverges from CI; hard to reproduce a past image for forensics.
- **Fix:** pin versions and commit lockfiles. `npm ci` (needs `package-lock.json`),
  `pip install -r requirements.txt` with hashes, `apt-get install foo=1.2.3`.

### `latest` / floating tags anywhere [High]
- **Look for:** `:latest` on base images, tools, or packages.
- **Why:** same as above — silent drift, unauditable builds.
- **Fix:** pin every external reference to an explicit version.

### Cache-busting layer order [Medium]
- **Look for:** `COPY . .` **before** the dependency-install `RUN`.
- **Why:** any source change invalidates the cache for dependency install, so every
  build reinstalls everything — slow CI.
- **Fix:** copy the manifest/lockfile first, install, *then* copy source:
  ```dockerfile
  COPY package.json package-lock.json ./
  RUN npm ci
  COPY . .
  ```

---

## Maintainability

### No HEALTHCHECK [Low]
- **Why:** orchestrators can't distinguish a live process from a wedged one.
- **Fix:** `HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost:8080/healthz || exit 1`
  (In Kubernetes, liveness/readiness probes often supersede this — note that rather
  than flagging hard.)

### No .dockerignore [Medium]
- **Why:** the whole context is sent to the daemon and risks landing in the image —
  slow builds, secret leakage, cache busting from irrelevant files.
- **Fix:** add `.dockerignore` with at least `.git`, `node_modules`, `*.env`,
  `__pycache__`, build output, CI files.

### ADD where COPY belongs [Low]
- **Why:** `ADD` auto-extracts archives and can fetch URLs — surprising behavior and
  a footgun.
- **Fix:** use `COPY` for local files; only use `ADD` when you intentionally want
  tar auto-extraction.

### Shell-form CMD/ENTRYPOINT [Low → Medium]
- **Look for:** `CMD npm start` (shell form) instead of `CMD ["npm","start"]`.
- **Why:** shell form wraps the process in `/bin/sh -c`, so `SIGTERM` hits the shell,
  not your app — graceful shutdown breaks.
- **Fix:** use exec form `["…"]`. Add a tiny init (`tini`) if you need signal/zombie
  reaping.

### Missing WORKDIR / unclear CMD vs ENTRYPOINT [Low]
- **Fix:** set an explicit `WORKDIR`; use `ENTRYPOINT` for the binary and `CMD` for
  default args when you want overridable arguments.
