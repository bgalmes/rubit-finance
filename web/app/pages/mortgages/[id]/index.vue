<script setup lang="ts">
const { t } = useI18n()
const route = useRoute()
const api = useMortgagesApi()

const id = computed(() => Number(route.params.id))
const { data: mortgage, error } = await useAsyncData(
  () => `mortgage-${id.value}`,
  () => api.get(id.value),
)
const { data: mortgages } = await useAsyncData('mortgages', api.list)

const switcherItems = computed(() =>
  (mortgages.value ?? []).map(m => ({ label: m.name, value: m.id })),
)
const selectedId = computed({
  get: () => id.value,
  set: (value: number) => navigateTo(`/mortgages/${value}`),
})

async function remove() {
  if (!mortgage.value) return
  if (!window.confirm(t('list.deleteConfirm', { name: mortgage.value.name }))) return
  await api.remove(mortgage.value.id)
  await navigateTo('/')
}
</script>

<template>
  <div class="space-y-8">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <UFormField :label="t('detail.switch')" orientation="horizontal">
        <USelect v-model="selectedId" :items="switcherItems" class="min-w-56" />
      </UFormField>
      <div v-if="mortgage" class="flex gap-2">
        <UButton
          :to="`/mortgages/${mortgage.id}/edit`"
          icon="i-lucide-pencil"
          color="neutral"
          variant="outline"
          :label="t('common.edit')"
        />
        <UButton
          icon="i-lucide-trash-2"
          color="error"
          variant="outline"
          :label="t('common.delete')"
          @click="remove"
        />
      </div>
    </div>

    <UAlert
      v-if="error"
      color="error"
      variant="subtle"
      :title="t('common.error', { message: apiErrorMessage(error) })"
    />

    <template v-if="mortgage">
      <MortgageSummary :mortgage="mortgage" />
      <section class="space-y-3">
        <h2 class="text-lg font-semibold">
          {{ t('detail.schedule') }}
        </h2>
        <AmortizationTable :schedule="mortgage.schedule" :frequency="mortgage.frequency" />
      </section>
    </template>
  </div>
</template>
