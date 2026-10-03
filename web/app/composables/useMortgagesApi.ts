import type {
  AmortizationInput,
  Comparison,
  Mortgage,
  MortgageDetail,
  MortgageInput,
} from '~/types/api'

const BASE = '/api/mortgages'

export function useMortgagesApi() {
  return {
    list: () => $fetch<Mortgage[]>(BASE),
    get: (id: number) => $fetch<MortgageDetail>(`${BASE}/${id}`),
    create: (body: MortgageInput) => $fetch<MortgageDetail>(BASE, { method: 'POST', body }),
    update: (id: number, body: MortgageInput) =>
      $fetch<MortgageDetail>(`${BASE}/${id}`, { method: 'PUT', body }),
    remove: (id: number) => $fetch(`${BASE}/${id}`, { method: 'DELETE' }),
    saveAmortization: (id: number, period: number, body: AmortizationInput) =>
      $fetch<MortgageDetail>(`${BASE}/${id}/amortizations/${period}`, { method: 'PUT', body }),
    removeAmortization: (id: number, period: number) =>
      $fetch<MortgageDetail>(`${BASE}/${id}/amortizations/${period}`, { method: 'DELETE' }),
    compare: (ids: number[]) =>
      $fetch<Comparison>(`${BASE}/compare`, { query: { ids: ids.join(',') } }),
  }
}
