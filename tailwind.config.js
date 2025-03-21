/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./**/templates/**/*.html', './node_modules/flowbite/**/*.js'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f8ff',
          100: '#e0f0fe',
          200: '#b9e2fe',
          300: '#7ccbfd',
          400: '#36b2fa',
          500: '#0c99eb',
          600: '#0071bc',
          700: '#015fa3',
          800: '#065186',
          900: '#0b446f',
          950: '#072b4a',
        },
      },
    },
    fontFamily: {
      body: [
        'Montserrat',
        'ui-sans-serif',
        'system-ui',
        '-apple-system',
        'system-ui',
        'Segoe UI',
        'Roboto',
        'Helvetica Neue',
        'Arial',
        'Noto Sans',
        'sans-serif',
        'Apple Color Emoji',
        'Segoe UI Emoji',
        'Segoe UI Symbol',
        'Noto Color Emoji',
      ],
      sans: [
        'Montserrat',
        'ui-sans-serif',
        'system-ui',
        '-apple-system',
        'system-ui',
        'Segoe UI',
        'Roboto',
        'Helvetica Neue',
        'Arial',
        'Noto Sans',
        'sans-serif',
        'Apple Color Emoji',
        'Segoe UI Emoji',
        'Segoe UI Symbol',
        'Noto Color Emoji',
      ],
    },
  },
  plugins: [require('flowbite/plugin')],
};
