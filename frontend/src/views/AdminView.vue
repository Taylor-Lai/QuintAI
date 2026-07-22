<template>
  <div class="admin-page">
    <AppHeader />

    <div class="admin-layout container">
      <!-- 左侧导航栏 -->
      <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
        <div class="sidebar-top">
          <div v-if="!sidebarCollapsed" class="sidebar-title">后台管理</div>
          <button class="collapse-btn" @click="toggleSidebar">
            <span v-if="sidebarCollapsed">☰</span>
            <span v-else>◀</span>
          </button>
        </div>

        <div class="sidebar-menu">
          <div
            class="menu-item"
            :class="{ active: route.path === '/admin' }"
            @click="goPage('/admin')"
          >
            <span class="menu-icon">👤</span>
            <span v-if="!sidebarCollapsed" class="menu-text">用户管理</span>
          </div>

          <div
            class="menu-item"
            :class="{ active: route.path === '/admin/feedback' }"
            @click="goPage('/admin/feedback')"
          >
            <span class="menu-icon">📝</span>
            <span v-if="!sidebarCollapsed" class="menu-text">问题反馈管理</span>
          </div>

          <div
            class="menu-item"
            :class="{ active: route.path === '/admin/dashboard' }"
            @click="goPage('/admin/dashboard')"
          >
            <span class="menu-icon">📊</span>
            <span v-if="!sidebarCollapsed" class="menu-text">数据总览</span>
          </div>

          <div
            class="menu-item"
            :class="{ active: route.path === '/admin/settings' }"
            @click="goPage('/admin/settings')"
          >
            <span class="menu-icon">⚙️</span>
            <span v-if="!sidebarCollapsed" class="menu-text">系统设置</span>
          </div>
        </div>
      </aside>

      <!-- 右侧内容区域 -->
      <main class="main-content">
        <!-- 工具栏 -->
        <section class="toolbar-card">
          <div class="toolbar-left">
            <div class="section-title">用户管理</div>
            <div class="toolbar-subtitle">
              支持按用户名、邮箱、手机号、状态进行筛选
            </div>
          </div>

          <div class="toolbar-right">
            <div class="search-box">
              <input
                v-model.trim="queryForm.keyword"
                class="search-input"
                type="text"
                placeholder="搜索用户名、邮箱或手机号..."
                @keyup.enter="handleSearch"
              />
              <button class="search-btn" @click="handleSearch">搜索</button>
            </div>

            <select
              v-model="queryForm.accountStatus"
              class="status-select"
              @change="handleSearch"
            >
              <option value="">全部状态</option>
              <option value="正常">正常</option>
              <option value="禁用">禁用</option>
            </select>

            <select
              v-model="queryForm.loginStatus"
              class="status-select"
              @change="handleSearch"
            >
              <option value="">全部登录状态</option>
              <option value="在线">在线</option>
              <option value="离线">离线</option>
            </select>

            <button class="reset-btn" @click="handleReset">重置</button>
          </div>
        </section>

        <!-- 用户列表表格 -->
        <section class="table-card">
          <div class="table-head">
            <div class="section-title">用户列表</div>
            <div class="table-tip">共 {{ total }} 条数据</div>
          </div>

          <div class="table-wrap">
            <table class="user-table">
              <thead>
                <tr>
                  <th>用户名</th>
                  <th>邮箱</th>
                  <th>手机号</th>
                  <th>角色</th>
                  <th>账号状态</th>
                  <th>登录状态</th>
                  <th>最后登录</th>
                  <th class="action-column">操作</th>
                </tr>
              </thead>

              <tbody>
                <tr v-for="item in userList" :key="item.id">
                  <td>
                    <div class="user-name-cell">
                      <div class="avatar">
                        {{ (item.username || 'U').slice(0, 1) }}
                      </div>
                      <div class="name-text">{{ item.username || '-' }}</div>
                    </div>
                  </td>
                  <td>{{ item.email || '-' }}</td>
                  <td>{{ item.phone || '-' }}</td>
                  <td class="role-cell-td">
                    <span v-if="item.isAdmin" class="admin-tag">
                      管理员
                    </span>
                    <span v-else class="role-text">
                      {{ item.role || '普通用户' }}
                    </span>
                  </td>
                  <td>
                    <span
                      class="status-badge"
                      :class="item.accountStatus === '正常' ? 'normal' : 'disabled'"
                    >
                      {{ item.accountStatus || '-' }}
                    </span>
                  </td>
                  <td>
                    <span
                      class="status-badge"
                      :class="item.loginStatus === '在线' ? 'online' : 'offline'"
                    >
                      {{ item.loginStatus || '-' }}
                    </span>
                  </td>
                  <td>{{ item.lastLoginTime || '-' }}</td>
                  <td class="action-cell">
                    <div class="action-group">
                      <button class="action-btn detail" @click="handleDetail(item.id)">
                        详情
                      </button>
                      <button class="action-btn delete" @click="handleDelete(item.id)">
                        删除
                      </button>
                    </div>
                  </td>
                </tr>

                <tr v-if="!loading && !userList.length">
                  <td colspan="8">
                    <div class="empty-box">暂无符合条件的用户数据</div>
                  </td>
                </tr>

                <tr v-if="loading">
                  <td colspan="8">
                    <div class="empty-box">加载中...</div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 分页 -->
          <div class="pagination">
            <button
              class="page-btn"
              :disabled="queryForm.pageNum === 1"
              @click="handlePrevPage"
            >
              上一页
            </button>

            <span class="page-text">
              第 {{ queryForm.pageNum }} / {{ totalPages }} 页
            </span>

            <button
              class="page-btn"
              :disabled="queryForm.pageNum >= totalPages"
              @click="handleNextPage"
            >
              下一页
            </button>
          </div>
        </section>
      </main>
    </div>

    <!-- 用户详情弹窗 -->
    <div v-if="detailVisible" class="dialog-mask" @click="closeDetail">
      <div class="dialog-card" @click.stop>
        <div class="dialog-head">
          <div>
            <div class="dialog-title">用户详情</div>
            <div class="dialog-subtitle">查看用户资料与登录信息</div>
          </div>
          <button class="close-btn" @click="closeDetail">×</button>
        </div>

        <div v-if="detailLoading" class="dialog-loading">
          正在加载用户详情...
        </div>

        <div v-else-if="currentUser" class="dialog-content">
          <div class="detail-top">
            <div class="detail-avatar">
              {{ (currentUser.username || 'U').slice(0, 1) }}
            </div>
            <div class="detail-main">
              <div class="detail-name">
                {{ currentUser.username || '-' }}
                <span v-if="currentUser.isAdmin" class="detail-admin-tag">管理员</span>
              </div>
              <div class="detail-role">{{ currentUser.role || '-' }}</div>
            </div>
          </div>

          <div class="detail-grid">
            <div class="detail-item">
              <span class="detail-label">邮箱</span>
              <span class="detail-value">{{ currentUser.email || '-' }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">手机号</span>
              <span class="detail-value">{{ currentUser.phone || '-' }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">账号状态</span>
              <span class="detail-value">{{ currentUser.accountStatus || '-' }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">登录状态</span>
              <span class="detail-value">{{ currentUser.loginStatus || '-' }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">最后登录时间</span>
              <span class="detail-value">{{ currentUser.lastLoginTime || '-' }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">注册时间</span>
              <span class="detail-value">{{ currentUser.createTime || '-' }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">最近IP</span>
              <span class="detail-value">{{ currentUser.lastLoginIp || '-' }}</span>
            </div>
            <div class="detail-item full">
              <span class="detail-label">备注</span>
              <span class="detail-value">{{ currentUser.remark || '暂无备注' }}</span>
            </div>
          </div>
        </div>

        <div class="dialog-actions">
          <button
            v-if="currentUser"
            class="primary-btn"
            :disabled="adminRoleLoading"
            @click="handleToggleAdminRole"
          >
            {{ adminRoleLoading ? '提交中...' : (currentUser.isAdmin ? '取消管理员' : '设为管理员') }}
          </button>
          <button class="secondary-btn" @click="closeDetail">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import {
  getUserPageApi,
  getUserDetailApi,
  deleteUserApi,
  getAdminStatisticsApi,
  updateUserAdminRoleApi
} from '../api/admin'

const router = useRouter()
const route = useRoute()

const sidebarCollapsed = ref(
  localStorage.getItem('admin_sidebar_collapsed') === 'true'
)

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
  localStorage.setItem('admin_sidebar_collapsed', String(sidebarCollapsed.value))
}

const goPage = (path) => {
  if (route.path === path) return
  router.push(path)
}

const loading = ref(false)
const detailLoading = ref(false)
const detailVisible = ref(false)
const adminRoleLoading = ref(false)
const currentUser = ref(null)

const userList = ref([])
const total = ref(0)

const statistics = reactive({
  totalUsers: 0,
  onlineUsers: 0,
  activeUsers: 0
})

const queryForm = reactive({
  pageNum: 1,
  pageSize: 8,
  keyword: '',
  accountStatus: '',
  loginStatus: ''
})

const totalPages = computed(() => {
  return Math.max(1, Math.ceil(total.value / queryForm.pageSize))
})

const unwrapData = (res) => {
  if (!res) return {}
  if (res.data !== undefined && res.data !== null) return res.data
  return res
}

const formatDateTime = (value) => {
  if (!value) return '-'
  return value
}

const normalizeAccountStatus = (value) => {
  if (value === null || value === undefined || value === '') return '-'
  const str = String(value)
  if (str === '1' || str === '正常' || str.toLowerCase() === 'normal') return '正常'
  if (str === '0' || str === '禁用' || str.toLowerCase() === 'disabled') return '禁用'
  return str
}

const normalizeLoginStatus = (value) => {
  if (value === null || value === undefined || value === '') return '-'
  const str = String(value)
  if (str === '1' || str === '在线' || str.toLowerCase() === 'online') return '在线'
  if (str === '0' || str === '离线' || str.toLowerCase() === 'offline') return '离线'
  return str
}

const normalizeIsAdmin = (item = {}) => {
  const candidates = [
    item.isAdmin,
    item.is_admin,
    item.admin,
    item.is_superuser,
    item.isSuperuser
  ]

  for (const value of candidates) {
    if (value === true || value === 1 || value === '1' || value === 'true') return true
    if (value === false || value === 0 || value === '0' || value === 'false') return false
  }

  const roleText = String(item.role ?? item.role_name ?? '').toLowerCase()
  if (roleText.includes('admin') || roleText.includes('管理员')) return true

  return false
}

const normalizeUser = (item = {}) => {
  const isAdmin = normalizeIsAdmin(item)
  const rawRole = item.role ?? item.role_name ?? '-'

  let roleText = rawRole
  if ((rawRole === '-' || !rawRole) && isAdmin) {
    roleText = '管理员'
  }

  return {
    id: item.id ?? item.user_id ?? '',
    username: item.username ?? item.user_name ?? item.nickname ?? '-',
    email: item.email ?? '-',
    phone: item.phone ?? item.mobile ?? item.phone_number ?? '-',
    role: roleText,
    isAdmin,
    accountStatus: normalizeAccountStatus(item.accountStatus ?? item.account_status),
    loginStatus: normalizeLoginStatus(item.loginStatus ?? item.login_status),
    lastLoginTime: formatDateTime(item.lastLoginTime ?? item.last_login_time),
    createTime: formatDateTime(item.createTime ?? item.create_time),
    lastLoginIp: item.lastLoginIp ?? item.last_login_ip ?? '-',
    remark: item.remark ?? item.notes ?? ''
  }
}

const getUserPage = async () => {
  loading.value = true
  try {
    const params = {
      page: queryForm.pageNum,
      page_size: queryForm.pageSize,
      keyword: queryForm.keyword,
      account_status: queryForm.accountStatus,
      login_status: queryForm.loginStatus
    }

    const res = await getUserPageApi(params)
    console.log('用户列表接口返回：', res)

    const data = unwrapData(res)
    const rawList = Array.isArray(data.list)
      ? data.list
      : Array.isArray(data.records)
        ? data.records
        : []

    const normalizedList = rawList.map(normalizeUser)
    userList.value = normalizedList

    const backendTotal = Number(data.total ?? data.count ?? 0)
    total.value = backendTotal
  } catch (error) {
    console.error('获取用户列表失败：', error)
    alert(error.message || '获取用户列表失败')
  } finally {
    loading.value = false
  }
}

const getStatistics = async () => {
  try {
    const res = await getAdminStatisticsApi()
    console.log('统计接口返回：', res)

    const data = unwrapData(res)
    statistics.totalUsers = Number(data.total_users ?? data.totalUsers ?? 0)
    statistics.onlineUsers = Number(data.online_users ?? data.onlineUsers ?? 0)
    statistics.activeUsers = Number(data.normal_users ?? data.activeUsers ?? 0)
  } catch (error) {
    console.error('获取统计数据失败：', error)
  }
}

const handleSearch = () => {
  queryForm.pageNum = 1
  getUserPage()
}

const handleReset = () => {
  queryForm.pageNum = 1
  queryForm.keyword = ''
  queryForm.accountStatus = ''
  queryForm.loginStatus = ''
  getUserPage()
}

const handlePrevPage = () => {
  if (queryForm.pageNum > 1) {
    queryForm.pageNum -= 1
    getUserPage()
  }
}

const handleNextPage = () => {
  if (queryForm.pageNum < totalPages.value) {
    queryForm.pageNum += 1
    getUserPage()
  }
}

const handleDetail = async (id) => {
  detailVisible.value = true
  detailLoading.value = true
  currentUser.value = null

  try {
    const res = await getUserDetailApi(id)
    console.log('用户详情接口返回：', res)
    currentUser.value = normalizeUser(unwrapData(res))
  } catch (error) {
    console.error('获取用户详情失败：', error)
    alert(error.message || '获取用户详情失败')
    detailVisible.value = false
  } finally {
    detailLoading.value = false
  }
}

const closeDetail = () => {
  detailVisible.value = false
  currentUser.value = null
}

const handleToggleAdminRole = async () => {
  if (!currentUser.value?.id) return

  const targetIsAdmin = !currentUser.value.isAdmin
  const tipText = targetIsAdmin ? '设为管理员' : '取消管理员'
  const confirmed = window.confirm(`确定要${tipText}吗？`)

  if (!confirmed) return

  adminRoleLoading.value = true
  try {
    await updateUserAdminRoleApi(currentUser.value.id, targetIsAdmin)
    alert(`${tipText}成功`)

    currentUser.value = {
      ...currentUser.value,
      isAdmin: targetIsAdmin,
      role: targetIsAdmin ? '管理员' : (currentUser.value.role === '管理员' ? '普通用户' : currentUser.value.role)
    }

    await Promise.all([
      handleDetail(currentUser.value.id),
      getUserPage(),
      getStatistics()
    ])
  } catch (error) {
    console.error('设置管理员失败：', error)
    alert(error.message || `${tipText}失败`)
  } finally {
    adminRoleLoading.value = false
  }
}

const handleDelete = async (id) => {
  const confirmed = window.confirm('确定删除该用户吗？此操作不可恢复。')
  if (!confirmed) return

  try {
    await deleteUserApi(id)
    alert('删除成功')

    if (userList.value.length === 1 && queryForm.pageNum > 1) {
      queryForm.pageNum -= 1
    }

    if (currentUser.value?.id === id) {
      closeDetail()
    }

    await Promise.all([getUserPage(), getStatistics()])
  } catch (error) {
    console.error('删除用户失败：', error)
    alert(error.message || '删除用户失败')
  }
}

onMounted(() => {
  getUserPage()
  getStatistics()
})
</script>

<style scoped>
.admin-page {
  min-height: 100vh;
  background: #ececec;
}

.container {
  width: 1400px;
  max-width: calc(100% - 40px);
  margin: 0 auto;
}

.admin-layout {
  display: flex;
  gap: 24px;
  padding: 24px 0 40px;
  align-items: flex-start;
}

/* 左侧导航栏 */
.sidebar {
  width: 240px;
  min-height: calc(100vh - 120px);
  background: #f8f8f8;
  border-radius: 20px;
  padding: 20px 18px;
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.05);
  flex-shrink: 0;
  transition: width 0.25s ease, padding 0.25s ease;
}

.sidebar.collapsed {
  width: 84px;
  padding: 20px 12px;
}

.sidebar-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  gap: 12px;
}

.sidebar-title {
  font-size: 22px;
  font-weight: 700;
  color: #2d2d2d;
  padding: 0 10px;
  white-space: nowrap;
}

.collapse-btn {
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 12px;
  background: #f1f1f1;
  color: #555;
  cursor: pointer;
  font-size: 18px;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.collapse-btn:hover {
  background: rgba(213, 176, 118, 0.16);
  color: #8a611d;
}

.sidebar-menu {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.menu-item {
  height: 48px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  border-radius: 14px;
  font-size: 15px;
  color: #555;
  cursor: pointer;
  transition: all 0.2s ease;
  background: transparent;
  gap: 12px;
}

.sidebar.collapsed .menu-item {
  justify-content: center;
  padding: 0;
}

.menu-item:hover {
  background: rgba(213, 176, 118, 0.12);
  color: #8a611d;
}

.menu-item.active {
  background: #d5b076;
  color: #fff;
  font-weight: 600;
}

.menu-icon {
  width: 22px;
  text-align: center;
  font-size: 18px;
  flex-shrink: 0;
}

.menu-text {
  white-space: nowrap;
}

/* 右侧主体内容 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-width: 0;
}

.toolbar-card,
.table-card {
  background: #f8f8f8;
  border-radius: 20px;
  padding: 28px;
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.05);
}

.toolbar-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  flex-wrap: wrap;
}

.section-title {
  font-size: 24px;
  font-weight: 700;
  color: #2d2d2d;
}

.toolbar-subtitle {
  margin-top: 8px;
  font-size: 14px;
  color: #999;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

.search-box {
  display: flex;
  align-items: center;
  background: #fff;
  border: 1px solid #e5e5e5;
  border-radius: 16px;
  overflow: hidden;
}

.search-input {
  width: 320px;
  height: 54px;
  border: none;
  outline: none;
  padding: 0 18px;
  background: transparent;
  font-size: 16px;
  color: #333;
}

.search-btn {
  height: 54px;
  padding: 0 24px;
  border: none;
  cursor: pointer;
  background: #d5b076;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
}

.status-select,
.reset-btn,
.page-btn,
.primary-btn,
.secondary-btn,
.action-btn,
.close-btn {
  outline: none;
}

.status-select {
  height: 54px;
  min-width: 140px;
  padding: 0 16px;
  border-radius: 16px;
  border: 1px solid #e5e5e5;
  background: #fff;
  font-size: 15px;
  color: #444;
  cursor: pointer;
}

.reset-btn {
  height: 54px;
  padding: 0 22px;
  border-radius: 16px;
  background: #fff;
  border: 1px solid #e5e5e5;
  cursor: pointer;
  font-size: 15px;
  color: #555;
}

.table-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 22px;
  gap: 12px;
  flex-wrap: wrap;
}

.table-tip {
  font-size: 14px;
  color: #888;
}

.table-wrap {
  width: 100%;
  overflow-x: auto;
}

.user-table {
  width: 100%;
  min-width: 1120px;
  border-collapse: separate;
  border-spacing: 0;
  background: #fff;
  border-radius: 18px;
  overflow: hidden;
  table-layout: fixed;
}

.user-table thead th {
  text-align: left;
  padding: 18px 20px;
  background: #f5efe5;
  color: #9c6a1f;
  font-size: 15px;
  font-weight: 700;
  border-bottom: 1px solid #ead8b9;
  white-space: nowrap;
}

.user-table tbody td {
  padding: 18px 20px;
  font-size: 14px;
  color: #444;
  border-bottom: 1px solid #f1f1f1;
  vertical-align: middle;
  word-break: break-word;
}

.user-table th:nth-child(1),
.user-table td:nth-child(1) {
  width: 170px;
}

.user-table th:nth-child(2),
.user-table td:nth-child(2) {
  width: 200px;
}

.user-table th:nth-child(3),
.user-table td:nth-child(3) {
  width: 150px;
}

.user-table th:nth-child(4),
.user-table td:nth-child(4) {
  width: 140px;
}

.user-table th:nth-child(5),
.user-table td:nth-child(5),
.user-table th:nth-child(6),
.user-table td:nth-child(6) {
  width: 120px;
}

.user-table th:nth-child(7),
.user-table td:nth-child(7) {
  width: 180px;
}

.action-column,
.action-cell {
  width: 180px;
}

.user-name-cell {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.avatar,
.detail-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #d5b076, #b48742);
  color: #fff;
  font-weight: 700;
  flex-shrink: 0;
}

.avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  font-size: 15px;
}

.name-text {
  color: #2d2d2d;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.role-cell-td {
  text-align: center;
  vertical-align: middle;
}

.admin-tag,
.detail-admin-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 28px;
  padding: 0 14px;
  border-radius: 999px;
  background: rgba(213, 176, 118, 0.18);
  color: #8a611d;
  font-size: 13px;
  font-weight: 700;
  white-space: nowrap;
}

.role-text {
  color: #666;
  font-size: 14px;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 72px;
  height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
}

.status-badge.normal {
  background: rgba(76, 175, 80, 0.12);
  color: #2e7d32;
}

.status-badge.disabled {
  background: rgba(244, 67, 54, 0.12);
  color: #c62828;
}

.status-badge.online {
  background: rgba(33, 150, 243, 0.12);
  color: #1565c0;
}

.status-badge.offline {
  background: rgba(158, 158, 158, 0.14);
  color: #666;
}

.action-cell {
  white-space: nowrap;
}

.action-group {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: nowrap;
  white-space: nowrap;
}

.action-btn {
  height: 34px;
  min-width: 58px;
  padding: 0 14px;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  flex-shrink: 0;
  transition: all 0.2s ease;
}

.action-btn:hover,
.primary-btn:hover,
.secondary-btn:hover {
  transform: translateY(-1px);
}

.action-btn.detail {
  background: rgba(33, 150, 243, 0.12);
  color: #1565c0;
}

.action-btn.delete {
  background: rgba(244, 67, 54, 0.12);
  color: #c62828;
}

.empty-box {
  text-align: center;
  padding: 44px 0;
  color: #999;
  font-size: 16px;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 14px;
  margin-top: 20px;
  flex-wrap: wrap;
}

.page-btn {
  height: 42px;
  padding: 0 18px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #e5e5e5;
  cursor: pointer;
  font-size: 14px;
  color: #444;
}

.page-btn:disabled,
.primary-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.page-text {
  color: #666;
  font-size: 14px;
}

.dialog-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.42);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  z-index: 999;
}

.dialog-card {
  width: 760px;
  max-width: 100%;
  background: #fff;
  border-radius: 20px;
  box-shadow: 0 18px 50px rgba(0, 0, 0, 0.18);
  overflow: hidden;
}

.dialog-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 24px 12px;
  gap: 16px;
}

.dialog-title {
  font-size: 24px;
  font-weight: 700;
  color: #2d2d2d;
}

.dialog-subtitle {
  margin-top: 6px;
  color: #888;
  font-size: 14px;
}

.close-btn {
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 50%;
  background: #f3f3f3;
  cursor: pointer;
  font-size: 22px;
  color: #666;
}

.dialog-loading {
  padding: 48px 24px;
  text-align: center;
  color: #888;
}

.dialog-content {
  padding: 12px 24px 24px;
}

.detail-top {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-bottom: 24px;
  border-bottom: 1px solid #f0f0f0;
}

.detail-avatar {
  width: 68px;
  height: 68px;
  border-radius: 50%;
  font-size: 24px;
}

.detail-main {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.detail-name {
  font-size: 24px;
  font-weight: 700;
  color: #2d2d2d;
}

.detail-role {
  font-size: 14px;
  color: #999;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  padding-top: 24px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
  border-radius: 14px;
  background: #fafafa;
  border: 1px solid #f0f0f0;
}

.detail-item.full {
  grid-column: 1 / -1;
}

.detail-label {
  font-size: 13px;
  color: #999;
}

.detail-value {
  font-size: 15px;
  color: #333;
  line-height: 1.7;
  word-break: break-all;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 0 24px 24px;
}

.primary-btn,
.secondary-btn {
  height: 42px;
  padding: 0 20px;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}

.primary-btn {
  background: #d5b076;
  color: #fff;
}

.secondary-btn {
  background: #f3f3f3;
  color: #444;
}

/* 响应式 */
@media (max-width: 992px) {
  .admin-layout {
    flex-direction: column;
  }

  .sidebar,
  .sidebar.collapsed {
    width: 100%;
    min-height: auto;
    padding: 20px;
  }

  .sidebar-menu {
    flex-direction: row;
    flex-wrap: wrap;
  }

  .menu-item,
  .sidebar.collapsed .menu-item {
    flex: 1 1 calc(50% - 12px);
    justify-content: center;
    padding: 0 16px;
  }

  .detail-grid {
    grid-template-columns: 1fr;
  }

  .container {
    max-width: calc(100% - 24px);
  }

  .search-input {
    width: 220px;
  }
}

@media (max-width: 768px) {
  .toolbar-card,
  .table-card,
  .sidebar,
  .sidebar.collapsed {
    padding: 20px;
  }

  .section-title,
  .sidebar-title {
    font-size: 20px;
  }

  .toolbar-right {
    width: 100%;
  }

  .search-box {
    width: 100%;
  }

  .search-input {
    width: 100%;
  }

  .status-select,
  .reset-btn {
    flex: 1;
    min-width: 0;
  }

  .dialog-actions {
    flex-direction: column;
  }

  .primary-btn,
  .secondary-btn {
    width: 100%;
  }

  .menu-item,
  .sidebar.collapsed .menu-item {
    flex: 1 1 100%;
  }

  .sidebar-top {
    margin-bottom: 16px;
  }
}
</style>
