import { describe, expect, it } from 'vitest'
import {
  emptyMortgageForm,
  mortgageFormToPayload,
  mortgageToForm,
  sameConditions,
  validateMortgageForm,
  type MortgageFormState,
} from '../../app/utils/mortgage-form'
import { loanMortgage, purchaseMortgage } from '../fixtures'

function purchaseForm(changes: Partial<MortgageFormState> = {}): MortgageFormState {
  return {
    ...emptyMortgageForm(),
    tin: 3,
    years: 30,
    purchase_price: 250000,
    initial_savings: 70000,
    initial_expenses: 20000,
    ...changes,
  }
}

function loanForm(changes: Partial<MortgageFormState> = {}): MortgageFormState {
  return { ...emptyMortgageForm(), mode: 'loan', tin: 3, years: 30, loan_amount: 200000, ...changes }
}

const errorsOf = (state: MortgageFormState) =>
  validateMortgageForm(state).map(e => `${e.name}:${e.message}`)

describe('validateMortgageForm', () => {
  it('accepts valid forms', () => {
    expect(errorsOf(purchaseForm())).toEqual([])
    expect(errorsOf(loanForm())).toEqual([])
    expect(errorsOf(loanForm({ tin: 0, years: 1 }))).toEqual([])
    expect(errorsOf(loanForm({ tin: 100, years: 50 }))).toEqual([])
  })

  it('requires the common fields', () => {
    expect(errorsOf(emptyMortgageForm())).toEqual([
      'tin:validation.required',
      'years:validation.required',
      'purchase_price:validation.required',
    ])
  })

  it('checks ranges', () => {
    expect(errorsOf(loanForm({ tin: 100.01 }))).toEqual(['tin:validation.tinRange'])
    expect(errorsOf(loanForm({ tin: -1 }))).toEqual(['tin:validation.tinRange'])
    expect(errorsOf(loanForm({ years: 0 }))).toEqual(['years:validation.yearsRange'])
    expect(errorsOf(loanForm({ years: 51 }))).toEqual(['years:validation.yearsRange'])
    expect(errorsOf(loanForm({ years: 2.5 }))).toEqual(['years:validation.yearsRange'])
  })

  it('checks money fields', () => {
    expect(errorsOf(loanForm({ loan_amount: null }))).toEqual(['loan_amount:validation.required'])
    expect(errorsOf(loanForm({ loan_amount: 0 }))).toEqual(['loan_amount:validation.positive'])
    expect(errorsOf(loanForm({ loan_amount: 10.001 }))).toEqual(['loan_amount:validation.cents'])
    expect(errorsOf(purchaseForm({ initial_savings: -1 }))).toEqual([
      'initial_savings:validation.nonNegative',
    ])
    expect(errorsOf(purchaseForm({ initial_expenses: null }))).toEqual([])
  })

  it('requires something to borrow', () => {
    expect(errorsOf(purchaseForm({ initial_savings: 270000 }))).toEqual([
      'initial_savings:validation.savingsTooHigh',
    ])
    expect(errorsOf(purchaseForm({ initial_savings: 269999.99 }))).toEqual([])
  })

  it('ignores the fields of the other mode', () => {
    expect(errorsOf(loanForm({ purchase_price: -5 }))).toEqual([])
    expect(errorsOf(purchaseForm({ loan_amount: -5 }))).toEqual([])
  })
})

describe('mortgageFormToPayload', () => {
  it('builds a purchase payload', () => {
    expect(mortgageFormToPayload(purchaseForm({ name: '  Flat  ' }))).toEqual({
      mode: 'purchase',
      name: 'Flat',
      tin: '3',
      years: 30,
      frequency: 'monthly',
      start_date: null,
      purchase_price: '250000',
      initial_savings: '70000',
      initial_expenses: '20000',
    })
  })

  it('builds a loan payload with a blank name', () => {
    expect(mortgageFormToPayload(loanForm({ frequency: 'annual' }))).toEqual({
      mode: 'loan',
      name: null,
      tin: '3',
      years: 30,
      frequency: 'annual',
      start_date: null,
      loan_amount: '200000',
    })
  })

  it('sends the signing date when set', () => {
    expect(mortgageFormToPayload(loanForm({ start_date: '2027-03-15' }))).toMatchObject({
      start_date: '2027-03-15',
    })
  })
})

describe('mortgageToForm', () => {
  it('round-trips a purchase mortgage', () => {
    const state = mortgageToForm(purchaseMortgage)
    expect(state).toMatchObject({
      mode: 'purchase',
      name: 'Flat in town',
      purchase_price: 250000,
      initial_savings: 70000,
      initial_expenses: 20000,
      loan_amount: null,
    })
    expect(validateMortgageForm(state)).toEqual([])
  })

  it('round-trips a loan mortgage', () => {
    const state = mortgageToForm(loanMortgage)
    expect(state).toMatchObject({
      mode: 'loan',
      tin: 5,
      frequency: 'annual',
      loan_amount: 100000,
      purchase_price: null,
      initial_savings: 0,
      start_date: '',
    })
    expect(validateMortgageForm(state)).toEqual([])
  })

  it('round-trips the signing date', () => {
    const state = mortgageToForm({ ...loanMortgage, start_date: '2027-03-15' })
    expect(state.start_date).toBe('2027-03-15')
    expect(mortgageFormToPayload(state).start_date).toBe('2027-03-15')
  })
})

describe('sameConditions', () => {
  const loan = mortgageFormToPayload(loanForm())

  it('ignores the name and number formatting', () => {
    expect(sameConditions(loan, { ...loan, name: 'Other' })).toBe(true)
    expect(sameConditions(loan, { ...loan, tin: '3.000' })).toBe(true)
  })

  it('detects changed conditions', () => {
    expect(sameConditions(loan, { ...loan, years: 25 })).toBe(false)
    expect(sameConditions(loan, { ...loan, frequency: 'annual' })).toBe(false)
    expect(sameConditions(loan, { ...loan, start_date: '2027-03-15' })).toBe(false)
    expect(sameConditions(loan, mortgageFormToPayload(purchaseForm()))).toBe(false)
  })
})
