# 📐 Spacing System Documentation

**Version:** 1.0  
**Last Updated:** February 23, 2026  
**Reference:** `theme/static_src/tailwind.config.js`

---

## Overview

The Exam Stellar platform uses a standardized spacing system to ensure consistent visual rhythm and maintainability across all templates. This system is built on Tailwind CSS and follows an 8px base unit system.

---

## Spacing Scale

### Standard Tailwind Spacing

Tailwind's default spacing scale (based on 4px increments):

| Class | Value | Pixels | Usage |
|-------|-------|--------|-------|
| `p-0` | 0 | 0px | No padding |
| `p-1` | 0.25rem | 4px | Minimal spacing |
| `p-2` | 0.5rem | 8px | Tight spacing |
| `p-3` | 0.75rem | 12px | Small spacing |
| `p-4` | 1rem | 16px | Base spacing unit |
| `p-5` | 1.25rem | 20px | Small-medium spacing |
| `p-6` | 1.5rem | 24px | **Standard card padding** |
| `p-8` | 2rem | 32px | **Large card padding** |
| `p-10` | 2.5rem | 40px | Extra large padding |
| `p-12` | 3rem | 48px | **Section padding** |
| `p-16` | 4rem | 64px | **Large section padding** |

### Custom Spacing Values

Custom spacing values added to `tailwind.config.js`:

| Variable | Class | Value | Pixels | Usage |
|----------|-------|-------|--------|-------|
| `section` | `py-section` | 3rem | 48px | Standard section vertical padding |
| `section-lg` | `py-section-lg` | 4rem | 64px | Large section vertical padding |
| `card` | `p-card` | 1.5rem | 24px | Standard card padding (all sides) |
| `card-lg` | `p-card-lg` | 2rem | 32px | Large card padding (all sides) |
| `gap` | `gap-gap` | 1.5rem | 24px | Standard gap between elements |
| `gap-sm` | `gap-gap-sm` | 1rem | 16px | Small gap between elements |
| `gap-lg` | `gap-gap-lg` | 2rem | 32px | Large gap between elements |

---

## Usage Guidelines

### Section Spacing

**Standard Sections:**
```html
<section class="py-section">
  <!-- Section content -->
</section>
```

**Large Sections:**
```html
<section class="py-section-lg">
  <!-- Hero sections, major content areas -->
</section>
```

**Responsive Section Spacing:**
```html
<section class="py-8 md:py-section lg:py-section-lg">
  <!-- Responsive spacing -->
</section>
```

### Card Padding

**Standard Cards:**
```html
<div class="bg-white rounded-xl p-card">
  <!-- Card content -->
</div>
```

**Large Cards:**
```html
<div class="bg-white rounded-xl p-card-lg">
  <!-- Large card content -->
</div>
```

**Responsive Card Padding:**
```html
<div class="bg-white rounded-xl p-4 sm:p-card lg:p-card-lg">
  <!-- Responsive card padding -->
</section>
```

### Gap Spacing

**Standard Gaps:**
```html
<div class="flex gap-gap">
  <!-- Elements with standard gap -->
</div>

<div class="grid grid-cols-3 gap-gap">
  <!-- Grid with standard gap -->
</div>
```

**Small Gaps:**
```html
<div class="flex gap-gap-sm">
  <!-- Tightly spaced elements -->
</div>
```

**Large Gaps:**
```html
<div class="flex gap-gap-lg">
  <!-- Widely spaced elements -->
</div>
```

### Container Padding

**Standard Container:**
```html
<div class="max-w-9xl mx-auto px-4 sm:px-6 lg:px-8">
  <!-- Container with responsive horizontal padding -->
</div>
```

**Breakpoint Guidelines:**
- Mobile (`px-4`): 16px horizontal padding
- Tablet (`sm:px-6`): 24px horizontal padding
- Desktop (`lg:px-8`): 32px horizontal padding

---

## Spacing Patterns

### Page Layout

