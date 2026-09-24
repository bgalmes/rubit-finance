// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  // SPA: FastAPI is the backend and serves the generated files.
  ssr: false,
  devtools: { enabled: true },

  modules: ['@nuxt/eslint', '@nuxt/ui', '@nuxtjs/i18n', '@nuxt/test-utils/module'],

  css: ['~/assets/css/main.css'],

  app: {
    head: { title: 'Rubit Finance' },
  },

  // Local app: don't fetch web fonts at build time, and bundle the icons
  // instead of loading them from the Iconify API at runtime.
  ui: { fonts: false },
  icon: { clientBundle: { scan: true }, provider: 'none' },

  i18n: {
    defaultLocale: 'en',
    strategy: 'no_prefix',
    locales: [{ code: 'en', language: 'en', name: 'English', file: 'en.json' }],
  },

  typescript: { strict: true },

  nitro: {
    devProxy: {
      '/api': { target: 'http://127.0.0.1:8000/api', changeOrigin: true },
    },
  },
})
