<script setup lang="ts">
import type { MortgageInput } from '~/types/api'

const { t } = useI18n()
const api = useMortgagesApi()

async function save(payload: MortgageInput) {
  const created = await api.create(payload)
  // The detail page doubles as the configuration summary.
  await navigateTo(`/mortgages/${created.id}`)
}
</script>

<template>
  <div class="max-w-3xl space-y-6">
    <h1 class="text-2xl font-semibold">
      {{ t('form.newTitle') }}
    </h1>
    <MortgageForm :save="save" @cancel="navigateTo('/')" />
  </div>
</template>
