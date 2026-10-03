// Early amortization form: state, client-side validation (mirrors the API rules) and payload.
// Field names match the API so server-side 422 errors map onto the same fields.
import type { Amortization, AmortizationInput, AmortizationType } from '../types/api'
import { hasAtMostTwoDecimals } from './mortgage-form'

/** How a periods amortization is entered: an amount, or the number of periods to cut. */
export type AmortizationEntry = 'amount' | 'periods'

export interface AmortizationFormState {
  type: AmortizationType
  entry: AmortizationEntry
  amount: number | null
  periods: number | null
}

/** `message` is an i18n key under `validation.*`. */
export interface AmortizationFormError {
  name: 'amount' | 'periods'
  message: string
}

export function emptyAmortizationForm(): AmortizationFormState {
  return { type: 'capital', entry: 'amount', amount: null, periods: null }
}

export function amortizationToForm(amortization: Amortization): AmortizationFormState {
  return {
    type: amortization.type,
    entry: amortization.periods === null ? 'amount' : 'periods',
    amount: amortization.amount === null ? null : Number(amortization.amount),
    periods: amortization.periods,
  }
}

/** Capital amortizations are always entered as an amount. */
export function usesPeriods(state: AmortizationFormState): boolean {
  return state.type === 'periods' && state.entry === 'periods'
}

/** `balance` is the outstanding balance the amortization is applied to. */
export function validateAmortizationForm(
  state: AmortizationFormState,
  balance: number,
): AmortizationFormError[] {
  if (usesPeriods(state)) {
    if (state.periods === null) return [{ name: 'periods', message: 'validation.required' }]
    if (!Number.isInteger(state.periods) || state.periods < 1) {
      return [{ name: 'periods', message: 'validation.wholePositive' }]
    }
    return []
  }
  if (state.amount === null) return [{ name: 'amount', message: 'validation.required' }]
  if (state.amount <= 0) return [{ name: 'amount', message: 'validation.positive' }]
  if (!hasAtMostTwoDecimals(state.amount)) return [{ name: 'amount', message: 'validation.cents' }]
  if (state.amount > balance) return [{ name: 'amount', message: 'validation.aboveBalance' }]
  return []
}

/** Build the API payload. Call only after `validateAmortizationForm` returned no errors. */
export function amortizationFormToPayload(state: AmortizationFormState): AmortizationInput {
  if (usesPeriods(state)) return { type: state.type, periods: state.periods ?? 0 }
  return { type: state.type, amount: String(state.amount ?? 0) }
}
