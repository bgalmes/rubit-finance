import { mountSuspended } from '@nuxt/test-utils/runtime'
import { describe, expect, it } from 'vitest'
import AmortizationTable from '~/components/AmortizationTable.vue'
import type { AmortizationRow } from '~/types/api'

function row(period: number, perYear: number, early = '0.00'): AmortizationRow {
  return {
    period,
    year: Math.floor((period - 1) / perYear) + 1,
    payment: '100.00',
    interest: '10.00',
    principal: '90.00',
    early_amortization: early,
    balance: String(3000 - period * 90),
    amortized: String(period * 90),
  }
}

describe('AmortizationTable', () => {
  it('shows the payment year and the early amortizations of monthly schedules', async () => {
    const schedule = Array.from({ length: 24 }, (_, i) => row(i + 1, 12, i === 2 ? '500.00' : '0.00'))
    const wrapper = await mountSuspended(AmortizationTable, {
      props: { schedule, frequency: 'monthly' },
    })

    const headers = wrapper.findAll('thead th').map(th => th.text())
    expect(headers.slice(0, 2)).toEqual(['Year', 'Period'])
    expect(headers).toContain('Early amortization')
    expect(wrapper.find('[data-testid="year-label"]').text()).toBe('Year 1 of 2')

    const rows = wrapper.findAll('tbody tr')
    expect(rows).toHaveLength(12)
    const third = rows[2]!.findAll('td').map(td => td.text())
    expect(third.slice(0, 2)).toEqual(['1', '3'])
    expect(third).toContain('€500.00')

    await rows[0]!.find('button').trigger('click')
    expect(wrapper.emitted('amortize')).toEqual([[1]])
    const [, remove] = rows[2]!.findAll('button')
    await remove!.trigger('click')
    expect(wrapper.emitted('remove')).toEqual([[3]])
  })

  it('has no year column for annual schedules', async () => {
    const schedule = Array.from({ length: 10 }, (_, i) => row(i + 1, 1))
    const wrapper = await mountSuspended(AmortizationTable, {
      props: { schedule, frequency: 'annual' },
    })
    expect(wrapper.findAll('thead th')[0]!.text()).toBe('Period')
    expect(wrapper.find('[data-testid="year-label"]').exists()).toBe(false)
  })
})
