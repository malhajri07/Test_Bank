# 🎯 Design Fixes Action Plan

**Based on:** `DESIGN_AUDIT_REPORT.md`  
**Priority:** High Impact, Quick Wins First

---

## Quick Wins (Implement First - 1-2 Days)

### 1. Remove Yellow Highlight Inconsistency ⚡

**Issue:** Yellow `<mark>` tags (`#fde047`) feel inconsistent with minimalist design.

**Fix:**
- Replace with purple accent or remove entirely
- Use subtle background or border instead

**Files to Update:**
- `templates/catalog/index.html` (lines 38, 42, 91, 94, 266)
- `templates/practice/practice_results.html` (lines 44, 76)
- `templates/accounts/dashboard.html` (lines 11, 72, 178)
- Any other templates using `<mark>` tags

**Action:**
```django
<!-- Replace this: -->
<mark class="bg-[#fde047] text-gray-900 px-3 rounded-sm">Text</mark>

<!-- With this: -->
<span class="bg-[#5624d0]/10 text-[#5624d0] px-3 py-1 rounded-lg font-semibold">Text</span>
```

---

### 2. Standardize Button Sizes ⚡

**Issue:** Buttons have inconsistent padding (`px-4 py-2`, `px-5 py-2.5`, `px-6 py-3`, `px-8 py-4`).

**Fix:** Create 3 standard sizes:
- Small: `px-4 py-2` (for secondary actions)
- Medium: `px-6 py-3` (default)
- Large: `px-8 py-4` (primary CTAs)

**Action:** Search and replace button classes across templates.

---

### 3. Fix Color Contrast Issues ⚡

**Issue:** Some text colors may not meet WCAG AA (4.5:1 contrast ratio).

**Fix:**
- Audit all `text-gray-500` and `text-gray-600` usage
- Replace with darker grays if needed
- Test with contrast checker tool

**Action:**
```bash
# Use browser DevTools or online contrast checker
# Replace low-contrast colors:
text-gray-500 → text-gray-600
text-gray-400 → text-gray-500
```

---

### 4. Add Missing ARIA Labels ⚡

**Issue:** Icons and buttons missing accessibility labels.

**Fix:** Add `aria-label` to all icon-only buttons and decorative elements.

**Files to Check:**
- `templates/base.html` (navigation icons)
- `templates/catalog/index.html` (carousel buttons)
- All templates with SVG icons

**Action:**
```django
<!-- Add aria-label to icon buttons -->
<button aria-label="{% trans 'Previous slide' %}">
    <svg>...</svg>
</button>
```

---

### 5. Standardize Card Padding ⚡

**Issue:** Cards use inconsistent padding (`p-5`, `p-6`, `p-8`, `p-10`).

**Fix:** Standardize to `p-6` (default) and `p-8` (large cards).

**Action:** Search and replace padding classes in card components.

---

## Component Library Creation (Week 1)

### Create Reusable Components

**1. Button Component**
```django
<!-- templates/components/button.html -->
{% comment %}
Usage: {% include 'components/button.html' with style="primary" size="md" text="Click" href="/url" %}
Styles: primary, secondary, ghost
Sizes: sm, md, lg
{% endcomment %}
```

**2. Form Input Component**
```django
<!-- templates/components/form_input.html -->
{% comment %}
Usage: {% include 'components/form_input.html' with field=form.username %}
Includes: label, input, error message, help text
{% endcomment %}
```

**3. Card Component**
```django
<!-- templates/components/card.html -->
{% comment %}
Usage: {% include 'components/card.html' with title="Title" content=content %}
Standardized padding, shadows, hover states
{% endcomment %}
```

**4. Badge Component**
```django
<!-- templates/components/badge.html -->
{% comment %}
Usage: {% include 'components/badge.html' with text="Easy" type="success" %}
Types: success, warning, error, info
{% endcomment %}
```

---

## Typography System (Week 1-2)

### Create Typography Utilities

