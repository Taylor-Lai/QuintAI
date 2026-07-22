const XLSX_MIME_TYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

export const createExcelBlob = async (headers, sheetName = '模板') => {
  const { default: ExcelJS } = await import('exceljs')
  const workbook = new ExcelJS.Workbook()
  const worksheet = workbook.addWorksheet(sheetName)
  worksheet.addRow(headers)
  worksheet.getRow(1).font = { bold: true }
  worksheet.columns = headers.map(header => ({
    header,
    width: Math.max(String(header).length * 2 + 4, 12)
  }))
  const buffer = await workbook.xlsx.writeBuffer()
  return new Blob([buffer], { type: XLSX_MIME_TYPE })
}

export const downloadExcel = async (headers, fileName, sheetName = '模板') => {
  const blob = await createExcelBlob(headers, sheetName)
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = fileName
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

export { XLSX_MIME_TYPE }
