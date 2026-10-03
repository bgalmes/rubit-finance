<script setup lang="ts">
import type { AmortizationInput } from '~/types/api'
import {
  amortizationToForm,
  emptyAmortizationForm,
  type AmortizationFormState,
} from '~/utils/amortization-form'

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

const modalOpen = ref(false)
const modalPeriod = ref(1)
const modalInitial = ref<AmortizationFormState>(emptyAmortizationForm())
const modalBalance = computed(() => {
  const row = mortgage.value?.schedule.find(r => r.period === modalPeriod.value)
  // The balance before this period's amortization, which is what it can repay.
  return row ? Number(row.balance) + Number(row.early_amortization) : 0
})

function openAmortization(period: number) {
  const existing = mortgage.value?.amortizations.find(a => a.period === period)
  modalPeriod.value = period
  modalInitial.value = existing ? amortizationToForm(existing) : emptyAmortizationForm()
  modalOpen.value = true
}

async function saveAmortization(payload: AmortizationInput) {
  mortgage.value = await api.saveAmortization(id.value, modalPeriod.value, payload)
}

async function removeAmortization(period: number) {
  if (!window.confirm(t('amortization.removeConfirm', { period }))) return
  mortgage.value = await api.removeAmortization(id.value, period)
}

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
      <MortgageSummary :mortgage="mortgage" :amortized="mortgage.amortizations.length > 0" />
      <section class="space-y-3">
        <h2 class="text-lg font-semibold">
          {{ t('detail.schedule') }}
        </h2>
        <AmortizationTable
          :key="mortgage.id"
          :schedule="mortgage.schedule"
          :frequency="mortgage.frequency"
          @amortize="openAmortization"
          @remove="removeAmortization"
        />
      </section>
      <AmortizationModal
        v-model:open="modalOpen"
        :period="modalPeriod"
        :frequency="mortgage.frequency"
        :balance="modalBalance"
        :initial="modalInitial"
        :save="saveAmortization"
      />
    </template>
  </div>
</template>
