import axios from 'axios'
import pinia from '../store'
import { useUserStore } from '../store/modules/user'

const service = axios.create({
  baseURL: '',
  timeout: 15000
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
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      '请求失败'
    return Promise.reject(new Error(message))
  }
)

export default service