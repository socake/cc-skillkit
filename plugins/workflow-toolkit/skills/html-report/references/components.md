# HTML report components

Copy-paste components. All carry light-theme CSS; pair with the variables in
[palette.md](palette.md).

## Hero

```html
<header class="hero">
  <div class="hero-badge">v1.0 · Self-contained</div>
  <h1 class="hero-title">Reliability Blueprint</h1>
  <p class="hero-subtitle">A multi-class monitoring model built on critical user journeys</p>
  <div class="hero-stats">
    <div class="stat"><div class="stat-num">14</div><div class="stat-label">Journeys</div></div>
    <div class="stat"><div class="stat-num">7</div><div class="stat-label">Invariants</div></div>
    <div class="stat"><div class="stat-num">13%</div><div class="stat-label">Alert coverage</div></div>
    <div class="stat"><div class="stat-num">72</div><div class="stat-label">Failure-mode items</div></div>
  </div>
</header>
```

```css
.hero { padding: 80px 0 60px; max-width: 1200px; margin: 0 auto; }
.hero-badge { display: inline-block; padding: 4px 12px; background: var(--blue-bg);
              color: var(--blue); border-radius: var(--radius-sm); font-size: 12px;
              font-weight: 600; margin-bottom: 16px; }
.hero-title { font-size: 36px; font-weight: 700; margin: 0 0 8px;
              color: var(--text-primary); }
.hero-subtitle { font-size: 16px; color: var(--text-secondary); margin: 0 0 32px; }
.hero-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.stat { background: var(--bg-card); border: 1px solid var(--border-light);
        border-radius: var(--radius-md); padding: 20px; }
.stat-num { font-size: 32px; font-weight: 700; color: var(--text-primary); line-height: 1; }
.stat-label { font-size: 12px; color: var(--text-secondary); margin-top: 6px; }
```

## Card grid (main body)

```html
<section class="card-grid">
  <article class="card">
    <div class="card-stripe blue"></div>  <!-- 3px left stripe -->
    <div class="card-body">
      <div class="card-header">
        <span class="card-id">J-3</span>
        <span class="badge p0">P0</span>
      </div>
      <h3 class="card-title">Complete one conversation</h3>
      <p class="card-story">As a user, after I send a message I expect the first token &lt; 8s…</p>
      <div class="card-meta">
        <span><strong>Indicator</strong>: completion rate / first-token p95</span>
        <span><strong>Status</strong>: blind spot</span>
      </div>
      <div class="card-subitems">
        <strong>Sub-items:</strong>
        <a href="#item-a3" class="anchor">A.3</a>
        <a href="#item-a4" class="anchor">A.4</a>
      </div>
    </div>
  </article>
</section>
```

```css
.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
             gap: var(--gap-card); }
.card { background: var(--bg-card); border: 1px solid var(--border-light);
        border-radius: var(--radius-md); overflow: hidden; display: flex;
        transition: box-shadow 0.15s; }
.card:hover { box-shadow: var(--shadow-card-hover); }
.card-stripe { width: 3px; flex-shrink: 0; }
.card-stripe.blue { background: var(--blue); }
.card-stripe.red { background: var(--red); }
.card-stripe.orange { background: var(--orange); }
.card-stripe.purple { background: var(--purple); }
.card-body { padding: 20px; flex: 1; }
.card-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.card-id { font-size: 12px; font-weight: 600; color: var(--text-tertiary); font-family: monospace; }
.card-title { font-size: 16px; font-weight: 600; margin: 0 0 8px; }
.card-story { font-size: 13px; color: var(--text-secondary); line-height: 1.5; margin: 0 0 12px; }
.card-meta { display: flex; flex-direction: column; gap: 4px; font-size: 12px;
             color: var(--text-secondary); padding: 12px 0; border-top: 1px solid var(--bg-stripe); }
.card-subitems { margin-top: 12px; padding-top: 12px; font-size: 12px; border-top: 1px solid var(--bg-stripe); }
.anchor { display: inline-block; padding: 2px 6px; margin: 2px; background: var(--blue-bg);
          color: var(--blue); border-radius: var(--radius-sm); font-family: monospace;
          text-decoration: none; font-size: 11px; }
.anchor:hover { background: var(--blue); color: white; }
```

## Badge / chip

```html
<span class="badge p0">P0</span>
<span class="badge red">⚠️ red line</span>
<span class="badge blind">blind spot</span>
<span class="badge has-metric">has metric</span>
```

```css
.badge { display: inline-block; padding: 2px 8px; border-radius: var(--radius-sm);
         font-size: 11px; font-weight: 600; line-height: 1.5; }
.badge.p0 { background: var(--red-bg); color: var(--red); }
.badge.p1 { background: var(--orange-bg); color: var(--orange); }
.badge.p2 { background: var(--bg-stripe); color: var(--text-secondary); }
.badge.red { background: var(--red-bg); color: var(--red); }
.badge.blind { background: var(--red-bg); color: var(--red); }
.badge.partial { background: var(--orange-bg); color: var(--orange); }
.badge.has-metric { background: var(--green-bg); color: var(--green); }
```

## Table

