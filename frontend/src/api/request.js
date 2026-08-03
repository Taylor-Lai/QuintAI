import axios from 'axios'
import pinia from '../stores'
import { useUserStore } from '../stores/user'

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api',
  timeout: 180000,
  withCredentials: true
})

service.interceptors.response.use(
  (response) => {
    // 文件下载需要保留响应头和状态码。
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
