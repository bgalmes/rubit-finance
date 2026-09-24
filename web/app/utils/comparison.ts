// Rows of the comparison table: one row per metric, one value per mortgage.
import type { Mortgage } from '../types/api'
import { formatEUR, formatPercent } from './format'

export interface ComparisonRow {
  key: string
  label: string
  values: string[]
}

type Translate = (key: string) => string

export function buildComparisonRows(mortgages: Mortgage[], t: Translate): ComparisonRow[] {
  const row = (key: string, value: (m: Mortgage) => string): ComparisonRow => ({
    key,
    label: t(`compare.rows.${key}`),
    values: mortgages.map(value),
  })
  return [
    row('name', m => m.name),
    row('years', m => String(m.years)),
    row('tin', m => formatPercent(m.tin)),
    row('frequency', m => t(`frequency.${m.frequency}`)),
    row('purchasePrice', m => formatEUR(m.purchase_price)),
    row('initialSavings', m => formatEUR(m.initial_savings)),
    row('initialExpenses', m => formatEUR(m.initial_expenses)),
    row('downPayment', m => formatEUR(m.down_payment)),
    row('loanAmount', m => formatEUR(m.loan_amount)),
    row('purchasePercentage', m => formatPercent(m.purchase_percentage)),
    row('payment', m => `${formatEUR(m.payment)} ${t(`frequency.perPeriod.${m.frequency}`)}`),
  ]
}
