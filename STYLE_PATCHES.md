# Style / CSS Hardening Patches — Apply in Order

**Target:** Test Bank Platform (Tailwind 3.4 via django-tailwind)
**Goal:** Remove the 82 `!important` rules, cut CDN dependencies, unify the design system, make dark mode complete.
**Do NOT migrate off Tailwind** — it is deeply integrated and the replacement cost is weeks. These patches improve Tailwind's implementation.

Apply sections in order. Each has **Why / File / Patch / Verify**. Run `cd theme/static_src && npm run build` after each structural change.

---

## 1. Self-host Swiper (kills ~40 `!important` rules)

**Why:** Swiper CSS is loaded from jsdelivr CDN *after* Tailwind. That ordering forces the custom CSS to use `!important` to beat Swiper's own rules. Vendoring Swiper through the Tailwind pipeline puts you in control of cascade order.

**Step 1.1 — Install Swiper locally**

**File:** `theme/static_src/package.json`

Add to `devDependencies`:
```json
"devDependencies": {
  "tailwindcss": "^3.4.0",
  "swiper": "^11.1.0"
}
```

Run:
```bash
cd theme/static_src && npm install
```

**Step 1.2 — Import Swiper CSS into your pipeline**

**File:** `theme/static_src/src/styles.css` (replace lines 1–6):
```css
/* stylelint-disable-next-line at-rule-no-unknown */
@tailwind base;

/* Vendor CSS (Swiper) — imported BEFORE components so our overrides win without !important */
@import "swiper/swiper-bundle.css";

/* stylelint-disable-next-line at-rule-no-unknown */
@tailwind components;
/* stylelint-disable-next-line at-rule-no-unknown */
@tailwind utilities;
```

**Step 1.3 — Serve Swiper JS locally**

Copy `node_modules/swiper/swiper-bundle.min.js` into `theme/static/vendor/swiper/` via a build script or add to `package.json` scripts:
```json
"scripts": {
  "build": "tailwindcss -i ./src/styles.css -o ../static/css/dist/styles.css --minify && mkdir -p ../static/vendor/swiper && cp node_modules/swiper/swiper-bundle.min.js ../static/vendor/swiper/",
  "start": "tailwindcss -i ./src/styles.css -o ../static/css/dist/styles.css --watch"
}
```

**Step 1.4 — Remove CDN references from base.html**

**File:** `templates/base.html` (lines 17–21), replace with:
```html
{# Swiper JS — self-hosted, no CDN #}
<script src="{% static 'vendor/swiper/swiper-bundle.min.js' %}" defer></script>
```
(The CSS now ships inside `{% tailwind_css %}`.)

**Step 1.5 — Now purge `!important` from Swiper rules**

**File:** `theme/static_src/src/styles.css` — remove every `!important` on lines involving `.swiper-*`. For example:

Before (lines 83–98):
```css
.hero-carousel-pagination {
  @apply bottom-6 !important;
  position: absolute !important;
  z-index: 20 !important;
}

.hero-carousel-pagination .swiper-pagination-bullet {
  @apply w-3 h-3 bg-white/50 opacity-100;
  margin: 0 6px !important;
  transition: all 0.3s ease;
}
```

After:
```css
.hero-carousel-pagination {
  @apply bottom-6 absolute z-20;
}

.hero-carousel-pagination .swiper-pagination-bullet {
  @apply w-3 h-3 bg-white/50 opacity-100;
  margin: 0 6px;
  transition: all 0.3s ease;
}
```

Apply the same pattern throughout lines 83–309. Target: **drop from 82 `!important`s to <10.**

**Verify:** `grep -c '!important' theme/static_src/src/styles.css` → should be under 10. Carousels still work in browser.

---

## 2. Self-host fonts (GDPR + offline + CSP)

**Why:** Google Fonts CDN leaks user IPs (GDPR concern in EU), adds DNS lookup + handshake latency on first paint, and breaks offline dev.

**Step 2.1 — Download font subsets**

