# Multi-color palette (alternative)

Two options. **Default is the clean Slate style in
[style-clean-slate.md](style-clean-slate.md)** — this multi-color palette is only for
when the user explicitly asks for something colorful / poster-like.

## Linear/Vercel style

### Base
- Node fill: white `#FFFFFF` or light gray `#F8FAFC`
- Node border: **2px** colored
- Hub nodes (1–3): **dark fill + white text + 3px border** as focal points
- Text: primary `#0F172A` (Slate 900), secondary `#64748B` (Slate 500)

### Semantic colors (node border / accent)

| Semantic | Color | HEX | Use |
|---|---|---|---|
| Core flow | Cyan 500 | `#06B6D4` | pipeline, services, deploy flow |
| User / entry | Indigo 500 | `#6366F1` | end users, internal users, gateway |
| Storage / artifact | Violet 500 | `#8B5CF6` | registries, databases, caches, queues |
| Platform / middleware | Amber 500 | `#F59E0B` | config center, mesh, observability, autoscaling |
| Cluster / cloud | Sky 500 | `#0EA5E9` | K8s cluster cloud nodes |
| Alert / risk | Rose 500 | `#F43F5E` | alert push, failure paths |
| Auxiliary / deprecated | Slate 400 | `#94A3B8` | deprecated/secondary, with `dashed=1` |

### Hub node coloring (dark)
- Fill: `#0F172A` (Slate 900)
- Border: its semantic color (e.g. flow hub = Cyan 500)
- Text: `#FFFFFF`
- Heavy border: `strokeWidth=3`

### Per-layer visuals
- A 4–12px colored binding stripe on each layer's left (the layer's main color)
- Layer name in that color one shade darker (600–700), bold, 13–14px

## Tailwind-scale style (backup)

For vivid poster-like diagrams.

| Semantic | fill 100 | stroke 600 | dark fill (hubs) |
|---|---|---|---|
| User / entry | `#E0E7FF` | `#4F46E5` | `#3730A3` |
| Core flow | `#D1FAE5` | `#059669` | `#047857` |
| Platform / middleware | `#FEF3C7` | `#D97706` | `#B45309` |
| Artifact / storage | `#EDE9FE` | `#7C3AED` | `#6D28D9` |
| Cluster / sandbox | `#E0F2FE` / `#FDE68A` | `#0284C7` / `#B45309` | — |
| Alert | `#FFE4E6` | `#E11D48` | `#BE123C` |
| Deprecated / aux | `#F1F5F9` | `#64748B` | — |

Scale encodes importance:
- 100 = normal
- 200 + 1.5 border = important
- 300 + 2.5 border = core
- 400 + 3 border = hub

## Edge coloring

| Situation | Color | strokeWidth | Style |
|---|---|---|---|
| Main trunk | semantic color, one shade darker | 3–4 | solid + bold + `fontStyle=1` |
| Plain sync call | Cyan `#06B6D4` | 2 | solid |
| Async message | Amber `#F59E0B` | 2 | `dashed=1` |
| Data read/write | Violet `#8B5CF6` | 1.5 | solid, label "R/W" / "cache" / "pub/sub" |
| External dependency | Violet light `#A855F7` | 2 | `dashed=1` |
| Monitoring scrape | Amber | 1 | `dashPattern=1 4` (dotted) |
| Alert / risk | Rose `#F43F5E` | 2.5 | `dashed=1` + `fontStyle=1` |
| Deprecated path | Slate 400 `#94A3B8` | 1 | `dashed=1`, gray text |

## Usage notes

- **Edge labels need a white background** `labelBackgroundColor=#FFFFFF`, else the
  line cuts the text.
- Trunk labels bold (`fontStyle=1`).
- Label every edge with a semantic (HTTP / queue / HTTPS / tool call / R/W / sync /
  pub-sub) — never an unlabeled arrow.

## Multi-class overview coloring (≥4 object classes in one diagram)

When 4–6 object classes appear together, be even more restrained or the visuals
explode.

1. **Don't flood whole cards — use "3px left stripe + title chip".** The node body
   stays white + light-gray border; category color only on the left stripe + type
   chip.
2. **Category color at the ~600 shade** (saturated but not harsh) on white. Avoid
   pale 200 fills.
3. **Safety/alert classes use a ⚠️ icon + red chip**, not a red wash.

| Class | stripe+chip | HEX |
|---|---|---|
| Primary (journeys) | Blue 600 | `#0969da` |
| Invariant | Red 600 | `#d1242f` |
| Ops action | Orange 600 | `#bc4c00` |
| Cross-cutting dependency | Purple 600 | `#8250df` |
| Reference | Gray 500 | `#6e7781` |

When the whole diagram is on a light background, these five give enough contrast —
don't also add dark hub nodes (they'd dominate); use a heavier border (2.5px) + bold
title to mean "important".