```html
<!-- Page Container -->
<div class="max-w-9xl mx-auto px-4 sm:px-6 lg:px-8">
  
  <!-- Section -->
  <section class="py-section">
    <h2 class="mb-6">Section Title</h2>
    
    <!-- Card Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-gap">
      
      <!-- Individual Card -->
      <div class="bg-white rounded-xl p-card">
        <h3 class="mb-4">Card Title</h3>
        <p>Card content</p>
      </div>
      
    </div>
  </section>
  
</div>
```

### Form Layout

```html
<form class="max-w-2xl mx-auto">
  <div class="space-y-6">
    <!-- Form Field -->
    <div>
      <label class="block mb-2">Label</label>
      <input class="w-full px-4 py-3">
    </div>
    
    <!-- Form Actions -->
    <div class="flex gap-4">
      <button class="px-6 py-3">Submit</button>
      <button class="px-6 py-3">Cancel</button>
    </div>
  </div>
</form>
```

### Navigation Spacing

```html
<nav class="px-4 sm:px-6 lg:px-8">
  <div class="flex items-center gap-6">
    <!-- Navigation items -->
  </div>
</nav>
```

---

## Component Spacing Standards

### Buttons

| Size | Padding | Gap (between icons/text) |
|------|---------|-------------------------|
| Small (`sm`) | `px-4 py-2` | `gap-2` |
| Medium (`md`) | `px-6 py-3` | `gap-2` |
| Large (`lg`) | `px-8 py-4` | `gap-3` |

### Cards

| Size | Padding | Margin Bottom |
|------|---------|---------------|
| Default | `p-card` (24px) | `mb-6` (24px) |
| Large | `p-card-lg` (32px) | `mb-8` (32px) |

### Form Elements

| Element | Padding | Margin Bottom |
|---------|---------|---------------|
| Input | `px-4 py-3` | `mb-4` |
| Label | `mb-2` | - |
| Form Group | - | `mb-6` |

### Lists

| Type | Gap | Padding |
|------|-----|---------|
| Vertical List | `space-y-4` | `py-4` |
| Horizontal List | `gap-4` | `px-4` |

---

## Responsive Spacing

### Mobile-First Approach

Always start with mobile spacing and scale up:

```html
<!-- Mobile: tight spacing -->
<!-- Tablet: standard spacing -->
<!-- Desktop: generous spacing -->
<div class="py-8 md:py-section lg:py-section-lg">
  <!-- Content -->
</div>
```

### Breakpoint Guidelines

| Breakpoint | Min Width | Spacing Multiplier |
|------------|-----------|-------------------|
| Mobile | 0px | Base (1x) |
| `sm:` | 640px | 1.25x |
| `md:` | 768px | 1.5x |
| `lg:` | 1024px | 2x |
| `xl:` | 1280px | 2x |

---

## Common Patterns

### Hero Section

```html
<section class="py-section-lg">
  <div class="max-w-9xl mx-auto px-4 sm:px-6 lg:px-8">
    <h1 class="mb-6">Hero Title</h1>
    <p class="mb-8">Hero description</p>
  </div>
</section>
```

### Content Section

```html
<section class="py-section">
  <div class="max-w-9xl mx-auto px-4 sm:px-6 lg:px-8">
    <h2 class="mb-8">Section Title</h2>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-gap">
      <!-- Content -->
    </div>
  </div>
</section>
```

### Card Grid

```html
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-gap">
  <div class="bg-white rounded-xl p-card">
    <!-- Card content -->
  </div>
</div>
```

### Footer

```html
<footer class="py-section">
  <div class="max-w-9xl mx-auto px-4 sm:px-6 lg:px-8">
    <!-- Footer content -->
  </div>
</footer>
```

---

## Migration Guide

### Replacing Inconsistent Spacing

**Before:**
```html
<div class="p-5">  <!-- Inconsistent -->
<div class="py-10">  <!-- Inconsistent -->
<div class="gap-4">  <!-- Inconsistent -->
```

