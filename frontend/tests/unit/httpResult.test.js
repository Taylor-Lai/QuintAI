import { describe, expect, it } from 'vitest'

import {
  formatFileSize,
  getFileNameFromDisposition,
  isBlobLike,
  parseJsonSafely
} from '../../src/utils/httpResult'

describe('HTTP result utilities', () => {
  it('formats byte sizes at stable unit boundaries', () => {
    expect(formatFileSize(0)).toBe('0 B')
    expect(formatFileSize(1024)).toBe('1.0 KB')
    expect(formatFileSize(1024 * 1024)).toBe('1.0 MB')
    expect(formatFileSize(undefined)).toBe('--')
  })

  it('prefers and decodes RFC 5987 filenames', () => {
    expect(
      getFileNameFromDisposition(
        "attachment; filename=ignored.xlsx; filename*=UTF-8''%E7%BB%93%E6%9E%9C.xlsx"
      )
    ).toBe('结果.xlsx')
    expect(getFileNameFromDisposition('attachment; filename="report.docx"')).toBe('report.docx')
  })

  it('keeps malformed filenames and non-JSON response text usable', () => {
    expect(getFileNameFromDisposition("attachment; filename*=UTF-8''bad%ZZ.txt")).toBe('bad%ZZ.txt')
    expect(parseJsonSafely('{"status":"success"}')).toEqual({ status: 'success' })
    expect(parseJsonSafely('plain text')).toBe('plain text')
  })

  it('recognizes Blob responses', () => {
    expect(isBlobLike(new Blob(['result']))).toBe(true)
    expect(isBlobLike({ size: 6 })).toBe(false)
  })
})
