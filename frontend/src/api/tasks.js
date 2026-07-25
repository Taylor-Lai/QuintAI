import request from './request'

export const getTasks = (params) => request.get('/tasks', { params })
export const getTask = (id) => request.get(`/tasks/${id}`)
export const getTaskReport = (id) => request.get(`/tasks/${id}/report`)
export const retryTask = (id) => request.post(`/tasks/${id}/retry`)
export const cancelTask = (id) => request.post(`/tasks/${id}/cancel`)
export const downloadTask = (id) => request.get(`/tasks/${id}/download`, { responseType: 'blob' })
