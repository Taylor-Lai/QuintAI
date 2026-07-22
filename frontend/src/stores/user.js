import { defineStore } from 'pinia'
import {
  heartbeatApi,
  loginApi,
  logoutApi,
  registerApi,
  getProfileApi,
  updateProfileApi
} from '../api/auth'

const TOKEN_KEY = 'sc_token'
const USER_KEY = 'sc_user'
const HISTORY_KEY = 'sc_history'
let heartbeatTimer = null

function getLocalToken() {
  return localStorage.getItem(TOKEN_KEY) || ''
}

function getLocalUser() {
  const userStr = localStorage.getItem(USER_KEY)
  return userStr ? JSON.parse(userStr) : null
}

function getLocalHistory() {
  const historyStr = localStorage.getItem(HISTORY_KEY)
  return historyStr ? JSON.parse(historyStr) : []
}

export const useUserStore = defineStore('user', {
  state: () => ({
    token: getLocalToken(),
    userInfo: getLocalUser(),
    historyList: getLocalHistory(),
    loading: false
  }),

  getters: {
    isLogin: (state) => !!state.token,
    username: (state) => state.userInfo?.username || '',
    email: (state) => state.userInfo?.email || ''
  },

  actions: {
    setToken(token) {
      this.token = token
      localStorage.setItem(TOKEN_KEY, token)
    },

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

    setHistoryList(list) {
      this.historyList = list
      localStorage.setItem(HISTORY_KEY, JSON.stringify(list))
    },

    addHistoryRecord(record) {
      const newRecord = {
        id: Date.now(),
        fileName: record.fileName || '未知文件',
        type: record.type || '未知类型',
        time: record.time || new Date().toLocaleString(),
        status: record.status || '处理完成',
        summary: record.summary || ''
      }

      const nextList = [newRecord, ...this.historyList]
      this.setHistoryList(nextList)
    },

    // updateProfile(payload) {
    //   if (!this.userInfo) return

    //   this.userInfo = {
    //     ...this.userInfo,
    //     ...payload
    //   }

    //   localStorage.setItem(USER_KEY, JSON.stringify(this.userInfo))
    // },

    updateAvatar(avatarBase64) {
      if (!this.userInfo) return
      this.userInfo.avatar = avatarBase64
      localStorage.setItem(USER_KEY, JSON.stringify(this.userInfo))
    },

    clearUser() {
      this.stopHeartbeat()
      this.token = ''
      this.userInfo = null
      this.historyList = []
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
      localStorage.removeItem(HISTORY_KEY)
    },

    async loginAction(payload) {
      this.loading = true
      try {
        const res = await loginApi(payload)
        console.log('loginAction 返回 res =', res)

        // 按后端返回结构取值
        const token = res.access_token
        const user = res.user_info

        if (!token) {
          throw new Error('登录成功，但未获取到 access_token')
        }

        this.setToken(token)

        if (user) {
          this.setUserInfo(user)
        }

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
        console.log('registerAction 返回 res =', res)

        // 注册接口当前不返回 token
        return res
      } finally {
        this.loading = false
      }
    },

    async updateProfileAction(payload) {
      const res = await updateProfileApi(payload)

    // 如果后端返回的是更新后的完整用户信息
      if (res && typeof res === 'object' && ('username' in res || 'email' in res || 'nickname' in res)) {
        this.setUserInfo({
          ...this.userInfo,
          ...res
        })
      } else {
    // 如果后端只返回成功消息，就用本次提交的数据先合并到本地
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

    async logoutAction() {
      try {
        if (this.token) await logoutApi()
      } finally {
        this.clearUser()
      }
    },

    startHeartbeat() {
      this.stopHeartbeat()
      if (!this.token) return
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
