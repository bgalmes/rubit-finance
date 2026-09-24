<script setup lang="ts">
import type { MortgageInput } from '~/types/api'
import { mortgageToForm } from '~/utils/mortgage-form'

const { t } = useI18n()
const route = useRoute()
const api = useMortgagesApi()

const id = Number(route.params.id)
const { data: mortgage, error } = await useAsyncData(`mortgage-${id}`, () => api.get(id))

async function save(payload: MortgageInput) {
  await api.update(id, payload)
  await navigateTo(`/mortgages/${id}`)
}
</script>

<template>
  <div class="max-w-3xl space-y-6">
    <UAlert
      v-if="error"
      color="error"
      variant="subtle"
      :title="t('common.error', { message: apiErrorMessage(error) })"
    />
    <template v-if="mortgage">
      <h1 class="text-2xl font-semibold">
        {{ t('form.editTitle', { name: mortgage.name }) }}
      </h1>
      <MortgageForm
        :initial="mortgageToForm(mortgage)"
        :save="save"
        @cancel="navigateTo(`/mortgages/${id}`)"
      />
    </template>
  </div>
</template>
