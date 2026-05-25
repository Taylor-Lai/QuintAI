<template>
  <header class="header">
    <div class="container header-inner">
      <div class="brand" @click="goHome">
        <div class="brand-logo">
          <div class="logo-circle"></div>
        </div>
        <span class="brand-name">智汇文枢</span>
      </div>

      <nav class="nav">
        <!-- 非首页时：只显示返回首页 -->
        <a
          v-if="!isHome"
          href="#"
          class="nav-item return-home"
          @click.prevent="goHome"
        >
          ← 返回首页
        </a>

        <!-- 仅首页显示首页按钮 -->
        <a
          v-if="isHome"
          href="#"
          class="nav-item"
          :class="{ active: isHome }"
          @click.prevent="goHome"
        >
          首页
        </a>

        <div
          class="nav-dropdown"
          @mouseenter="showMenu = true"
          @mouseleave="showMenu = false"
        >
          <a
            href="#"
            class="nav-item"
            :class="{ active: isFeaturePage }"
            @click.prevent
          >
            功能
            <span class="arrow" :class="{ open: showMenu }">▼</span>
          </a>

          <transition name="dropdown-fade">
            <div v-show="showMenu" class="dropdown-menu">
              <div class="dropdown-item" @click="goFeature('/feature/doc-chat')">
                文档智能操作交互
              </div>
              <div class="dropdown-item" @click="goFeature('/feature/doc-extract')">
                非结构化文档信息提取
              </div>
              <div class="dropdown-item" @click="goFeature('/feature/table-fill')">
                表格自定义数据填写
              </div>
            </div>
          </transition>
        </div>

        <a
          href="#"
          class="nav-item"
          :class="{ active: isTemplatePage }"
          @click.prevent="goTemplate"
        >
          模板库
        </a>

        <a
          href="#"
          class="nav-item"
          :class="{ active: isEditorPage }"
          @click.prevent="goEditor"
        >
          在线编辑
        </a>

        <!-- 首页显示更多 -->
        <div
          v-if="isHome"
          class="nav-dropdown"
          @mouseenter="showMoreMenu = true"
          @mouseleave="showMoreMenu = false"
        >
          <a
            href="#"
            class="nav-item"
            :class="{ active: isGuidePage || isFeedbackPage }"
            @click.prevent
          >
            更多
            <span class="arrow" :class="{ open: showMoreMenu }">▼</span>
          </a>

          <transition name="dropdown-fade">
            <div v-show="showMoreMenu" class="dropdown-menu">
              <div
                class="dropdown-item"
                :class="{ 'active-dropdown': isGuidePage }"
                @click="goGuide"
              >
                上手指南
              </div>
              <div
                class="dropdown-item"
                :class="{ 'active-dropdown': isFeedbackPage }"
                @click="goFeedback"
              >
                问题反馈
              </div>
            </div>
          </transition>
        </div>

        <!-- 我的资产：放在更多右侧 -->
        <a
          href="#"
          class="nav-item"
          :class="{ active: isMyAssetsPage }"
          @click.prevent="goMyAssets"
        >
          我的资产
        </a>

        <!-- guide 页面单独显示 -->
        <a
          v-if="isGuidePage"
          href="#"
          class="nav-item"
          :class="{ active: isGuidePage }"
          @click.prevent="goGuide"
        >
          上手指南
        </a>

        <!-- feedback 页面单独显示 -->
        <a
          v-if="isFeedbackPage"
          href="#"
          class="nav-item"
          :class="{ active: isFeedbackPage }"
          @click.prevent="goFeedback"
        >
          问题反馈
        </a>
      </nav>

      <div class="header-actions">
        <template v-if="userStore.isLogin">
          <span class="user-name">你好，{{ userStore.username }}</span>
          <button class="profile-btn" @click="goProfile">个人中心</button>

          <button
            class="logout-btn"
            @click="handleLogout"
            :disabled="logoutLoading"
          >
            {{ logoutLoading ? '退出中...' : '退出' }}
          </button>

          <button
            v-if="isProfilePage && isAdmin"
            class="admin-btn"
            @click="goAdmin"
          >
            后台管理
          </button>
        </template>

        <template v-else>
          <button class="trial-btn" @click="goAuth">登录/注册</button>
        </template>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '../store/modules/user'
import { logoutApi } from '../api/auth'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const showMenu = ref(false)
const showMoreMenu = ref(false)
const logoutLoading = ref(false)

const isAdmin = computed(() => {
  if (!userStore.isLogin || !userStore.userInfo) return false

  const role = String(
    userStore.userInfo?.role ||
    userStore.role ||
    userStore.userInfo?.role_name ||
    ''
  ).toLowerCase().trim()

  return role.includes('admin') || role.includes('管理员')
})

const isHome = computed(() => route.path === '/')
const isFeaturePage = computed(() => route.path.startsWith('/feature'))
const isTemplatePage = computed(() => route.path.startsWith('/template'))
const isEditorPage = computed(() => route.path.startsWith('/editor'))
const isProfilePage = computed(() => route.path === '/profile')
const isGuidePage = computed(() => route.path === '/guide')
const isFeedbackPage = computed(() => route.path === '/feedback')
const isMyAssetsPage = computed(() => route.path.startsWith('/my-assets'))

const goHome = () => {
  showMenu.value = false
  showMoreMenu.value = false
  router.push('/')
}

const goAuth = () => {
  router.push('/auth')
}

const goProfile = () => {
  if (userStore.isLogin) {
    router.push('/profile')
  } else {
    router.push('/auth')
  }
}

