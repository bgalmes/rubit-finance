// Display formatting. The API sends Decimals as strings; converting to number
// here is for display only, all maths happens in the API.

export const NOT_AVAILABLE = '—'

type Numeric = string | number | null | undefined

const eurFormatter = new Intl.NumberFormat('en', { style: 'currency', currency: 'EUR' })
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
