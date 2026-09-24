import { describe, expect, it } from 'vitest'
import { buildComparisonRows } from '../../app/utils/comparison'
import { loanMortgage, purchaseMortgage } from '../fixtures'

const identity = (key: string) => key

describe('buildComparisonRows', () => {
  const rows = buildComparisonRows([purchaseMortgage, loanMortgage], identity)
  const byKey = Object.fromEntries(rows.map(row => [row.key, row.values]))

  it('has one row per metric, in PLAN.md order', () => {
    expect(rows.map(row => row.key)).toEqual([
      'name',
      'years',
      'tin',
      'frequency',
      'purchasePrice',
      'initialSavings',
      'initialExpenses',
      'downPayment',
      'loanAmount',
      'purchasePercentage',
      'payment',
    ])
    expect(rows[0]?.label).toBe('compare.rows.name')
  })

  it('has one value per mortgage', () => {
    expect(byKey.name).toEqual(['Flat in town', 'Mortgage 1'])
    expect(byKey.loanAmount).toEqual(['€200,000.00', '€100,000.00'])
    expect(byKey.tin).toEqual(['3.00%', '5.00%'])
    expect(byKey.frequency).toEqual(['frequency.monthly', 'frequency.annual'])
    expect(byKey.payment).toEqual([
      '€843.21 frequency.perPeriod.monthly',
      '€12,950.46 frequency.perPeriod.annual',
    ])
  })

  it('shows a dash for purchase data of loan-mode mortgages', () => {
    for (const key of [
      'purchasePrice',
      'initialSavings',
      'initialExpenses',
      'downPayment',
      'purchasePercentage',
    ]) {
      expect(byKey[key]?.[1]).toBe('—')
    }
    expect(byKey.downPayment?.[0]).toBe('€50,000.00')
    expect(byKey.purchasePercentage?.[0]).toBe('80.00%')
  })
})
