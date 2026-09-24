<script setup lang="ts">
import type { TableColumn } from '@nuxt/ui'
import type { Mortgage } from '~/types/api'

const { t } = useI18n()
const api = useMortgagesApi()
const { data: mortgages, status, error, refresh } = await useAsyncData('mortgages', api.list)

const columns = computed<TableColumn<Mortgage>[]>(() => [
  { accessorKey: 'name', header: t('fields.name') },
  {
    accessorKey: 'loan_amount',
    header: t('fields.loanAmount'),
    cell: ({ row }) => formatEUR(row.original.loan_amount),
  },
  {
    accessorKey: 'payment',
    header: t('fields.payment'),
    cell: ({ row }) =>
      `${formatEUR(row.original.payment)} ${t(`frequency.perPeriod.${row.original.frequency}`)}`,
  },
  { accessorKey: 'tin', header: t('fields.tin'), cell: ({ row }) => formatPercent(row.original.tin) },
  { accessorKey: 'years', header: t('fields.years') },
  { id: 'actions', header: '' },
])

async function remove(mortgage: Mortgage) {
  if (!window.confirm(t('list.deleteConfirm', { name: mortgage.name }))) return
  await api.remove(mortgage.id)
  await refresh()
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-semibold">
        {{ t('list.title') }}
      </h1>
      <UButton to="/mortgages/new" icon="i-lucide-plus" :label="t('app.nav.new')" />
    </div>

    <UAlert
      v-if="error"
      color="error"
      variant="subtle"
      :title="t('common.error', { message: apiErrorMessage(error) })"
    />

    <UTable
      :data="mortgages ?? []"
      :columns="columns"
      :loading="status === 'pending'"
      :empty="t('list.empty')"
      class="rounded-md border border-default"
    >
      <template #name-cell="{ row }">
        <NuxtLink :to="`/mortgages/${row.original.id}`" class="font-medium hover:underline">
          {{ row.original.name }}
        </NuxtLink>
      </template>
      <template #actions-cell="{ row }">
        <div class="flex justify-end gap-1">
          <UButton
            :to="`/mortgages/${row.original.id}`"
            icon="i-lucide-eye"
            color="neutral"
            variant="ghost"
            :aria-label="t('common.view')"
          />
          <UButton
            :to="`/mortgages/${row.original.id}/edit`"
            icon="i-lucide-pencil"
            color="neutral"
            variant="ghost"
            :aria-label="t('common.edit')"
          />
          <UButton
            icon="i-lucide-trash-2"
            color="error"
            variant="ghost"
            :aria-label="t('common.delete')"
            @click="remove(row.original)"
          />
        </div>
      </template>
    </UTable>
  </div>
</template>
