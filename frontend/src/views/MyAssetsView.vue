<template>
  <div class="assets-page">
    <AppHeader />

    <div class="container assets-container">
      <div class="main-layout">
        <!-- 左侧 -->
        <aside class="left-panel">
          <section class="profile-card">
            <div class="panel-title">我的资产</div>

            <div class="profile-top">
              <div class="avatar">{{ userAssets.nickname.slice(0, 1) }}</div>
              <div class="profile-info">
                <div class="profile-name">{{ userAssets.nickname }}</div>
                <div class="profile-id">邮箱：{{ userAssets.account }}</div>
              </div>
            </div>

            <div class="level-box">
              <div class="level-head">
                <span class="level-title">活跃度成长</span>
                <span class="level-value">Lv.{{ userAssets.level }}</span>
              </div>

              <div class="progress-track">
                <div
                  class="progress-fill"
                  :style="{ width: activityPercent + '%' }"
                ></div>
              </div>

              <div class="level-desc">
                当前活跃度 {{ userAssets.activity }} / 下一级需 {{ nextLevelNeed }}
              </div>
            </div>

            <div class="asset-summary">
              <div class="summary-item">
                <div class="summary-value">{{ totalUsedCount }}</div>
                <div class="summary-label">累计使用次数</div>
              </div>
              <div class="summary-item">
                <div class="summary-value">{{ usedTemplates.length }}</div>
                <div class="summary-label">已用模板</div>
              </div>
              <div class="summary-item">
                <div class="summary-value">{{ favoriteCategories.length }}</div>
                <div class="summary-label">常用分类</div>
              </div>
            </div>
          </section>

          <section class="quick-card">
            <div class="panel-title">快捷操作</div>

            <div class="quick-grid">
              <div class="quick-item" @click="goTemplateLibrary">
                <div class="quick-icon">📚</div>
                <div>
                  <div class="quick-name">去模板库</div>
                  <div class="quick-desc">继续选择并使用模板</div>
                </div>
              </div>

              <div class="quick-item" @click="clearLogs">
                <div class="quick-icon">🧹</div>
                <div>
                  <div class="quick-name">清空明细</div>
                  <div class="quick-desc">清理当前活跃度记录示例数据</div>
                </div>
              </div>
            </div>
          </section>

          <section class="category-card">
            <div class="panel-title">常用分类</div>

            <div v-if="favoriteCategories.length" class="category-list-box">
              <div
                v-for="item in favoriteCategories"
                :key="item.name"
                class="category-item"
              >
                <div>
                  <div class="category-name">{{ item.name }}</div>
                  <div class="category-desc">累计使用 {{ item.count }} 次</div>
                </div>
                <div class="category-badge">{{ item.count }}</div>
              </div>
            </div>

            <div v-else class="empty-inline">暂无分类数据</div>
          </section>
        </aside>

        <!-- 右侧 -->
        <main class="right-panel">
          <!-- 最近使用记录 -->
          <section class="record-card">
            <div class="section-head">
              <div>
                <div class="section-title">最近使用记录</div>
                <div class="section-subtitle">保存你近期使用过的模板资产</div>
              </div>
              <div class="section-extra">
                共 {{ usedTemplates.length }} 条记录
              </div>
            </div>

            <div v-if="displayedUsedTemplates.length" class="record-list">
              <div
                v-for="item in displayedUsedTemplates"
                :key="item.recordId"
                class="record-item"
              >
                <div class="record-left">
                  <div class="record-icon">{{ item.shortName }}</div>

                  <div class="record-info">
                    <div class="record-name-row">
                      <div class="record-name">{{ item.name }}</div>
                      <span class="record-tag">{{ item.category }}</span>
                    </div>

                    <div class="record-desc">{{ item.description }}</div>

                    <div class="record-meta">
                      <span>使用场景：{{ item.scene }}</span>
                      <span>最近使用：{{ item.lastUsedAt }}</span>
                      <span>累计使用 {{ item.useCount }} 次</span>
                    </div>
                  </div>
                </div>

                <div class="record-right">
                  <div class="activity-reward">+{{ item.rewardActivity }} 活跃度</div>

                  <div class="record-actions">
                    <button class="use-btn" @click="handleUseAsset(item)">
                      继续使用
                    </button>
                    <button class="delete-btn" @click="deleteUsedRecord(item.recordId)">
                      删除
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <div v-else class="empty-box">
              你还没有使用记录，快去模板库体验一下吧
            </div>

            <div
              v-if="usedTemplates.length > 2"
              class="more-row"
            >
              <button class="more-btn" @click="toggleShowAllUsed">
                {{ showAllUsed ? '收起记录' : '展示更多' }}
              </button>
            </div>
          </section>

          <!-- 资产统计 -->
          <section class="stats-card">
            <div class="section-head">
              <div>
                <div class="section-title">资产统计</div>
                <div class="section-subtitle">帮助你快速了解自己的使用习惯</div>
              </div>
            </div>

            <div class="stats-grid">
              <div class="stats-item highlight">
                <div class="stats-label">本周使用</div>
                <div class="stats-value">{{ weeklyUsage }}</div>
              </div>
              <div class="stats-item">
                <div class="stats-label">最常用模板</div>
                <div class="stats-value text-ellipsis">{{ mostUsedTemplate }}</div>
              </div>
              <div class="stats-item">
                <div class="stats-label">最近获得活跃度</div>
                <div class="stats-value">+{{ recentActivityGain }}</div>
              </div>
            </div>
          </section>

          <!-- 活跃度明细 -->
          <section class="activity-card">
            <div class="section-head">
              <div>
                <div class="section-title">活跃度明细</div>
                <div class="section-subtitle">每次使用模板都可以积累成长值</div>
              </div>
            </div>

            <div v-if="activityLogs.length" class="activity-log-list">
              <div
                v-for="log in activityLogs"
                :key="log.id"
                class="activity-log-item"
              >
                <div class="log-left">
                  <div class="log-dot"></div>
                  <div>
                    <div class="log-title">{{ log.title }}</div>
                    <div class="log-time">{{ log.time }}</div>
                  </div>
                </div>
                <div class="log-score">+{{ log.score }}</div>
              </div>
            </div>

            <div v-else class="empty-box small-empty">
              暂无活跃度明细
            </div>
          </section>

          <!-- 历史处理记录 -->
          <section class="history-card">
            <div class="section-head">
              <div>
                <div class="section-title">历史处理记录</div>
                <div class="section-subtitle">按功能分类查看你的历史处理内容</div>
              </div>
            </div>

            <div class="history-tabs">
              <button
                v-for="tab in historyTabs"
                :key="tab"
                class="history-tab"
                :class="{ active: currentHistoryType === tab }"
                @click="currentHistoryType = tab"
              >
                {{ tab }}
              </button>
            </div>

            <div v-if="filteredHistoryList.length" class="history-list">
              <div
                v-for="item in filteredHistoryList"
                :key="item.id"
                class="history-item"
              >
                <div class="history-left">
                  <div class="history-type-badge">
                    {{ getHistoryTypeShort(item.type) }}
                  </div>
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

            <div v-else class="empty-box small-empty">
              当前分类下暂无处理记录
            </div>
          </section>
        </main>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'

