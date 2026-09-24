<script setup lang="ts">
const { t } = useI18n()

const nav = computed(() => [
  { label: t('app.nav.mortgages'), to: '/', icon: 'i-lucide-list' },
  { label: t('app.nav.new'), to: '/mortgages/new', icon: 'i-lucide-plus' },
  { label: t('app.nav.compare'), to: '/compare', icon: 'i-lucide-columns-3' },
])
</script>

<template>
  <UApp>
    <NuxtRouteAnnouncer />
    <header class="border-b border-default">
      <UContainer class="flex h-14 items-center justify-between gap-4">
        <NuxtLink to="/" class="font-semibold">
          {{ t('app.title') }}
        </NuxtLink>
        <UNavigationMenu :items="nav" />
      </UContainer>
    </header>
    <UContainer class="py-8">
      <NuxtPage />
    </UContainer>
  </UApp>
</template>
