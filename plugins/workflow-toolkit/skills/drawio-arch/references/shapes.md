# Shape ↔ semantic mapping

**All-rectangles = a PowerPoint draft**, not an architecture diagram. Using shape to
carry meaning is what makes a diagram read as "engineering".

## Shape selection

| Semantic | Shape | draw.io style (copy as-is) |
|---|---|---|
| Person (user / developer) | actor | `shape=umlActor` |
| Folder / code repo | folder with tab | `shape=folder;tabWidth=100;tabHeight=22;tabPosition=left` |
| Script / tool | parallelogram | `shape=parallelogram;perimeter=parallelogramPerimeter` |
| **Hub / orchestration core** | hexagon | `shape=hexagon;perimeter=hexagonPerimeter2` |
| Storage / database / registry | cylinder | `shape=cylinder3;boundedLbl=1;backgroundOutline=1;size=12` |
| Cluster / cloud service | cloud | `shape=cloud` |
| Note / spec / sticky | dog-ear note | `shape=note;size=14` |
| Alert / reminder | callout bubble | `shape=callout;size=8` |
| Service mesh | ellipse | `ellipse` |
| Plain service / component | rectangle | `rounded=0` |
| Button / entry / user card | rounded rect | `rounded=1` |
| Document (Dockerfile / template) | document | `shape=document` |
| Message queue (alt to cylinder) | tape | `shape=tape` |

## Padding regions (subtract when computing height)

| Shape | Padding | Min content height (3 lines @ fontSize=12) |
|---|---|---|
| rectangle | 0 | 60 |
| folder | `tabHeight` (20–22) + spacingTop (10–14) | 80 |
| cylinder3 | `size` top and bottom (default 12) | 75 |
| cloud | ~15% inner edge | 85 |
| callout | pointer-tail `size` | 70 |
| note | dog-ear `size` | 65 |
| hexagon | ~20% width to the side points | needs ~40px more width than a rect |

Chinese/CJK at fontSize=12 is ~16px per line incl. leading; Latin similar.

## The "visual story" of shape combos

A good architecture diagram lets the reader **tell at a glance from shape alone**:
- who is a person (actor)
- what is code (folder)
- what is a script (parallelogram)
- what is a hub (hexagon, dark fill)
- what is data (cylinder)
- what runs in the cloud (cloud)
- what is an alert (callout, red)
- what is a note (note, faint)

Shape difference ≥ color difference, because color-blind readers and black-and-white
prints still read shape.

## Anti-patterns

- ✗ Every node `rounded=0`, distinguished only by color — flat, no hierarchy
- ✗ shadow+gradient on every node — visual noise that hides structure
- ✗ Stacking detailed cloud-vendor icons — the diagram becomes an illustration and
  the relationships disappear

## A worked example (generic layered architecture)

```
① Code layer:   folder × 3 (repo groups)
② CI layer:     hexagon (CI orchestrator) + document × 2 (template / Dockerfile) + note × 2 (lint / approval)
③ Artifact:     cylinder3 × 2 (registries)
④ GitOps:       parallelogram (deploy script) + folder (gitops repo, dark hub)
⑤ CD:           hexagon (CD controller, dark hub) + hexagon dashed (legacy, deprecated)
⑥ Runtime:      cloud × N (clusters)
⑦ Services:     rectangle × N (services) + cylinder × M (data stores) + cloud (sandbox) + dashed-rect (external LLM)
⑧ Users:        rounded=1 × 3 (user cards)
⑨ Platform:     hexagon (config center) + cylinder (middleware) + ellipse (mesh) + rect (observability) + callout (alerting)
```
