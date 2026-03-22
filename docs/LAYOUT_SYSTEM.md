# Layout system (Exam Stellar)

This document matches the project skills: thin Django views (`01_backend`), Tailwind-first UI (`02_frontEnd_UI_UX`), shared shell for payment pages (`03_payment_eng`), a11y & purge-safe alerts (`04_QA_Eng`), and consistent IA/CTAs (`05_product`).

## Shell

- **Fixed header:** `h-16` (4rem). Body uses **`pt-16` only** — no duplicate `padding-top` inline/`!important`.
- **CSS variable:** `:root { --header-h: 4rem }` for alignment (dropdowns, scroll margins). Defined in `theme/static_src/tailwind.config.js` (`addBase`).
- **Z-index scale (Tailwind theme):** `z-nav` (1000), `z-nav-mega` (1010), `z-nav-dropdown` (1020), `z-overlay` (2000), `z-toast` (3000). Prefer these over ad-hoc `z-[9999]`.

## Page contract

- **`.page`** — full-width flex child under `<main>`.
- **`.page__inner`** — `max-w-9xl` + responsive horizontal padding (`px-4` / `sm:px-6` / `lg:px-8`).

Use for standard content pages (e.g. dashboard). Full-bleed heroes (carousel) can stay outside `.page__inner`; put constrained sections inside.

## Brand tokens

- Use **`brand-500`** / **`brand-600`** / **`brand-700`** in templates instead of raw hex.
- Legacy **`udemy-purple`** remains in config for older references.
- **Stripe checkout** (`templates/payments/checkout.html`): legacy `<style>` uses CSS variables **`--es-brand-500`** / **`--es-brand-600`** (same values) so submit buttons match the Tailwind theme.

## Django messages

- Do **not** build Tailwind class names from `message.tags` strings (purge risk).
- Use semantic classes: **`es-alert`**, **`es-alert--success`**, **`es-alert--error`**, **`es-alert--warning`**, **`es-alert--info`** (defined in Tailwind `addComponents`; borders use **logical** `border-inline-start` for RTL).

## Accessibility

- **Skip link** in `templates/base.html` → `#main-content`.
- **`<main id="main-content" tabindex="-1">`** for focus target after skip.

## Tailwind `content` paths

`tailwind.config.js` includes `templates/**`, app templates, **`cms/templates`**, **`forum/templates`** so classes are not dropped in production builds.

## Payments

Checkout and Tap templates should extend `base.html` and reuse **`.page` / `.page__inner`** where layout is not full-screen gateway UI.

## Templates using `.page` / `.page__inner` (rolling adoption)

- **Shell:** `base.html` (messages, nav — inner widths unchanged where global).
- **Accounts:** `accounts/dashboard.html`.
- **Payments:** `checkout.html`, `tap_checkout.html`, `purchase_list.html`.
- **Forum:** `index`, `category_detail`, `topic_detail`, `topic_create`, `post_edit`.
- **Catalog:** `index` (root `page w-full`), `testbank_detail`, `package_detail`, `contact`, `subcategory_list`, `certification_list`, `testbank_list`, `category_list`, `vocational_index`, `search_results`.
- **CMS:** `page_detail` (narrow `max-w-4xl` on `page__inner`).
- **Practice:** `practice_results` (`.page` wraps `.results-content`); `practice_session` legend uses `gap-2`.
- **Includes:** `breadcrumbs.html`, `partners.html`, `testimonials.html`, `user_intent.html` use **`page__inner`** for width/padding.

Hero / full-bleed blocks stay **outside** extra wrappers; constrained rows use **`page__inner`**.
