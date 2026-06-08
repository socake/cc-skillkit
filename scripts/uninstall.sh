#!/usr/bin/env bash
#
# Remove cc-skillkit from Claude Code on the current machine.
# Uninstalls every plugin declared in the manifest, then drops the marketplace.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MANIFEST="$ROOT/.claude-plugin/marketplace.json"

command -v claude >/dev/null 2>&1 || { echo "✗ 'claude' CLI not found." >&2; exit 1; }
command -v jq     >/dev/null 2>&1 || { echo "✗ 'jq' not found." >&2; exit 1; }

MARKETPLACE="$(jq -r '.name' "$MANIFEST")"

jq -r '.plugins[].name' "$MANIFEST" | while read -r plugin; do
  [ -n "$plugin" ] || continue
  echo "→ uninstalling $plugin"
  claude plugin uninstall "$plugin" 2>/dev/null || echo "  (not installed)"
done

echo "→ removing marketplace $MARKETPLACE"
claude plugin marketplace remove "$MARKETPLACE" 2>/dev/null || echo "  (not registered)"

echo "✓ removed."
