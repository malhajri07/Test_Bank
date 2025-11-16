# Tailwind CSS Setup for Udemy-Style Design

The application has been redesigned with a Udemy-like look and feel using Tailwind CSS.

## To See the New Design

You need to build Tailwind CSS. Follow these steps:

### 1. Install Node.js (if not already installed)

**On macOS:**
```bash
brew install node
```

**Or download from:** https://nodejs.org/

### 2. Install Tailwind Dependencies

```bash
cd /Users/mohammedalhajri/Test_Bank
source venv/bin/activate
python manage.py tailwind install
```

### 3. Build Tailwind CSS

**For one-time build:**
```bash
python manage.py tailwind build
```

**For development (auto-rebuild on changes):**
```bash
# Run in a separate terminal
python manage.py tailwind start
```

### 4. Restart Django Server

After building Tailwind, restart your Django server to see the changes:

```bash
python manage.py runserver
```

## Design Features

The new design includes:

- **Udemy-style navigation** - Clean white header with purple/blue gradient logo
- **Modern hero sections** - Gradient backgrounds with call-to-action buttons
- **Card-based layouts** - Clean, professional cards with hover effects
- **Purple/blue color scheme** - Matching Udemy's brand colors
- **Smooth transitions** - Hover effects and animations
- **Responsive design** - Works on all screen sizes
- **Professional typography** - Inter font for English, Cairo for Arabic

## Quick Start

1. Install Node.js
2. Run: `python manage.py tailwind install`
3. Run: `python manage.py tailwind build`
4. Refresh your browser

The design will automatically apply once Tailwind CSS is built!

