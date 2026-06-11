# cc-skillkit

**English** | [中文](README.zh-CN.md)

> A personal, portable kit of **Claude Code skills** — DevOps, SRE, cloud-governance
> and engineering-workflow skills packaged as installable plugins. Install on any
> machine in one command, no clone required.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin%20marketplace-d97757)](https://code.claude.com/docs/en/plugin-marketplaces)
[![Validate](https://github.com/socake/cc-skillkit/actions/workflows/validate.yml/badge.svg)](https://github.com/socake/cc-skillkit/actions/workflows/validate.yml)

**13 skills · 3 plugins · 1 command to install.** 🌐 [Landing page](https://socake.github.io/cc-skillkit/)

Skills are folders of instructions that Claude Code loads on demand to do
specialized tasks in a repeatable way. This repo packages mine as a proper
**plugin marketplace** so they're versioned, CI-validated, and portable across
machines — not a pile of symlinks tied to one laptop.

## Install

On any machine with [Claude Code](https://code.claude.com) installed — **no clone
needed**. Add the marketplace once, then install whichever toolkit you want:

```bash
claude plugin marketplace add socake/cc-skillkit

claude plugin install ops-toolkit@cc-skillkit       # K8s/EKS/ACK triage, RCA, Dockerfile audit
claude plugin install cloud-toolkit@cc-skillkit     # AWS cost scan, IAM/RAM audit
claude plugin install workflow-toolkit@cc-skillkit  # PR descriptions, ops sessions, diagrams, reports…
# restart Claude Code, then:  claude plugin list
```

Or from a local checkout (for development): `./scripts/install.sh`. Remove with
`./scripts/uninstall.sh`.

## Skills

### `ops-toolkit` — triage & review

| Skill | What it does |
|-------|--------------|
| [`k8s-triage`](plugins/ops-toolkit/skills/k8s-triage/SKILL.md) | Read-only, evidence-first triage of an unhealthy Kubernetes workload — fixed order, named root cause, not a log dump. |
| [`incident-rca`](plugins/ops-toolkit/skills/incident-rca/SKILL.md) | Methodical root-cause analysis: timeline, change correlation, parallel hypotheses under evidence discipline, root-cause card / postmortem. |
| [`eks-triage`](plugins/ops-toolkit/skills/eks-triage/SKILL.md) | EKS-specific triage: nodegroup won't join, VPC CNI CrashLoop, IRSA/IAM gaps, Karpenter not scaling, subnet IP exhaustion. |
| [`ack-triage`](plugins/ops-toolkit/skills/ack-triage/SKILL.md) | Aliyun ACK-specific triage: ECI image-pull timeouts, node pools, Terway CNI, CCM/SLB with no backends. |
| [`dockerfile-audit`](plugins/ops-toolkit/skills/dockerfile-audit/SKILL.md) | Audit a Dockerfile across security, size, reproducibility and maintainability — severity-ranked issues with fixes. |

### `cloud-toolkit` — cloud governance

| Skill | What it does |
|-------|--------------|
| [`aws-cost-scan`](plugins/cloud-toolkit/skills/aws-cost-scan/SKILL.md) | Read-only sweep for AWS waste — idle load balancers, unattached EIPs, orphan snapshots, over-provisioned pools — ranked by monthly savings. |
| [`ram-iam-audit`](plugins/cloud-toolkit/skills/ram-iam-audit/SKILL.md) | Least-privilege audit for AWS IAM + Aliyun RAM — wildcard actions, FullAccess sprawl, stale keys, privilege-escalation combos. |

### `workflow-toolkit` — engineering workflow & output

| Skill | What it does |
|-------|--------------|
| [`pr-describe`](plugins/workflow-toolkit/skills/pr-describe/SKILL.md) | Turn a diff into a clear, reviewer-friendly PR description — what/why/how, risks, testing, rollback, reviewer notes. |
| [`ops-session`](plugins/workflow-toolkit/skills/ops-session/SKILL.md) | A structured operational-session protocol — Plan→RootCause→Action→Verify→Learn, weak root causes hard-block writes, conclusions cite evidence. |
| [`task-kickoff`](plugins/workflow-toolkit/skills/task-kickoff/SKILL.md) | An opening protocol for complex, long tasks — plan/implement split, HITL gates, stop-loss after two failures, multi-round verification. |
| [`html-report`](plugins/workflow-toolkit/skills/html-report/SKILL.md) | Render a long markdown report into a polished, self-contained HTML onepager — cards, tables, collapsible sections, filter chips. |
| [`drawio-arch`](plugins/workflow-toolkit/skills/drawio-arch/SKILL.md) | End-to-end draw.io diagrams — architecture, flows, topology — rendered to PNG/SVG via the CLI, with a semantic style system. |
| [`browser-verify`](plugins/workflow-toolkit/skills/browser-verify/SKILL.md) | Containerized real-browser e2e verification over CDP — drive a click path, capture console/network, correlate with backend logs, return pass/fail. |

_Every skill is vendor-neutral and secret-free._

## Add your own skill

```bash
./scripts/new-skill.sh my-skill ops-toolkit   # scaffolds a spec-compliant SKILL.md
$EDITOR plugins/ops-toolkit/skills/my-skill/SKILL.md
./scripts/install.sh                            # reload
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
  skills/<skill>/SKILL.md         a skill (+ optional references/, assets/)
scripts/                          install · uninstall · new-skill · validate
site/                             GitHub Pages landing page
vendored/                         third-party skills (NOT my work; unregistered)
.github/workflows/                validate.yml (CI) · pages.yml (deploy)
CLAUDE.md                         authoring guide
```

## Vendored (third-party) skills

[`vendored/`](vendored/) holds third-party / community skills I carry for cross-machine reuse.
They are **not my work** and are **not part of the marketplace** — only the `plugins/` toolkits
are mine. See [`vendored/README.md`](vendored/README.md) for origins and attribution.

## License

[MIT](LICENSE) © Wenzhuo Huang
