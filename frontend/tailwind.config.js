/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#EF816B',
        'primary-light': '#DEDAD9',
        'primary-dark': '#D46A52',
        accent: '#F4A896',
        success: '#10B981',
        warning: '#F59E0B',
        error: '#EF4444',
        'gray-50': '#F9FAFB',
        'gray-100': '#F3F4F6',
        'gray-200': '#E5E7EB',
        'gray-600': '#4B5563',
        'gray-800': '#1F2937',
        'gray-900': '#111827',
      },
      borderRadius: {
        'smooth': '16px',
        'smoother': '20px',
      },
    },
  },
  plugins: [],
}
