# Pre-delivery self-review checklist

**Mandatory:** after rendering the PNG, Read the image and review it visually. Each
round that finds ≥2 issues earns another iteration.

## Visual layer (where it breaks most)

- [ ] Readable text: CJK fontSize ≥ 11, key titles 14–16
- [ ] No node overlaps (wrong coordinates cause these)
- [ ] **No edge passing through a node interior** (the most common problem)
- [ ] **No diagonal line crossing ≥3 layers** (aggregate onto a bus instead)
- [ ] No large empty areas (canvas too big)
- [ ] Legend present and well-placed (default top-right)
- [ ] Edge labels have a white background so the line doesn't cut the text
      (`labelBackgroundColor=#FFFFFF`)

## Content layer (text overflow)

- [ ] Every node's text is fully inside the border
  - **folder**: height ≥ `lines×16 + tabHeight + spacingTop` (tabHeight ~20–22)
  - **cylinder3**: height ≥ `lines×16 + size×2` (size ~12)
  - **callout**: height ≥ `lines×16 + size`
  - **note**: height ≥ `lines×16 + size`
  - **plain rectangle**: height ≥ `lines×16 + 8`
- [ ] Note boxes aren't overstuffed
  - 8 lines of body ⇒ min height ~150
  - if it won't fit: compress to a 1–2 line bus strip, or delete and use an edge label
- [ ] Subgroup titles aren't crushed by child nodes (reserve `spacingTop=6`)

## Semantic layer (easiest to do shallowly)

- [ ] Node shapes match semantics (not all rectangles)
  - person → actor, repo → folder, script → parallelogram
  - hub → hexagon, storage → cylinder3, cluster → cloud
  - alert → callout, note → note
- [ ] Color expresses the right semantic (see palette.md)
- [ ] Edge styles are semantic
  - sync solid / async dashed / monitoring `dashPattern=1 4` / alert red dashed /
    deprecated gray dashed
