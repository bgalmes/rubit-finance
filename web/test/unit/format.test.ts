import { describe, expect, it } from 'vitest'
import {
  formatDate,
  formatEUR,
  formatMonth,
  formatPercent,
  NOT_AVAILABLE,
} from '../../app/utils/format'

describe('formatEUR', () => {
  it('formats decimal strings as euros', () => {
    expect(formatEUR('843.21')).toBe('€843.21')
    expect(formatEUR('200000.00')).toBe('€200,000.00')
    expect(formatEUR(0)).toBe('€0.00')
  })

  it('shows a dash for missing values', () => {
    expect(formatEUR(null)).toBe(NOT_AVAILABLE)
    expect(formatEUR(undefined)).toBe(NOT_AVAILABLE)
    expect(formatEUR('')).toBe(NOT_AVAILABLE)
    expect(formatEUR('abc')).toBe(NOT_AVAILABLE)
  })
})

describe('formatPercent', () => {
  it('formats percentage points', () => {
    expect(formatPercent('80.00')).toBe('80.00%')
    expect(formatPercent('3')).toBe('3.00%')
    expect(formatPercent('3.125')).toBe('3.125%')
  })

  it('shows a dash for missing values', () => {
    expect(formatPercent(null)).toBe(NOT_AVAILABLE)
  })
})

describe('formatMonth and formatDate', () => {
  it('formats ISO dates', () => {
    expect(formatMonth('2027-03-01')).toBe('Mar 2027')
    expect(formatMonth('2027-12-01')).toBe('Dec 2027')
    expect(formatDate('2027-03-15')).toBe('15 Mar 2027')
  })

  it('shows a dash for missing values', () => {
    expect(formatMonth(null)).toBe(NOT_AVAILABLE)
    expect(formatDate('')).toBe(NOT_AVAILABLE)
    expect(formatDate('nope')).toBe(NOT_AVAILABLE)
  })
})
