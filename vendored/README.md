# Vendored skills (third-party)

> **Not my work.** This directory collects useful **third-party / community** Claude Code
> skills, copied in verbatim for personal cross-machine reuse. They are **not** authored by me
> and are **deliberately kept out of the marketplace** (`.claude-plugin/marketplace.json`) —
> the `plugins/` toolkits are my own work; this folder is not.

## Why it exists

cc-skillkit has two jobs: a curated portfolio of skills I wrote (`plugins/`), and a portable
kit I can pull onto any machine. This folder serves only the second job, for skills I didn't
write but want to carry around. Keeping them here — separate, labelled, and unregistered —
keeps the portfolio honest.

## Contents

| Skill | Source / origin | What it does |
|-------|-----------------|--------------|
| `stitch-design-taste` | Third-party community skill (installed via `npx skills`); targets [Google Stitch](https://labs.google/stitch) | Generates an agent-friendly `DESIGN.md` encoding a premium, anti-generic design system. |

## Using these

These are **not** installed by `claude plugin install ops-toolkit@cc-skillkit` (they aren't part
of any plugin). To use one, copy the folder into a project's `.claude/skills/` or your
`~/.claude/skills/`:

```bash
cp -r vendored/stitch-design-taste ~/.claude/skills/
```

If a skill here is available upstream via `npx skills`, prefer installing it from source so you
get updates and proper attribution.
