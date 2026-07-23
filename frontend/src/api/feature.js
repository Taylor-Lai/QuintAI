import request from './request'

export function uploadDocChatApi(formData) {
  return request({
    url: '/doc-chat/upload',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
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
    }
  })
}

export function getTaskApi(taskId) {
  return request.get(`/tasks/${taskId}`)
}

export function downloadTaskApi(taskId) {
  return request.get(`/tasks/${taskId}/download`, { responseType: 'blob' })
}

export async function waitForTask(taskId, onProgress, timeoutMs = 20 * 60 * 1000) {
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    const task = await getTaskApi(taskId)
    onProgress?.(task)
    if (task.status === 'succeeded') return task
    if (task.status === 'failed' || task.status === 'cancelled') {
      throw new Error(task.error?.message || task.stage || '任务执行失败')
    }
    await new Promise((resolve) => window.setTimeout(resolve, 1000))
  }
  throw new Error('任务等待超时，可稍后在任务记录中查看结果')
}
