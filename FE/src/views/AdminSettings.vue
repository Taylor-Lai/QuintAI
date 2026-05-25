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
        <!-- 标题 -->
        <section class="page-head card">
          <div>
            <div class="section-title">系统设置</div>
            <div class="section-subtitle">
              配置平台基础信息、功能参数及首页展示内容
            </div>
          </div>
        </section>

        <!-- 基础信息设置 -->
        <section class="card">
          <div class="card-title">基础信息设置</div>

          <div class="form-grid">
            <div class="form-item">
              <label class="form-label">平台名称</label>
              <input
                v-model.trim="form.siteName"
                type="text"
                class="form-input"
                placeholder="请输入平台名称"
              />
            </div>

            <div class="form-item">
              <label class="form-label">平台副标题</label>
              <input
                v-model.trim="form.siteSubtitle"
                type="text"
                class="form-input"
                placeholder="请输入平台副标题"
              />
            </div>

            <div class="form-item">
              <label class="form-label">联系邮箱</label>
              <input
                v-model.trim="form.contactEmail"
                type="text"
                class="form-input"
                placeholder="请输入联系邮箱"
              />
            </div>

            <div class="form-item">
              <label class="form-label">联系电话</label>
              <input
                v-model.trim="form.contactPhone"
                type="text"
                class="form-input"
                placeholder="请输入联系电话"
              />
            </div>

            <div class="form-item full">
              <label class="form-label">网站备案号</label>
              <input
                v-model.trim="form.icp"
                type="text"
                class="form-input"
                placeholder="请输入网站备案号"
              />
            </div>
          </div>
        </section>

        <!-- 功能参数设置 -->
        <section class="card">
          <div class="card-title">功能参数设置</div>

          <div class="form-grid">
            <div class="form-item">
              <label class="form-label">默认分页大小</label>
              <input
                v-model.number="form.pageSize"
                type="number"
                class="form-input"
                placeholder="请输入默认分页大小"
              />
            </div>

            <div class="form-item">
              <label class="form-label">最大上传文件大小（MB）</label>
              <input
                v-model.number="form.maxUploadSize"
                type="number"
                class="form-input"
                placeholder="请输入最大上传文件大小"
              />
            </div>

            <div class="form-item full">
              <label class="form-label">允许上传文件类型</label>
              <input
                v-model.trim="form.allowFileTypes"
                type="text"
                class="form-input"
                placeholder="例如：pdf,doc,docx,xls,xlsx"
              />
            </div>
          </div>

          <div class="switch-grid">
            <div class="switch-item">
              <div class="switch-info">
                <div class="switch-title">反馈自动处理提醒</div>
                <div class="switch-desc">收到新的用户反馈后，自动提醒管理员处理</div>
              </div>
              <label class="switch">
                <input v-model="form.feedbackNotice" type="checkbox" />
                <span class="slider"></span>
              </label>
            </div>

            <div class="switch-item">
              <div class="switch-info">
                <div class="switch-title">允许新用户注册</div>
                <div class="switch-desc">关闭后，平台将停止普通用户自主注册</div>
              </div>
              <label class="switch">
                <input v-model="form.allowRegister" type="checkbox" />
                <span class="slider"></span>
              </label>
            </div>

            <div class="switch-item">
              <div class="switch-info">
                <div class="switch-title">智能文档分析功能</div>
                <div class="switch-desc">控制文档智能操作交互模块是否启用</div>
              </div>
              <label class="switch">
                <input v-model="form.docAiEnabled" type="checkbox" />
                <span class="slider"></span>
              </label>
            </div>
          </div>
        </section>

        <!-- 首页展示设置 -->
        <section class="card">
          <div class="card-title">首页展示设置</div>

          <div class="form-grid">
            <div class="form-item full">
              <label class="form-label">首页公告</label>
              <textarea
                v-model.trim="form.notice"
                class="form-textarea"
                placeholder="请输入首页公告内容"
              ></textarea>
            </div>

            <div class="form-item full">
              <label class="form-label">平台简介</label>
              <textarea
                v-model.trim="form.introduction"
                class="form-textarea"
                placeholder="请输入平台简介"
              ></textarea>
            </div>
          </div>
        </section>

        <!-- Logo 设置 -->
        <section class="card">
          <div class="card-title">Logo / 图标设置</div>

          <div class="form-grid">
            <div class="form-item">
              <label class="form-label">平台 Logo 地址</label>
              <input
                v-model.trim="form.logoUrl"
                type="text"
                class="form-input"
                placeholder="请输入 Logo 图片地址"
              />
            </div>

            <div class="form-item">
              <label class="form-label">网站图标地址</label>
              <input
                v-model.trim="form.faviconUrl"
                type="text"
                class="form-input"
                placeholder="请输入 favicon 图片地址"
              />
            </div>
          </div>

          <div class="preview-grid">
            <div class="preview-card">
              <div class="preview-label">Logo 预览</div>
              <div class="preview-box">
                <img
                  v-if="form.logoUrl"
                  :src="form.logoUrl"
                  alt="logo"
                  class="preview-image"
                />
                <span v-else>暂无图片</span>
              </div>
            </div>

            <div class="preview-card">
              <div class="preview-label">图标预览</div>
              <div class="preview-box small">
                <img
                  v-if="form.faviconUrl"
                  :src="form.faviconUrl"
                  alt="favicon"
                  class="preview-image small"
                />
                <span v-else>暂无图片</span>
              </div>
            </div>
          </div>
        </section>

        <!-- 操作区域 -->
        <section class="action-bar card">
          <button
            class="primary-btn"
            :disabled="saving"
            @click="handleSave"
          >
            {{ saving ? '保存中...' : '保存设置' }}
          </button>
          <button class="secondary-btn" @click="handleReset">重置内容</button>
        </section>
      </main>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
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

