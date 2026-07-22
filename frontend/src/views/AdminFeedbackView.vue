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

      <!-- 右侧内容区 -->
      <main class="main-content">
        <!-- 工具栏 -->
        <section class="toolbar-card">
          <div class="toolbar-left">
            <div class="section-title">问题反馈管理</div>
            <div class="toolbar-subtitle">
              支持按问题类型、处理状态、关键词进行筛选与查看
            </div>
          </div>

          <div class="toolbar-right">
            <div class="search-box">
              <input
                v-model.trim="queryForm.keyword"
                class="search-input"
                type="text"
                placeholder="搜索标题、内容或联系方式..."
                @keyup.enter="handleSearch"
              />
              <button class="search-btn" @click="handleSearch">搜索</button>
            </div>

            <select
              v-model="queryForm.type"
              class="status-select"
              @change="handleSearch"
            >
              <option value="">全部类型</option>
              <option value="功能异常">功能异常</option>
              <option value="页面显示问题">页面显示问题</option>
              <option value="文档处理问题">文档处理问题</option>
              <option value="账号登录问题">账号登录问题</option>
              <option value="功能建议">功能建议</option>
              <option value="其他">其他</option>
            </select>

            <select
              v-model="queryForm.status"
              class="status-select"
              @change="handleSearch"
            >
              <option value="">全部状态</option>
              <option value="待处理">待处理</option>
              <option value="处理中">处理中</option>
              <option value="已解决">已解决</option>
            </select>

            <button class="reset-btn" @click="handleReset">重置</button>
          </div>
        </section>

        <!-- 列表区域 -->
        <section class="table-card">
          <div class="table-head">
            <div class="section-title">反馈列表</div>
            <div class="table-tip">共 {{ total }} 条数据</div>
          </div>

          <div class="table-wrap">
            <table class="feedback-table">
              <thead>
                <tr>
                  <th>问题类型</th>
                  <th>标题</th>
                  <th>联系方式</th>
                  <th>处理状态</th>
                  <th>提交时间</th>
                  <th class="action-column">操作</th>
                </tr>
              </thead>

              <tbody>
                <tr v-for="item in feedbackList" :key="item.id">
                  <td>
                    <span class="type-badge">{{ item.type || '-' }}</span>
                  </td>
                  <td>
                    <div class="title-cell">{{ item.title || '-' }}</div>
                  </td>
                  <td>{{ item.contact || '-' }}</td>
                  <td>
                    <span
                      class="status-badge"
                      :class="getStatusClass(item.status)"
                    >
                      {{ item.status || '-' }}
                    </span>
                  </td>
                  <td>{{ item.createTime || '-' }}</td>
                  <td class="action-cell">
                    <div class="action-group">
                      <button class="action-btn detail" @click="handleDetail(item)">
                        详情
                      </button>
                      <button
                        v-if="item.status !== '已解决'"
                        class="action-btn success"
                        @click="handleResolve(item.id)"
                      >
                        标记解决
                      </button>
                      <button
                        class="action-btn delete"
                        @click="handleDelete(item.id)"
                      >
                        删除
                      </button>
                    </div>
                  </td>
                </tr>

                <tr v-if="!loading && !feedbackList.length">
                  <td colspan="6">
                    <div class="empty-box">暂无符合条件的反馈数据</div>
                  </td>
                </tr>

                <tr v-if="loading">
                  <td colspan="6">
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

    <!-- 详情弹窗 -->
    <div v-if="detailVisible" class="dialog-mask" @click="closeDetail">
      <div class="dialog-card" @click.stop>
        <div class="dialog-head">
          <div>
            <div class="dialog-title">反馈详情</div>
            <div class="dialog-subtitle">查看用户提交的问题反馈信息</div>
          </div>
          <button class="close-btn" @click="closeDetail">×</button>
        </div>

        <div v-if="currentFeedback" class="dialog-content">
          <div class="detail-grid">
            <div class="detail-item">
              <span class="detail-label">问题类型</span>
              <span class="detail-value">{{ currentFeedback.type || '-' }}</span>
            </div>

            <div class="detail-item">
              <span class="detail-label">联系方式</span>
              <span class="detail-value">{{ currentFeedback.contact || '-' }}</span>
            </div>

            <div class="detail-item full">
              <span class="detail-label">问题标题</span>
              <span class="detail-value">{{ currentFeedback.title || '-' }}</span>
            </div>

            <div class="detail-item full">
              <span class="detail-label">问题描述</span>
              <span class="detail-value">{{ currentFeedback.content || '-' }}</span>
            </div>

            <div class="detail-item full">
              <span class="detail-label">补充说明</span>
              <span class="detail-value">{{ currentFeedback.remark || '暂无补充说明' }}</span>
            </div>

            <div class="detail-item">
              <span class="detail-label">允许联系</span>
              <span class="detail-value">{{ currentFeedback.allowContact ? '是' : '否' }}</span>
            </div>

            <div class="detail-item">
              <span class="detail-label">处理状态</span>
              <span class="detail-value">{{ currentFeedback.status || '-' }}</span>
            </div>

            <div class="detail-item">
              <span class="detail-label">提交时间</span>
              <span class="detail-value">{{ currentFeedback.createTime || '-' }}</span>
            </div>
          </div>
        </div>

        <div class="dialog-actions">
          <button
            v-if="currentFeedback && currentFeedback.status !== '已解决'"
            class="primary-btn"
            @click="handleResolve(currentFeedback.id)"
          >
            标记为已解决
          </button>
          <button class="secondary-btn" @click="closeDetail">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'

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
const detailVisible = ref(false)
const currentFeedback = ref(null)

