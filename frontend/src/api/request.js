import axios from 'axios'
import pinia from '../stores'
import { useUserStore } from '../stores/user'

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? (import.meta.env.DEV ? '/api' : ''),
  timeout: 180000
})

service.interceptors.request.use(
  (config) => {
    const userStore = useUserStore(pinia)

    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }

    return config
  },
  (error) => Promise.reject(error)
)

service.interceptors.response.use(
  (response) => {
    // ⭐ 关键：如果是文件流，返回完整 response
    if (response.config.responseType === 'blob') {
      return response
    }

    // 普通 JSON 继续返回 data
    return response.data
  },
  (error) => {
    if (error.response?.status === 401) {
      const userStore = useUserStore(pinia)
      userStore.clearUser()
    }
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      '请求失败'
    return Promise.reject(new Error(message))
  }
)

export default service
