<script setup lang="ts">
import type { Mortgage } from '~/types/api'
import { buildComparisonRows } from '~/utils/comparison'

const props = defineProps<{ mortgages: Mortgage[] }>()
const { t } = useI18n()

const rows = computed(() => buildComparisonRows(props.mortgages, key => t(key)))
</script>

<template>
  <div class="overflow-x-auto rounded-md border border-default">
    <table class="min-w-full text-sm" data-testid="comparison-table">
      <thead class="bg-elevated/50">
        <tr>
          <th class="sticky left-0 bg-default px-4 py-3 text-left font-medium" />
          <th
            v-for="mortgage in mortgages"
            :key="mortgage.id"
            class="px-4 py-3 text-right font-semibold"
          >
            <NuxtLink :to="`/mortgages/${mortgage.id}`" class="hover:underline">
              {{ mortgage.name }}
            </NuxtLink>
          </th>
        </tr>
      </thead>
      <tbody class="divide-y divide-default">
        <tr v-for="row in rows.slice(1)" :key="row.key" :data-row="row.key">
          <th class="sticky left-0 bg-default px-4 py-2 text-left font-medium text-muted">
            {{ row.label }}
          </th>
          <td
            v-for="(value, index) in row.values"
            :key="index"
            class="px-4 py-2 text-right tabular-nums"
          >
            {{ value }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