const router = useRouter()

const showAllUsed = ref(false)
const currentHistoryType = ref('文档智能操作交互')

const historyTabs = [
  '文档智能操作交互',
  '非结构化文档信息提取',
  '表格自定义数据填写'
]

const userAssets = ref({
  nickname: 'zhangsan',
  account: 'zhangsan@example.com',
  activity: 86,
  level: 3
})

const usedTemplates = ref([
  {
    recordId: 1,
    id: 101,
    name: '合同信息登记表',
    shortName: '合',
    category: '行政办公',
    scene: '合同管理',
    description: '适用于合同基础信息登记、审批流转及归档管理。',
    lastUsedAt: '今天 14:22',
    useCount: 6,
    rewardActivity: 8
  },
  {
    recordId: 2,
    id: 102,
    name: '费用报销申请表',
    shortName: '报',
    category: '财务管理',
    scene: '费用报销',
    description: '适合日常差旅、办公采购、项目支出等报销场景。',
    lastUsedAt: '今天 10:18',
    useCount: 9,
    rewardActivity: 10
  },
  {
    recordId: 3,
    id: 103,
    name: '项目进度跟踪表',
    shortName: '项',
    category: '项目管理',
    scene: '进度管理',
    description: '适合团队项目阶段任务跟踪、负责人分配与完成状态记录。',
    lastUsedAt: '昨天 18:05',
    useCount: 4,
    rewardActivity: 12
  },
  {
    recordId: 4,
    id: 104,
    name: '员工入职信息表',
    shortName: '入',
    category: '人事管理',
    scene: '员工档案',
    description: '用于员工入职基础信息采集与统一录入。',
    lastUsedAt: '昨天 09:42',
    useCount: 7,
    rewardActivity: 9
  }
])

