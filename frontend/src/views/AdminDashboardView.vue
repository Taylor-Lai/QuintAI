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

      <!-- 右侧主内容 -->
      <main ref="mainContentRef" class="main-content">
        <!-- 页面标题 -->
        <section class="overview-header card">
          <div>
            <div class="section-title">数据总览</div>
            <div class="section-subtitle">
              展示平台各业务模块的使用情况、活跃趋势与交互统计
            </div>
          </div>

          <div class="date-tip">统计周期：近 7 天</div>
        </section>

        <!-- 顶部统计卡片 -->
        <section class="stats-grid">
          <div class="stat-card card">
            <div class="stat-label">总用户数</div>
            <div class="stat-value">126</div>
            <div class="stat-trend up">较昨日 +3.8%</div>
          </div>

          <div class="stat-card card">
            <div class="stat-label">今日活跃用户</div>
            <div class="stat-value">23</div>
            <div class="stat-trend up">较昨日 +5.2%</div>
          </div>

          <div class="stat-card card">
            <div class="stat-label">模块总调用次数</div>
            <div class="stat-value">369</div>
            <div class="stat-trend up">较昨日 +8.1%</div>
          </div>

          <div class="stat-card card">
            <div class="stat-label">问题反馈总量</div>
            <div class="stat-value">4</div>
            <div class="stat-trend down">较昨日 -1.4%</div>
          </div>
        </section>

        <!-- 图表区域 -->
        <section class="chart-grid">
          <div class="chart-card card large">
            <div class="card-title">近7日模块使用趋势</div>
            <div ref="trendChartRef" class="chart-box trend-chart-box"></div>
          </div>

          <div class="chart-card card">
            <div class="card-title">模块使用占比</div>
            <div ref="pieChartRef" class="chart-box pie-chart-box"></div>
          </div>

          <div class="chart-card card">
            <div class="card-title">模块活跃用户数</div>
            <div ref="barChartRef" class="chart-box"></div>
          </div>

          <div class="chart-card card large">
            <div class="card-title">近7日活跃状态变化</div>
            <div ref="activeChartRef" class="chart-box"></div>
          </div>
        </section>

        <!-- 模块数据表 -->
        <section class="table-card card">
          <div class="table-head">
            <div class="section-title">模块运行统计</div>
            <div class="table-tip">当前展示核心模块使用情况</div>
          </div>

          <div class="table-wrap">
            <table class="data-table">
              <thead>
                <tr>
                  <th>模块名称</th>
                  <th>累计访问量</th>
                  <th>今日访问量</th>
                  <th>活跃用户数</th>
                  <th>平均停留时长</th>
                  <th>使用状态</th>
                </tr>
              </thead>

              <tbody>
                <tr v-for="item in moduleTableData" :key="item.name">
                  <td>{{ item.name }}</td>
                  <td>{{ item.totalVisits }}</td>
                  <td>{{ item.todayVisits }}</td>
                  <td>{{ item.activeUsers }}</td>
                  <td>{{ item.avgDuration }}</td>
                  <td>
                    <span
                      class="status-badge"
                      :class="item.status === '活跃' ? 'active' : item.status === '稳定' ? 'stable' : 'warning'"
                    >
                      {{ item.status }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import * as echarts from 'echarts/core'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import AppHeader from '../components/AppHeader.vue'

echarts.use([
  BarChart,
  LineChart,
  PieChart,
  GridComponent,
  LegendComponent,
  TooltipComponent,
  CanvasRenderer
])

const router = useRouter()
const route = useRoute()

const sidebarCollapsed = ref(
  localStorage.getItem('admin_sidebar_collapsed') === 'true'
)

const mainContentRef = ref(null)
const trendChartRef = ref(null)
const pieChartRef = ref(null)
const barChartRef = ref(null)
const activeChartRef = ref(null)

let trendChart = null
let pieChart = null
let barChart = null
let activeChart = null

let mainResizeObserver = null
let trendResizeObserver = null
let animationFrameId = null

const moduleTableData = [
  {
    name: '文档智能操作交互',
    totalVisits: '152',
    todayVisits: '18',
    activeUsers: '11',
    avgDuration: '8分24秒',
    status: '活跃'
  },
  {
    name: '非结构化文档信息提取',
    totalVisits: '124',
    todayVisits: '14',
    activeUsers: '9',
    avgDuration: '7分16秒',
    status: '稳定'
  },
  {
    name: '表格自定义数据填写',
    totalVisits: '91',
    todayVisits: '9',
    activeUsers: '6',
    avgDuration: '5分52秒',
    status: '活跃'
  }
]

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
  localStorage.setItem('admin_sidebar_collapsed', String(sidebarCollapsed.value))
}

