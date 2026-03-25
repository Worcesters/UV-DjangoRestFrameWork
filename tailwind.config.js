/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./apps/**/templates/**/*.html",
    "./apps/**/*.py",
    "./static/**/*.js",
  ],
  theme: {
    extend: {},
  },
  /* Classes définies dans les widgets Django (forms.py) : le scanner ne les voit pas toujours */
  safelist: [
    "file:mr-3",
    "file:rounded-lg",
    "file:border-0",
    "file:bg-indigo-50",
    "file:bg-fuchsia-50",
    "file:bg-teal-50",
    "file:px-3",
    "file:py-1.5",
    "file:text-xs",
    "file:font-bold",
    "file:text-indigo-700",
    "file:text-fuchsia-700",
    "file:text-teal-700",
    "hover:file:bg-indigo-100",
    "hover:file:bg-fuchsia-100",
    "hover:file:bg-teal-100",
  ],
  plugins: [],
};
