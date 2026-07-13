/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        "inverse-primary": "#5d5f5f",
        "on-secondary-fixed": "#001a41",
        "background": "#131313",
        "on-secondary-fixed-variant": "#004493",
        "on-background": "#e5e2e1",
        "surface-dim": "#131313",
        "surface": "#131313",
        "tertiary-fixed-dim": "#c8c6c5",
        "surface-container-low": "#1c1b1b",
        "tertiary": "#ffffff",
        "surface-bright": "#3a3939",
        "secondary": "#adc6ff",
        "surface-container-lowest": "#0e0e0e",
        "secondary-fixed-dim": "#adc6ff",
        "surface-container-high": "#2a2a2a",
        "primary": "#ffffff",
        "secondary-container": "#4b8eff",
        "on-tertiary-fixed-variant": "#474746",
        "on-primary": "#2f3131",
        "on-primary-fixed-variant": "#454747",
        "primary-fixed-dim": "#c6c6c7",
        "outline-variant": "#444748",
        "primary-container": "#e2e2e2",
        "tertiary-fixed": "#e5e2e1",
        "tertiary-container": "#e5e2e1",
        "surface-container": "#201f1f",
        "on-surface": "#e5e2e1",
        "inverse-surface": "#e5e2e1",
        "on-tertiary": "#313030",
        "inverse-on-surface": "#313030",
        "on-tertiary-container": "#656464",
        "error": "#ffb4ab",
        "secondary-fixed": "#d8e2ff",
        "on-surface-variant": "#c4c7c8",
        "error-container": "#93000a",
        "on-primary-fixed": "#1a1c1c",
        "outline": "#8e9192",
        "surface-container-highest": "#353534",
        "primary-fixed": "#e2e2e2",
        "on-tertiary-fixed": "#1b1b1b",
        "surface-tint": "#c6c6c7",
        "on-primary-container": "#636565",
        "on-secondary": "#002e69",
        "on-error-container": "#ffdad6",
        "on-secondary-container": "#00285c",
        "surface-variant": "#353534",
        "on-error": "#690005"
      },
      borderRadius: {
        "DEFAULT": "0.125rem",
        "lg": "0.25rem",
        "xl": "0.5rem",
        "full": "0.75rem"
      },
      spacing: {
        "xs": "8px",
        "gutter": "24px",
        "margin-safe": "48px",
        "xl": "128px",
        "unit": "4px",
        "md": "32px",
        "sm": "16px",
        "lg": "64px",
        "gutter-xl": "80px",
        "nav-width": "280px"
      },
      fontFamily: {
        "display-lg": ["Geist", "sans-serif"],
        "body-md": ["Inter", "sans-serif"],
        "display-lg-mobile": ["Geist", "sans-serif"],
        "label-mono": ["JetBrains Mono", "monospace"],
        "headline-md": ["Geist", "sans-serif"],
        "caption": ["Inter", "sans-serif"],
        "body-lg": ["Inter", "sans-serif"],
        "transcript": ["Newsreader", "serif"]
      },
      fontSize: {
        "display-lg": ["72px", { lineHeight: "80px", letterSpacing: "-0.04em", fontWeight: "200" }],
        "body-md": ["16px", { lineHeight: "24px", letterSpacing: "0.01em", fontWeight: "400" }],
        "display-lg-mobile": ["40px", { lineHeight: "44px", letterSpacing: "-0.02em", fontWeight: "300" }],
        "label-mono": ["12px", { lineHeight: "16px", letterSpacing: "0.08em", fontWeight: "500" }],
        "headline-md": ["32px", { lineHeight: "40px", letterSpacing: "-0.01em", "fontWeight": "400" }],
        "caption": ["13px", { lineHeight: "18px", letterSpacing: "0.02em", fontWeight: "500" }],
        "body-lg": ["18px", { lineHeight: "28px", letterSpacing: "0.01em", fontWeight: "400" }]
      },
      animation: {
        'fade-up-stitch': 'fadeUpStitch 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'pulse-glow': 'pulseGlow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeUpStitch: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseGlow: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '.5' },
        }
      }
    },
  },
  plugins: [],
}