const goPage = (path) => {
  if (route.path === path) return
  router.push(path)
}

const safeResizeCharts = () => {
  if (animationFrameId) cancelAnimationFrame(animationFrameId)

  animationFrameId = requestAnimationFrame(() => {
    trendChart?.resize({
      animation: {
        duration: 120
      }
    })
    pieChart?.resize({
      animation: {
        duration: 120
      }
    })
    barChart?.resize({
      animation: {
        duration: 120
      }
    })
    activeChart?.resize({
      animation: {
        duration: 120
      }
    })
  })
}

const initTrendChart = () => {
  if (!trendChartRef.value) return
  trendChart = echarts.init(trendChartRef.value)

  trendChart.setOption({
    animationDuration: 400,
    animationDurationUpdate: 250,
    animationEasing: 'cubicOut',
    animationEasingUpdate: 'cubicOut',
    tooltip: {
      trigger: 'axis',
      confine: true
    },
    legend: {
      top: 12,
      left: 'center',
      textStyle: {
        color: '#666'
      }
    },
    grid: {
      left: '4%',
      right: '6%',
      bottom: '6%',
      top: 64,
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: ['03-20', '03-21', '03-22', '03-23', '03-24', '03-25', '03-26'],
      axisLine: {
        lineStyle: {
          color: '#ddd'
        }
      },
      axisLabel: {
        color: '#666',
        margin: 12
      },
      axisTick: {
        show: false
      }
    },
    yAxis: {
      type: 'value',
      axisLine: {
        show: false
      },
      splitLine: {
        lineStyle: {
          color: '#eee'
        }
      },
      axisLabel: {
        color: '#666',
        margin: 12
      }
    },
    series: [
      {
        name: '文档智能操作交互',
        type: 'line',
        smooth: 0.35,
        symbol: 'circle',
        symbolSize: 7,
        clip: true,
        data: [132, 145, 151, 168, 175, 182, 186],
        lineStyle: {
          color: '#d5b076',
          width: 3
        },
        itemStyle: {
          color: '#d5b076'
        },
        areaStyle: {
          color: 'rgba(213, 176, 118, 0.16)'
        }
      },
      {
        name: '非结构化文档信息提取',
        type: 'line',
        smooth: 0.35,
        symbol: 'circle',
        symbolSize: 7,
        clip: true,
        data: [98, 105, 111, 124, 131, 138, 142],
        lineStyle: {
          color: '#5b8ff9',
          width: 3
        },
        itemStyle: {
          color: '#5b8ff9'
        },
        areaStyle: {
          color: 'rgba(91, 143, 249, 0.12)'
        }
      },
      {
        name: '表格自定义数据填写',
        type: 'line',
        smooth: 0.35,
        symbol: 'circle',
        symbolSize: 7,
        clip: true,
        data: [62, 71, 75, 81, 86, 91, 93],
        lineStyle: {
          color: '#61d9a5',
          width: 3
        },
        itemStyle: {
          color: '#61d9a5'
        },
        areaStyle: {
          color: 'rgba(97, 217, 165, 0.12)'
        }
      }
    ]
  })
}

