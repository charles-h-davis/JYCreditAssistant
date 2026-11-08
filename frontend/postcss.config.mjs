/**
 * Tailwind v4 via PostCSS.
 *
 * The scaffolded app used `@tailwindcss/turbopack`, which only runs under
 * Turbopack. This machine lacks Turbopack's native bindings (so `dev`/`build`
 * pass `--webpack`), which means the PostCSS plugin has to do the work instead.
 */
const config = {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};

export default config;
