<template>
  <div class="profile-page">
    <AppHeader />

    <div class="container profile-container">
      <!-- 上半部分：个人信息 -->
      <section class="profile-card">
        <div class="section-head">
          <div class="section-title">个人资料</div>
          <button class="edit-btn" @click="toggleEdit">
            {{ isEditing ? '取消编辑' : '编辑资料' }}
          </button>
        </div>

        <div class="profile-top">
          <div class="avatar-area">
            <div class="avatar-box">
              <img
                v-if="userStore.userInfo?.avatar"
                :src="userStore.userInfo.avatar"
                alt="avatar"
                class="avatar-img"
              />
              <span v-else class="avatar-text">
                {{ avatarText }}
              </span>
            </div>

            <label class="avatar-upload-btn">
              更换头像
              <input
                type="file"
                accept="image/*"
                class="hidden-input"
                @change="handleAvatarChange"
              />
            </label>
          </div>

          <div class="info-grid">
            <div class="info-item">
              <label>昵称</label>
              <template v-if="isEditing">
                <input v-model="form.nickname" class="info-input" />
              </template>
              <div v-else class="info-value">
                {{ userStore.userInfo?.nickname || '未设置' }}
              </div>
            </div>

            <div class="info-item">
              <label>用户名</label>
              <div class="info-value">
                {{ userStore.userInfo?.username || '未设置' }}
              </div>
            </div>

            <div class="info-item">
              <label>邮箱</label>
              <template v-if="isEditing">
                <input v-model="form.email" class="info-input" />
              </template>
              <div v-else class="info-value">
                {{ userStore.userInfo?.email || '未设置' }}
              </div>
            </div>

            <div class="info-item">
              <label>性别</label>
              <template v-if="isEditing">
                <select v-model="form.gender" class="info-input">
                  <option value="未设置">未设置</option>
                  <option value="男">男</option>
                  <option value="女">女</option>
                </select>
              </template>
              <div v-else class="info-value">
                {{ userStore.userInfo?.gender || '未设置' }}
              </div>
            </div>

            <div class="info-item">
              <label>手机号</label>
              <template v-if="isEditing">
                <input v-model="form.phone" class="info-input" />
              </template>
              <div v-else class="info-value">
                {{ userStore.userInfo?.phone || '未设置' }}
              </div>
            </div>

            <div class="info-item">
              <label>角色</label>
              <div class="info-value">
                {{ userStore.userInfo?.role || '普通用户' }}
              </div>
            </div>
          </div>
        </div>

        <div v-if="isEditing" class="save-row">
          <button class="save-btn" @click="saveProfile">保存修改</button>
        </div>
      </section>

      <!-- 下半部分：历史记录 -->
      <section class="history-card">
        <div class="section-head history-head">
          <div class="section-title">历史处理记录</div>
          <div class="history-head-actions">
            <button
              class="action-btn"
              :disabled="!hasHistory"
              @click="toggleBatchMode"
            >
              {{ batchMode ? '取消批量' : '批量删除' }}
            </button>
            <button
              class="action-btn danger-btn"
              :disabled="!hasHistory"
              @click="deleteAllHistory"
            >
              全部删除
            </button>
          </div>
        </div>

        <div v-if="historyList.length" class="history-list">
          <div
            v-for="item in historyList"
            :key="item.id"
            class="history-item"
          >
            <div class="history-left">
              <label v-if="batchMode" class="history-check">
                <input
                  type="checkbox"
                  :value="item.id"
                  v-model="selectedIds"
                />
                <span>选择</span>
              </label>

              <button
                v-else
                class="item-delete-btn"
                @click="deleteHistoryItem(item.id)"
              >
                删除
              </button>
            </div>

            <div class="history-center">
              <div class="history-name">{{ item.fileName }}</div>
              <div class="history-meta">
                {{ item.type }} ｜ {{ item.time }}
              </div>
              <div v-if="item.summary" class="history-summary">
                {{ item.summary }}
              </div>
            </div>

            <div class="history-right">
              <span class="history-status">{{ item.status }}</span>
            </div>
          </div>
        </div>

        <div v-if="batchMode && historyList.length" class="batch-bar">
          <div class="batch-info">
            已选择 <strong>{{ selectedIds.length }}</strong> 条记录
          </div>
          <button
            class="save-btn danger-solid-btn"
            :disabled="!selectedIds.length"
            @click="deleteSelectedHistory"
          >
            删除选中
          </button>
        </div>

        <div v-else-if="!historyList.length" class="empty-box">
          暂无上传处理记录
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watchEffect, onMounted } from 'vue'
import AppHeader from '../components/AppHeader.vue'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const isEditing = ref(false)
const batchMode = ref(false)
const selectedIds = ref([])