const initPieChart = () => {
  if (!pieChartRef.value) return
  pieChart = echarts.init(pieChartRef.value)

  pieChart.setOption({
    animationDuration: 400,
    animationDurationUpdate: 250,
    animationEasing: 'cubicOut',
    animationEasingUpdate: 'cubicOut',
    tooltip: {
      trigger: 'item',
      confine: true
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
      itemWidth: 12,
      itemHeight: 12,
      textStyle: {
        color: '#666',
        fontSize: 13
      },
      width: 130
    },
    series: [
      {
        name: '使用占比',
        type: 'pie',
        radius: ['40%', '62%'],
        center: ['30%', '50%'],
        avoidLabelOverlap: true,
        label: {
          show: true,
          formatter: '{d}%',
          fontSize: 12,
          color: '#666'
        },
        labelLine: {
          show: true,
          length: 10,
          length2: 8
        },
        data: [
          {
            value: 138,
            name: '文档智能操作交互',
            itemStyle: { color: '#d5b076' }
          },
          {
            value: 131,
            name: '非结构化文档信息提取',
            itemStyle: { color: '#5b8ff9' }
          },
          {
            value: 100,
            name: '表格自定义数据填写',
            itemStyle: { color: '#61d9a5' }
          }
        ]
      }
    ]
  })
}

const initBarChart = () => {
  if (!barChartRef.value) return
  barChart = echarts.init(barChartRef.value)

  barChart.setOption({
    animationDuration: 400,
    animationDurationUpdate: 250,
    animationEasing: 'cubicOut',
    animationEasingUpdate: 'cubicOut',
    tooltip: {
      trigger: 'axis',
      confine: true
    },
    grid: {
      left: '6%',
      right: '6%',
      bottom: '12%',
      top: 40,
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: [
        '文档智能操作交互',
        '非结构化文档信息提取',
        '表格自定义数据填写'
      ],
      axisLabel: {
        color: '#666',
        interval: 0,
        rotate: 12
      },
      axisLine: {
        lineStyle: {
          color: '#ddd'
        }
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: '#666'
      },
      splitLine: {
        lineStyle: {
          color: '#eee'
        }
      }
    },
    series: [
      {
        type: 'bar',
        barWidth: 42,
        data: [
          {
            value: 31,
            itemStyle: { color: '#d5b076', borderRadius: [8, 8, 0, 0] }
          },
          {
            value: 22,
            itemStyle: { color: '#5b8ff9', borderRadius: [8, 8, 0, 0] }
          },
          {
            value: 26,
            itemStyle: { color: '#61d9a5', borderRadius: [8, 8, 0, 0] }
          }
        ]
      }
    ]
  })
}

const initActiveChart = () => {
  if (!activeChartRef.value) return
  activeChart = echarts.init(activeChartRef.value)

  activeChart.setOption({
    animationDuration: 400,
    animationDurationUpdate: 250,
    animationEasing: 'cubicOut',
    animationEasingUpdate: 'cubicOut',
    tooltip: {
      trigger: 'axis',
      confine: true
    },
    legend: {
      top: 10,
      left: 'center',
      textStyle: {
        color: '#666'
      }
    },
    grid: {
      left: '4%',
      right: '6%',
      bottom: '6%',
      top: 60,
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: ['3-20', '03-21', '03-22', '03-23', '03-24', '03-25', '03-26'],
      axisLabel: {
        color: '#666'
      },
      axisLine: {
        lineStyle: {
          color: '#ddd'
        }
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: '#666'
      },
      splitLine: {
        lineStyle: {
          color: '#eee'
        }
      }
    },
    series: [
      {
        name: '整体活跃用户数',
        type: 'line',
        smooth: 0.35,
        symbol: 'circle',
        symbolSize: 8,
        clip: true,
        data: [19, 20, 21, 21, 23, 17, 28],
        lineStyle: {
          width: 3,
          color: '#ff8a65'
        },
        itemStyle: {
          color: '#ff8a65'
        },
        areaStyle: {
          color: 'rgba(255, 138, 101, 0.12)'
        }
      }
    ]
  })
}

const initResizeObserver = () => {
  const resizeHandler = () => {
    safeResizeCharts()
  }

  if (window.ResizeObserver) {
    if (mainContentRef.value) {
      mainResizeObserver = new ResizeObserver(() => {
        resizeHandler()
      })
      mainResizeObserver.observe(mainContentRef.value)
    }

    if (trendChartRef.value) {
      trendResizeObserver = new ResizeObserver(() => {
        resizeHandler()
      })
      trendResizeObserver.observe(trendChartRef.value)
    }
  } else {
    window.addEventListener('resize', resizeHandler)
  }
}

