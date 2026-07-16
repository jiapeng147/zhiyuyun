export const DEFAULT_PAGE = 'data'
export const NOT_FOUND_PAGE = 'not-found'

function safeDecode(value) {
  try {
    return decodeURIComponent(value)
  } catch {
    return value
  }
}

export function extractHashPage(hash, defaultPage = DEFAULT_PAGE) {
  const route = String(hash || '')
    .replace(/^#\/?/, '')
    .split('?')[0]
    .split('/')[0]
  return safeDecode(route) || defaultPage
}

export function resolveHashRoute(hash, isKnownPage, defaultPage = DEFAULT_PAGE) {
  const requestedPage = extractHashPage(hash, defaultPage)
  const normalizedPage = requestedPage === 'dashboard' ? defaultPage : requestedPage
  const known = Boolean(isKnownPage?.(normalizedPage))
  return {
    page: known ? normalizedPage : NOT_FOUND_PAGE,
    requestedPage,
    known,
  }
}
