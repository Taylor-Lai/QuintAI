import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import AuthView from '../views/AuthView.vue'
import UploadView from '../views/UploadView.vue'
import ProfileView from '../views/ProfileView.vue'
import TemplateLibraryView from '../views/TemplateLibraryView.vue'
import EditorView from '../views/EditorView.vue'
import MyAssets from '../views/MyAssets.vue'
import pinia from '../store'
import { useUserStore } from '../store/modules/user'
import AdminView from '../views/AdminView.vue'
import FeedbackPage from '../views/FeedbackPage.vue'
import GuidePage from '../views/GuidePage.vue'
import AdminFeedback from '../views/AdminFeedback.vue'
import AdminDashboard from '../views/AdminDashboard.vue'
import AdminSettings from '../views/AdminSettings.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
    meta: {
      title: '首页'
    }
  },
  {
    path: '/auth',
    name: 'auth',
    component: AuthView,
    meta: {
      title: '登录 / 注册'
    }
  },
  {
    path: '/profile',
    name: 'profile',
    component: ProfileView,
    meta: {
      title: '个人中心',
      requiresAuth: true
    }
  },
  {
    path: '/template',
    name: 'template',
    component: TemplateLibraryView,
    meta: {
      title: '模板库'
    }
  },
  {
    path: '/editor',
    name: 'editor',
    component: EditorView,
    meta: {
      title: '在线编辑',
      requiresAuth: true
    }
  },
  {
    path: '/my-assets',
    name: 'myAssets',
    component: MyAssets,
    meta: {
      title: '我的资产',
      requiresAuth: true
    }
  },

  /* 管理员后台相关页面 */
  {
    path: '/admin',
    name: 'admin',
    component: AdminView,
    meta: {
      title: '用户管理',
      requiresAuth: true
    }
  },
  {
    path: '/admin/feedback',
    name: 'adminFeedback',
    component: AdminFeedback,
    meta: {
      title: '问题反馈管理',
      requiresAuth: true
    }
  },
  {
    path: '/admin/dashboard',
    name: 'adminDashboard',
    component: AdminDashboard,
    meta: {
      title: '数据总览',
      requiresAuth: true
    }
  },
  {
    path: '/admin/settings',
    name: 'adminSettings',
    component: AdminSettings,
    meta: {
      title: '系统设置',
      requiresAuth: true
    }
  },

  {
    path: '/guide',
    name: 'guide',
    component: GuidePage,
    meta: {
      title: '上手指南'
    }
  },
  {
    path: '/feedback',
    name: 'feedback',
    component: FeedbackPage,
    meta: {
      title: '问题反馈'
    }
  },
  {
    path: '/feature/doc-chat',
    name: 'docChat',
    component: UploadView,
    meta: {
      title: '文档智能操作交互',
      requiresAuth: true
    }
  },
  {
    path: '/feature/doc-extract',
    name: 'docExtract',
    component: UploadView,
    meta: {
      title: '非结构化文档信息提取',
      requiresAuth: true
    }
  },
  {
    path: '/feature/table-fill',
    name: 'tableFill',
    component: UploadView,
    meta: {
      title: '表格自定义数据填写',
      requiresAuth: true
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'notFound',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore(pinia)

  if (to.meta.requiresAuth && !userStore.isLogin) {
    next('/auth')
    return
  }

  if (to.path === '/auth' && userStore.isLogin) {
    next('/')
    return
  }

  next()
})

router.afterEach((to) => {
  document.title = to.meta.title
    ? `智汇文枢 - ${to.meta.title}`
    : '智汇文枢'
})

export default router