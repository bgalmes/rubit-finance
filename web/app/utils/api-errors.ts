// Turn API error responses into form errors / a readable message.

export interface FieldError {
  name: string
  message: string
}

interface ValidationDetail {
  loc: (string | number)[]
  msg: string
}

function errorData(error: unknown): unknown {
  if (typeof error === 'object' && error !== null && 'data' in error) {
    return (error as { data: unknown }).data
  }
  return undefined
}

function isValidationDetail(value: unknown): value is ValidationDetail {
  return (
    typeof value === 'object'
    && value !== null
    && Array.isArray((value as ValidationDetail).loc)
    && typeof (value as ValidationDetail).msg === 'string'
  )
}

/** 422 responses (`{"detail": [{"loc": ["body", "tin"], "msg": ...}]}`) → field errors. */
export function apiFieldErrors(error: unknown): FieldError[] {
  const data = errorData(error)
  if (typeof data !== 'object' || data === null) return []
  const detail = (data as { detail?: unknown }).detail
  if (!Array.isArray(detail)) return []
  return detail.filter(isValidationDetail).map(item => ({
    name: String(item.loc.at(-1) ?? ''),
    message: item.msg,
  }))
}

export function apiErrorMessage(error: unknown): string {
  const data = errorData(error)
  if (typeof data === 'object' && data !== null) {
    const detail = (data as { detail?: unknown }).detail
    if (typeof detail === 'string') return detail
  }
  return error instanceof Error ? error.message : String(error)
}
