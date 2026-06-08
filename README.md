# cc-skillkit

> A personal, portable kit of **Claude Code skills** — DevOps & SRE workflows
> packaged as an installable plugin marketplace. Install on any machine in one
> command, no clone required.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin%20marketplace-d97757)](https://code.claude.com/docs/en/plugin-marketplaces)
[![Validate](https://github.com/socake/cc-skillkit/actions/workflows/validate.yml/badge.svg)](https://github.com/socake/cc-skillkit/actions/workflows/validate.yml)

Skills are folders of instructions that Claude Code loads on demand to do
specialized tasks in a repeatable way. This repo packages mine as a proper
**plugin marketplace** so they're versioned, CI-validated, and portable across
machines — not a pile of symlinks tied to one laptop.

## Install

On any machine with [Claude Code](https://code.claude.com) installed — **no clone
needed**:

```bash
claude plugin marketplace add socake/cc-skillkit
claude plugin install ops-toolkit@cc-skillkit
# restart Claude Code, then:  claude plugin list
```

Or, working from a local checkout (for development):

```bash
git clone https://github.com/socake/cc-skillkit.git
cd cc-skillkit
./scripts/install.sh        # idempotent; registers the marketplace by path
```

Remove everything with `./scripts/uninstall.sh`.

## Skills

| Plugin | Skill | What it does |
|--------|-------|--------------|
| `ops-toolkit` | [`k8s-triage`](plugins/ops-toolkit/skills/k8s-triage/SKILL.md) | Read-only, evidence-first triage of an unhealthy Kubernetes workload (CrashLoop / Pending / OOM / ImagePull / stuck rollout / post-deploy 5xx). Drives a fixed order and reports a *named root cause*, not a log dump. |
| `ops-toolkit` | [`incident-rca`](plugins/ops-toolkit/skills/incident-rca/SKILL.md) | Methodical root-cause analysis for an incident/outage/regression: reconstruct the timeline, correlate with changes, test hypotheses in parallel with evidence discipline, and produce a root-cause card or blameless postmortem. |

_More skills are added over time — each one vendor-neutral and secret-free._

## Add your own skill

```bash
./scripts/new-skill.sh my-skill            # scaffolds a spec-compliant SKILL.md
$EDITOR plugins/ops-toolkit/skills/my-skill/SKILL.md
./scripts/install.sh                        # reload
```

Authoring conventions live in [`CLAUDE.md`](CLAUDE.md); CI enforces them.

## Why a marketplace (not symlinks)?

- **Portable** — `marketplace add socake/cc-skillkit` works on a fresh box with
  zero local state. No absolute paths baked in.
- **Versioned & validated** — plugins carry semver; [CI](.github/workflows/validate.yml)
  checks every `SKILL.md`'s frontmatter, naming, and manifest consistency on each push.
- **One-command lifecycle** — install / update / uninstall / enable / disable via
  the official `claude plugin` CLI.

Design notes and trade-offs: [`docs/design.md`](docs/design.md).

## Repository layout

```
.claude-plugin/marketplace.json   marketplace entry (lists plugins)
plugins/<plugin>/
  .claude-plugin/plugin.json      plugin manifest
  skills/<skill>/SKILL.md         a skill (+ optional references/)
scripts/                          install · uninstall · new-skill
.github/workflows/validate.yml    CI
CLAUDE.md                         authoring guide
```

## License

[MIT](LICENSE) © Wenzhuo Huang
