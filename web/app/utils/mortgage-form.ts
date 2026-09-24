// Form state, client-side validation (mirrors the API rules) and payload mapping.
// Field names match the API so server-side 422 errors map onto the same fields.
import type { Mortgage, MortgageInput, MortgageMode, PaymentFrequency } from '../types/api'

export interface MortgageFormState {
  mode: MortgageMode
  name: string
  tin: number | null
  years: number | null
  frequency: PaymentFrequency
  purchase_price: number | null
  initial_savings: number | null
  initial_expenses: number | null
  loan_amount: number | null
}

export type MortgageFormField = keyof MortgageFormState

/** `message` is an i18n key under `validation.*`. */
export interface MortgageFormError {
  name: MortgageFormField
  message: string
}

export const MAX_TIN = 100
export const MIN_YEARS = 1
export const MAX_YEARS = 50

export function emptyMortgageForm(): MortgageFormState {
  return {
    mode: 'purchase',
    name: '',
    tin: null,
    years: null,
    frequency: 'monthly',
    purchase_price: null,
    initial_savings: 0,
    initial_expenses: 0,
    loan_amount: null,
  }
}

function toNumberOrNull(value: string | null): number | null {
  return value === null ? null : Number(value)
}

export function mortgageToForm(mortgage: Mortgage): MortgageFormState {
  return {
    mode: mortgage.mode,
    name: mortgage.name,
    tin: Number(mortgage.tin),
    years: mortgage.years,
    frequency: mortgage.frequency,
    purchase_price: toNumberOrNull(mortgage.purchase_price),
    initial_savings: toNumberOrNull(mortgage.initial_savings) ?? 0,
    initial_expenses: toNumberOrNull(mortgage.initial_expenses) ?? 0,
    loan_amount: mortgage.mode === 'loan' ? Number(mortgage.loan_amount) : null,
  }
}

function hasAtMostTwoDecimals(value: number): boolean {
  return Math.abs(Math.round(value * 100) - value * 100) < 1e-6
}

function checkMoney(value: number | null, rule: 'positive' | 'nonNegative'): string | null {
  if (value === null) return rule === 'positive' ? 'validation.required' : null
  if (rule === 'positive' && value <= 0) return 'validation.positive'
  if (rule === 'nonNegative' && value < 0) return 'validation.nonNegative'
  if (!hasAtMostTwoDecimals(value)) return 'validation.cents'
  return null
}

export function validateMortgageForm(state: MortgageFormState): MortgageFormError[] {
  const errors: MortgageFormError[] = []
  const add = (name: MortgageFormField, message: string | null) => {
    if (message) errors.push({ name, message })
  }

  if (state.tin === null) add('tin', 'validation.required')
  else if (state.tin < 0 || state.tin > MAX_TIN) add('tin', 'validation.tinRange')

  if (state.years === null) add('years', 'validation.required')
  else if (!Number.isInteger(state.years) || state.years < MIN_YEARS || state.years > MAX_YEARS) {
    add('years', 'validation.yearsRange')
  }

  if (state.mode === 'purchase') {
    const before = errors.length
    add('purchase_price', checkMoney(state.purchase_price, 'positive'))
    add('initial_savings', checkMoney(state.initial_savings, 'nonNegative'))
    add('initial_expenses', checkMoney(state.initial_expenses, 'nonNegative'))
    const price = state.purchase_price ?? 0
    const savings = state.initial_savings ?? 0
    const expenses = state.initial_expenses ?? 0
    if (errors.length === before && savings >= price + expenses) {
      add('initial_savings', 'validation.savingsTooHigh')
    }
  } else {
    add('loan_amount', checkMoney(state.loan_amount, 'positive'))
  }
  return errors
}

/** Build the API payload. Call only after `validateMortgageForm` returned no errors. */
export function mortgageFormToPayload(state: MortgageFormState): MortgageInput {
  const base = {
    name: state.name.trim() || null,
    tin: String(state.tin ?? 0),
    years: state.years ?? 0,
    frequency: state.frequency,
  }
  if (state.mode === 'purchase') {
    return {
      ...base,
      mode: 'purchase',
      purchase_price: String(state.purchase_price ?? 0),
      initial_savings: String(state.initial_savings ?? 0),
      initial_expenses: String(state.initial_expenses ?? 0),
    }
  }
  return { ...base, mode: 'loan', loan_amount: String(state.loan_amount ?? 0) }
}