const saving = ref(false)

const createDefaultForm = () => ({
  siteName: '智能文档处理平台',
  siteSubtitle: '让文档操作更智能、更高效',
  contactEmail: 'support@example.com',
  contactPhone: '400-800-1234',
  icp: '京ICP备12345678号-1',
  pageSize: 10,
  maxUploadSize: 50,
  allowFileTypes: 'pdf,doc,docx,xls,xlsx,ppt,pptx',
  feedbackNotice: true,
  allowRegister: true,
  docAiEnabled: true,
  notice: '欢迎使用智能文档处理平台，如遇到问题可通过反馈模块提交建议。',
  introduction:
    '本平台提供用户文档智能操作交互、文档智能操作交互、表格自定义数据填写等核心能力，帮助用户提升处理效率。',
  logoUrl: '',
  faviconUrl: ''
})

const form = reactive(createDefaultForm())

const loadSettings = () => {
  const saved = localStorage.getItem('system_settings')
  if (!saved) return

  try {
    const parsed = JSON.parse(saved)
    Object.assign(form, createDefaultForm(), parsed)
  } catch (error) {
    console.error('读取系统设置失败：', error)
  }
}

const validateForm = () => {
  if (!form.siteName) {
    alert('请输入平台名称')
    return false
  }

  if (!form.contactEmail) {
    alert('请输入联系邮箱')
    return false
  }

  if (!form.pageSize || form.pageSize <= 0) {
    alert('默认分页大小必须大于0')
    return false
  }

  if (!form.maxUploadSize || form.maxUploadSize <= 0) {
    alert('最大上传文件大小必须大于0')
    return false
  }

  return true
}

const handleSave = async () => {
  if (saving.value) return
  if (!validateForm()) return

  saving.value = true

  try {
    console.log('保存的系统设置：', {
      ...form
    })

    await new Promise((resolve) => setTimeout(resolve, 1000))

    localStorage.setItem(
      'system_settings',
      JSON.stringify({
        ...form
      })
    )

    alert('系统设置保存成功')
  } catch (error) {
    console.error('保存系统设置失败：', error)
    alert('保存失败，请稍后重试')
  } finally {
    saving.value = false
  }
}

