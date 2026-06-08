# Clean Slate style (default)

The default look for new diagrams unless the user asks for something else. Most
"ugly" diagrams come from multi-color binding stripes + dark title bars + 3–4px
strokes — this style is the correction.

## One-line DNA

**A single slate gray scale + one accent (indigo) + ≤3 dark hub nodes + thin strokes
+ very-light container groups.** Restrained to the extreme; it wins on whitespace and
hierarchy, not color.

## Why it looks good (6 rules)

1. **One palette + one accent.** The whole diagram uses only the slate gray scale
   (borders/text in different grays) + **one** indigo `#4F46E5` for the main flow /
   active node. Don't recolor every layer.
2. **≤3 dark hubs.** Give dark slate `#1E293B` + white text only to the 2–3 most
   central nodes, to create focal points; everything else is a white card. Too many
   dark blocks looks dirty.
3. **Thin strokes.** Node border `strokeWidth=1.5`, main-flow arrow `2`, secondary
   arrow `1.5`. No 3–4px strokes.
4. **Group with "very-light fill + very-faint border + top-left text label".** A
   subsystem box is `fillColor=#F8FAFC` + `strokeColor=#E2E8F0` with a **plain-text
   label** top-left (11px bold gray). No colored stripes, no dark title bars — let
   the white cards inside float.
5. **Uniform rounding, no shadows.** Nodes `arcSize=12`, containers `arcSize=8`,
   global `shadow=0`.
6. **Straight arrows + white-background labels.** Use precise `exitX/entryX` anchors
   so lines run straight; every label gets `labelBackgroundColor=#FFFFFF`.

## Palette (copy, don't invent)

| Use | Hex | Notes |
|---|---|---|
| Canvas / card fill | `#FFFFFF` | most nodes are white |
| Container group fill | `#F8FAFC` | subsystem box, a touch off-white |
| Dark hub fill | `#1E293B` | only ≤3 core nodes, with white text |
| Hub border | `#0F172A` | dark slate |
| Default node border | `#CBD5E1` | slate-300, most common |
| Container / weak border | `#E2E8F0` | slate-200, fainter |
| **Accent (main flow / active node)** | `#4F46E5` | indigo, the only color, use sparingly |
| Secondary arrow | `#94A3B8` | slate-400 |
| Title text | `#0F172A` | darkest |
| Body / secondary text | `#64748B` | slate-500 |
| Muted text | `#475569` / `#94A3B8` | annotations, optionals |

## Paste-ready style strings

**Four node tiers:**
```
# Hub (dark, ≤3 total) — remember fontColor=#FFFFFF
rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#1E293B;strokeColor=#0F172A;strokeWidth=1.5;fontSize=13;fontColor=#FFFFFF;align=center;verticalAlign=middle;

# Active / on-the-main-flow (white + indigo border)
rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#4F46E5;strokeWidth=1.5;fontSize=13;align=center;verticalAlign=middle;

# Normal node (white + slate border) — default
rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#CBD5E1;strokeWidth=1.5;fontSize=13;align=center;verticalAlign=middle;

# Optional / placeholder (dashed, faint)
rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#E2E8F0;strokeWidth=1;fontSize=11;fontColor=#475569;align=center;verticalAlign=middle;dashed=1;
```

**Container group + its label:**
```
# Subsystem container (very-light fill, verticalAlign=top so content sits up, leaving room for the label)
rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#F8FAFC;strokeColor=#E2E8F0;strokeWidth=1.5;verticalAlign=top;align=left;

# Top-left plain-text label (e.g. "WORKER container · process boundary")
text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=11;fontStyle=1;fontColor=#64748B;
```

**Three arrow tiers:**
```
# Main flow (indigo, width 2) — set exit/entry anchors per direction
endArrow=classic;html=1;strokeColor=#4F46E5;strokeWidth=2;endFill=1;endSize=8;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;

# Secondary connection (slate, width 1.5)
endArrow=classic;html=1;strokeColor=#94A3B8;strokeWidth=1.5;endFill=1;endSize=6;

# Async / return (dashed + curved)
endArrow=classic;html=1;strokeColor=#94A3B8;strokeWidth=1.5;endFill=1;endSize=6;dashed=1;curved=1;labelBackgroundColor=#F8FAFC;fontSize=10;fontColor=#64748B;

# Add a label to any arrow: append ↓
labelBackgroundColor=#FFFFFF;fontSize=10;fontColor=#64748B;
# Main-flow label in bold indigo: fontColor=#4F46E5;fontStyle=1;
```

## Type scale

| Element | fontSize | Color / style |
|---|---|---|
| Title | 26 bold | `#0F172A` |
| Subtitle (one-line path summary under the title) | 13 | `#64748B` |
| Container section label | 11 bold | `#64748B` |
| Node body | 13 (secondary 11–12) | black / hub white |
| Node sub-note | 11 | `#64748B` |
| Corner annotation | 10 italic | `#94A3B8` |

## Layout skeleton

- **Top-to-bottom main flow:** client → entry hub → dispatch → [container: core
  components in a row] → toolset → sandbox → storage/deploy.
- **Each subsystem = one `#F8FAFC` container**, white cards inside in a row, a text
  label top-left naming the layer.
- **One indigo line threads the main path top to bottom**; branches/returns are pale
  slate (including one dashed curved return channel).
- Lots of whitespace, grid-aligned; don't pack the boxes.

## Self-check (in addition to checklist.md)

- [ ] Is the only color indigo? More than one accent → cut.
- [ ] Are dark blocks ≤3? More → demote to white cards.
- [ ] Any stroke ≥3? → drop to 2/1.5.
- [ ] Any dark title bar / colored stripe? → replace with `#F8FAFC` container + text
      label.
- [ ] Overall reads "mostly white, restrained gray, one touch of indigo"? If not,
      not there yet.
