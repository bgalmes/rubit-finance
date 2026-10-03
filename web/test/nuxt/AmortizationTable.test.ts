import { mountSuspended } from '@nuxt/test-utils/runtime'
import { describe, expect, it } from 'vitest'
import AmortizationTable from '~/components/AmortizationTable.vue'
import type { AmortizationRow } from '~/types/api'

function row(period: number, perYear: number, early = '0.00', date: string | null = null): AmortizationRow {
  return {
    date,
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

  it('shows payment dates and pages by calendar year when the mortgage has a signing date', async () => {
    // Signed in Mar 2027: period 0 is the interest-only stub, period 1 is Apr 2027.
    const schedule = Array.from({ length: 25 }, (_, i) => {
      const month = 2 + i // 0-based month index from Jan 2027
      const date = `${2027 + Math.floor(month / 12)}-${String((month % 12) + 1).padStart(2, '0')}-01`
      return { ...row(i, 12, '0.00', date), year: Math.max(1, Math.floor((i - 1) / 12) + 1) }
    })
    const wrapper = await mountSuspended(AmortizationTable, {
      props: { schedule, frequency: 'monthly' },
    })

    expect(wrapper.findAll('thead th').map(th => th.text()).slice(0, 2)).toEqual(['Date', 'Period'])
    expect(wrapper.find('[data-testid="year-label"]').text()).toBe('2027')
    const rows = wrapper.findAll('tbody tr')
    // Mar..Dec 2027
    expect(rows).toHaveLength(10)
    expect(rows[0]!.findAll('td').map(td => td.text()).slice(0, 2)).toEqual(['Mar 2027', '0'])
    expect(rows[0]!.find('button').exists()).toBe(false)
    expect(rows[1]!.find('button').exists()).toBe(true)
    expect(rows.at(-1)!.find('td').text()).toBe('Dec 2027')
  })

  it('shows the calendar year of annual schedules with a signing date', async () => {
    const schedule = Array.from({ length: 4 }, (_, i) => row(i, 1, '0.00', `${2027 + i}-12-01`))
    const wrapper = await mountSuspended(AmortizationTable, {
      props: { schedule, frequency: 'annual' },
    })
    expect(wrapper.findAll('thead th')[0]!.text()).toBe('Year')
    expect(wrapper.findAll('tbody tr').map(tr => tr.find('td').text())).toEqual([
      '2027',
      '2028',
      '2029',
      '2030',
    ])
    expect(wrapper.find('[data-testid="year-label"]').exists()).toBe(false)
  })
})