Use [google-webfonts-helper](https://gwfh.mranftl.com/fonts) to download Inter and Cairo in woff2:
- Inter weights: 300, 400, 500, 600, 700 (Latin subset)
- Cairo weights: 300, 400, 500, 600, 700 (Arabic + Latin subsets)

Place files in `theme/static/fonts/inter/` and `theme/static/fonts/cairo/`.

**Step 2.2 — Add @font-face declarations**

**File:** `theme/static_src/src/styles.css` — add at the top, above `@tailwind base`:

```css
@font-face {
  font-family: 'Inter';
  font-style: normal;
  font-weight: 300 700;
  font-display: swap;
  src: url('/static/fonts/inter/inter-variable.woff2') format('woff2');
}

@font-face {
  font-family: 'Cairo';
  font-style: normal;
  font-weight: 300 700;
  font-display: swap;
  src: url('/static/fonts/cairo/cairo-variable.woff2') format('woff2');
}
```

**Step 2.3 — Remove Google Fonts from base.html**

**File:** `templates/base.html` — delete lines 24–33 (the entire `preconnect` + `link` block for Google Fonts).

**Verify:** Network tab shows no requests to `fonts.googleapis.com` or `fonts.gstatic.com`. Both English and Arabic render with correct fonts.

---

## 3. Clean the color alias mess

**Why:** [tailwind.config.js:22–56](theme/static_src/tailwind.config.js:22) defines the same colors under multiple names: `primary` / `coursera-blue` / `apple-bg` / `bg`, plus `udemy-purple` / `brand.500`. This is dead weight and causes drift — new code uses `brand-*`, old code uses `udemy-*`.

**Step 3.1 — Pick one naming scheme**

Canonical names (keep these):
- `brand-500` / `brand-600` / `brand-700` (action / brand)
- `primary` / `primary-dark` (secondary accent)
- `accent` (warm neutral)
- `dark-bg` / `dark-surface` / `dark-border` (dark mode surfaces)

**Step 3.2 — Run a find/replace pass**

Map these legacy names → canonical:

| Legacy | Canonical |
|---|---|
| `udemy-purple` | `brand-500` |
| `udemy-purple-dark` | `brand-600` |
| `coursera-blue` | `primary` |
| `coursera-blue-dark` | `primary-dark` |
| `coursera-bg` / `apple-bg` | `bg` |
| `coursera-text` / `apple-text` | `text` |
| `coursera-text-light` / `apple-text-secondary` | `text-light` |
| `coursera-accent` / `purple-accent` | `accent` |

Run (from repo root):
```bash
# Dry run first
grep -rn "udemy-purple\|coursera-blue\|apple-bg\|apple-text" templates/ accounts/ catalog/ payments/ practice/ cms/ forum/ | head -40

# Apply replacements per row above — use sed or your editor's project-wide replace
```

**Step 3.3 — Remove legacy aliases from config**

**File:** `theme/static_src/tailwind.config.js` — replace the `colors` block (lines 22–56) with:

```js
colors: {
  brand: {
    500: '#5624d0',
    600: '#4a1fb8',
    700: '#3d1a9e',
  },
  primary: '#8FABD4',
  'primary-dark': '#4A70A9',
  accent: '#EFECE3',
  text: '#000000',
  'text-light': '#666666',
  bg: 'rgb(245, 245, 247)',
  // Dark mode surfaces (keep)
  'dark-bg': '#0F172A',
  'dark-surface': '#1E293B',
  'dark-border': '#334155',
},
```

**Verify:** `npm run build` succeeds. Grep for removed names returns zero:
```bash
grep -rn "udemy-\|coursera-\|apple-bg\|apple-text\|purple-accent" templates/ accounts/ catalog/ payments/ practice/ cms/ forum/
```

---

## 4. Kill inline `style=` in non-email templates

**Why:** Inline styles beat `dark:` variants and bypass the design system. Email templates (`accounts/emails/*`, `payments/emails/*`) must keep them — email clients ignore classes.

**Files to scrub (app-facing only, NOT emails):**
- [templates/practice/practice_session.html](templates/practice/practice_session.html) — 1 occurrence
- [templates/practice/practice_results.html](templates/practice/practice_results.html) — 1
- [templates/catalog/index.html](templates/catalog/index.html) — 2
- [templates/components/timer.html](templates/components/timer.html) — 1
- [templates/components/progress_bar.html](templates/components/progress_bar.html) — 1
- [templates/components/button.html](templates/components/button.html) — 3
- [templates/payments/checkout.html](templates/payments/checkout.html) — 11
- [templates/forum/topic_create.html](templates/forum/topic_create.html) — 1
- [templates/admin/base_site.html](templates/admin/base_site.html) — 3
- [templates/admin/catalog/testbank/change_list.html](templates/admin/catalog/testbank/change_list.html) — 1
- [templates/admin/catalog/testbank/upload_json.html](templates/admin/catalog/testbank/upload_json.html) — 29 (by far the worst)

**Pattern to apply:**

Before:
```html
<div style="background: linear-gradient(to right, #e28f64, #df804f); padding: 1rem;">
```

After (either use existing `.btn-coursera` component class or Tailwind utilities):
```html
<div class="bg-gradient-to-r from-[#e28f64] to-[#df804f] p-4">
```

For truly dynamic values from Django context (e.g. a CMS-picked color), keep `style` but scope it minimally and use CSS custom properties:
```html
<div class="hero-gradient" style="--hero-from: {{ slide.gradient_from }}; --hero-to: {{ slide.gradient_to }};">
```

Then in CSS:
```css
.hero-gradient {
  @apply bg-gradient-to-r;
  --tw-gradient-from: var(--hero-from);
  --tw-gradient-to: var(--hero-to);
}
```

**Verify:**
```bash
grep -rn 'style=' templates/ | grep -v emails | grep -v ".md" | wc -l
```
Should drop from ~50 to <5 (CSS-variable passthroughs for user-configurable CMS colors).

---

## 5. Extend dark mode to custom component CSS

**Why:** Custom rules like `.swiper-button-next`, `.btn-coursera`, and the trending-card shadows don't react to `.dark` on `<html>`. Users in dark mode see a white Swiper button on a navy page.

**File:** `theme/static_src/src/styles.css` — audit each custom component and add `.dark` overrides where surface/text colors are hardcoded.

Example — Swiper button currently (lines 100–106):
```css
.swiper-button-next,
.swiper-button-prev {
  @apply text-udemy-purple bg-white w-12 h-12 rounded-full shadow-swiper-button m-0 transition-all duration-300 border border-black/5;
  color: #5624d0 !important;
}
```

After (uses the canonical `brand-500` token + dark variant):
```css
.swiper-button-next,
.swiper-button-prev {
  @apply text-brand-500 bg-white w-12 h-12 rounded-full shadow-swiper-button m-0 transition-all duration-300 border border-black/5;
}

.dark .swiper-button-next,
.dark .swiper-button-prev {
  @apply bg-dark-surface text-brand-500 border-dark-border;
}
```

Repeat for:
- `.swiper-pagination-bullet` (hardcoded `#e28f64`) → use a design token + dark variant
- `.btn-coursera` (gradient fine, but check contrast on `.dark` bg)
- `.hero-carousel-pagination .swiper-pagination-bullet-active` (currently `bg-white` — fine in both modes)
- `.trending-swiper .swiper-slide > div` shadow — already uses `shadow-card`; verify card background responds to dark mode
- `.es-alert--*` (bg-green-50 etc. are hard-coded; add `.dark` variants with darker surfaces)

**Verify:** Toggle dark mode on homepage, dashboard, practice results page. Screenshot-compare: no white-on-white, no dark-on-dark, all buttons still discoverable.

---

## 6. Adopt the typography scale

**Why:** [tailwind.config.js:93–103](theme/static_src/tailwind.config.js:93) defines `text-display`, `text-h1`…`text-caption` — but grep shows most templates use raw `text-2xl`, `text-4xl` instead. The design system is documented but unused.

**Step 6.1 — Audit current usage**

Run from repo root:
```bash
# Count legitimate scale uses
grep -rE '\btext-(display|h1|h2|h3|h4|body|body-sm|caption)\b' templates/ | wc -l

# Count raw utility uses of common sizes
grep -rE '\btext-(xs|sm|base|lg|xl|2xl|3xl|4xl|5xl|6xl)\b' templates/ | wc -l
```

**Step 6.2 — Map replacements**

Approximate mapping (one-time mechanical pass):

| Raw | Scale |
|---|---|
| `text-5xl` / `text-6xl` on headings | `text-display` |
| `text-3xl` / `text-4xl` on headings | `text-h1` |
| `text-2xl` on headings | `text-h2` |
| `text-xl` on headings | `text-h3` |
| `text-lg` on card titles | `text-h4` |
| `text-base` on paragraphs | `text-body` |
| `text-sm` on small text | `text-body-sm` |
| `text-xs` on labels/meta | `text-caption` |

Only apply inside actual heading elements (`h1`–`h6`, card titles, section headings). Don't blanket-replace every `text-sm` — many are navigation metadata where raw sizes are fine.

**Step 6.3 — Enforce in code review**

Add to `CONTRIBUTING.md` (create if missing):
> Use the typography scale tokens (`text-display`, `text-h1`…`text-caption`) for headings, body copy, and captions. Raw Tailwind sizes (`text-lg` etc.) are acceptable only inside components that don't represent semantic text hierarchy (buttons, badges, inputs).

---

## 7. CI check that Tailwind output is up to date

**Why:** [theme/static/css/dist/styles.css](theme/static/css/dist/styles.css) is a build artifact. A developer who forgets to rebuild ships stale CSS. CI should fail loudly.

**File:** `.github/workflows/style-check.yml` (create if missing):

```yaml
name: Style Check

on: [push, pull_request]

jobs:
  tailwind-fresh:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install Tailwind deps
        working-directory: theme/static_src
        run: npm ci

      - name: Rebuild Tailwind CSS
        working-directory: theme/static_src
        run: npm run build

      - name: Fail if build artifact drifted
        run: |
          if ! git diff --quiet theme/static/css/dist/styles.css; then
            echo "❌ theme/static/css/dist/styles.css is out of date."
            echo "Run: cd theme/static_src && npm run build"
            git diff --stat
            exit 1
          fi
          echo "✅ Tailwind CSS is up to date."
```

**Step 7.1 — Add to `.gitignore`? No** — keep the compiled file committed so production deploys don't need npm at build time (or configure your deploy to run `npm run build`). Decide based on your deploy pipeline.

**Alternative (recommended if your deploy already runs npm):**
Put `theme/static/css/dist/styles.css` **in** `.gitignore` and have the Dockerfile / Cloud Run build step run `npm run build` before `collectstatic`.

---

## 8. Content Security Policy (prerequisite for #2 paying off)

**Why:** Once Google Fonts and jsdelivr are removed, you can ship a strict CSP. Today, CSP is wide-open because of CDN dependencies.

**File:** `testbank_platform/settings.py` — add:

```python
INSTALLED_APPS += ['csp']

MIDDLEWARE.insert(
    MIDDLEWARE.index('django.middleware.security.SecurityMiddleware') + 1,
    'csp.middleware.CSPMiddleware',
)

CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")  # 'unsafe-inline' needed until inline styles (#4) are cleaned
CSP_FONT_SRC = ("'self'", 'data:')
CSP_IMG_SRC = ("'self'", 'data:', 'https:')  # keep https: for user-uploaded Cloud Storage URLs
CSP_CONNECT_SRC = ("'self'", 'https://api.stripe.com', 'https://api.tap.company')
CSP_FRAME_SRC = ('https://js.stripe.com', 'https://hooks.stripe.com')
```

Install:
```bash
pip install django-csp>=3.7
```
Add to `requirements.txt`.

**After** #4 (inline styles removed), tighten:
```python
CSP_STYLE_SRC = ("'self'",)  # drop 'unsafe-inline'
```

---

## 9. Delete empty files and fix minor drift

**Files to delete:**
- [theme/urls.py](theme/urls.py) — 0 bytes, not registered anywhere
- Root-level junk: `=0.25.0`, `=2.0.0`, `=4.0.0`, `=20.0.0` — these are pip install artifacts from someone running `pip install 'Django>=4.2'` in a shell that interpreted `>` as redirect

```bash
rm theme/urls.py =0.25.0 =2.0.0 =4.0.0 =20.0.0
```

**Fix:** [static/manifest.json](static/manifest.json) — 331 bytes, has no icons. Either complete it (add `icons`, `start_url`, `display`, `background_color`, `theme_color`) or remove the `<link rel="manifest">` from base.html.

---

## Post-apply verification checklist

- [ ] `cd theme/static_src && npm install && npm run build` succeeds
- [ ] `grep -c '!important' theme/static_src/src/styles.css` → under 10
- [ ] `grep -rn 'udemy-\|coursera-\|apple-bg\|apple-text' templates/` → zero results
- [ ] Network tab shows zero requests to `fonts.googleapis.com`, `fonts.gstatic.com`, or `cdn.jsdelivr.net`
- [ ] Homepage, dashboard, practice session, practice results all render correctly in light mode
- [ ] Toggle dark mode → same pages render correctly, no white-on-white
- [ ] Arabic (RTL) view renders with Cairo font, carousels flow RTL
- [ ] `grep -rn 'style=' templates/ | grep -v emails | wc -l` → under 5
- [ ] CI style-check workflow passes
- [ ] Lighthouse performance score unchanged or improved (fewer round-trips from self-hosting)

---

## Estimated effort

| Section | Effort | Risk |
|---|---|---|
| 1. Self-host Swiper | 2–3 hrs | Low (well-scoped) |
| 2. Self-host fonts | 1–2 hrs | Low |
| 3. Color alias cleanup | 3–4 hrs (mechanical replace) | Low if grep-driven |
| 4. Inline styles → utilities | 4–6 hrs (mostly the admin upload_json template) | Medium — easy to miss edge cases |
| 5. Dark mode for custom CSS | 2–3 hrs | Low |
| 6. Typography scale adoption | 4–6 hrs (manual judgment calls) | Low |
| 7. CI check | 30 min | None |
| 8. CSP | 1 hr + 1 week of tightening after #4 | Medium — easy to break fonts/images at first |
| 9. Delete junk | 5 min | None |

**Total:** ~20–30 hours. Biggest wins first: **#1 (Swiper) + #2 (fonts) + #9 (junk)** in one afternoon.

---

## What is NOT covered here

- Migrating to Tailwind 4 (different build system, out of scope)
- Component extraction to separate files (`components/button.html`, `components/card.html` pattern)
- Design token revision (the current palette is fine; if rebrand, that's separate work)
- Accessibility audit (contrast ratios, focus rings, ARIA) — own document
- Admin theme customization beyond the current `admin/base_site.html`
- Storybook or visual regression setup
