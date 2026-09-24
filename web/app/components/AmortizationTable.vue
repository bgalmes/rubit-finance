<script setup lang="ts">
import type { TableColumn } from '@nuxt/ui'
import type { AmortizationRow, PaymentFrequency } from '~/types/api'

const props = defineProps<{
  schedule: AmortizationRow[]
  frequency: PaymentFrequency
}>()
const { t } = useI18n()

// Monthly schedules show one year per page; annual ones fit on a single page.
const perPage = computed(() => (props.frequency === 'monthly' ? 12 : props.schedule.length))
const page = ref(1)
watch(() => props.schedule, () => (page.value = 1))

const rows = computed(() => {
  const start = (page.value - 1) * perPage.value
  return props.schedule.slice(start, start + perPage.value)
})

const moneyKeys = ['payment', 'interest', 'principal', 'balance', 'amortized'] as const
const columns = computed<TableColumn<AmortizationRow>[]>(() => [
  { accessorKey: 'period', header: t('schedule.period') },
  ...moneyKeys.map(key => ({
    accessorKey: key,
    header: t(`schedule.${key}`),
    cell: ({ row }: { row: { original: AmortizationRow } }) => formatEUR(row.original[key]),
    meta: { class: { td: 'text-right tabular-nums', th: 'text-right' } },
  })),
])
</script>

<template>
  <div class="space-y-3">
    <UTable :data="rows" :columns="columns" class="rounded-md border border-default" />
    <div v-if="schedule.length > perPage" class="flex justify-center">
      <UPagination v-model:page="page" :total="schedule.length" :items-per-page="perPage" />
    </div>
  </div>
</template>
