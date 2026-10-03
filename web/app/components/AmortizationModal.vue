<script setup lang="ts">
import type { FormError, FormSubmitEvent } from '@nuxt/ui'
import type { AmortizationInput, PaymentFrequency } from '~/types/api'
import {
  amortizationFormToPayload,
  usesPeriods,
  validateAmortizationForm,
  type AmortizationFormState,
} from '~/utils/amortization-form'

const props = defineProps<{
  period: number
  frequency: PaymentFrequency
  /** Outstanding balance after `period`'s regular payment. */
  balance: number
  initial: AmortizationFormState
  /** Persists the payload. A rejected 422 is shown on the matching fields. */
  save: (payload: AmortizationInput) => Promise<unknown>
}>()
const open = defineModel<boolean>('open', { required: true })

const { t } = useI18n()
const form = useTemplateRef('form')
const state = reactive<AmortizationFormState>({ ...props.initial })
watch(() => props.initial, value => Object.assign(state, value))
const saving = ref(false)
const generalError = ref<string | null>(null)

const typeItems = computed(() => [
  {
    label: t('amortization.type.capital'),
    description: t('amortization.typeHelp.capital'),
    value: 'capital',
  },
  {
    label: t('amortization.type.periods'),
    description: t('amortization.typeHelp.periods'),
    value: 'periods',
  },
])
const entryItems = computed(() => [
  { label: t('amortization.entry.amount'), value: 'amount' },
  { label: t('amortization.entry.periods', { unit: t(`amortization.unit.${props.frequency}`) }), value: 'periods' },
])

function validate(current: AmortizationFormState): FormError[] {
  return validateAmortizationForm(current, props.balance).map(error => ({
    name: error.name,
    message: t(error.message),
  }))
}

async function onSubmit(event: FormSubmitEvent<AmortizationFormState>) {
  generalError.value = null
  saving.value = true
  try {
    await props.save(amortizationFormToPayload(event.data))
    open.value = false
  }
  catch (error) {
    const fieldErrors = apiFieldErrors(error).filter(e => ['amount', 'periods'].includes(e.name))
    if (fieldErrors.length > 0) form.value?.setErrors(fieldErrors)
    else generalError.value = t('common.error', { message: apiErrorMessage(error) })
  }
  finally {
    saving.value = false
  }
}
</script>

<template>
  <UModal
    v-model:open="open"
    :title="t('amortization.title', { period })"
    :description="t('amortization.balanceHint', { balance: formatEUR(balance) })"
  >
    <template #body>
      <UForm
        ref="form"
        :state="state"
        :validate="validate"
        class="space-y-5"
        @submit="onSubmit"
      >
        <UFormField :label="t('amortization.typeLabel')" name="type">
          <URadioGroup v-model="state.type" :items="typeItems" variant="table" />
        </UFormField>

        <UFormField v-if="state.type === 'periods'" :label="t('amortization.entryLabel')" name="entry">
          <URadioGroup
            v-model="state.entry"
            :items="entryItems"
            orientation="horizontal"
            variant="table"
          />
        </UFormField>

        <UFormField
          v-if="usesPeriods(state)"
          :label="t('amortization.periodsLabel', { unit: t(`amortization.unit.${frequency}`) })"
          name="periods"
          required
        >
          <UInputNumber v-model="state.periods" :min="1" :step="1" class="w-full" />
        </UFormField>
        <UFormField v-else :label="t('amortization.amountLabel')" name="amount" required>
          <UInputNumber
            v-model="state.amount"
            :format-options="{ style: 'currency', currency: 'EUR', maximumFractionDigits: 2 }"
            locale="en"
            :min="0"
            :increment="false"
            :decrement="false"
            class="w-full"
          />
        </UFormField>

        <UAlert v-if="generalError" color="error" variant="subtle" :title="generalError" />

        <div class="flex gap-2">
          <UButton type="submit" :loading="saving" :label="t('common.save')" />
          <UButton
            color="neutral"
            variant="ghost"
            :label="t('common.cancel')"
            @click="open = false"
          />
        </div>
      </UForm>
    </template>
  </UModal>
</template>
