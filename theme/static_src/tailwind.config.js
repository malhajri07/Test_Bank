/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    '../../templates/**/*.html',
    '../../accounts/templates/**/*.html',
    '../../catalog/templates/**/*.html',
    '../../payments/templates/**/*.html',
    '../../practice/templates/**/*.html',
  ],
  theme: {
    extend: {
      colors: {
        // Main color palette
        'primary': '#8FABD4',
        'primary-dark': '#4A70A9',
        'accent': '#EFECE3',
        'text': '#000000',
        'text-light': '#666666',
        'bg': 'rgb(245, 245, 247)',
        // Legacy color names for backward compatibility
        'coursera-blue': '#8FABD4',
        'coursera-blue-dark': '#4A70A9',
        'coursera-text': '#000000',
        'coursera-text-light': '#666666',
        'coursera-bg': 'rgb(245, 245, 247)',
        'coursera-accent': '#EFECE3',
        'purple-accent': '#EFECE3',
        // Apple-style colors
        'apple-bg': 'rgb(245, 245, 247)',
        'apple-text': '#1d1d1f',
        'apple-text-secondary': '#86868b',
        'apple-border': 'rgba(0, 0, 0, 0.1)',
        // Udemy colors
        'udemy-purple': '#5624d0',
        'udemy-purple-dark': '#4a1fb8',
      },
      backgroundColor: {
        'app': 'rgb(245, 245, 247)',
        'default': 'rgb(245, 245, 247)',
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        arabic: ['Cairo', 'sans-serif'],
      },
      maxWidth: {
        '7xl': '960px', // Override default to match custom requirement
        '9xl': '1440px',
      },
      zIndex: {
        '9999': '9999',
        '10000': '10000',
      },
      boxShadow: {
        'swiper-button': '0 4px 12px rgba(0, 0, 0, 0.12)',
        'swiper-button-hover': '0 6px 16px rgba(0, 0, 0, 0.18)',
        'card': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        'card-hover': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        'card-hover-alt': '0 10px 25px rgba(0, 0, 0, 0.1)',
        'btn-coursera': '0 4px 12px rgba(226, 143, 100, 0.3)',
        'btn-coursera-hover': '0 6px 16px rgba(226, 143, 100, 0.4)',
      },
      dropShadow: {
        'card': '0 4px 6px rgba(0, 0, 0, 0.1)',
        'card-hover': '0 10px 15px rgba(0, 0, 0, 0.15)',
      },
      fontSize: {
        // Standardized Typography Scale
        'display': ['3rem', { lineHeight: '1.1', fontWeight: '700', letterSpacing: '-0.02em' }],      // 48px - Hero headings
        'h1': ['2.25rem', { lineHeight: '1.2', fontWeight: '700', letterSpacing: '-0.02em' }],        // 36px - Page titles
        'h2': ['1.875rem', { lineHeight: '1.3', fontWeight: '700', letterSpacing: '-0.02em' }],        // 30px - Section headings
        'h3': ['1.5rem', { lineHeight: '1.4', fontWeight: '600', letterSpacing: '-0.01em' }],          // 24px - Subsection headings
        'h4': ['1.25rem', { lineHeight: '1.5', fontWeight: '600', letterSpacing: '-0.01em' }],        // 20px - Card titles
        'body': ['1rem', { lineHeight: '1.6', fontWeight: '400', letterSpacing: '-0.01em' }],         // 16px - Body text
        'body-sm': ['0.875rem', { lineHeight: '1.5', fontWeight: '400', letterSpacing: '-0.01em' }],  // 14px - Small body text
        'caption': ['0.75rem', { lineHeight: '1.4', fontWeight: '400', letterSpacing: '0' }],         // 12px - Captions, labels
      },
      spacing: {
        // Standardized Spacing Scale
        'section': '3rem',      // 48px - Section padding (py-section)
        'section-lg': '4rem',   // 64px - Large section padding
        'card': '1.5rem',      // 24px - Card padding (p-card)
        'card-lg': '2rem',      // 32px - Large card padding
        'gap': '1.5rem',       // 24px - Standard gap (gap-gap)
        'gap-sm': '1rem',      // 16px - Small gap
        'gap-lg': '2rem',      // 32px - Large gap
      },
      letterSpacing: {
        'apple': '-0.01em',
        'apple-heading': '-0.02em',
      },
      transitionTimingFunction: {
        'apple': 'cubic-bezier(0.4, 0, 0.2, 1)',
      },
    },
  },
  plugins: [
    function({ addBase, addComponents, addUtilities }) {
      addBase({
        '*': {
          '-webkit-font-smoothing': 'antialiased',
          '-moz-osx-font-smoothing': 'grayscale',
        },
        'html': {
          'margin': '0',
          'padding': '0',
          'scroll-behavior': 'smooth',
        },
        'body': {
          'font-weight': '400',
          'letter-spacing': '-0.01em',
        },
        'h1, h2, h3, h4, h5, h6': {
          'font-weight': '600',
          'letter-spacing': '-0.02em',
          'line-height': '1.1',
        },
        'a, button': {
          'transition': 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
        },
      });
      addUtilities({
        '.select-none': {
          '-webkit-user-select': 'none',
          '-moz-user-select': 'none',
          '-ms-user-select': 'none',
          'user-select': 'none',
          '-webkit-touch-callout': 'none',
        },
        '.select-text': {
          '-webkit-user-select': 'text',
          '-moz-user-select': 'text',
          '-ms-user-select': 'text',
          'user-select': 'text',
        },
        '.drag-none': {
          '-webkit-user-drag': 'none',
          '-khtml-user-drag': 'none',
          '-moz-user-drag': 'none',
          '-o-user-drag': 'none',
        },
      });
    },
  ],
}

