# Design notes

Why this repo is shaped the way it is. Short, opinionated, and meant to show the
reasoning — not just the result.

## Goal

A personal skill library that is (1) **portable** across any machine I sit at, and
(2) **shareable** as a clean piece of work. Those two goals drive every decision
below.

## Decision 1 — Plugin marketplace, not loose skills

Claude Code can load skills three ways: a global `~/.claude/skills/` directory,
symlinks into it, or an installable **plugin marketplace**. I chose the marketplace.

| Approach | Portable to a new box | Versioned | One-command lifecycle | Shareable as a product |
|----------|:---:|:---:|:---:|:---:|
| `~/.claude/skills/` files | ✗ (manual copy) | ✗ | ✗ | ✗ |
| symlinks into that dir | ✗ (path-bound) | ✗ | ✗ | ✗ |
| **plugin marketplace** | ✓ | ✓ | ✓ | ✓ |

The marketplace is the only option where `marketplace add USER/repo` reconstructs
everything on a fresh machine with no local state. That single property is worth
the extra manifest files.

## Decision 2 — One marketplace, plugins as the grouping unit

The repo root is the *marketplace*; `plugins/<name>/` are the installable units.
This lets the library grow into multiple themed plugins (`ops-toolkit`,
later maybe `data-toolkit`, `writing-toolkit`) that users install independently,
without splitting into multiple repos. Skills are the leaves; plugins are how you
ship a coherent set.

## Decision 3 — Portability has no absolute paths

`marketplace.json` references plugins by **relative** path (`./plugins/ops-toolkit`),
and `install.sh` resolves the repo root from its own location. Nothing assumes a
home directory or a checkout location. The same scripts run from `~/projects`,
`~/code`, or a CI runner. Remote install (`CC_SKILLKIT_SOURCE=USER/repo`) skips the
checkout entirely.

## Decision 4 — Progressive disclosure inside skills

A `SKILL.md` is always in context once the skill triggers, so it stays lean — the
trigger, the operating rules, the decision order. Heavy material (per-symptom
command catalogs) lives in `references/*.md`, which the model opens only when
relevant. This keeps token cost low and dispatch sharp. `k8s-triage` is the worked
example: ~1 screen of `SKILL.md`, with the long playbooks one level down.

## Decision 5 — Public means vendor-neutral

The library distills real operational experience, but the repo is public, so every
skill is abstracted to be useful to anyone and carries no internal names, hosts,
secrets, or recognizable incidents. The interesting, hard-won lessons survive as
*general* guidance (e.g. "`Pending` is usually unschedulable, not out of capacity")
— which is also what makes them more broadly valuable.

## Decision 6 — CI as a quality gate

`validate.yml` runs on every push: valid JSON manifests, `kebab-case` names that
match folder names, required frontmatter present, and version agreement between
each plugin's `plugin.json` and its marketplace entry. A red build blocks merge.
The gate keeps the library trustworthy as it grows and signals that the project is
maintained, not abandoned.

## Non-goals

- Not a general framework or runtime — it leans entirely on Claude Code's native
  plugin mechanism.
- Not a kitchen-sink mega-collection — quality and coherence over count.
- No cloud services, no daemons. Plain files, the `claude` CLI, and CI.
