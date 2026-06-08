---
name: dockerfile-audit
description: Use when reviewing a Dockerfile (or container build) for security, image size, reproducibility, and maintainability — runs as root? secrets baked into layers? unpinned base/deps? no multi-stage? missing .dockerignore/HEALTHCHECK? Produces a severity-ranked issue list with concrete fixes. Read-only: it audits and recommends, it does not modify the build.
---

# dockerfile-audit

A read-only review of a Dockerfile against four axes: **security**, **size**,
**reproducibility**, and **maintainability**. The goal is a severity-ranked list of
named issues, each with the concrete fix — not a vague "looks fine" or a wall of
nitpicks. The most expensive Dockerfile mistakes (secrets in layers, running as
root, `latest` everywhere) are invisible until they bite, so this skill checks for
them explicitly.

## When to use

- Reviewing a new or changed `Dockerfile` / `Containerfile`
- "Is this image safe / lean / reproducible?" before it ships to a registry
- Hardening an inherited image that "just works" but was never reviewed
- A build is bloated, slow to cache, or flagged by an image scanner and you want the
  *why* and the fix

**When *not* to use:** debugging a *running* container's runtime behavior (that's
ops triage), or authoring app code. This audits the build definition, statically.

## Operating rules

1. **Read-only.** Report issues and propose edits; don't rewrite the user's
   Dockerfile unless they ask. The deliverable is the findings list.
2. **Read the whole file plus its context.** Also check for a `.dockerignore`
   sitting beside it and skim the build context — a missing `.dockerignore` is one
   of the most common findings and isn't visible from the Dockerfile alone.
3. **Rank by severity, lead with the worst.** A baked-in secret outranks a missing
   `HEALTHCHECK`. Don't bury a critical under ten style nits.
4. **Every finding carries a fix.** Name the issue, why it matters, and the concrete
   change. No finding without a remedy.

## What to check

Walk the file once per axis. The full checklist with the exact "what to grep for"
and rationale per item is in `references/audit-checklist.md`; the high-signal items:

**Security**
- **Runs as root** — no `USER` directive, or `USER root` at the end. Containers
  should drop to a non-root UID. *Critical* for anything network-facing.
- **Secrets in layers** — `ARG`/`ENV` holding tokens/passwords, `COPY` of a creds
  file, `RUN curl -H "Authorization: …"`. Anything in a layer is extractable from
  the image forever, even if a later layer deletes it. Use BuildKit
  `RUN --mount=type=secret` instead.
- **Untrusted / unpinned base image** — `FROM image:latest` or a floating tag. Pin
  to a specific tag *and* ideally a digest (`@sha256:…`). Prefer minimal, trusted
  bases (distroless / `-slim` / `alpine` where the libc fits).
- **Over-broad `COPY . .`** — drags the whole context (including `.git`, `.env`,
  CI files) into the image. Copy only what's needed.

**Size**
- **No multi-stage build** — build tools, compilers, and dev dependencies shipped in
  the final image. Build in one stage, `COPY --from=build` only the artifact into a
  slim runtime stage.
- **Cache not cleaned in the same layer** — `apt-get install` without
  `rm -rf /var/lib/apt/lists/*` *in the same `RUN`*; package-manager caches left
  behind. Cleaning in a later layer doesn't shrink the image.
- **Many `RUN` layers** that could be one — each is a layer; chain related commands
  with `&&`.

**Reproducibility**
- **Unpinned dependencies** — `pip install requests`, `npm install` without a
  lockfile, `apt-get install foo` without a version. Builds drift over time. Pin
  versions / commit lockfiles / use `npm ci`.
- **`latest` anywhere** — base image, package, or tooling. A build that's
  reproducible today silently changes tomorrow.
- **Cache-busting layer order** — `COPY . .` *before* `RUN install deps` invalidates
  the dependency cache on every source change. Copy the manifest/lockfile and
  install deps *first*, then copy source.

**Maintainability**
- **No `HEALTHCHECK`** — orchestrators can't tell live from wedged.
- **No `.dockerignore`** — slow builds, fat context, accidental secret inclusion.
- **`ADD` where `COPY` belongs** — `ADD`'s URL-fetch / auto-extract behavior is a
  footgun; use `COPY` unless you specifically need extraction.
- **No `WORKDIR`** / unclear `CMD` vs `ENTRYPOINT` / shell-form `CMD` that breaks
  signal handling (use exec-form `["…"]` so `SIGTERM` reaches the process).

## Before / after

A worked example (insecure, bloated Dockerfile → audited and fixed, line by line) is
in `references/before-after.md`. Point to it when the user wants to see the fixes
applied, not just listed.

## Output template

Lead with a one-line verdict, then the ranked table, then the top fixes.

```
Verdict: <ship-blocker | needs work | minor polish> — <one line>

Findings (severity-ranked):
| # | Severity | Issue                          | Line(s) | Fix (short)                     |
|---|----------|--------------------------------|---------|---------------------------------|
| 1 | Critical | Secret baked via ARG token     | 4       | Use RUN --mount=type=secret     |
| 2 | High     | Runs as root (no USER)         | —       | Add non-root USER before CMD    |
| 3 | High     | FROM node:latest unpinned      | 1       | Pin node:20.11-slim@sha256:…    |
| 4 | Medium   | No multi-stage; build tools ship| 1–12   | Split build/runtime stages      |
| 5 | Low      | No HEALTHCHECK                 | —       | Add HEALTHCHECK CMD             |

Top fixes to make first: <#1, #2 — the ship-blockers>
Already good: <call out what's done right — be honest, not only critical>
```

Severity guide: **Critical** = secret exposure / remote-root risk; **High** =
root runtime, unpinned/untrusted base, no isolation of build deps; **Medium** =
reproducibility drift, avoidable bloat; **Low** = polish (HEALTHCHECK, labels,
exec-form CMD).
