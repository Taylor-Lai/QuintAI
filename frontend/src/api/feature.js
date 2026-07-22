import request from './request'

export function uploadDocChatApi(formData) {
  return request({
    url: '/doc-chat/upload',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    responseType: 'blob'
  })
}

export function uploadDocExtractApi(formData) {
  return request({
    url: '/doc-extract/upload',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export function uploadTableFillApi(formData) {
  return request({
    url: '/table-fill/upload',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    responseType: 'blob'
  })
}