const activityLogs = ref([
  {
    id: 1,
    title: '使用「费用报销申请表」获得活跃度',
    score: 10,
    time: '今天 10:18'
  },
  {
    id: 2,
    title: '使用「合同信息登记表」获得活跃度',
    score: 8,
    time: '今天 14:22'
  },
  {
    id: 3,
    title: '使用「项目进度跟踪表」获得活跃度',
    score: 12,
    time: '昨天 18:05'
  },
  {
    id: 4,
    title: '使用「员工入职信息表」获得活跃度',
    score: 9,
    time: '昨天 09:42'
  }
])

const historyList = ref([
  {
    id: 1,
    fileName: '合同草案.docx',
    type: '文档智能操作交互',
    time: '今天 15:20',
    status: '已完成',
    summary: '已完成文档问答、重点条款定位与摘要生成。'
  },
  {
    id: 2,
    fileName: '发票识别材料.docx',
    type: '非结构化文档信息提取',
    time: '今天 11:08',
    status: '已完成',
    summary: '已提取票据编号、金额、日期与开票方信息。'
  },
  {
    id: 3,
    fileName: '项目模板.xlsx',
    type: '表格自定义数据填写',
    time: '昨天 17:42',
    status: '已完成',
    summary: '已按照字段规则自动填写项目日报表格内容。'
  },
  {
    id: 4,
    fileName: '采购合同.docx',
    type: '文档智能操作交互',
    time: '昨天 14:15',
    status: '已完成',
    summary: '已完成内容检索、问答交互与风险点初步识别。'
  },
  {
    id: 5,
    fileName: '客户资料.docx',
    type: '非结构化文档信息提取',
    time: '昨天 09:30',
    status: '已完成',
    summary: '已提取客户名称、联系方式、地址等字段信息。'
  }
])

const displayedUsedTemplates = computed(() => {
  return showAllUsed.value ? usedTemplates.value : usedTemplates.value.slice(0, 2)
})

const filteredHistoryList = computed(() => {
  return historyList.value.filter(item => item.type === currentHistoryType.value)
})

const totalUsedCount = computed(() => {
  return usedTemplates.value.reduce((sum, item) => sum + item.useCount, 0)
})

const favoriteCategories = computed(() => {
  const map = {}

  usedTemplates.value.forEach(item => {
    if (!map[item.category]) {
      map[item.category] = 0
    }
    map[item.category] += item.useCount
  })

  return Object.keys(map)
    .map(key => ({
      name: key,
      count: map[key]
    }))
    .sort((a, b) => b.count - a.count)
})

const weeklyUsage = computed(() => {
  return usedTemplates.value.reduce((sum, item) => sum + Math.min(item.useCount, 3), 0)
})

const mostUsedTemplate = computed(() => {
  if (!usedTemplates.value.length) return '暂无'
  const top = [...usedTemplates.value].sort((a, b) => b.useCount - a.useCount)[0]
  return top?.name || '暂无'
})

const recentActivityGain = computed(() => {
  return activityLogs.value.slice(0, 3).reduce((sum, item) => sum + item.score, 0)
})

const nextLevelNeed = computed(() => {
  return userAssets.value.level * 50
})

const activityPercent = computed(() => {
  return Math.min((userAssets.value.activity / nextLevelNeed.value) * 100, 100)
})

const getCurrentTimeText = () => {
  const now = new Date()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const date = String(now.getDate()).padStart(2, '0')
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  return `${month}-${date} ${hours}:${minutes}`
}

const handleUseAsset = (item) => {
  if (!item) return

  item.useCount += 1
  item.lastUsedAt = '刚刚'
  userAssets.value.activity += item.rewardActivity

  activityLogs.value.unshift({
    id: Date.now(),
    title: `使用「${item.name}」获得活跃度`,
    score: item.rewardActivity,
    time: getCurrentTimeText()
  })

  updateLevel()
}

const updateLevel = () => {
  while (userAssets.value.activity >= userAssets.value.level * 50) {
    userAssets.value.level += 1
  }
}

const deleteUsedRecord = (recordId) => {
  const confirmed = window.confirm('确定删除这条最近使用记录吗？')
  if (!confirmed) return

  usedTemplates.value = usedTemplates.value.filter(item => item.recordId !== recordId)
}

const toggleShowAllUsed = () => {
  showAllUsed.value = !showAllUsed.value
}

const clearLogs = () => {
  activityLogs.value = []
}

const goTemplateLibrary = () => {
  router.push('/template')
}

const getHistoryTypeShort = (type) => {
  if (type === '文档智能操作交互') return '智'
  if (type === '非结构化文档信息提取') return '提'
  if (type === '表格自定义数据填写') return '填'
  return '记'
}
</script>

<style scoped>
.assets-page {
  min-height: 100vh;
  background: #ececec;
}

