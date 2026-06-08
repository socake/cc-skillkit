# CLAUDE.md — cc-skillkit development guide

Project-level guidance for working **inside this repository**. This is a kit of
Claude Code skills packaged as an installable plugin marketplace. When you (the
assistant) are helping develop skills here, follow these rules.

## What this repo is

- A **Claude Code plugin marketplace**. `/.claude-plugin/marketplace.json` is the
  entry point; it lists plugins under `plugins/`.
- Each plugin (`plugins/<name>/`) has `.claude-plugin/plugin.json` and a `skills/`
  directory. Each skill is a folder with a `SKILL.md`.
- Designed to be **portable**: install on any machine via the official CLI, with no
  clone required (`CC_SKILLKIT_SOURCE=USER/cc-skillkit ./scripts/install.sh`).

## Hard rules — non-negotiable

1. **Vendor-neutral and secret-free.** This repo is public. Never commit: company
   names, internal hostnames, cluster/context names, IPs, tokens, employee names,
   internal URLs, or any product-specific detail. Skills must read as generally
   useful to *anyone*. Real operational lessons are welcome — but **abstracted**,
   never as a recognizable internal incident.
2. **Skills are read-only-first where they touch infrastructure.** A triage/review
   skill proposes actions; it does not mutate state as a diagnostic step.
3. **Spec compliance is enforced by CI.** `.github/workflows/validate.yml` must pass.
   Don't merge red.

## Skill authoring conventions

- **Naming:** skill folder and `name:` are `kebab-case`, matching exactly. One skill
  per folder.
- **Frontmatter:** every `SKILL.md` starts with YAML frontmatter containing exactly
  `name` and `description` (no extra required keys).
  - `description` must **lead with the trigger** ("Use when …") so dispatch is
    accurate, then say what the skill does. Keep it under ~500 chars, single line.
- **Body shape:** `# <name>` → `## When to use` (concrete triggers, and when *not*
  to fire) → the actual procedure → an output/wrap-up convention.
- **Progressive disclosure:** keep `SKILL.md` lean. Push long checklists, command
  catalogs, and per-case detail into `references/*.md` and point to them. The model
  opens references on demand — don't front-load everything.
- **Self-contained:** no reliance on the author's machine, private network, or
  unstated tools. If a skill needs a script, ship it in the skill folder.
- **Voice:** imperative, specific, evidence-first. Prefer "run X, read line Y" over
  vague advice. Conclusions over dumps.

## Adding a skill

```bash
./scripts/new-skill.sh <skill-name> [plugin-name]   # default plugin: ops-toolkit
```

This scaffolds a compliant `SKILL.md`. Edit it, then:

```bash
./scripts/install.sh        # register marketplace + (re)install plugins
# restart Claude Code / start a new session to load
claude plugin list          # verify
```

## Testing a change

- Validate structure the way CI does (frontmatter present, names match, JSON valid).
- Manually exercise the skill: start a session, give it a prompt that should trigger
  the skill, confirm it activates and behaves.
- `claude plugin details <plugin>` shows the component inventory and token cost — use
  it to keep skills lean.

## Versioning & release

- Bump `version` in both `marketplace.json` (plugin entry) and the plugin's
  `plugin.json` together; CI checks they agree.
- Tag releases with `claude plugin tag` (creates `<name>--v<version>` and validates
  the manifests agree).
- Commit messages: imperative mood, scoped (`ops-toolkit: add helm-values-review`).

## Layout

```
.claude-plugin/marketplace.json   marketplace entry (lists plugins)
plugins/<plugin>/
  .claude-plugin/plugin.json      plugin manifest
  skills/<skill>/SKILL.md         a skill (+ optional references/, scripts/)
scripts/                          install / uninstall / new-skill
.github/workflows/validate.yml    CI: schema + naming + frontmatter checks
docs/                             design notes
```
