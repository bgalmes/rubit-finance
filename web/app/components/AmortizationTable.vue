<script setup lang="ts">
import type { TableColumn } from '@nuxt/ui'
import type { AmortizationRow, PaymentFrequency } from '~/types/api'

const props = defineProps<{
  schedule: AmortizationRow[]
  frequency: PaymentFrequency
}>()
const emit = defineEmits<{
  /** Add or edit the early amortization made after `period`'s payment. */
  amortize: [period: number]
  remove: [period: number]
}>()
const { t } = useI18n()

// Monthly schedules show one year per page; annual ones fit on a single page.
const isMonthly = computed(() => props.frequency === 'monthly')
const perPage = computed(() => (isMonthly.value ? 12 : props.schedule.length))
const pageCount = computed(() => Math.max(1, Math.ceil(props.schedule.length / perPage.value)))
const page = ref(1)
// Amortizations can shorten the schedule: stay on the same year while it still exists.
watch(pageCount, count => (page.value = Math.min(page.value, count)))

const rows = computed(() => {
  const start = (page.value - 1) * perPage.value
  return props.schedule.slice(start, start + perPage.value)
})

const hasEarly = (row: AmortizationRow) => Number(row.early_amortization) > 0

const money = (key: 'payment' | 'interest' | 'principal' | 'balance' | 'amortized') => ({
  accessorKey: key,
  header: t(`schedule.${key}`),
  cell: ({ row }: { row: { original: AmortizationRow } }) => formatEUR(row.original[key]),
  meta: { class: { td: 'text-right tabular-nums', th: 'text-right' } },
})
const right = { class: { td: 'text-right tabular-nums', th: 'text-right' } }

const columns = computed<TableColumn<AmortizationRow>[]>(() => [
  ...(isMonthly.value ? [{ accessorKey: 'year', header: t('schedule.year') }] : []),
  { accessorKey: 'period', header: t('schedule.period') },
  money('payment'),
  money('interest'),
  money('principal'),
  {
    accessorKey: 'early_amortization',
    header: t('schedule.earlyAmortization'),
    cell: ({ row }) => (hasEarly(row.original) ? formatEUR(row.original.early_amortization) : ''),
    meta: right,
  },
  money('balance'),
  money('amortized'),
  { id: 'actions', header: '', meta: { class: { td: 'text-right' } } },
])
</script>

<template>
  <div class="space-y-3">
    <UTable :data="rows" :columns="columns" class="rounded-md border border-default">
      <template #actions-cell="{ row }">
        <div v-if="hasEarly(row.original)" class="flex justify-end gap-1">
          <UButton
            icon="i-lucide-pencil"
            size="xs"
            color="neutral"
            variant="ghost"
            :aria-label="t('amortization.edit')"
            @click="emit('amortize', row.original.period)"
          />
          <UButton
            icon="i-lucide-trash-2"
            size="xs"
            color="error"
            variant="ghost"
            :aria-label="t('amortization.remove')"
            @click="emit('remove', row.original.period)"
          />
        </div>
        <UButton
          v-else-if="Number(row.original.balance) > 0"
          icon="i-lucide-piggy-bank"
          size="xs"
          color="neutral"
          variant="ghost"
          :label="t('amortization.add')"
          @click="emit('amortize', row.original.period)"
        />
      </template>
    </UTable>
    <div v-if="pageCount > 1" class="flex flex-wrap items-center justify-center gap-3">
      <span class="text-sm text-muted" data-testid="year-label">
        {{ t('schedule.yearOf', { year: page, total: pageCount }) }}
      </span>
      <UPagination v-model:page="page" :total="schedule.length" :items-per-page="perPage" />
    </div>
  </div>
</template>