const handleReset = () => {
  const confirmed = window.confirm('确定要重置当前填写内容吗？')
  if (!confirmed) return

  Object.assign(form, createDefaultForm())
  localStorage.removeItem('system_settings')
}

onMounted(() => {
  loadSettings()
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

/* 右侧主体 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-width: 0;
}

.card {
  background: #f8f8f8;
  border-radius: 20px;
  padding: 28px;
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.05);
}

.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-title {
  font-size: 24px;
  font-weight: 700;
  color: #2d2d2d;
}

.section-subtitle {
  margin-top: 8px;
  font-size: 14px;
  color: #999;
}

.card-title {
  font-size: 20px;
  font-weight: 700;
  color: #2d2d2d;
  margin-bottom: 20px;
}

/* 表单 */
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
}

.form-item.full {
  grid-column: 1 / -1;
}

.form-label {
  font-size: 14px;
  font-weight: 600;
  color: #555;
}

.form-input,
.form-textarea {
  width: 100%;
  border: 1px solid #e5e5e5;
  border-radius: 16px;
  background: #fff;
  font-size: 15px;
  color: #333;
  outline: none;
  transition: all 0.2s ease;
  box-sizing: border-box;
}

.form-input {
  height: 54px;
  padding: 0 16px;
}

.form-textarea {
  min-height: 140px;
  padding: 16px;
  resize: vertical;
  line-height: 1.8;
}

.form-input:focus,
.form-textarea:focus {
  border-color: #d5b076;
  box-shadow: 0 0 0 3px rgba(213, 176, 118, 0.12);
}

/* 开关区域 */
.switch-grid {
  margin-top: 24px;
  display: grid;
  gap: 16px;
}

.switch-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  background: #fff;
  border: 1px solid #eeeeee;
  border-radius: 16px;
  padding: 18px 20px;
}

.switch-info {
  flex: 1;
  min-width: 0;
}

.switch-title {
  font-size: 15px;
  font-weight: 700;
  color: #333;
}

.switch-desc {
  margin-top: 6px;
  font-size: 13px;
  color: #999;
  line-height: 1.6;
}

.switch {
  position: relative;
  width: 52px;
  height: 30px;
  display: inline-block;
  flex-shrink: 0;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  inset: 0;
  cursor: pointer;
  background: #dcdcdc;
  border-radius: 999px;
  transition: 0.25s;
}

.slider::before {
  content: '';
  position: absolute;
  width: 22px;
  height: 22px;
  left: 4px;
  top: 4px;
  border-radius: 50%;
  background: #fff;
  transition: 0.25s;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}

.switch input:checked + .slider {
  background: #d5b076;
}

.switch input:checked + .slider::before {
  transform: translateX(22px);
}

/* 图片预览 */
.preview-grid {
  margin-top: 24px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}

.preview-card {
  background: #fff;
  border: 1px solid #eeeeee;
  border-radius: 16px;
  padding: 18px;
  min-width: 0;
}

.preview-label {
  font-size: 14px;
  font-weight: 700;
  color: #555;
  margin-bottom: 14px;
}

.preview-box {
  height: 140px;
  border: 1px dashed #d9d9d9;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #aaa;
  background: #fafafa;
  overflow: hidden;
  text-align: center;
  padding: 10px;
}

.preview-box.small {
  height: 100px;
}

.preview-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.preview-image.small {
  width: 48px;
  height: 48px;
  object-fit: contain;
}

/* 底部操作 */
.action-bar {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  flex-wrap: wrap;
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

.primary-btn:hover,
.secondary-btn:hover {
  transform: translateY(-1px);
}

.primary-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
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

  .form-grid,
  .preview-grid {
    grid-template-columns: 1fr;
  }

  .container {
    max-width: calc(100% - 24px);
  }
}

@media (max-width: 768px) {
  .card,
  .sidebar,
  .sidebar.collapsed {
    padding: 20px;
  }

  .section-title,
  .sidebar-title {
    font-size: 20px;
  }

  .switch-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .action-bar {
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