const form = reactive({
  nickname: '',
  email: '',
  gender: '未设置',
  phone: ''
})

watchEffect(() => {
  form.nickname = userStore.userInfo?.nickname || ''
  form.email = userStore.userInfo?.email || ''
  form.gender = userStore.userInfo?.gender || '未设置'
  form.phone = userStore.userInfo?.phone || ''
})

const historyList = computed(() => userStore.historyList || [])
const hasHistory = computed(() => historyList.value.length > 0)

const avatarText = computed(() => {
  const name = userStore.userInfo?.nickname || userStore.userInfo?.username || 'U'
  return name.slice(0, 1).toUpperCase()
})

const toggleEdit = () => {
  isEditing.value = !isEditing.value
}

const toggleBatchMode = () => {
  batchMode.value = !batchMode.value
  if (!batchMode.value) {
    selectedIds.value = []
  }
}

const syncHistoryList = async (nextList) => {
  if (typeof userStore.setHistoryList === 'function') {
    userStore.setHistoryList(nextList)
  } else {
    userStore.historyList = nextList
  }

  if (typeof userStore.saveHistoryList === 'function') {
    await userStore.saveHistoryList(nextList)
  } else if (typeof window !== 'undefined') {
    localStorage.setItem('historyList', JSON.stringify(nextList))
  }
}

const deleteHistoryByIds = async (ids) => {
  if (!ids.length) return

  if (typeof userStore.deleteHistoryAction === 'function') {
    await userStore.deleteHistoryAction(ids)
  } else {
    const nextList = historyList.value.filter((item) => !ids.includes(item.id))
    await syncHistoryList(nextList)
  }
}

const deleteHistoryItem = async (id) => {
  const confirmed = window.confirm('确定删除这条历史处理记录吗？')
  if (!confirmed) return

  try {
    await deleteHistoryByIds([id])
    selectedIds.value = selectedIds.value.filter((itemId) => itemId !== id)
    alert('删除成功')
  } catch (error) {
    alert(error.message || '删除失败')
  }
}

const deleteSelectedHistory = async () => {
  if (!selectedIds.value.length) {
    alert('请先选择要删除的记录')
    return
  }

  const confirmed = window.confirm(`确定删除选中的 ${selectedIds.value.length} 条记录吗？`)
  if (!confirmed) return

  try {
    await deleteHistoryByIds(selectedIds.value)
    selectedIds.value = []
    batchMode.value = false
    alert('批量删除成功')
  } catch (error) {
    alert(error.message || '批量删除失败')
  }
}

const deleteAllHistory = async () => {
  if (!historyList.value.length) {
    alert('暂无可删除的历史记录')
    return
  }

  const confirmed = window.confirm('确定删除全部历史处理记录吗？')
  if (!confirmed) return

  try {
    if (typeof userStore.clearHistoryAction === 'function') {
      await userStore.clearHistoryAction()
    } else {
      await syncHistoryList([])
    }

    selectedIds.value = []
    batchMode.value = false
    alert('已全部删除')
  } catch (error) {
    alert(error.message || '全部删除失败')
  }
}

const saveProfile = async () => {
  try {
    await userStore.updateProfileAction({
      nickname: form.nickname,
      email: form.email,
      gender: form.gender,
      phone: form.phone
    })

    isEditing.value = false
    alert('个人信息已更新')
  } catch (error) {
    alert(error.message || '更新失败')
  }
}

onMounted(async () => {
  try {
    await userStore.getProfileAction()
  } catch (error) {
    alert(error.message || '获取个人信息失败')
  }
})