const goAdmin = () => {
  router.push('/admin')
}

const goFeature = (path) => {
  showMenu.value = false
  showMoreMenu.value = false

  if (userStore.isLogin) {
    router.push(path)
  } else {
    router.push('/auth')
  }
}

const goTemplate = () => {
  showMenu.value = false
  showMoreMenu.value = false
  router.push('/template')
}

const goEditor = () => {
  showMenu.value = false
  showMoreMenu.value = false
  router.push('/editor')
}

const goGuide = () => {
  showMoreMenu.value = false
  showMenu.value = false
  router.push('/guide')
}

const goFeedback = () => {
  showMoreMenu.value = false
  showMenu.value = false
  router.push('/feedback')
}

const goMyAssets = () => {
  showMenu.value = false
  showMoreMenu.value = false
  router.push('/my-assets')
}

const handleLogout = async () => {
  if (logoutLoading.value) return

  const confirmed = window.confirm('确定要退出登录吗？')
  if (!confirmed) return

  logoutLoading.value = true

  try {
    await logoutApi()
    console.log('后端退出接口调用成功')
  } catch (error) {
    console.error('后端退出接口调用失败：', error)
  } finally {
    userStore.logoutAction()
    router.push('/')
    logoutLoading.value = false
  }
}
</script>

<style scoped>
.header {
  width: 100%;
  height: 72px;
  border-bottom: 1px solid #ddd8cf;
  background: #ececec;
  position: sticky;
  top: 0;
  z-index: 50;
}

.container {
  width: 1200px;
  max-width: calc(100% - 48px);
  margin: 0 auto;
}

.header-inner {
  height: 100%;
  display: flex;
  align-items: center;
  gap: 24px;
}

.brand {
  width: 220px;
  min-width: 220px;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  flex-shrink: 0;
}

.brand-logo {
  width: 34px;
  height: 34px;
  background: linear-gradient(135deg, #e2c08c, #cfa15c);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 10px rgba(213, 176, 118, 0.18);
}

.logo-circle {
  width: 16px;
  height: 16px;
  border: 3px solid #fff;
  border-left-color: transparent;
  border-radius: 50%;
  transform: rotate(20deg);
}

.brand-name {
  font-size: 22px;
  font-weight: 700;
  color: #2d2d2d;
  font-family: serif;
}

.nav {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 42px;
}

.nav-item {
  position: relative;
  font-size: 17px;
  color: #666;
  padding: 4px 0;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: color 0.2s ease;
  text-decoration: none;
  white-space: nowrap;
  font-family: serif;
}

.nav-item.active {
  color: #d5b076;
  font-weight: 700;
}

.return-home {
  color: #d5b076 !important;
  font-weight: 600;
  margin-right: 12px;
  padding: 4px 12px;
  border-radius: 6px;
  background: rgba(213, 176, 118, 0.08);
  transition: all 0.2s ease;
}

.return-home:hover {
  background: rgba(213, 176, 118, 0.15);
  color: #c59d60 !important;
}

.nav-dropdown {
  position: relative;
  display: flex;
  align-items: center;
  padding-bottom: 12px;
  margin-bottom: -12px;
}

.nav-dropdown .nav-item {
  color: #666;
}

.nav-dropdown:hover .nav-item {
  color: #666;
}

.nav-dropdown .nav-item.active {
  color: #d5b076;
  font-weight: 700;
}

.arrow {
  font-size: 10px;
  transition: transform 0.25s ease;
}

.arrow.open {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + 2px);
  left: 50%;
  transform: translateX(-50%);
  min-width: 230px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.1);
  padding: 8px;
  z-index: 100;
  border: 1px solid #eee6d8;
}

.dropdown-item {
  min-height: 40px;
  padding: 10px 14px;
  display: flex;
  align-items: center;
  border-radius: 8px;
  color: #444;
  font-size: 14px;
  line-height: 1.5;
  cursor: pointer;
  transition: all 0.2s ease;
}

.dropdown-item:hover {
  background: #faf6ef;
  color: #b88c47;
}

.active-dropdown {
  background: rgba(213, 176, 118, 0.12);
  color: #9c6a1f;
  font-weight: 700;
}

.dropdown-fade-enter-active,
.dropdown-fade-leave-active {
  transition: all 0.2s ease;
}

.dropdown-fade-enter-from,
.dropdown-fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-6px);
}

.header-actions {
  width: 360px;
  min-width: 360px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  flex-shrink: 0;
}

.user-name {
  font-size: 14px;
  color: #555;
  white-space: nowrap;
  font-family: serif;
}

.profile-btn,
.logout-btn,
.trial-btn,
.admin-btn {
  height: 38px;
  padding: 0 16px;
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
  font-family: serif;
}

.profile-btn {
  background: #d5b076;
}

.profile-btn:hover {
  background: #c59d60;
}

.logout-btn {
  background: #8b8b8b;
}

.logout-btn:hover {
  background: #737373;
}

.logout-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.admin-btn {
  background: #5aa4f8;
}

.admin-btn:hover {
  background: #4295f3;
}

.trial-btn {
  background: #d5b076;
}

.trial-btn:hover {
  background: #c59d60;
}

@media (max-width: 900px) {
  .nav {
    display: none;
  }

  .brand {
    width: auto;
    min-width: auto;
  }

  .brand-name {
    font-size: 18px;
  }

  .header-actions {
    width: auto;
    min-width: auto;
  }

  .user-name {
    display: none;
  }
}
</style>