```html
<table class="data-table">
  <thead><tr><th>ID</th><th>Name</th><th>Affects</th><th>Source</th></tr></thead>
  <tbody>
    <tr><td><code>DEP-1</code></td><td>WS hub</td><td>J-3/4/7/8</td><td>A.8</td></tr>
  </tbody>
</table>
```

```css
.data-table { width: 100%; border-collapse: collapse; background: var(--bg-card);
              border: 1px solid var(--border-light); border-radius: var(--radius-md); overflow: hidden; }
.data-table th, .data-table td { padding: 12px 16px; text-align: left;
                                  border-bottom: 1px solid var(--border-light); }
.data-table th { background: var(--bg-stripe); font-size: 12px; font-weight: 600;
                 color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; }
.data-table tr:nth-child(even) td { background: var(--bg-stripe); }
.data-table tr:last-child td { border-bottom: none; }
.data-table code { background: var(--bg-stripe); padding: 2px 6px; border-radius: var(--radius-sm); font-size: 12px; }
```

## Collapsible details (the core)

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
    <div class="fm-section"><strong>Failure mode</strong>: …</div>
  </div>
</details>
```

```css
.fm-item { background: var(--bg-card); border: 1px solid var(--border-light);
           border-radius: var(--radius-md); margin-bottom: 8px; overflow: hidden; }
.fm-item > summary { padding: 12px 16px; cursor: pointer; list-style: none;
                     display: flex; align-items: center; gap: 12px; }
.fm-item > summary::-webkit-details-marker { display: none; }
.fm-item > summary::before { content: '▸'; color: var(--text-tertiary); font-size: 10px; flex-shrink: 0; }
.fm-item[open] > summary::before { content: '▾'; }
.fm-id { font-family: monospace; font-size: 12px; font-weight: 600; color: var(--text-tertiary); }
.fm-title { flex: 1; font-weight: 500; }
.fm-tags { display: flex; gap: 4px; }
.fm-body { padding: 0 16px 16px 32px; font-size: 13px; line-height: 1.6; }
.fm-section { margin-bottom: 8px; }
.fm-item:target { box-shadow: 0 0 0 2px var(--blue); background: var(--bg-highlight); }
.fm-item.hide-by-filter { display: none; }
```

## Filter chips + JS

```html
<div class="fm-filter sticky">
  <button class="chip active" data-filter="all">All (72)</button>
  <button class="chip" data-filter="p0">P0 (44)</button>
  <button class="chip" data-filter="p1">P1 (24)</button>
  <button class="chip" data-filter="blind">Blind spot (8)</button>
  <button class="chip" data-filter="has-metric">Has metric (25)</button>
</div>
```

```css
.fm-filter { display: flex; gap: 8px; flex-wrap: wrap; padding: 12px 0;
             background: var(--bg-page); margin-bottom: 16px; }
.fm-filter.sticky { position: sticky; top: 0; z-index: 10; box-shadow: var(--shadow-sticky); }
.chip { padding: 6px 12px; border: 1px solid var(--border-light); background: var(--bg-card);
        border-radius: 20px; font-size: 12px; cursor: pointer; transition: all 0.15s; }
.chip:hover { background: var(--bg-card-hover); }
.chip.active { background: var(--blue); color: white; border-color: var(--blue); }
```

```javascript
// filter + anchor auto-expand, under 30 lines
document.addEventListener('DOMContentLoaded', () => {
  const filter = document.querySelector('.fm-filter');
  const items = document.querySelectorAll('.fm-item');

  filter?.addEventListener('click', e => {
    const btn = e.target.closest('.chip');
    if (!btn) return;
    filter.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
    btn.classList.add('active');
    const f = btn.dataset.filter;
    items.forEach(item => {
      const match = f === 'all'
        || item.dataset.priority === f
        || item.dataset.status === f;
      item.classList.toggle('hide-by-filter', !match);
    });
  });

  // anchor jump auto-expands the target <details>
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', () => {
      const target = document.querySelector(a.getAttribute('href'));
      if (target?.tagName === 'DETAILS') target.open = true;
    });
  });
});
```

## Bar chart (pure CSS, no chart.js)

```html
<div class="bar-chart">
  <div class="bar-item"><span class="bar-label">Existing alerts</span>
    <div class="bar"><div class="bar-fill blue" style="width: 100%">220</div></div>
  </div>
  <div class="bar-item"><span class="bar-label">Actual incidents</span>
    <div class="bar"><div class="bar-fill orange" style="width: 17%">37</div></div>
  </div>
  <div class="bar-item"><span class="bar-label">Caught incidents</span>
    <div class="bar"><div class="bar-fill red" style="width: 2.5%">5 (13%)</div></div>
  </div>
</div>
```

```css
.bar-chart { display: grid; gap: 16px; }
.bar-item { display: grid; grid-template-columns: 120px 1fr; align-items: center; gap: 12px; }
.bar-label { font-size: 13px; color: var(--text-secondary); }
.bar { background: var(--bg-stripe); border-radius: var(--radius-sm); height: 28px; overflow: hidden; }
.bar-fill { height: 100%; padding: 0 12px; display: flex; align-items: center;
            color: white; font-size: 13px; font-weight: 600; }
.bar-fill.blue { background: var(--blue); }
.bar-fill.orange { background: var(--orange); }
.bar-fill.red { background: var(--red); }
```