const queryForm = reactive({
  pageNum: 1,
  pageSize: 8,
  keyword: '',
  type: '',
  status: ''
})

const mockFeedbackList = ref([
  {
    id: 1,
    type: '功能异常',
    contact: 'zhangsan@example.com',
    title: '上传文档后无法解析',
    content: '上传 PDF 文件后，页面一直显示处理中，超过5分钟也没有结果。',
    remark: '浏览器是 Chrome 123，电脑是 Windows 11',
    allowContact: true,
    status: '待处理',
    createTime: '2026-03-27 10:12:33'
  },
  {
    id: 2,
    type: '页面布局优化',
    contact: 'lisi@example.com',
    title: '左右布局更美观',
    content: '在手机端打开时，左右布局更美观。',
    remark: 'iPhone 13 Safari 浏览器',
    allowContact: true,
    status: '处理中',
    createTime: '2026-03-28 11:26:10'
  },
  {
    id: 3,
    type: '功能建议',
    contact: 'wangwu@example.com',
    title: '建议增加更多功能',
    content: '希望可以支持将多个处理结果批量导出，减少重复下载操作。',
    remark: '',
    allowContact: false,
    status: '已解决',
    createTime: '2026-03-02 13:45:21'
  },
  {
    id: 4,
    type: '账号登录问题',
    contact: 'zhaoliu@example.com',
    title: '登录失败',
    content: '无法登录。',
    remark: '今天下午2点左右开始出现',
    allowContact: true,
    status: '待处理',
    createTime: '2026-03-24 14:10:08'
  }
])

const filteredList = computed(() => {
  let list = [...mockFeedbackList.value]

  if (queryForm.keyword) {
    const keyword = queryForm.keyword.trim()
    list = list.filter(item =>
      [item.title, item.content, item.contact]
        .filter(Boolean)
        .some(v => String(v).includes(keyword))
    )
  }

  if (queryForm.type) {
    list = list.filter(item => item.type === queryForm.type)
  }

  if (queryForm.status) {
    list = list.filter(item => item.status === queryForm.status)
  }

  return list
})

const total = computed(() => filteredList.value.length)

const totalPages = computed(() => {
  return Math.max(1, Math.ceil(total.value / queryForm.pageSize))
})

const feedbackList = computed(() => {
  const start = (queryForm.pageNum - 1) * queryForm.pageSize
  const end = start + queryForm.pageSize
  return filteredList.value.slice(start, end)
})

const handleSearch = () => {
  queryForm.pageNum = 1
}

