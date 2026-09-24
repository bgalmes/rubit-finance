import type { Mortgage } from '../app/types/api'

export const purchaseMortgage: Mortgage = {
  id: 1,
  name: 'Flat in town',
  mode: 'purchase',
  tin: '3',
  years: 30,
  frequency: 'monthly',
  purchase_price: '250000',
  initial_savings: '70000',
  initial_expenses: '20000',
  down_payment: '50000',
  loan_amount: '200000.00',
  purchase_percentage: '80.00',
  payment: '843.21',
  total_interest: '103556.37',
  total_paid: '303556.37',
}

export const loanMortgage: Mortgage = {
  id: 2,
  name: 'Mortgage 1',
  mode: 'loan',
  tin: '5',
  years: 10,
  frequency: 'annual',
  purchase_price: null,
  initial_savings: null,
  initial_expenses: null,
  down_payment: null,
  loan_amount: '100000.00',
  purchase_percentage: null,
  payment: '12950.46',
  total_interest: '29504.57',
  total_paid: '129504.57',
}