**After:**
```html
<div class="p-card">  <!-- Standardized -->
<div class="py-section">  <!-- Standardized -->
<div class="gap-gap">  <!-- Standardized -->
```

### Common Replacements

| Old Pattern | New Pattern | Reason |
|------------|-------------|--------|
| `p-5` | `p-card` | Standard card padding |
| `p-10` | `p-card-lg` | Large card padding |
| `py-6` | `py-section` | Standard section padding |
| `py-12` | `py-section` | Standard section padding |
| `py-16` | `py-section-lg` | Large section padding |
| `gap-4` | `gap-gap-sm` | Small gap |
| `gap-6` | `gap-gap` | Standard gap |
| `gap-8` | `gap-gap-lg` | Large gap |

---

## Best Practices

### ✅ Do

- Use semantic spacing classes (`p-card`, `py-section`, `gap-gap`)
- Start with mobile spacing and scale up
- Use consistent spacing within components
- Maintain visual rhythm with regular spacing intervals
- Use `space-y-*` for vertical lists
- Use `gap-*` for flex/grid layouts

### ❌ Don't

- Mix different spacing values arbitrarily
- Use hardcoded pixel values in templates
- Skip spacing on mobile (always provide base spacing)
- Use inconsistent padding within the same component type
- Mix `margin` and `padding` without reason

---

## Examples

### Example 1: Landing Page Section

```html
<section class="py-section">
  <div class="max-w-9xl mx-auto px-4 sm:px-6 lg:px-8">
    <h2 class="text-h2 mb-8">Featured Test Banks</h2>
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-gap">
      {% for test_bank in test_banks %}
      <div class="bg-white rounded-xl p-card shadow-sm hover:shadow-lg transition-shadow">
        <h3 class="text-h4 mb-4">{{ test_bank.title }}</h3>
        <p class="text-body">{{ test_bank.description }}</p>
      </div>
      {% endfor %}
    </div>
  </div>
</section>
```

### Example 2: Form Layout

```html
<form class="max-w-2xl mx-auto">
  <div class="space-y-6">
    <div>
      <label class="block text-body-sm font-medium mb-2">Email</label>
      <input type="email" class="w-full px-4 py-3 rounded-lg border border-gray-300">
    </div>
    
    <div>
      <label class="block text-body-sm font-medium mb-2">Password</label>
      <input type="password" class="w-full px-4 py-3 rounded-lg border border-gray-300">
    </div>
    
    <div class="flex gap-4">
      <button class="px-6 py-3 bg-[#5624d0] text-white rounded-lg">Submit</button>
      <button class="px-6 py-3 bg-gray-200 text-gray-900 rounded-lg">Cancel</button>
    </div>
  </div>
</form>
```

### Example 3: Card Component

```html
<div class="bg-white rounded-xl p-card shadow-sm">
  <h3 class="text-h4 mb-4">Card Title</h3>
  <p class="text-body mb-6">Card description</p>
  <div class="flex gap-4">
    <button class="px-6 py-3">Action 1</button>
    <button class="px-6 py-3">Action 2</button>
  </div>
</div>
```

---

## Checklist for Template Updates

When updating templates, ensure:

- [ ] Sections use `py-section` or `py-section-lg`
- [ ] Cards use `p-card` or `p-card-lg`
- [ ] Grids/flex containers use `gap-gap`, `gap-gap-sm`, or `gap-gap-lg`
- [ ] Containers use responsive padding: `px-4 sm:px-6 lg:px-8`
- [ ] Consistent spacing within component types
- [ ] Mobile-first responsive spacing
- [ ] No hardcoded pixel values

---

## Reference

- **Config File:** `theme/static_src/tailwind.config.js`
- **Base Unit:** 4px (Tailwind default)
- **Custom Values:** Defined in `spacing` section of config
- **Component Library:** `templates/components/`

---

*Last Updated: February 23, 2026*  
*Documentation Version: 1.0*
