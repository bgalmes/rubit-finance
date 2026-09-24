// Friendly aliases over the types generated from the API's OpenAPI schema
// (`pnpm gen:api` regenerates openapi.d.ts).
import type { components } from './openapi'

type Schemas = components['schemas']

export type Mortgage = Schemas['MortgageOut']
export type MortgageDetail = Schemas['MortgageDetailOut']
export type AmortizationRow = Schemas['AmortizationRowOut']
export type Comparison = Schemas['ComparisonOut']
export type PurchaseMortgageInput = Schemas['PurchaseMortgageIn']
export type LoanMortgageInput = Schemas['LoanMortgageIn']
export type MortgageInput = PurchaseMortgageInput | LoanMortgageInput
export type MortgageMode = Schemas['MortgageMode']
export type PaymentFrequency = Schemas['PaymentFrequency']