**Add to `tailwind.config.js`:**
```javascript
theme: {
  extend: {
    fontSize: {
      'display': ['3rem', { lineHeight: '1.1', fontWeight: '700' }],
      'h1': ['2.25rem', { lineHeight: '1.2', fontWeight: '700' }],
      'h2': ['1.875rem', { lineHeight: '1.3', fontWeight: '700' }],
      'h3': ['1.5rem', { lineHeight: '1.4', fontWeight: '600' }],
      'h4': ['1.25rem', { lineHeight: '1.5', fontWeight: '600' }],
      'body': ['1rem', { lineHeight: '1.6', fontWeight: '400' }],
      'small': ['0.875rem', { lineHeight: '1.5', fontWeight: '400' }],
      'caption': ['0.75rem', { lineHeight: '1.4', fontWeight: '500' }],
    },
  }
}
```

**Usage:**
```django
<h1 class="text-display">Display Text</h1>
<h2 class="text-h1">Heading 1</h2>
<p class="text-body">Body text</p>
```

---

## Spacing System (Week 2)

### Standardize Spacing Values

**Create spacing constants:**
- Cards: `p-6` (default), `p-8` (large)
- Sections: `py-12` (default), `py-16` (large)
- Gaps: `gap-6` (default), `gap-8` (large)
- Max width: `max-w-9xl` (1440px) for all main content

**Action:** Update all templates to use standardized spacing.

---

## Accessibility Improvements (Week 3)

### Priority Fixes

1. **Keyboard Navigation**
   - Test all interactive elements
   - Ensure focus indicators are visible
   - Add skip links

2. **Screen Reader Support**
   - Add `aria-live` regions for dynamic content
   - Associate form errors with inputs
   - Add descriptive alt text to images

3. **Color Contrast**
   - Audit all color combinations
   - Fix low-contrast text
   - Test with contrast checker

---

## Mobile Optimization (Week 3-4)

### Touch Targets

**Fix:** Ensure all interactive elements are at least 44x44px.

**Action:**
```django
<!-- Update small buttons -->
<button class="w-11 h-11">  <!-- Too small -->
<button class="w-12 h-12">  <!-- Better (48px) -->
```

### Text Sizes

**Fix:** Increase base font size on mobile.

**Action:**
```django
<!-- Use responsive text sizes -->
<p class="text-base sm:text-lg">Text</p>
```

---

## Implementation Checklist

### Quick Wins (Day 1-2)
- [ ] Remove yellow highlight from all templates
- [ ] Standardize button sizes
- [ ] Fix color contrast issues
- [ ] Add missing ARIA labels
- [ ] Standardize card padding

### Component Library (Week 1)
- [ ] Create button component
- [ ] Create form input component
- [ ] Create card component
- [ ] Create badge component
- [ ] Update templates to use components

### Typography System (Week 1-2)
- [ ] Add typography utilities to Tailwind config
- [ ] Update heading styles
- [ ] Update body text styles
- [ ] Document typography system

### Spacing System (Week 2)
- [ ] Standardize padding values
- [ ] Standardize gap values
- [ ] Standardize max-width values
- [ ] Update all templates

### Accessibility (Week 3)
- [ ] Add ARIA labels
- [ ] Fix color contrast
- [ ] Test keyboard navigation
- [ ] Add screen reader support
- [ ] Test with screen readers

### Mobile Optimization (Week 3-4)
- [ ] Fix touch targets
- [ ] Adjust text sizes
- [ ] Test on real devices
- [ ] Fix spacing issues

---

## Testing Checklist

### Design Consistency
- [ ] All buttons use component system
- [ ] All forms use component system
- [ ] Consistent spacing across pages
- [ ] Consistent typography hierarchy

### Accessibility
- [ ] WCAG AA compliance (4.5:1 contrast)
- [ ] Keyboard navigation works
- [ ] Screen reader compatible
- [ ] All images have alt text

### Mobile
- [ ] All touch targets ≥ 44x44px
- [ ] Text readable without zooming
- [ ] Navigation works on mobile
- [ ] Forms usable on mobile

### Performance
- [ ] Lighthouse score > 90
- [ ] Images optimized
- [ ] JavaScript minified
- [ ] CSS purged properly

---

## Next Steps

1. **Review** `DESIGN_AUDIT_REPORT.md` for detailed analysis
2. **Prioritize** fixes based on impact
3. **Start** with Quick Wins (Day 1-2)
4. **Create** component library (Week 1)
5. **Implement** systematically (Week 2-4)
6. **Test** thoroughly at each stage
7. **Document** design system for future reference

---

*Last Updated: February 23, 2026*
