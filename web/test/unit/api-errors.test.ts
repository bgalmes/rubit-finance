import { describe, expect, it } from 'vitest'
import { apiErrorMessage, apiFieldErrors } from '../../app/utils/api-errors'

describe('apiFieldErrors', () => {
  it('maps FastAPI 422 details to fields', () => {
    const error = {
      data: {
        detail: [
          { type: 'value_error', loc: ['body', 'initial_savings'], msg: 'too high' },
          { type: 'less_than_equal', loc: ['body', 'loan', 'tin'], msg: 'max 100' },
          { unexpected: true },
        ],
      },
    }
    expect(apiFieldErrors(error)).toEqual([
      { name: 'initial_savings', message: 'too high' },
      { name: 'tin', message: 'max 100' },
    ])
  })

  it('returns nothing for other errors', () => {
    expect(apiFieldErrors(new Error('boom'))).toEqual([])
    expect(apiFieldErrors({ data: { detail: 'Mortgage 9 not found' } })).toEqual([])
    expect(apiFieldErrors(null)).toEqual([])
  })
})

describe('apiErrorMessage', () => {
  it('prefers the API detail', () => {
    expect(apiErrorMessage({ data: { detail: 'Mortgage 9 not found' } })).toBe(
      'Mortgage 9 not found',
    )
  })

  it('falls back to the error message', () => {
    expect(apiErrorMessage(new Error('Network down'))).toBe('Network down')
    expect(apiErrorMessage('odd')).toBe('odd')
  })
})
