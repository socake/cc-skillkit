#!/usr/bin/env bash
#
# Scaffold a new, spec-compliant skill.
#
#   ./scripts/new-skill.sh <skill-name> [plugin-name]
#
# Defaults plugin-name to "ops-toolkit". Enforces kebab-case naming and
# writes a SKILL.md with valid frontmatter so CI passes out of the box.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

NAME="${1:-}"
PLUGIN="${2:-ops-toolkit}"

[ -n "$NAME" ] || { echo "usage: $0 <skill-name> [plugin-name]" >&2; exit 1; }
[[ "$NAME" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]] || { echo "✗ skill name must be kebab-case (e.g. helm-values-review)" >&2; exit 1; }

PLUGIN_DIR="$ROOT/plugins/$PLUGIN"
[ -d "$PLUGIN_DIR" ] || { echo "✗ plugin '$PLUGIN' not found at $PLUGIN_DIR" >&2; exit 1; }

SKILL_DIR="$PLUGIN_DIR/skills/$NAME"
[ -e "$SKILL_DIR" ] && { echo "✗ skill already exists: $SKILL_DIR" >&2; exit 1; }

mkdir -p "$SKILL_DIR"
cat > "$SKILL_DIR/SKILL.md" <<EOF
---
name: $NAME
description: One sentence — when Claude should reach for this skill and what it does. Lead with the trigger so dispatch is accurate.
---

# $NAME

## When to use

Describe the concrete trigger conditions. Be specific so the skill fires at
the right time and stays quiet otherwise.

## Steps

1. First do this.
2. Then this.
3. Report the conclusion, not the raw dump.

## Notes

- Keep it vendor-neutral and secret-free.
EOF

echo "✓ created $SKILL_DIR/SKILL.md"
echo "  edit it, then run ./scripts/install.sh (or restart the session) to load."