const handleAvatarChange = (event) => {
  const file = event.target.files?.[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = () => {
    userStore.updateAvatar(reader.result)
  }
  reader.readAsDataURL(file)
}
</script>

<style scoped>
.profile-page {
  min-height: 100vh;
  background: #ececec;
}

.container {
  width: 1200px;
  max-width: calc(100% - 48px);
  margin: 0 auto;
}

.profile-container {
  padding: 32px 0 48px;
  display: grid;
  gap: 24px;
}

.profile-card,
.history-card {
  background: #f8f8f8;
  border-radius: 18px;
  padding: 28px 28px 30px;
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.05);
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  gap: 16px;
}

.history-head {
  min-height: 40px;
}

.section-title {
  font-size: 24px;
  font-weight: 700;
  color: #2d2d2d;
}

.history-head-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.edit-btn,
.save-btn,
.action-btn,
.item-delete-btn {
  height: 40px;
  padding: 0 18px;
  border: none;
  border-radius: 20px;
  background: #d5b076;
  color: #fff;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}

.action-btn:disabled,
.save-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-btn:hover:not(:disabled),
.edit-btn:hover,
.save-btn:hover,
.item-delete-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 16px rgba(213, 176, 118, 0.22);
}

.danger-btn,
.danger-solid-btn,
.item-delete-btn {
  background: #d86c6c;
}

.danger-btn:hover:not(:disabled),
.danger-solid-btn:hover:not(:disabled),
.item-delete-btn:hover {
  box-shadow: 0 8px 16px rgba(216, 108, 108, 0.22);
}

.profile-top {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 28px;
  align-items: start;
}

.avatar-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.avatar-box {
  width: 140px;
  height: 140px;
  border-radius: 50%;
  background: #ffffff;
  border: 2px solid #e8d6b4;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-text {
  font-size: 42px;
  font-weight: 700;
  color: #d5b076;
}

.avatar-upload-btn {
  height: 40px;
  padding: 0 18px;
  border-radius: 20px;
  background: #d5b076;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 14px;
}

.hidden-input {
  display: none;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px 22px;
}

.info-item {
  background: #fff;
  border-radius: 12px;
  padding: 16px 18px;
  border: 1px solid #ececec;
}

.info-item label {
  display: block;
  font-size: 13px;
  color: #999;
  margin-bottom: 8px;
}

.info-value {
  font-size: 15px;
  color: #333;
  line-height: 1.6;
  word-break: break-all;
}

.info-input {
  width: 100%;
  height: 40px;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 0 12px;
  font-size: 14px;
  color: #333;
  background: #fff;
  outline: none;
}

.save-row {
  margin-top: 22px;
  display: flex;
  justify-content: flex-end;
}

.history-list {
  display: grid;
  gap: 14px;
  margin-top: 15px;
}

.history-item {
  background: #fff;
  border-radius: 12px;
  padding: 18px 20px;
  border: 1px solid #ececec;
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 20px;
}

.history-left {
  width: 96px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.history-check {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #666;
  cursor: pointer;
}

.history-check input {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.history-center {
  min-width: 0;
}

.history-name {
  font-size: 16px;
  font-weight: 600;
  color: #2d2d2d;
  margin-bottom: 6px;
  word-break: break-all;
}

.history-meta {
  font-size: 13px;
  color: #999;
  margin-bottom: 6px;
}

.history-summary {
  font-size: 13px;
  color: #666;
  line-height: 1.7;
}

.history-right {
  flex-shrink: 0;
}

.history-status {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 88px;
  height: 32px;
  border-radius: 16px;
  background: rgba(213, 176, 118, 0.16);
  color: #b48742;
  font-size: 13px;
  font-weight: 600;
}

.batch-bar {
  margin-top: 16px;
  padding: 16px 18px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #ececec;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.batch-info {
  font-size: 14px;
  color: #666;
}

.empty-box {
  min-height: 180px;
  background: #fff;
  border: 1px dashed #ddd;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  font-size: 15px;
  margin-top: 15px;
}

@media (max-width: 900px) {
  .profile-top {
    grid-template-columns: 1fr;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }

  .section-head,
  .history-head-actions,
  .batch-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .history-item {
    grid-template-columns: 1fr;
    align-items: flex-start;
  }

  .history-left,
  .history-right {
    width: 100%;
  }
}
</style>
