/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      colors: {
        // Tokens legados wa-* remapeados para paleta Aray
        wa: {
          green: '#00A3FF',
          dark: '#020617',
          panel: '#0A1628',
          chat: '#050A14',
          bubble: '#0B4F8A',
          bubbleIn: '#0F1D32',
          muted: '#94A3B8',
          border: '#1E3A5F',
          accent: '#FFB800',
        },
        aray: {
          primary: '#00A3FF',
          'primary-dark': '#0047AB',
          accent: '#FFB800',
          'accent-muted': '#FFA500',
          dark: '#020617',
          panel: '#0A1628',
          chat: '#050A14',
          bubble: '#0B4F8A',
          bubbleIn: '#0F1D32',
          muted: '#94A3B8',
          border: '#1E3A5F',
        },
      },
      fontSize: {
        display: ['2rem', { lineHeight: '2.5rem', fontWeight: '700' }],
        title: ['1.25rem', { lineHeight: '1.75rem', fontWeight: '600' }],
        body: ['0.875rem', { lineHeight: '1.25rem' }],
        caption: ['0.75rem', { lineHeight: '1rem' }],
      },
      borderRadius: {
        panel: '0.75rem',
        card: '1rem',
      },
      boxShadow: {
        panel: '0 4px 24px rgba(0, 0, 0, 0.35)',
        'glow-green': '0 0 24px rgba(0, 163, 255, 0.25)',
        'glow-green-lg': '0 0 48px rgba(0, 163, 255, 0.15)',
        'glow-accent': '0 0 24px rgba(255, 184, 0, 0.2)',
      },
      keyframes: {
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'slide-up': {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-in-right': {
          '0%': { opacity: '0', transform: 'translateX(-8px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        'glow-pulse': {
          '0%, 100%': { opacity: '0.4' },
          '50%': { opacity: '0.8' },
        },
        'progress-indeterminate': {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(400%)' },
        },
      },
      animation: {
        'fade-in': 'fade-in 0.3s ease-out forwards',
        'slide-up': 'slide-up 0.35s ease-out forwards',
        'slide-in-right': 'slide-in-right 0.25s ease-out forwards',
        shimmer: 'shimmer 1.5s infinite linear',
        'glow-pulse': 'glow-pulse 4s ease-in-out infinite',
        'progress-indeterminate': 'progress-indeterminate 1.2s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
