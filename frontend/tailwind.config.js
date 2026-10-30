/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: '#FFFFFF',
        'bg-subtle': '#F7F8FA',
        'bg-muted': '#EFF1F5',
        surface: '#FFFFFF',
        'surface-glass': 'rgba(255, 255, 255, 0.72)',
        border: '#E4E7EC',
        'border-strong': '#D0D5DD',
        text: {
          DEFAULT: '#0B1220',
          secondary: '#475467',
          tertiary: '#667085',
        },
        brand: {
          DEFAULT: '#0A66FF',
          hover: '#0052CC',
          soft: '#EAF2FF',
        },
        accent: {
          teal: '#0EA5A4',
        },
        status: {
          pass: '#067647',
          'pass-bg': '#ECFDF3',
          fail: '#B42318',
          'fail-bg': '#FEF3F2',
          notrun: '#475467',
          'notrun-bg': '#F2F4F7',
          pending: '#B54708',
          'pending-bg': '#FFFAEB',
          unverified: '#6941C6',
          'unverified-bg': '#F4F3FF',
          tested: '#175CD3',
          'tested-bg': '#EFF8FF',
          disclaimer: '#B54708',
          'disclaimer-bg': '#FFFAEB',
        },
        flood: {
          d1: '#D6F0FF', // 0 - 0.5m
          d2: '#8FD0F8', // 0.5 - 1.5m
          d3: '#41A6E8', // 1.5 - 3m
          d4: '#1874C7', // 3 - 5m
          d5: '#0B4C99', // 5 - 8m
          d6: '#062B5F', // > 8m
        },
        map: {
          evac: '#12B76A',
          severed: '#F04438',
          marooned: '#F79009',
          extent: '#0A66FF',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Inter Display', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['Geist Mono', 'JetBrains Mono', 'monospace'],
        devanagari: ['Noto Sans Devanagari', 'sans-serif'],
      },
      boxShadow: {
        sm: '0 1px 2px rgba(16, 24, 40, 0.05)',
        md: '0 4px 12px rgba(16, 24, 40, 0.06), 0 1px 3px rgba(16, 24, 40, 0.04)',
        lg: '0 24px 48px -12px rgba(16, 24, 40, 0.12)',
      },
      borderRadius: {
        sm: '8px',
        md: '12px',
        lg: '16px',
        xl: '24px',
        pill: '9999px',
      },
    },
  },
  plugins: [],
};
