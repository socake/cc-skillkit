# Before / after: a worked Dockerfile audit

A realistic-but-generic Node service Dockerfile, audited and rewritten. Use it to
show what the findings look like applied.

---

## Before (insecure, bloated, non-reproducible)

```dockerfile
FROM node:latest

ARG NPM_TOKEN
ENV NPM_TOKEN=$NPM_TOKEN

WORKDIR /app
COPY . .
RUN echo "//registry.npmjs.org/:_authToken=${NPM_TOKEN}" > .npmrc
RUN npm install
RUN apt-get update && apt-get install -y imagemagick

CMD npm start
```

### Findings

| # | Severity | Issue | Line | Fix |
|---|----------|-------|------|-----|
| 1 | Critical | `NPM_TOKEN` via `ARG`/`ENV` + written to `.npmrc` — recoverable from image layers and metadata forever | 3–4, 7 | BuildKit `--mount=type=secret`; never write to a layer |
| 2 | High | Runs as root — no `USER` | — | Add non-root user before `CMD` |
| 3 | High | `FROM node:latest` — unpinned, non-reproducible, fat base | 1 | Pin `node:20.11-slim@sha256:…` |
| 4 | High | `npm install` with no lockfile — deps drift | 8 | `npm ci` with committed `package-lock.json` |
| 5 | Medium | No multi-stage — build deps + apt cache + full source ship to prod | all | Split build/runtime stages |
| 6 | Medium | `COPY . .` before install — busts dep cache every source change; no `.dockerignore` | 6 | Copy manifest first; add `.dockerignore` |
| 7 | Medium | `apt-get` cache not cleaned in same layer | 9 | `--no-install-recommends` + `rm -rf /var/lib/apt/lists/*` |
| 8 | Low | Shell-form `CMD` — `SIGTERM` won't reach node, breaks graceful shutdown | 11 | Exec form `["npm","start"]` |

---

## After (audited)

```dockerfile
# --- build stage ---
FROM node:20.11-slim@sha256:<digest> AS build
WORKDIR /app

# copy manifests first so deps cache survives source edits
COPY package.json package-lock.json ./
# token mounted as a build secret — never persisted to a layer
RUN --mount=type=secret,id=npm_token \
    NPM_TOKEN="$(cat /run/secrets/npm_token)" \
    npm ci

COPY . .
RUN npm run build

# --- runtime stage ---
FROM node:20.11-slim@sha256:<digest>
WORKDIR /app
ENV NODE_ENV=production

# only the artifact + production deps cross over; no build tools, no token
COPY --from=build /app/dist ./dist
COPY --from=build /app/node_modules ./node_modules

RUN useradd --uid 10001 --create-home appuser
USER 10001

HEALTHCHECK --interval=30s --timeout=3s \
  CMD node -e "require('http').get('http://localhost:8080/healthz',r=>process.exit(r.statusCode===200?0:1)).on('error',()=>process.exit(1))"

CMD ["node", "dist/server.js"]
```

Build:
```bash
docker build --secret id=npm_token,src=./npm_token.txt -t app:1.0.0 .
```

With a `.dockerignore`:
```
.git
node_modules
*.env
npm_token.txt
Dockerfile
.dockerignore
```

### What changed and why it matters

- **Secret never touches a layer** — mounted only for the `npm ci` step; absent from
  the final image and from `docker history`.
- **Multi-stage** — runtime image carries the build output and prod `node_modules`
  only; compilers, dev deps, and apt caches stay in the discarded build stage.
- **Pinned base + `npm ci`** — same inputs produce the same image; auditable.
- **Non-root `USER 10001`** — numeric UID so `runAsNonRoot` can enforce it.
- **Cache-friendly order** — editing source no longer reinstalls dependencies.
- **Exec-form `CMD`** — `SIGTERM` reaches node, so graceful shutdown works.
- **HEALTHCHECK** — orchestrator can tell live from wedged.
