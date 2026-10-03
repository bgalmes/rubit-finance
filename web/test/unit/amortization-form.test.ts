import { describe, expect, it } from 'vitest'
import {
  amortizationFormToPayload,
  amortizationToForm,
  emptyAmortizationForm,
  validateAmortizationForm,
  type AmortizationFormState,
} from '../../app/utils/amortization-form'

function form(changes: Partial<AmortizationFormState> = {}): AmortizationFormState {
  return { ...emptyAmortizationForm(), amount: 1000, ...changes }
}

const errorsOf = (state: AmortizationFormState, balance = 5000) =>
  validateAmortizationForm(state, balance).map(e => `${e.name}:${e.message}`)

describe('validateAmortizationForm', () => {
  it('accepts valid forms', () => {
    expect(errorsOf(form())).toEqual([])
    expect(errorsOf(form({ amount: 5000 }))).toEqual([])
    expect(errorsOf(form({ type: 'periods', entry: 'periods', amount: null, periods: 12 }))).toEqual([])
  })

  it('checks the amount', () => {
    expect(errorsOf(form({ amount: null }))).toEqual(['amount:validation.required'])
    expect(errorsOf(form({ amount: 0 }))).toEqual(['amount:validation.positive'])
    expect(errorsOf(form({ amount: 1.005 }))).toEqual(['amount:validation.cents'])
    expect(errorsOf(form({ amount: 5000.01 }))).toEqual(['amount:validation.aboveBalance'])
  })

  it('checks the number of periods', () => {
    const periods = (value: number | null) => form({ type: 'periods', entry: 'periods', periods: value })
    expect(errorsOf(periods(null))).toEqual(['periods:validation.required'])
    expect(errorsOf(periods(0))).toEqual(['periods:validation.wholePositive'])
    expect(errorsOf(periods(1.5))).toEqual(['periods:validation.wholePositive'])
  })

  it('ignores the periods entry for capital amortizations', () => {
    expect(errorsOf(form({ type: 'capital', entry: 'periods', periods: null }))).toEqual([])
  })
})

describe('amortizationFormToPayload', () => {
  it('sends the amount or the periods', () => {
    expect(amortizationFormToPayload(form({ amount: 1234.5 }))).toEqual({
      type: 'capital',
      amount: '1234.5',
    })
    expect(amortizationFormToPayload(form({ type: 'periods' }))).toEqual({
      type: 'periods',
      amount: '1000',
    })
    expect(amortizationFormToPayload(form({ type: 'periods', entry: 'periods', periods: 6 }))).toEqual({
      type: 'periods',
      periods: 6,
    })
  })
})

describe('amortizationToForm', () => {
  it('round-trips stored amortizations', () => {
    const byAmount = { period: 3, type: 'capital', amount: '2000', periods: null, applied_amount: '2000.00' } as const
    expect(amortizationToForm(byAmount)).toEqual({ type: 'capital', entry: 'amount', amount: 2000, periods: null })
    const byPeriods = { period: 3, type: 'periods', amount: null, periods: 4, applied_amount: '3100.20' } as const
    expect(amortizationToForm(byPeriods)).toEqual({ type: 'periods', entry: 'periods', amount: null, periods: 4 })
  })
})
