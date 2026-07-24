<template>
  <div class="overview-view">
    <header class="page-heading">
      <div><div class="eyebrow">QUINTAI WORKSPACE</div><h1>工作台概览</h1><p>集中管理文档、复核任务和自动化流程。</p></div>
      <RouterLink to="/workspace/documents" class="primary-btn">＋ 导入文档</RouterLink>
    </header>

    <div v-if="loading" class="state-card">正在加载工作台数据...</div>
    <template v-else>
      <section class="metric-grid">
        <article v-for="metric in metrics" :key="metric.label" class="metric-card">
          <div class="metric-icon">{{ metric.icon }}</div>
          <div><div class="metric-value">{{ metric.value }}</div><div class="metric-label">{{ metric.label }}</div></div>
          <div class="metric-hint">{{ metric.hint }}</div>
        </article>
      </section>

      <section class="content-grid">
        <article class="panel recent-panel">
          <div class="panel-head"><div><h2>最近文档</h2><p>追踪刚刚进入系统的材料</p></div><RouterLink to="/workspace/documents">查看全部 →</RouterLink></div>
          <div v-if="overview.recent_documents?.length" class="document-list">
            <div v-for="item in overview.recent_documents" :key="item.id" class="document-row">
              <div class="file-mark">{{ item.file_type?.toUpperCase() }}</div>
              <div class="file-info"><strong>{{ item.filename }}</strong><span>{{ item.category }} · {{ formatSize(item.size_bytes) }}</span></div>
              <span class="status" :class="item.status">{{ statusText[item.status] || item.status }}</span>
            </div>
          </div>
          <div v-else class="empty"><span>还没有入库文档</span><RouterLink to="/workspace/documents">导入第一批材料</RouterLink></div>
        </article>

        <article class="panel action-panel">
          <div class="panel-head"><div><h2>快速开始</h2><p>继续使用现有智能能力</p></div></div>
          <RouterLink v-for="action in actions" :key="action.to" :to="action.to" class="action-row">
            <span class="action-symbol">{{ action.icon }}</span><span><strong>{{ action.title }}</strong><small>{{ action.desc }}</small></span><b>›</b>
          </RouterLink>
        </article>
      </section>

      <section class="flow-panel">
        <div class="panel-head"><div><h2>标准处理链路</h2><p>从材料进入到业务交付，每一步都有状态和记录</p></div><RouterLink to="/workspace/workflows">配置工作流 →</RouterLink></div>
        <div class="flow-line">
          <template v-for="(step, index) in flow" :key="step.title">
            <div class="flow-step"><span>{{ index + 1 }}</span><strong>{{ step.title }}</strong><small>{{ step.desc }}</small></div>
            <div v-if="index < flow.length - 1" class="flow-arrow">→</div>
          </template>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { getWorkspaceOverview } from '../../api/workspace'

const loading = ref(true)
const overview = ref({})
const statusText = { ready: '待处理', processing: '处理中', needs_review: '待复核', completed: '已完成', archived: '已归档' }
const actions = [
  { icon: '⌁', title: '提取文档信息', desc: '将非结构化内容转换为字段', to: '/feature/doc-extract' },
  { icon: '▦', title: '填写复杂表格', desc: '根据多份材料完成业务表格', to: '/feature/table-fill' },
  { icon: '✦', title: '编辑文档内容', desc: '通过自然语言调整 Word 文档', to: '/feature/doc-chat' }
]
const flow = [
  { title: '接收', desc: '文档入库' }, { title: '理解', desc: '分类与提取' }, { title: '校验', desc: '规则检查' },
  { title: '复核', desc: '人工确认' }, { title: '交付', desc: '导出与回写' }
]
const metrics = computed(() => [
  { label: '文档总量', value: overview.value.documents_total || 0, hint: '工作空间内全部材料', icon: '▤' },
  { label: '待复核', value: overview.value.pending_reviews || 0, hint: '需要人工确认的任务', icon: '✓' },
  { label: '运行中任务', value: overview.value.active_tasks || 0, hint: '正在执行的智能处理', icon: '↻' },
  { label: '启用工作流', value: overview.value.active_workflows || 0, hint: '已发布的自动化流程', icon: '⌘' }
])
const formatSize = (size = 0) => size < 1024 * 1024 ? `${Math.max(1, Math.round(size / 1024))} KB` : `${(size / 1024 / 1024).toFixed(1)} MB`
onMounted(async () => { try { overview.value = await getWorkspaceOverview() } catch (error) { console.error(error) } finally { loading.value = false } })
</script>