.container {
  width: 1200px;
  max-width: calc(100% - 48px);
  margin: 0 auto;
}

.assets-container {
  padding: 32px 0 48px;
}

.main-layout {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 24px;
  align-items: start;
}

.left-panel,
.right-panel {
  display: grid;
  gap: 24px;
}

.profile-card,
.quick-card,
.category-card,
.record-card,
.activity-card,
.stats-card,
.history-card {
  background: #f8f8f8;
  border-radius: 18px;
  padding: 28px;
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.05);
}

.panel-title,
.section-title {
  font-size: 22px;
  font-weight: 700;
  color: #2d2d2d;
}

.section-subtitle {
  margin-top: 4px;
  font-size: 14px;
  color: #999;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 22px;
  gap: 16px;
}

.section-extra {
  font-size: 13px;
  color: #999;
  background: #fff;
  border: 1px solid #ececec;
  padding: 8px 12px;
  border-radius: 999px;
}

.profile-top {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 22px;
}

.avatar {
  width: 68px;
  height: 68px;
  border-radius: 22px;
  background: linear-gradient(135deg, #e8d0a4, #d5b076);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 30px;
  font-weight: 700;
  box-shadow: 0 8px 18px rgba(213, 176, 118, 0.3);
}

.profile-name {
  font-size: 20px;
  font-weight: 700;
  color: #2d2d2d;
  margin-bottom: 4px;
}

.profile-id {
  font-size: 13px;
  color: #999;
}

.level-box {
  margin-top: 24px;
  background: #fff;
  border-radius: 16px;
  border: 1px solid #ececec;
  padding: 18px;
}

.level-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.level-title {
  font-size: 15px;
  font-weight: 700;
  color: #2d2d2d;
}

.level-value {
  font-size: 14px;
  color: #b48742;
  font-weight: 700;
}

.progress-track {
  width: 100%;
  height: 10px;
  background: #f0ede7;
  border-radius: 999px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #d5b076, #e8c790);
  transition: width 0.4s ease;
}

.level-desc {
  margin-top: 10px;
  font-size: 13px;
  color: #888;
}

.asset-summary {
  margin-top: 18px;
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

.summary-item {
  background: #fff;
  border: 1px solid #ececec;
  border-radius: 14px;
  padding: 16px 16px;
  transition: all 0.2s ease;
}

.summary-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 18px rgba(0, 0, 0, 0.04);
}

.summary-value {
  font-size: 22px;
  font-weight: 700;
  color: #2d2d2d;
  margin-bottom: 6px;
}

.summary-label {
  font-size: 13px;
  color: #999;
}

.quick-grid {
  margin-top: 20px;
  display: grid;
  gap: 14px;
}

.quick-item {
  background: #fff;
  border: 1px solid #ececec;
  border-radius: 16px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.quick-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 20px rgba(0, 0, 0, 0.05);
  border-color: #e8d6b4;
}

.quick-icon {
  width: 46px;
  height: 46px;
  border-radius: 14px;
  background: #faf6ef;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
}

.quick-name {
  font-size: 15px;
  font-weight: 700;
  color: #2d2d2d;
  margin-bottom: 4px;
}

.quick-desc {
  font-size: 13px;
  color: #999;
}

.category-list-box {
  margin-top: 18px;
  display: grid;
  gap: 12px;
}

.category-item {
  background: #fff;
  border: 1px solid #ececec;
  border-radius: 14px;
  padding: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  transition: all 0.2s ease;
}

.category-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 18px rgba(0, 0, 0, 0.04);
}

.category-name {
  font-size: 15px;
  font-weight: 700;
  color: #2d2d2d;
}

.category-desc {
  margin-top: 4px;
  font-size: 13px;
  color: #999;
}

.category-badge {
  min-width: 34px;
  height: 34px;
  border-radius: 17px;
  background: rgba(213, 176, 118, 0.14);
  color: #b48742;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 13px;
}

.record-list,
.activity-log-list,
.history-list {
  display: grid;
  gap: 16px;
}

.record-item {
  background: #fff;
  border: 1px solid #ececec;
  border-radius: 18px;
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  transition: all 0.25s ease;
  position: relative;
  overflow: hidden;
}

.record-item::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: linear-gradient(180deg, #d5b076, #e8c790);
  opacity: 0;
  transition: opacity 0.25s ease;
}

.record-item:hover {
  transform: translateY(-3px);
  box-shadow: 0 14px 24px rgba(0, 0, 0, 0.05);
  border-color: #ead8ba;
}

.record-item:hover::after {
  opacity: 1;
}

.record-left {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  min-width: 0;
}

