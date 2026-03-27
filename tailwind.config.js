/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html"
  ],
  theme: {
    extend: {
      colors: {
        // Surface Hierarchy (No-Line Rule)
        background: '#060e20',
        surface: '#060e20',
        'surface-container-lowest': '#091328',
        'surface-container-low': '#0f1930',
        'surface-container': '#0f1930',
        'surface-container-high': '#141f38',
        'surface-container-highest': '#192540',
        'surface-bright': '#1f2b49',
        
        // Primary (Indigo/Violet Spectrum)
        primary: '#a3a6ff',
        'primary-dim': '#6063ee',
        'primary-fixed': '#9396ff',
        'primary-fixed-dim': '#8387ff',
        
        // Secondary
        secondary: '#a28efc',
        'secondary-fixed': '#d6cbff',
        'secondary-dim': '#a28efc',
        
        // Tertiary
        tertiary: '#ffa5d9',
        'tertiary-fixed': '#ff8ed2',
        'tertiary-dim': '#ef81c4',
        
        // Error
        error: '#ff6e84',
        'error-dim': '#d73357',
        
        // Text Colors
        'on-surface': '#dee5ff',
        'on-surface-variant': '#a3aac4',
        'on-primary': '#0f00a4',
        'on-primary-fixed': '#000000',
        'on-primary-fixed-variant': '#0e009d',
        'on-secondary': '#21006d',
        'on-tertiary': '#701455',
        
        // Other
        outline: '#6d758c',
        'outline-variant': '#40485d',
      },
      fontFamily: {
        headline: ['Manrope', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
        label: ['Inter', 'sans-serif'],
      },
      borderRadius: {
        'none': '0',
        'sm': '0.25rem',
        'DEFAULT': '0.5rem',
        'md': '0.75rem',
        'lg': '1rem',
        'xl': '1.5rem',
        '2xl': '2rem',
        'full': '9999px',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.5s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  darkMode: 'class',
  plugins: [],
}
