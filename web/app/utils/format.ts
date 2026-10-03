// Display formatting. The API sends Decimals as strings; converting to number
// here is for display only, all maths happens in the API.

export const NOT_AVAILABLE = '—'

type Numeric = string | number | null | undefined

const eurFormatter = new Intl.NumberFormat('en', { style: 'currency', currency: 'EUR' })
// Dates come as ISO `YYYY-MM-DD`; formatting in UTC keeps them on the same day everywhere.
const monthFormatter = new Intl.DateTimeFormat('en', {
  month: 'short',
  year: 'numeric',
  timeZone: 'UTC',
})
const dateFormatter = new Intl.DateTimeFormat('en-GB', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
  timeZone: 'UTC',
})
const percentFormatter = new Intl.NumberFormat('en', {
  style: 'percent',
  minimumFractionDigits: 2,
  maximumFractionDigits: 4,
})

function toNumber(value: Numeric): number | null {
  if (value === null || value === undefined || value === '') return null
  const n = Number(value)
  return Number.isFinite(n) ? n : null
}

/** `"843.21"` → `"€843.21"`; missing values → `"—"`. */
export function formatEUR(value: Numeric): string {
  const n = toNumber(value)
  return n === null ? NOT_AVAILABLE : eurFormatter.format(n)
}

/** Percentage points: `"80"` → `"80.00%"`, `"3.125"` → `"3.125%"`; missing values → `"—"`. */
export function formatPercent(value: Numeric): string {
  const n = toNumber(value)
  return n === null ? NOT_AVAILABLE : percentFormatter.format(n / 100)
}

function toDate(value: string | null | undefined): Date | null {
  if (!value) return null
  const date = new Date(`${value}T00:00:00Z`)
  return Number.isNaN(date.getTime()) ? null : date
}

/** `"2027-03-01"` → `"Mar 2027"`; missing values → `"—"`. */
export function formatMonth(value: string | null | undefined): string {
  const date = toDate(value)
  return date === null ? NOT_AVAILABLE : monthFormatter.format(date)
}

/** `"2027-03-15"` → `"15 Mar 2027"`; missing values → `"—"`. */
export function formatDate(value: string | null | undefined): string {
  const date = toDate(value)
  return date === null ? NOT_AVAILABLE : dateFormatter.format(date)
}
