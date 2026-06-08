#!/usr/bin/env bash
#
# Install cc-skillkit into Claude Code on the current machine.
#
# Two modes, same command:
#   Local  (default): registers this checkout as a marketplace by path.
#   Remote (CI / fresh box, no clone needed):
#       CC_SKILLKIT_SOURCE=USERNAME/cc-skillkit ./scripts/install.sh
#
# Idempotent: safe to re-run; updates instead of failing if already present.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MANIFEST="$ROOT/.claude-plugin/marketplace.json"

command -v claude >/dev/null 2>&1 || { echo "✗ 'claude' CLI not found on PATH. Install Claude Code first." >&2; exit 1; }
command -v jq     >/dev/null 2>&1 || { echo "✗ 'jq' not found. Install jq (brew/apt install jq)." >&2; exit 1; }
[ -f "$MANIFEST" ] || { echo "✗ marketplace.json not found at $MANIFEST" >&2; exit 1; }

MARKETPLACE="$(jq -r '.name' "$MANIFEST")"
SOURCE="${CC_SKILLKIT_SOURCE:-$ROOT}"   # local path by default; export to a GitHub repo for clone-free install
SCOPE="${CC_SKILLKIT_SCOPE:-user}"      # user | project | local

echo "▶ marketplace : $MARKETPLACE"
echo "▶ source      : $SOURCE"
echo "▶ scope       : $SCOPE"
echo

# 1) Register (or refresh) the marketplace — idempotent.
if claude plugin marketplace add "$SOURCE" 2>/dev/null; then
  echo "✓ marketplace added"
else
  echo "• marketplace already known — updating"
  claude plugin marketplace update "$MARKETPLACE"
fi

# 2) Install every plugin declared in the manifest — idempotent.
jq -r '.plugins[].name' "$MANIFEST" | while read -r plugin; do
  [ -n "$plugin" ] || continue
  echo "→ installing $plugin@$MARKETPLACE"
  claude plugin install "$plugin@$MARKETPLACE" --scope "$SCOPE" 2>/dev/null \
    || claude plugin update "$plugin" \
    || echo "  (already installed)"
done

echo
echo "✓ done. Restart Claude Code (or start a new session) to load the skills."
echo "  Verify with:  claude plugin list"
