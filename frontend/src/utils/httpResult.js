export function formatFileSize(size) {
  if (!size && size !== 0) return '--'
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

export function getFileNameFromDisposition(contentDisposition = '') {
  if (!contentDisposition) return ''

  const utf8Match = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i)
  if (utf8Match?.[1]) {
    try {
      return decodeURIComponent(utf8Match[1])
    } catch {
      return utf8Match[1]
    }
  }

  const normalMatch = contentDisposition.match(/filename="?([^";]+)"?/i)
  return normalMatch?.[1] || ''
}

export function isBlobLike(value) {
  return typeof Blob !== 'undefined' && value instanceof Blob
}

export function parseJsonSafely(value) {
  if (typeof value !== 'string') return value

  try {
    return JSON.parse(value)
  } catch {
    return value
  }
}