- [ ] Main flow heavier than secondary lines (per the chosen style's stroke widths)
- [ ] Edges have a label naming the protocol (HTTP / queue / HTTPS / tool call / R/W)
- [ ] Deprecated items gray + `dashed=1` + the word "deprecated"
- [ ] Hub nodes dark fill + white text (1–3 total) to create focal points
- [ ] Many-to-many (N×M edges > 10) aggregated onto a bus node

## Architecture truthfulness (easiest to become an "imaginary diagram")

- [ ] Service names are real (not abstract "API service" / "backend")
- [ ] Call relationships are real (not guessed "might call")
- [ ] Protocols labeled accurately (e.g. backend→dispatcher over a queue, not HTTP;
      worker→MCP is a tool-call over HTTP)
- [ ] Data relationships drawn: each service ↔ its concrete store (SQL / cache /
      queue / graph / vector DB)
- [ ] External dependencies drawn: LLM providers / third-party APIs
- [ ] Auth path drawn: SSO / identity / user-auth

## Delivery layer (mechanical checks)

- [ ] Source saved to `<DIAG_DIR>/<name>.drawio`
- [ ] PNG exported (`--scale 2` for crisp embedding)
- [ ] SVG exported (vector, scales without blurring)
- [ ] Shareable links/paths produced
- [ ] **You Read the PNG and reviewed it visually** (the step most often skipped)
- [ ] Reply to the user: links + local path + a one-line note on changes — **no XML**

## When to stop iterating

Don't chase a perfect first pass; accept iteration:
- v1: skeleton + layout (may be messy)
- v2: fix edges and overlapping text
- v3: upgrade palette and shapes
- v4: expand key detail
- v5+: change wherever the user points

If the user reports 3+ specific issues, **don't fix one and ship** — fix them all,
then render once.

If the user says "not detailed enough" / "imaginary", check whether you only drew
the namespace layer without the real call paths.

If the user says "dull/monotone", check whether everything is a rectangle / a single
flat color.

## Edge-organization rules

Choosing *when* to draw an edge and *how* matters more than "connect everything then
delete".

| Relationship | Draw it? | How |
|---|---|---|
| "contains" within a band | **no** | the band border already says it |
| "calls" within a band | yes | one main path; align node x to avoid crossing |
| many-to-one (≥3 in-edges) | **add a merge node** | N short lines into the merge, then 1 out |
| cross-layer / long distance | **don't go straight** | `edgeStyle=orthogonalEdgeStyle;rounded=0` + waypoints |
| bidirectional / symmetric | double arrow | `startArrow=classic;endArrow=classic` |

Orthogonal routing example (avoid diagonals):
```xml
<mxCell edge="1" style="edgeStyle=orthogonalEdgeStyle;rounded=0;..." source="A" target="B">
  <mxGeometry relative="1" as="geometry">
    <Array as="points">
      <mxPoint x="500" y="1093" />  <!-- bend 1 -->
      <mxPoint x="210" y="1093" />  <!-- bend 2 -->
    </Array>
  </mxGeometry>
</mxCell>
```

## Wallpaper / desktop-background fit

If the diagram will be used as a wallpaper:

1. **Use 16:9** (covers 1080p / 2K / 4K / 5K). 16:10 only fits some laptops.
2. **Safe margin ≥ 10–12%**: "fill screen" crops edges; content against the edge gets
   cut.
3. **Add a `page_bg` rect to anchor the output ratio.** draw.io crops to content
   bounds by default, so PNG size ≠ pageWidth × pageHeight. Add before all nodes:
   ```xml
   <mxCell id="page_bg" value="" style="rounded=0;fillColor=#FFFFFF;strokeColor=none;" vertex="1" parent="1">
     <mxGeometry x="0" y="0" width="<pageWidth>" height="<pageHeight>" as="geometry" />
   </mxCell>
   ```
4. **Size fonts for the smallest target screen**: a 4800px PNG on a 1080p screen
   scales ~0.4, so title ≥16px / subtitle ≥13px to stay readable.
5. **Enough contrast**: borders from slate-500 (`#64748B`), subtitle text from
   slate-700 (`#334155`). Pale grays (`#CBD5E1` / `#94A3B8`) suit on-screen close
   viewing, not wallpaper.

## Batch translate / re-layout (don't hand-edit mxGeometry)

To shift or grow the canvas, use perl with a lookbehind to avoid `dx=` / `dy=`:

```bash
# add +300 to every mxGeometry/mxPoint x (without touching mxGraphModel dx)
perl -i -pe 's/(?<![a-z])x="(\d+)"/sprintf("x=\"%d\"", $1+300)/ge' file.drawio
perl -i -pe 's/(?<![a-z])y="(\d+)"/sprintf("y=\"%d\"", $1+214)/ge' file.drawio

# change canvas size
sed -i 's/pageWidth="2400"/pageWidth="3000"/; s/pageHeight="1350"/pageHeight="1688"/' file.drawio
```

Batch font/color bump (largest first to avoid chain-replacement):
```bash
sed -i '
s/fontSize="14"/fontSize="16"/g
s/fontSize="13"/fontSize="15"/g
s/fontSize="12"/fontSize="14"/g
s/fontSize="11"/fontSize="13"/g
s/strokeColor=#CBD5E1/strokeColor=#64748B/g
s/strokeColor=#E2E8F0/strokeColor=#94A3B8/g
' file.drawio
```

## Typical feedback → cause mapping

- "ugly" → inconsistent palette/shapes → switch to the minimal card style (white +
  gray border + dark hub + indigo accent)
- "messy" → edges crossing / many-to-many fan-out → merge nodes + orthogonal routing
- "faint / hard to read" → font + contrast → darken borders +2 steps, text +1–2
- "cut off / incomplete" → safe margin too small → grow canvas 20–25%, center content
- "wrong ratio" → screen-ratio mismatch → 16:9 + `page_bg` to anchor output
