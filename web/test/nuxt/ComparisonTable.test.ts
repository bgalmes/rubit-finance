import { mountSuspended } from '@nuxt/test-utils/runtime'
import { describe, expect, it } from 'vitest'
import ComparisonTable from '~/components/ComparisonTable.vue'
import { loanMortgage, purchaseMortgage } from '../fixtures'

describe('ComparisonTable', () => {
  it('renders one column per mortgage and dashes for missing purchase data', async () => {
    const wrapper = await mountSuspended(ComparisonTable, {
      props: { mortgages: [purchaseMortgage, loanMortgage] },
    })

    const headers = wrapper.findAll('thead th').map(th => th.text())
    expect(headers).toEqual(['', 'Flat in town', 'Mortgage 1'])

    const priceRow = wrapper.find('[data-row="purchasePrice"]')
    expect(priceRow.find('th').text()).toBe('Purchase price')
    expect(priceRow.findAll('td').map(td => td.text())).toEqual(['€250,000.00', '—'])

    const paymentRow = wrapper.find('[data-row="payment"]')
    expect(paymentRow.findAll('td').map(td => td.text())).toEqual([
      '€843.21 / month',
      '€12,950.46 / year',
    ])
  })
})