<style scoped>
.overview-view { display: grid; gap: 22px; }
.page-heading { background: linear-gradient(135deg,#f9f7f2,#f5ede0); border: 1px solid #e4d6c0; border-radius: 18px; padding: 28px 30px; display:flex; justify-content:space-between; align-items:center; box-shadow:0 10px 28px rgba(0,0,0,.035); }
.eyebrow { font: 700 11px/1.2 system-ui,sans-serif; letter-spacing:1.8px; color:#b78a49; }
h1 { margin:7px 0 5px; font-size:28px; color:#292929; } .page-heading p,.panel-head p { margin:0;color:#8e877e;font-size:14px; }
.primary-btn { height:42px;padding:0 20px;border-radius:21px;background:#d5b076;color:white;display:flex;align-items:center;font-size:14px;box-shadow:0 7px 16px rgba(190,143,73,.18); }
.metric-grid { display:grid;grid-template-columns:repeat(4,1fr);gap:16px; }
.metric-card,.panel,.flow-panel,.state-card { background:#f8f8f8;border:1px solid #e5e2dd;border-radius:16px;box-shadow:0 8px 24px rgba(0,0,0,.035); }
.metric-card { padding:21px;display:grid;grid-template-columns:42px 1fr;gap:12px;align-items:center; }
.metric-icon { width:42px;height:42px;border-radius:12px;background:#f2e8d8;color:#b37d31;display:grid;place-items:center;font:20px system-ui; }
.metric-value { font:700 27px system-ui;color:#292929; }.metric-label{font-size:14px;color:#615d57;margin-top:2px}.metric-hint{grid-column:1/-1;color:#aaa39a;font-size:12px;padding-top:9px;border-top:1px solid #ece8e2}
.content-grid{display:grid;grid-template-columns:minmax(0,1.6fr) minmax(300px,.8fr);gap:18px}.panel,.flow-panel{padding:23px}.panel-head{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:18px}.panel-head h2{font-size:19px;margin:0 0 5px}.panel-head a{font-size:13px;color:#b17d36}
.document-list{display:grid}.document-row{display:flex;align-items:center;gap:13px;padding:14px 0;border-top:1px solid #ece9e4}.file-mark{width:45px;height:45px;border-radius:10px;background:#eee8df;display:grid;place-items:center;color:#98713b;font:700 10px system-ui}.file-info{min-width:0;flex:1;display:grid;gap:5px}.file-info strong{font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.file-info span{font-size:12px;color:#9d968d}.status{font-size:12px;padding:5px 10px;border-radius:12px;background:#eee;color:#777}.status.needs_review{background:#fff0d8;color:#aa6f1e}.status.completed{background:#e5f4eb;color:#48805b}.status.processing{background:#e7effa;color:#547aa8}
.action-row{min-height:65px;display:grid;grid-template-columns:38px 1fr auto;align-items:center;gap:12px;border-top:1px solid #ece9e4;color:#444}.action-symbol{width:34px;height:34px;border-radius:9px;background:#f2e8d8;color:#a87836;display:grid;place-items:center}.action-row span:nth-child(2){display:grid;gap:4px}.action-row strong{font-size:14px}.action-row small{color:#9b948b}.action-row b{font:22px system-ui;color:#c7b79f}.empty{min-height:180px;border:1px dashed #dcd5ca;border-radius:12px;display:grid;place-content:center;text-align:center;gap:12px;color:#999}.empty a{color:#b27e37}.flow-line{display:flex;align-items:center;justify-content:space-between}.flow-step{flex:1;min-width:100px;border:1px solid #e7e0d5;border-radius:12px;background:#fff;padding:15px;display:grid;grid-template-columns:27px 1fr;gap:3px 9px}.flow-step span{grid-row:1/3;width:27px;height:27px;border-radius:50%;background:#d5b076;color:#fff;display:grid;place-items:center;font:12px system-ui}.flow-step strong{font-size:14px}.flow-step small{color:#9c958c}.flow-arrow{padding:0 9px;color:#c6af8d}.state-card{min-height:240px;display:grid;place-items:center;color:#999}
@media(max-width:1100px){.metric-grid{grid-template-columns:repeat(2,1fr)}.content-grid{grid-template-columns:1fr}.flow-line{overflow:auto;justify-content:flex-start}.flow-step{min-width:150px}}
@media(max-width:600px){.page-heading{align-items:flex-start;gap:18px;flex-direction:column}.metric-grid{grid-template-columns:1fr}}
</style>