const handleReset = () => {
  queryForm.pageNum = 1
  queryForm.keyword = ''
  queryForm.type = ''
  queryForm.status = ''
}

const handlePrevPage = () => {
  if (queryForm.pageNum > 1) {
    queryForm.pageNum -= 1
  }
}

const handleNextPage = () => {
  if (queryForm.pageNum < totalPages.value) {
    queryForm.pageNum += 1
  }
}

const handleDetail = (item) => {
  currentFeedback.value = { ...item }
  detailVisible.value = true
}

const closeDetail = () => {
  detailVisible.value = false
  currentFeedback.value = null
}

const handleResolve = (id) => {
  const target = mockFeedbackList.value.find(item => item.id === id)
  if (!target) return

  const confirmed = window.confirm('确定将该反馈标记为已解决吗？')
  if (!confirmed) return

  target.status = '已解决'

  if (currentFeedback.value?.id === id) {
    currentFeedback.value = { ...target }
  }

  alert('已标记为已解决')
}

const handleDelete = (id) => {
  const confirmed = window.confirm('确定删除该反馈吗？删除后不可恢复。')
  if (!confirmed) return

  const index = mockFeedbackList.value.findIndex(item => item.id === id)
  if (index === -1) return

  mockFeedbackList.value.splice(index, 1)

  if (currentFeedback.value?.id === id) {
    closeDetail()
  }

  if (feedbackList.value.length === 1 && queryForm.pageNum > 1) {
    queryForm.pageNum -= 1
  }

  alert('删除成功')
}

const getStatusClass = (status) => {
  if (status === '待处理') return 'pending'
  if (status === '处理中') return 'processing'
  if (status === '已解决') return 'resolved'
  return ''
}
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
  border: 1px solid #e5e5e5;
  border-radius: 16px;
  background: #fff;
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

.feedback-table {
  width: 100%;
  min-width: 1080px;
  border-collapse: separate;
  border-spacing: 0;
  background: #fff;
  border-radius: 18px;
  overflow: hidden;
  table-layout: fixed;
}

.feedback-table thead th {
  text-align: left;
  padding: 18px 20px;
  background: #f5efe5;
  color: #9c6a1f;
  font-size: 15px;
  font-weight: 700;
  border-bottom: 1px solid #ead8b9;
  white-space: nowrap;
}

.feedback-table tbody td {
  padding: 18px 20px;
  font-size: 14px;
  color: #444;
  border-bottom: 1px solid #f1f1f1;
  vertical-align: middle;
  word-break: break-word;
}

.feedback-table th:nth-child(1),
.feedback-table td:nth-child(1) {
  width: 140px;
}

.feedback-table th:nth-child(2),
.feedback-table td:nth-child(2) {
  width: 220px;
}

.feedback-table th:nth-child(3),
.feedback-table td:nth-child(3) {
  width: 220px;
}

.feedback-table th:nth-child(4),
.feedback-table td:nth-child(4) {
  width: 120px;
}

.feedback-table th:nth-child(5),
.feedback-table td:nth-child(5) {
  width: 180px;
}

.action-column,
.action-cell {
  width: 300px;
}

.title-cell {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #2d2d2d;
  font-weight: 600;
}

.type-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 88px;
  height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(213, 176, 118, 0.18);
  color: #8a611d;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 78px;
  height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
}

.status-badge.pending {
  background: rgba(255, 152, 0, 0.12);
  color: #ef6c00;
}

.status-badge.processing {
  background: rgba(33, 150, 243, 0.12);
  color: #1565c0;
}

.status-badge.resolved {
  background: rgba(76, 175, 80, 0.12);
  color: #2e7d32;
}

.action-cell {
  white-space: nowrap;
}

.action-group {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: nowrap;
}

.action-btn {
  height: 36px;
  min-width: 72px;
  padding: 0 12px;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  transition: all 0.2s ease;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}

.action-btn.success {
  min-width: 88px;
  background: rgba(76, 175, 80, 0.12);
  color: #2e7d32;
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
  border: 1px solid #e5e5e5;
  border-radius: 12px;
  background: #fff;
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

.dialog-content {
  padding: 12px 24px 24px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  padding-top: 8px;
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