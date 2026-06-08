---
name: drawio-arch
description: Use when asked to draw an architecture diagram, flowchart, call/sequence path, deployment topology, troubleshooting SOP, or before/after comparison as a draw.io / diagrams.net diagram. Designs the layout first (six-segment plan), writes semantic XML, renders to PNG/SVG with the draw.io CLI, and self-reviews the rendered image — delivers files, never raw XML for the user to paste.
---

# drawio-arch

End-to-end diagram production with draw.io / diagrams.net. The rules below are a
distilled set that keeps diagrams from looking like PowerPoint sketches: design
before XML, give shapes semantic meaning, keep the palette restrained, aggregate
many-to-many edges onto buses, and **always self-review the rendered PNG** before
delivering. You deliver rendered files (`.drawio` + PNG + SVG), not XML.

## When to use

- Architecture diagrams (components + relationships)
- Call/sequence/request-path diagrams
- Flowcharts / runbooks / SOPs with branches or loops
- Deployment topology (region → VPC → cluster → namespace nesting)
- Before/after or option-A/option-B comparisons
- State machines

**When *not* to use:** a one-box doodle, or when the user explicitly wants raw XML
to hand-edit. This skill assumes the draw.io CLI toolchain is available (see
[Rendering](#step-5--render--self-review-mandatory)).

## Core principles (non-negotiable)

1. **Design first, XML second.** No six-segment plan ⇒ almost certain rework.
2. **Deliver rendered diagrams, not raw XML.** Use the toolchain.
3. **Read the rendered PNG yourself before delivering.** Skipping review ⇒ rework.
4. **Shapes carry semantics.** All-rectangles reads as a draft, not an architecture.
5. **Restrained palette (default clean Slate, see
   [references/style-clean-slate.md](references/style-clean-slate.md)).** Single
   slate gray scale + **one** accent (indigo) + ≤3 dark hub nodes + **thin strokes**
   (node 1.5, main arrow 2). **Forbidden:** multi-color binding stripes, dark title
   bars, 3–4px strokes — those three are the usual cause of ugly diagrams.
6. **Edge labels get a white background.** `labelBackgroundColor=#FFFFFF` is mandatory.
7. **Draw real relationships, not just box names.** An architecture diagram shows the
   actual call path (client → gateway → service → queue → worker → external API), not
   a pile of namespace labels with no edges.

## Six-step workflow

### Step 1 — Requirement analysis

Decide the diagram type, which drives layout:

- **Architecture** (components + relations) → vertical layering + a side/bottom bus
- **Call path** (request flow) → horizontal, left to right
- **Flowchart / SOP** (≥3 branch levels / loops / complex control flow) → vertical
  flow + diamond decisions
- **Simple decision tree** (≤2 branch levels, every leaf a definite end-state, no
  loops) → **horizontal tree + category labels + terminal pills, no diamonds**
- **Deployment topology** → nested group boxes (Region → VPC → AZ → Cluster → NS)
- **Comparison** (before/after, A/B) → left/right split columns
- **State machine** → state nodes + directed arrows
- **Multi-class overview** (≥4 object classes + cross-class links + roadmap) →
  **three columns + a full-width bottom band** (primary classes left / secondary
  middle / meta & distribution right / timeline below)

If information is missing, **don't ask more than one round** — make reasonable
assumptions from context and list them under an `[Assumptions]` block in the output.

### Step 2 — Design plan (six segments)

Output these six segments *before* touching XML:

```
[Type]       <architecture / call path / flow / comparison / topology / …>
[Layout]     <vertical layers / horizontal flow / swimlanes / nested groups>
[Core path]  A → B → C → D
[Layers]
  1. …
  2. …
[Emphasis]
  - …
[Assumptions]
  - …
```

### Step 3 — Palette

**Default: clean Slate** (see
[references/style-clean-slate.md](references/style-clean-slate.md)) — white cards +
slate borders + **one** indigo `#4F46E5` for the main flow/active node + ≤3 dark
slate `#1E293B` hubs. [references/palette.md](references/palette.md) is the older
multi-color alternative, only when the user explicitly wants something colorful.

### Step 4 — Write the XML

- Semantic node IDs (`backend` / `api_gateway` / `mcp_server`, not `n1` / `cell-a3f2`)
- Pick shapes by semantics (see [references/shapes.md](references/shapes.md))
- **Group subsystems in a very-light container** (`fillColor=#F8FAFC` +
  `strokeColor=#E2E8F0`) with a **plain-text top-left label** (11px bold gray). No
  colored stripes, no dark title bars — let the white cards inside float.
- **Title area stays light:** large title 26px `#0F172A` + subtitle 13px `#64748B`,
  no dark background.
- **Edge labels get a white background** (`labelBackgroundColor=#FFFFFF`).
- **Thin strokes:** node border `strokeWidth=1.5`, main-flow arrow `2` (indigo),
  secondary `1.5` (slate). No 3–4px strokes.
- **Many-to-many across 3+ layers → aggregate onto a "bus" node** (3×8 edges → 3+1).
- **Use exit/entry anchors** to pin edge endpoints and avoid lines cutting through
  node interiors.

### Step 5 — Render + self-review (mandatory)

```bash
# Fixed output location (adjust DIAG_DIR to your project)
DIAG_DIR="${DIAG_DIR:-$HOME/diagrams}"
mkdir -p "$DIAG_DIR"

# Export PNG (2x) and SVG from the .drawio source
xvfb-run -a drawio -x -f png --scale 2 -o "$DIAG_DIR/NAME.png"  "$DIAG_DIR/NAME.drawio"
xvfb-run -a drawio -x -f svg               -o "$DIAG_DIR/NAME.svg"  "$DIAG_DIR/NAME.drawio"
```

> Toolchain: the `drawio` CLI (drawio-desktop / diagrams.net desktop) plus `xvfb-run`
> for headless rendering on Linux. On a machine with a display you can drop
> `xvfb-run -a`.

Then **Read `$DIAG_DIR/NAME.png`** and visually check it against
[references/checklist.md](references/checklist.md):

- text overflowing a node → raise height or shorten text
- edge cutting through a node → add an anchor or reroute
- long diagonal across layers → switch to a bus
- large empty areas → re-lay-out
- missing legend → add it back

**Do at least two review rounds.** If a round finds ≥2 issues, iterate again.

### Step 6 — Deliver

Deliver the three artifacts (`.drawio` source + PNG + SVG) — e.g. by hosting them on
any file server for shareable links, or by attaching paths. Give the user the
links/paths + local path + a one-line note on what changed. **Don't paste XML.**

## Common pitfalls

### 1. Actor → many repos: edges cut through nodes
A user/developer actor on the left will route through middle nodes to reach several
targets on the right. **Fix:** drop the low-information actor node, or use waypoints
to route around the outside.

### 2. One hub fanning out to N clusters
A CD controller wired to 8 clusters ⇒ 8 crossing rays. **Fix:** a single thick bus
line from the hub down to the runtime layer, labeled "sync to all clusters".

### 3. Registry → cluster image-pull crossing layers
A registry-to-cluster dotted line crossing two layers. **Fix:** drop the line, add
text inside the registry node ("kubelet pulls in each cluster").

### 4. Node text overflowing the border
- `folder`: subtract tabHeight, then spacingTop
- `cylinder3`: subtract size top and bottom
- `callout`: subtract the pointer-tail size
- `note`: subtract the dog-ear size
- 3 lines at fontSize=12: min rectangle height ≈ 60, folder ≈ 80, cylinder3 ≈ 75

### 5. A note box that won't fit its content
Either give it enough room (8 lines ≈ 180 high), compress to a 1–2 line strip, or
delete it and express via an edge label.

### 6. A services layer with only namespace names and no real calls
That's an "imaginary diagram". A real architecture diagram shows:
- entry: gateway / route
- main calls: client → gateway → backend → (queue) → dispatcher → (queue) → worker
  → ai-gateway → external LLM
- tool calls: worker → mcp-gateway → MCP servers → sandbox (exec in isolation)
- data layer: backend ↔ SQL / cache / queue, worker ↔ graph / vector DB
- auth: admin → SSO → user-auth

## Meta-rules

- Don't skip the Step 2 six-segment plan, even when it feels redundant.
- Don't skip the Step 5 self-review, even when v1 looks good enough.
- Don't fix one issue and ship — fix all identified issues, then re-render once.
- Never paste 400 lines of XML into chat — always render + deliver files.
- One coherent diagram beats two split ones, unless the user asks for a split.

## References

- [references/style-clean-slate.md](references/style-clean-slate.md) — **default**
  clean Slate recipe: exact hex + paste-ready node/arrow/container style strings.
- [references/palette.md](references/palette.md) — older multi-color palette (only
  when the user explicitly wants color).
- [references/shapes.md](references/shapes.md) — shape ↔ semantic mapping + draw.io
  style codes.
- [references/checklist.md](references/checklist.md) — pre-delivery self-review.
- [assets/template-layered.drawio](assets/template-layered.drawio) — minimal layered
  architecture skeleton.
