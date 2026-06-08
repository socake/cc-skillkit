#!/usr/bin/env python3
"""Validate cc-skillkit structure. Runs locally and in CI — no third-party deps.

Checks:
  1. marketplace.json and every plugin.json are valid JSON with required fields.
  2. Each plugin entry's version matches its plugin.json version.
  3. Every skill has a SKILL.md with frontmatter containing `name` + `description`.
  4. Skill `name` is kebab-case and equals its folder name.
  5. `description` is a single non-empty line within the length budget.

Exit non-zero on any failure, printing every problem found.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DESC_MAX = 500

errors: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def load_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        err(f"missing file: {path.relative_to(ROOT)}")
    except json.JSONDecodeError as e:
        err(f"invalid JSON in {path.relative_to(ROOT)}: {e}")
    return None


def parse_frontmatter(path: Path) -> dict[str, str] | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        err(f"{path.relative_to(ROOT)}: missing YAML frontmatter (must start with '---')")
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        err(f"{path.relative_to(ROOT)}: unterminated frontmatter")
        return None
    fm: dict[str, str] = {}
    for line in parts[1].strip().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        fm[key.strip()] = val.strip()
    return fm


def main() -> int:
    market = load_json(ROOT / ".claude-plugin" / "marketplace.json")
    if market is None:
        return fail()

    if not market.get("name"):
        err("marketplace.json: missing 'name'")
    plugins = market.get("plugins", [])
    if not isinstance(plugins, list) or not plugins:
        err("marketplace.json: 'plugins' must be a non-empty array")
        return fail()

    for entry in plugins:
        name = entry.get("name", "<unnamed>")
        if not entry.get("description"):
            err(f"marketplace.json: plugin '{name}' missing description")
        src = entry.get("source", "")
        # source may be a relative path string or an object; only path strings are local
        plugin_dir = ROOT / src if isinstance(src, str) and src.startswith("./") else None
        if plugin_dir is None:
            continue
        manifest = load_json(plugin_dir / ".claude-plugin" / "plugin.json")
        if manifest is None:
            continue
        if manifest.get("name") != name:
            err(f"plugin '{name}': plugin.json name '{manifest.get('name')}' != marketplace entry")
        mv, pv = entry.get("version"), manifest.get("version")
        if mv != pv:
            err(f"plugin '{name}': version mismatch (marketplace {mv} != plugin.json {pv})")

        validate_skills(plugin_dir, name)

    return fail() if errors else ok()


def validate_skills(plugin_dir: Path, plugin_name: str) -> None:
    skills_dir = plugin_dir / "skills"
    if not skills_dir.is_dir():
        return
    found = False
    for skill in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
        found = True
        md = skill / "SKILL.md"
        if not md.exists():
            err(f"skill '{skill.name}': missing SKILL.md")
            continue
        fm = parse_frontmatter(md)
        if fm is None:
            continue
        nm = fm.get("name", "")
        desc = fm.get("description", "")
        if not nm:
            err(f"{md.relative_to(ROOT)}: frontmatter missing 'name'")
        elif nm != skill.name:
            err(f"{md.relative_to(ROOT)}: name '{nm}' != folder '{skill.name}'")
        elif not KEBAB.match(nm):
            err(f"{md.relative_to(ROOT)}: name '{nm}' is not kebab-case")
        if not desc:
            err(f"{md.relative_to(ROOT)}: frontmatter missing 'description'")
        elif len(desc) > DESC_MAX:
            err(f"{md.relative_to(ROOT)}: description {len(desc)} chars > {DESC_MAX} budget")
    if not found:
        err(f"plugin '{plugin_name}': no skills found under skills/")


def fail() -> int:
    print(f"✗ validation failed — {len(errors)} problem(s):", file=sys.stderr)
    for e in errors:
        print(f"  - {e}", file=sys.stderr)
    return 1


def ok() -> int:
    print("✓ cc-skillkit valid: manifests, naming, frontmatter, and versions all check out.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
