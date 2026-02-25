# Component Library

Reusable UI components for the Exam Stellar platform.

## Components

### Button Component (`button.html`)

Standardized button component with three styles and three sizes.

**Usage:**
```django
{% include 'components/button.html' with style="primary" size="md" text="Click me" href="/url" %}
{% include 'components/button.html' with style="secondary" size="sm" text="Cancel" %}
{% include 'components/button.html' with style="ghost" size="lg" text="Learn More" %}
```

**Parameters:**
- `style`: `"primary"` (default), `"secondary"`, `"ghost"`
- `size`: `"sm"`, `"md"` (default), `"lg"`
- `text`: Button text (required)
- `href`: URL for link button (optional, creates `<a>` tag)
- `onclick`: JavaScript onclick handler (optional)
- `type`: Button type: `"submit"`, `"button"` (default), `"reset"`
- `class`: Additional CSS classes (optional)
- `disabled`: `"true"` to disable button
- `aria_label`: ARIA label for accessibility (optional)

**Sizes:**
- Small (`sm`): `px-4 py-2 text-sm`
- Medium (`md`): `px-6 py-3 text-sm` (default)
- Large (`lg`): `px-8 py-4 text-base`

---

### Badge Component (`badge.html`)

Semantic badge component for status indicators.

**Usage:**
```django
{% include 'components/badge.html' with text="Easy" type="success" %}
{% include 'components/badge.html' with text="Warning" type="warning" %}
{% include 'components/badge.html' with text="Error" type="error" %}
{% include 'components/badge.html' with text="Info" type="info" %}
```

**Parameters:**
- `text`: Badge text (required)
- `type`: `"success"` (green), `"warning"` (yellow), `"error"` (red), `"info"` (blue), `"purple"` (default)
- `size`: `"sm"` (default), `"md"`, `"lg"`
- `class`: Additional CSS classes (optional)

---

### Card Component (`card.html`)

Reusable card component with consistent styling.

**Usage:**
```django
{% include 'components/card.html' with title="Card Title" content="Card content" %}
{% include 'components/card.html' with title="Card Title" size="large" hover="true" %}
```

**Parameters:**
- `title`: Card title (optional)
- `content`: Card content (optional, can use block content instead)
- `size`: `"default"` (p-6), `"large"` (p-8)
- `hover`: `"true"` to enable hover shadow effect
- `class`: Additional CSS classes (optional)
- `href`: URL to make card clickable (optional, creates link wrapper)

---

### Form Input Component (`form_input.html`)

Standardized form input with label, error handling, and help text.

**Usage:**
```django
{% include 'components/form_input.html' with field=form.username %}
{% include 'components/form_input.html' with field=form.email label="Email Address" %}
{% include 'components/form_input.html' with field=form.password help_text="Must be at least 8 characters" %}
```

**Parameters:**
- `field`: Django form field (required)
- `label`: Custom label text (optional, uses field.label if not provided)
- `help_text`: Help text to display below input (optional)
- `class`: Additional CSS classes for input (optional)
- `wrapper_class`: Additional CSS classes for wrapper div (optional)

**Features:**
- Automatic label generation
- Required field indicator (*)
- Error message display
- Help text support
- Supports text, textarea, and select inputs

---

## Design Principles

All components follow these principles:

1. **Consistency**: Standardized spacing, colors, and typography
2. **Accessibility**: ARIA labels, keyboard navigation, focus states
3. **Responsiveness**: Mobile-first design with breakpoints
4. **Minimalism**: Clean, distraction-free design
5. **Reusability**: Flexible parameters for different use cases

---

## Color Palette

- **Primary**: `#5624d0` (purple)
- **Primary Dark**: `#4a1fb8`
- **Success**: Green (`bg-green-100`, `text-green-800`)
- **Warning**: Yellow (`bg-yellow-100`, `text-yellow-800`)
- **Error**: Red (`bg-red-100`, `text-red-800`)
- **Info**: Blue (`bg-blue-100`, `text-blue-800`)

---

## Spacing Standards

- **Small**: `px-4 py-2` (buttons, badges)
- **Medium**: `px-6 py-3` (default buttons, cards)
- **Large**: `px-8 py-4` (large buttons, large cards)

---

*Last Updated: February 23, 2026*