const destroyResizeObserver = () => {
  mainResizeObserver?.disconnect()
  trendResizeObserver?.disconnect()
  mainResizeObserver = null
  trendResizeObserver = null
}

onMounted(async () => {
  await nextTick()
  initTrendChart()
  initPieChart()
  initBarChart()
  initActiveChart()
  initResizeObserver()
  safeResizeCharts()
})

onBeforeUnmount(() => {
  destroyResizeObserver()
  window.removeEventListener('resize', safeResizeCharts)

  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId)
    animationFrameId = null
  }

  trendChart?.dispose()
  pieChart?.dispose()
  barChart?.dispose()
  activeChart?.dispose()
})
</script>

<style scoped>
.admin-page {
  min-height: 100vh;
  background: #ececec;
}

.container {
  width: 1440px;
  max-width: calc(100% - 40px);
  margin: 0 auto;
}

.admin-layout {
  display: flex;
  gap: 24px;
  padding: 24px 0 40px;
  align-items: flex-start;
}

/* 左侧导航 */
.sidebar {
  width: 240px;
  min-height: calc(100vh - 120px);
  background: #f8f8f8;
  border-radius: 20px;
  padding: 20px 18px;
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.05);
  flex-shrink: 0;
  transition: width 0.32s ease, padding 0.32s ease;
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

/* 主体区域 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-width: 0;
  transition: all 0.32s ease;
}

.card {
  background: #f8f8f8;
  border-radius: 20px;
  padding: 28px;
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.overview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
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

.date-tip {
  font-size: 14px;
  color: #8a611d;
  background: rgba(213, 176, 118, 0.12);
  padding: 10px 14px;
  border-radius: 12px;
}

/* 顶部统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 20px;
}

.stat-card {
  background: linear-gradient(135deg, #fffaf2, #ffffff);
}

.stat-label {
  font-size: 14px;
  color: #888;
  margin-bottom: 12px;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #2d2d2d;
}

.stat-trend {
  margin-top: 12px;
  font-size: 14px;
  font-weight: 600;
}

.stat-trend.up {
  color: #2e7d32;
}

.stat-trend.down {
  color: #c62828;
}

/* 图表布局 */
.chart-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 24px;
}

.chart-card.large {
  grid-column: span 2;
}

.card-title {
  font-size: 18px;
  font-weight: 700;
  color: #2d2d2d;
  margin-bottom: 18px;
}

.chart-box {
  width: 100%;
  height: 360px;
  overflow: hidden;
}

.trend-chart-box {
  will-change: width;
  transform: translateZ(0);
}

.pie-chart-box {
  height: 400px;
}

/* 表格 */
.table-card {
  padding-top: 24px;
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

.data-table {
  width: 100%;
  min-width: 980px;
  border-collapse: separate;
  border-spacing: 0;
  background: #fff;
  border-radius: 18px;
  overflow: hidden;
}

.data-table thead th {
  text-align: left;
  padding: 18px 20px;
  background: #f5efe5;
  color: #9c6a1f;
  font-size: 15px;
  font-weight: 700;
  border-bottom: 1px solid #ead8b9;
  white-space: nowrap;
}

.data-table tbody td {
  padding: 18px 20px;
  font-size: 14px;
  color: #444;
  border-bottom: 1px solid #f1f1f1;
  vertical-align: middle;
  word-break: break-word;
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

.status-badge.active {
  background: rgba(76, 175, 80, 0.12);
  color: #2e7d32;
}

.status-badge.stable {
  background: rgba(33, 150, 243, 0.12);
  color: #1565c0;
}

.status-badge.warning {
  background: rgba(255, 152, 0, 0.14);
  color: #ef6c00;
}

/* 响应式 */
@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
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

  .chart-grid {
    grid-template-columns: 1fr;
  }

  .chart-card.large {
    grid-column: span 1;
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

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .chart-box,
  .pie-chart-box {
    height: 300px;
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
