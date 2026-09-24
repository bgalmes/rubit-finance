<script setup lang="ts">
import type { FormError, FormSubmitEvent } from '@nuxt/ui'
import type { MortgageInput } from '~/types/api'
import {
  emptyMortgageForm,
  mortgageFormToPayload,
  validateMortgageForm,
  type MortgageFormState,
} from '~/utils/mortgage-form'

const props = defineProps<{
  initial?: MortgageFormState
  /** Persists the payload. A rejected 422 is shown on the matching fields. */
  save: (payload: MortgageInput) => Promise<unknown>
}>()
const emit = defineEmits<{ cancel: [] }>()

const { t } = useI18n()
const form = useTemplateRef('form')
const state = reactive<MortgageFormState>({ ...(props.initial ?? emptyMortgageForm()) })
const saving = ref(false)
const generalError = ref<string | null>(null)

const modeItems = computed(() => [
  { label: t('mode.purchase'), value: 'purchase' },
  { label: t('mode.loan'), value: 'loan' },
])
const frequencyItems = computed(() => [
  { label: t('frequency.monthly'), value: 'monthly' },
  { label: t('frequency.annual'), value: 'annual' },
])

const moneyInput = {
  formatOptions: { style: 'currency', currency: 'EUR', maximumFractionDigits: 2 },
  locale: 'en',
  min: 0,
  increment: false,
  decrement: false,
  class: 'w-full',
} as const

function validate(current: MortgageFormState): FormError[] {
  return validateMortgageForm(current).map(error => ({
    name: error.name,
    message: t(error.message),
  }))
}

async function onSubmit(event: FormSubmitEvent<MortgageFormState>) {
  generalError.value = null
  saving.value = true
  try {
    await props.save(mortgageFormToPayload(event.data))
  }
  catch (error) {
    const fieldErrors = apiFieldErrors(error)
    if (fieldErrors.length > 0) form.value?.setErrors(fieldErrors)
    else generalError.value = t('common.error', { message: apiErrorMessage(error) })
  }
  finally {
    saving.value = false
  }
}
</script>

<template>
  <UForm
    ref="form"
    :state="state"
    :validate="validate"
    class="space-y-6"
    @submit="onSubmit"
  >
    <UFormField :label="t('fields.name')" name="name">
      <UInput v-model="state.name" :placeholder="t('fields.namePlaceholder')" class="w-full" />
    </UFormField>

    <UFormField :label="t('form.modeLabel')" name="mode">
      <URadioGroup
        v-model="state.mode"
        :items="modeItems"
        orientation="horizontal"
        variant="table"
      />
    </UFormField>

    <div v-if="state.mode === 'purchase'" class="grid gap-4 sm:grid-cols-3">
      <UFormField :label="t('fields.purchasePrice')" name="purchase_price" required>
        <UInputNumber v-model="state.purchase_price" v-bind="moneyInput" />
      </UFormField>
      <UFormField :label="t('fields.initialSavings')" name="initial_savings">
        <UInputNumber v-model="state.initial_savings" v-bind="moneyInput" />
      </UFormField>
      <UFormField
        :label="t('fields.initialExpenses')"
        :help="t('fields.initialExpensesHelp')"
        name="initial_expenses"
      >
        <UInputNumber v-model="state.initial_expenses" v-bind="moneyInput" />
      </UFormField>
    </div>
    <div v-else class="grid gap-4 sm:grid-cols-3">
      <UFormField :label="t('fields.loanAmount')" name="loan_amount" required>
        <UInputNumber v-model="state.loan_amount" v-bind="moneyInput" />
      </UFormField>
    </div>

    <div class="grid gap-4 sm:grid-cols-3">
      <UFormField :label="t('fields.tin')" name="tin" required>
        <UInputNumber
          v-model="state.tin"
          :format-options="{ maximumFractionDigits: 4 }"
          locale="en"
          :min="0"
          :max="100"
          :step="0.05"
          class="w-full"
        />
      </UFormField>
      <UFormField :label="t('fields.years')" name="years" required>
        <UInputNumber v-model="state.years" :min="1" :max="50" :step="1" class="w-full" />
      </UFormField>
      <UFormField :label="t('fields.frequency')" name="frequency" required>
        <USelect v-model="state.frequency" :items="frequencyItems" class="w-full" />
      </UFormField>
    </div>

    <UAlert v-if="generalError" color="error" variant="subtle" :title="generalError" />

    <div class="flex gap-2">
      <UButton type="submit" :loading="saving" :label="t('common.save')" />
      <UButton color="neutral" variant="ghost" :label="t('common.cancel')" @click="emit('cancel')" />
    </div>
  </UForm>
</template>
