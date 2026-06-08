# Light HTML report palette

Modern light theme (Linear/Notion family). Copy the variables, keep the restraint.

## CSS variables (paste as-is)

```css
:root {
  /* backgrounds */
  --bg-page: #fafbfc;          /* page (NOT pure white — pure white glares) */
  --bg-card: #ffffff;          /* card */
  --bg-card-hover: #f6f8fa;
  --bg-stripe: #f6f8fa;        /* zebra table rows */
  --bg-highlight: #fff8c5;     /* anchor-jump highlight */

  /* borders */
  --border-light: #e1e4e8;
  --border-strong: #d0d7de;

  /* text */
  --text-primary: #1d2125;     /* primary (NOT pure black — slightly softer) */
  --text-secondary: #5d6772;
  --text-tertiary: #8a93a0;
  --text-link: #0969da;

  /* category colors (600-ish: saturated enough, not harsh) */
  --blue: #0969da;             /* primary class */
  --red: #d1242f;              /* invariant / red line / alert */
  --orange: #bc4c00;           /* ops action */
  --purple: #8250df;           /* cross-cutting dependency */
  --green: #1a7f37;            /* success / done */
  --gray: #6e7781;             /* reference / de-emphasized */

  /* light category fills (badge backgrounds) */
  --blue-bg: #ddf4ff;
  --red-bg: #ffebe9;
  --orange-bg: #fff1e5;
  --purple-bg: #fbefff;
  --green-bg: #dafbe1;
  --gray-bg: #f6f8fa;

  /* shadows (use sparingly) */
  --shadow-card: 0 1px 3px rgba(15,17,21,0.06);
  --shadow-card-hover: 0 4px 12px rgba(15,17,21,0.08);
  --shadow-sticky: 0 2px 8px rgba(15,17,21,0.04);

  /* radius */
  --radius-sm: 6px;            /* badge / chip */
  --radius-md: 8px;            /* card */
  --radius-lg: 12px;           /* large module / hero */

  /* spacing */
  --gap-section: 80px;
  --gap-card: 24px;
  --gap-inner: 12px;
}
```

## Category-color usage

| Class | Color | Light bg | Where it appears |
|---|---|---|---|
| Primary objects | `--blue` | `--blue-bg` | card left 3px stripe + chip text + anchor links |
| Invariant / safety | `--red` | `--red-bg` | emphasized table rows + ⚠️ tags |
| Ops action | `--orange` | `--orange-bg` | tables + owner chips |
| Cross-cutting dependency | `--purple` | `--purple-bg` | tables + "affects N" chips |
| Reference / de-emphasized | `--gray` | `--gray-bg` | de-emphasized detail summaries |

### Three rules for category color

1. **Never flood a whole card with color.** Category color only on a 3px left
   stripe + chip text + table emphasis; the card body stays white.
2. **Use the ~600 shade** (saturated but not harsh), not pale 200/400 fills.
3. **Warnings get a chip + icon, not a red wash**: e.g. a `⚠️ P0 red line` chip,
   not a fully red background block.

## Type

```css
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
               "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue",
               Helvetica, Arial, sans-serif;
  font-size: 14px;
  line-height: 1.65;
  color: var(--text-primary);
  background: var(--bg-page);
}
code, pre {
  font-family: "SF Mono", Monaco, Consolas, "Liberation Mono", monospace;
  font-size: 13px;
}
```

### Size rhythm

- Hero title `36px / 700`
- Section title `24px / 600`
- Card title `16px / 600`
- Body `14px`
- De-emphasized `12px`, `--text-tertiary`
- Code `13px`

## If the user originally wanted a dark theme

Map the dark palette to light rather than refusing:

| Dark | Light |
|---|---|
| `#0a0a0b` bg | `#fafbfc` |
| `#131316` card | `#ffffff` |
| `#25252b` border | `#e1e4e8` |
| `#e8e8ea` text | `#1d2125` |
| `#9b9ba3` muted | `#5d6772` |
| `#6ee7b7` accent | `#0969da` or `#1a7f37` |
| `#a78bfa` accent-2 | `#8250df` |

Bump category colors from the 400 shade (dark theme) to ~600 on light to keep
contrast.