.record-icon {
  width: 58px;
  height: 58px;
  border-radius: 18px;
  background: linear-gradient(135deg, #f2e4cf, #ead3ac);
  color: #9a6d2f;
  font-size: 24px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 8px 18px rgba(213, 176, 118, 0.16);
}

.record-info {
  min-width: 0;
}

.record-name-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.record-name {
  font-size: 18px;
  font-weight: 700;
  color: #2d2d2d;
}

.record-tag {
  display: inline-flex;
  align-items: center;
  height: 26px;
  padding: 0 10px;
  border-radius: 13px;
  background: #faf6ef;
  border: 1px solid #ead8ba;
  color: #b48742;
  font-size: 12px;
}

.record-desc {
  margin-top: 8px;
  font-size: 14px;
  line-height: 1.8;
  color: #666;
}

.record-meta {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  font-size: 13px;
  color: #999;
}

.record-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 12px;
  flex-shrink: 0;
}

.record-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.activity-reward {
  font-size: 14px;
  color: #d84f4f;
  font-weight: 700;
}

.use-btn,
.delete-btn,
.more-btn,
.history-tab {
  height: 40px;
  padding: 0 18px;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}

.use-btn {
  background: #d5b076;
  color: #fff;
}

.use-btn:hover {
  background: #c59d60;
  transform: translateY(-1px);
}

.delete-btn {
  background: #d86c6c;
  color: #fff;
}

.delete-btn:hover {
  background: #c95a5a;
  transform: translateY(-1px);
}

.more-row {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.more-btn {
  background: #fff;
  color: #b48742;
  border: 1px solid #e8d6b4;
}

.more-btn:hover {
  background: #faf6ef;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.stats-item {
  background: #fff;
  border: 1px solid #ececec;
  border-radius: 16px;
  padding: 20px 18px;
  transition: all 0.2s ease;
}

.stats-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 20px rgba(0, 0, 0, 0.04);
}

.stats-item.highlight {
  background: linear-gradient(135deg, #f7efe1, #fffaf3);
  border-color: #ead8ba;
}

.stats-label {
  font-size: 13px;
  color: #999;
  margin-bottom: 10px;
}

.stats-value {
  font-size: 22px;
  font-weight: 700;
  color: #2d2d2d;
}

.text-ellipsis {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.activity-log-item {
  background: #fff;
  border: 1px solid #ececec;
  border-radius: 14px;
  padding: 16px 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  transition: all 0.2s ease;
}

.activity-log-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 18px rgba(0, 0, 0, 0.04);
  border-color: #ead8ba;
}

.log-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.log-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #d5b076;
  box-shadow: 0 0 0 6px rgba(213, 176, 118, 0.12);
}

.log-title {
  font-size: 15px;
  color: #2d2d2d;
  font-weight: 600;
}

.log-time {
  margin-top: 4px;
  font-size: 13px;
  color: #999;
}

.log-score {
  font-size: 16px;
  font-weight: 700;
  color: #d84f4f;
}

.history-tabs {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}

.history-tab {
  background: #fff;
  color: #666;
  border: 1px solid #ececec;
}

.history-tab:hover {
  background: #faf6ef;
  color: #b48742;
}

.history-tab.active {
  background: #d5b076;
  color: #fff;
  border-color: #d5b076;
}

.history-item {
  background: #fff;
  border-radius: 16px;
  padding: 18px 20px;
  border: 1px solid #ececec;
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 18px;
  transition: all 0.2s ease;
}

.history-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 18px rgba(0, 0, 0, 0.04);
  border-color: #ead8ba;
}

.history-type-badge {
  width: 46px;
  height: 46px;
  border-radius: 14px;
  background: linear-gradient(135deg, #f2e4cf, #ead3ac);
  color: #9a6d2f;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 700;
}

.history-center {
  min-width: 0;
}

.history-name {
  font-size: 16px;
  font-weight: 700;
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

.empty-box {
  min-height: 220px;
  background: #fff;
  border: 1px dashed #ddd;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  font-size: 15px;
}

.small-empty {
  min-height: 120px;
}

.empty-inline {
  margin-top: 18px;
  background: #fff;
  border: 1px dashed #ddd;
  border-radius: 12px;
  padding: 18px;
  text-align: center;
  color: #999;
  font-size: 14px;
}

@media (max-width: 1100px) {
  .main-layout,
  .stats-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .assets-container {
    padding: 24px 0 40px;
  }

  .record-item,
  .section-head,
  .history-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .record-right {
    width: 100%;
    align-items: flex-start;
  }

  .record-actions {
    justify-content: flex-start;
  }

  .history-item {
    grid-template-columns: 1fr;
  }
}
</style>