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
      },
      backgroundColor: {
        'app': 'rgb(245, 245, 247)',
        'default': 'rgb(245, 245, 247)',
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        arabic: ['Cairo', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

