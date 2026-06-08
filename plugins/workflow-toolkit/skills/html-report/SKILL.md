---
name: html-report
description: Use when you need to turn a long markdown report, design doc, research writeup, or blueprint into a polished, shareable single-file HTML onepager — light Linear/Notion style, card grid + tables + collapsible details library + top filter chips, no external CSS/JS. Triggers like "make an HTML version", "a web page I can show", "a browser-friendly report", "visualize this doc".
---

# html-report

Render a long markdown report into a single, self-contained HTML onepager that a
reader can actually skim. The job is not to dump markdown into `<p>` tags — it's
to give the content *structure*: a scannable hero, card grids and tables for the
substance, and a collapsible, filterable appendix for the long tail. Light theme
by default, no framework dependency, one `.html` file you can open or host.

## When to use

- A markdown report/design doc/blueprint that's too long to read top-to-bottom and
  you want a presentable web view.
- Content with many sub-items (failure modes, findings, checklist entries) that
  needs to be browsable, not an endless wall of text.
- Anything you'd "send someone a link to" rather than paste raw markdown.

**When *not* to use:** a short note (just send the markdown); something that needs
live data or interactivity beyond filtering (build a real app); a slide deck.

## Core principles

1. **Light by default, never dark.** Dark backgrounds tire the eyes over a long
   read. Use a modern light theme (Linear/Notion): off-white page, white cards,
   near-black text — *not* washed-out Material, *not* a Tailwind rainbow.
2. **Single self-contained file.** All CSS/JS inlined, no CDN, no build step. A few
   hundred KB with ~70 collapsed sub-items stays smooth in the browser.
3. **Body large, detail folded.** The main objects (card grid, key table) carry the
   visual weight; fine detail (evidence, per-item breakdowns) collapses into a
   `<details>` appendix reached by anchors + filter chips.
4. **No "v1 was wrong, v2 fixes it" narrative.** Present the current state. The
   reader doesn't care how an earlier draft was wrong, only how to use this one.
5. **Restrained emoji.** One or two only for genuine warnings/red lines, never as
   decoration.

## Six-step workflow

### Step 1 — Information architecture

List the section order *before* writing HTML:

```
1. Hero        · title + one-line positioning + 4–5 headline stat chips
2. Overview    · the object classes / a matrix / a distribution — visible above the fold
3. Method / key definitions (if applicable)
4. Main body   · largest section — card grid and/or tables
5..N. Per-category detail
N+1. Roadmap / timeline
N+2. Key findings + next steps
last. Appendix · collapsible detail library + mapping tables
```

Main cards default **open**; detail items default **collapsed**.

### Step 2 — Palette & type

See [references/palette.md](references/palette.md) for the full CSS-variable set.
Baseline: off-white page (not pure white — pure white glares), white cards with a
light border, near-black primary text + muted secondary, soft hover shadow, 8–12px
radius, system font stack, line-height 1.6–1.7, generous section spacing, zebra
table rows.

### Step 3 — Pick the body component

| Situation | Use |
|---|---|
| 5–15 core objects (journeys, customers, indicators…) | **card grid** (CSS grid, 3–4 cols) |
| 5–10 rows of structured attributes | **table** (zebra rows, tight padding) |
| Overview of several object classes | **large color-coded cards** (one per class, in the hero area) |
| Comparison / ratios | **pure-CSS bar chart** (don't pull in chart.js) |
| Index into long detail | **`<details>` + anchor jump + top filter chips** |

Avoid: plain bullet lists (use cards/tables); pure SVG (poor accessibility);
external chart libraries.

### Step 4 — Collapsible detail library (the key technique)

When the source has 50+ sub-items, do **not** lay them all flat (the page becomes
unreadably long). Wrap each in `<details>` with an id, tags, and data-attributes:

```html
<details class="fm-item" id="item-a3" data-priority="p0" data-status="blind">
  <summary>
    <span class="fm-id">A.3</span>
    <span class="fm-title">First message delivered to the worker</span>
    <span class="fm-tags">
      <span class="badge p0">P0</span>
      <span class="badge blind">blind spot</span>
    </span>
  </summary>
  <div class="fm-body">
    <div class="fm-section"><strong>Belongs to</strong>: Journey-3</div>
    <div class="fm-section"><strong>Path</strong>: <code>handler:455</code> → …</div>
  </div>
</details>
```

Make anchored jumps auto-expand, either with CSS `:target` highlighting or one line
of JS that sets `open = true` on the linked `<details>`. (Both shown in
[references/components.md](references/components.md).)

### Step 5 — Top filter chips

For a 50+ item library, add chips that hide non-matching `<details>`:

```html
<div class="fm-filter sticky">
  <button class="chip active" data-filter="all">All (72)</button>
  <button class="chip" data-filter="p0">P0 (44)</button>
  <button class="chip" data-filter="blind">Blind spot (8)</button>
</div>
```

~30 lines of JS toggles a `hide-by-filter` class on each `.fm-item`; also hide any
section whose children are all filtered out. Full snippet in components.md.

### Step 6 — Deliver

1. Save as a single self-contained `.html` (e.g. `<name>.html` in your reports dir).
2. Open it locally to eyeball it, and optionally host it for a shareable link
   (any static host / file server works — the file has no external dependencies).
3. Give the reader: the link (if hosted) + the local path + a one-line description.
4. **Do not paste the full HTML into chat** for large files — it blows up context.

## Common pitfalls

1. **Dark background tires the eyes** — default to light; switch instantly if the
   user says it's "too dark" or "hard on the eyes after a while".
2. **All sub-items expanded → the page explodes** — 50+ flat items means scrolling
   forever. Always `<details>`-collapse them.
3. **"v1 was wrong" narrative eats space** — the reader only wants the current
   version. Drop the before/after apology.
4. **Emoji pileup** — five icons in a row reads like kindergarten stickers. One, for
   real warnings only.
5. **>500KB file stalls the browser** — ~300KB (≈70 inlined sub-items) is the
   ceiling. Past that, split sections or lazy-load.
6. **Markdown-to-HTML with no semantics** — don't emit `<p>title</p><p>body</p>`.
   Use `<section>`, `<article>` for cards, `<details>` for detail, `<button>` for
   filters.

## References

- [references/palette.md](references/palette.md) — light-theme CSS variables +
  category-color usage.
- [references/components.md](references/components.md) — copy-paste hero / card /
  table / details / chip / bar-chart components with CSS + JS.
- [references/template.html](references/template.html) — minimal self-contained
  skeleton to fork.
