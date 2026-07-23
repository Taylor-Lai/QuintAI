import { createRouter, createWebHistory } from 'vue-router'
import pinia from '../stores'
import { useUserStore } from '../stores/user'

const HomeView = () => import('../views/HomeView.vue')
const AuthView = () => import('../views/AuthView.vue')
const UploadView = () => import('../views/UploadView.vue')
const ProfileView = () => import('../views/ProfileView.vue')
const TemplateLibraryView = () => import('../views/TemplateLibraryView.vue')
const EditorView = () => import('../views/EditorView.vue')
const AdminView = () => import('../views/AdminView.vue')
const GuideView = () => import('../views/GuideView.vue')

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
    path: '/guide',
    name: 'guide',
    component: GuideView,
    meta: {
      title: '上手指南'
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

  if (to.path.startsWith('/admin') && userStore.userInfo?.role !== '管理员') {
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
