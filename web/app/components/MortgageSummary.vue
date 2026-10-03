<script setup lang="ts">
import type { Mortgage } from '~/types/api'

const props = defineProps<{
  mortgage: Mortgage
  /** Whether the mortgage has early amortizations; adds their effect to the stats. */
  amortized?: boolean
}>()
const { t } = useI18n()

const perPeriod = computed(() => t(`frequency.perPeriod.${props.mortgage.frequency}`))
const stats = computed(() => [
  { label: t('fields.loanAmount'), value: formatEUR(props.mortgage.loan_amount) },
  {
    label: t('fields.purchasePercentage'),
    value: formatPercent(props.mortgage.purchase_percentage),
  },
  {
    label: t('fields.payment'),
    value: `${formatEUR(props.mortgage.payment)} ${perPeriod.value}`,
  },
  { label: t('fields.totalInterest'), value: formatEUR(props.mortgage.total_interest) },
  { label: t('fields.totalPaid'), value: formatEUR(props.mortgage.total_paid) },
  ...(props.amortized
    ? [
        {
          label: t('fields.currentPayment'),
          value: `${formatEUR(props.mortgage.current_payment)} ${perPeriod.value}`,
        },
        {
          label: t('fields.totalEarlyAmortized'),
          value: formatEUR(props.mortgage.total_early_amortized),
        },
        { label: t('fields.interestSaved'), value: formatEUR(props.mortgage.interest_saved) },
        {
          label: t('fields.paymentsSaved'),
          value: t(`amortization.count.${props.mortgage.frequency}`, props.mortgage.payments_saved),
        },
      ]
    : []),
])
</script>

<template>
  <div class="space-y-4">
    <div>
      <h1 class="text-2xl font-semibold">
        {{ mortgage.name }}
      </h1>
      <p class="text-muted">
        {{
          t('detail.conditions', {
            tin: Number(mortgage.tin),
            years: mortgage.years,
            frequency: t(`frequency.${mortgage.frequency}`),
          })
        }}
      </p>
    </div>
    <dl class="grid gap-3 sm:grid-cols-3 lg:grid-cols-5">
      <UCard v-for="stat in stats" :key="stat.label" :ui="{ body: 'p-4 sm:p-4' }">
        <dt class="text-sm text-muted">
          {{ stat.label }}
        </dt>
        <dd class="text-lg font-semibold tabular-nums">
          {{ stat.value }}
        </dd>
      </UCard>
    </dl>
  </div>
</template>
