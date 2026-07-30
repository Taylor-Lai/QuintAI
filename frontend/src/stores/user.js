import { defineStore } from 'pinia'
import {
  heartbeatApi,
  loginApi,
  logoutApi,
  registerApi,
  getProfileApi,
  updateProfileApi
} from '../api/auth'

const USER_KEY = 'sc_user'
let heartbeatTimer = null

function getLocalUser() {
  try {
    const userStr = localStorage.getItem(USER_KEY)
    return userStr ? JSON.parse(userStr) : null
  } catch {
    localStorage.removeItem(USER_KEY)
    return null
  }
}

export const useUserStore = defineStore('user', {
  state: () => ({
    userInfo: getLocalUser(),
    loading: false,
    sessionChecked: false
  }),

  getters: {
    isLogin: (state) => !!state.userInfo,
    username: (state) => state.userInfo?.username || '',
    email: (state) => state.userInfo?.email || ''
  },

  actions: {
    setUserInfo(userInfo) {
      const mergedUser = {
        avatar: '',
        username: '',
        nickname: userInfo?.username || '',
        email: '',
        gender: '未设置',
        phone: '未设置',
        role: '普通用户',
        ...userInfo
      }

      this.userInfo = mergedUser
      localStorage.setItem(USER_KEY, JSON.stringify(mergedUser))
    },

    clearUser() {
      this.stopHeartbeat()
      this.userInfo = null
      localStorage.removeItem(USER_KEY)
    },

    async loginAction(payload) {
      this.loading = true
      try {
        const res = await loginApi(payload)
        // 按后端返回结构取值
        const user = res.user_info

        if (user) {
          this.setUserInfo(user)
        }
        this.sessionChecked = true

        this.startHeartbeat()

        return res
      } finally {
        this.loading = false
      }
    },

    async registerAction(payload) {
      this.loading = true
      try {
        const res = await registerApi(payload)
        // 注册接口当前不返回 token
        return res
      } finally {
        this.loading = false
      }
    },

    async updateProfileAction(payload) {
      const res = await updateProfileApi(payload)
      if (res && typeof res === 'object' && ('username' in res || 'email' in res || 'nickname' in res)) {
        this.setUserInfo({
          ...this.userInfo,
          ...res
        })
      } else {
        this.setUserInfo({
          ...this.userInfo,
          ...payload
        })
      }

      return res
    },


    async getProfileAction() {
      const res = await getProfileApi()
      this.setUserInfo(res.data || res)
      return res.data || res
    },

    async initializeSession() {
      if (this.sessionChecked) return this.userInfo
      try {
        const user = await this.getProfileAction()
        this.startHeartbeat()
        return user
      } catch {
        this.clearUser()
        return null
      } finally {
        this.sessionChecked = true
      }
    },

    async logoutAction() {
      try {
        if (this.userInfo) await logoutApi()
      } finally {
        this.clearUser()
      }
    },

    startHeartbeat() {
      this.stopHeartbeat()
      if (!this.userInfo) return
      heartbeatApi().catch(() => {})
      heartbeatTimer = window.setInterval(() => {
        heartbeatApi().catch(() => {})
      }, 5 * 60 * 1000)
    },

    stopHeartbeat() {
      if (heartbeatTimer) {
        window.clearInterval(heartbeatTimer)
        heartbeatTimer = null
      }
    }
  }
})
