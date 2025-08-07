export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Sora", "sans-serif"],
      },
      colors: {
        primary: '#07f468',
        dark: {
          DEFAULT: '#181c2b',
          light: '#23272e',
        },
        light: '#fff',
      },
      backgroundImage: {
        'gradient-green-dark': 'linear-gradient(135deg, #07f468 0%, #23272e 100%)',
        'gradient-dark': 'linear-gradient(135deg, #23272e 0%, #181c2b 100%)',
        'gradient-green-white': 'linear-gradient(135deg, #fff 0%, #07f468 100%)',
      },
    },
  },
  plugins: [],
}; 