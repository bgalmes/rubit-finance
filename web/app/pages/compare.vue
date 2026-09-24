<script setup lang="ts">
const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const api = useMortgagesApi()

const { data: mortgages } = await useAsyncData('mortgages', api.list)

// Selection lives in the URL (?ids=1,2) so a comparison can be bookmarked.
const selectedIds = computed<number[]>({
  get: () =>
    String(route.query.ids ?? '')
      .split(',')
      .filter(Boolean)
      .map(Number)
      .filter(Number.isInteger),
  set: ids => router.replace({ query: ids.length ? { ids: ids.join(',') } : {} }),
})

const items = computed(() => (mortgages.value ?? []).map(m => ({ label: m.name, value: m.id })))

const { data: comparison, error } = await useAsyncData(
  () => `compare-${selectedIds.value.join(',')}`,
  () => (selectedIds.value.length >= 2 ? api.compare(selectedIds.value) : Promise.resolve(null)),
)
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-semibold">
      {{ t('compare.title') }}
    </h1>

    <p v-if="(mortgages?.length ?? 0) < 2" class="text-muted">
      {{ t('compare.needMortgages') }}
    </p>
    <template v-else>
      <USelectMenu
        v-model="selectedIds"
        :items="items"
        value-key="value"
        multiple
        :placeholder="t('compare.pick')"
        class="w-full max-w-xl"
      />
      <p v-if="selectedIds.length < 2" class="text-muted">
        {{ t('compare.needTwo') }}
      </p>
    </template>

    <UAlert
      v-if="error"
      color="error"
      variant="subtle"
      :title="t('common.error', { message: apiErrorMessage(error) })"
    />
    <ComparisonTable v-if="comparison" :mortgages="comparison.mortgages" />
  </div>
</template>
