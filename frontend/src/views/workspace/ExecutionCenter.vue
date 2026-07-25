<template>
  <div class="execution-view">
    <header class="hero"><div><span>AI EXECUTION COCKPIT</span><h1>AI 执行驾驶舱</h1><p>进度来自真实处理节点，完整保留证据、校验和修复过程。</p></div><button @click="load">刷新任务</button></header>
    <section class="metrics"><article v-for="item in metrics" :key="item.label"><b>{{ item.value }}</b><span>{{ item.label }}</span></article></section>
    <section class="cockpit">
      <aside>
        <div class="aside-head"><strong>最近任务</strong><small>{{ tasks.length }} 条</small></div>
        <button v-for="item in tasks" :key="item.id" :class="{active:selected?.id===item.id}" @click="select(item)">
          <i :class="item.status"></i><span><b>{{ kindNames[item.kind] || item.kind }}</b><small>{{ item.stage }}</small></span><em>{{ item.progress }}%</em>
        </button>
        <div v-if="!tasks.length" class="empty">还没有执行记录</div>
      </aside>
      <main v-if="selected">
        <div class="task-head"><div><small>{{ selected.id }}</small><h2>{{ kindNames[selected.kind] || selected.kind }}</h2><p>{{ selected.stage }}</p></div><div class="task-actions"><button v-if="canCancel" @click="cancel">取消</button><button v-if="canRetry" @click="retry">重新执行</button><button v-if="selected.has_file && selected.status==='succeeded'" class="primary" @click="download">下载结果</button></div></div>
        <div class="real-progress"><div><span>真实节点进度</span><b>{{ selected.completed_steps || 0 }} / {{ selected.total_steps || 1 }}</b></div><i><em :style="{width:`${selected.progress}%`}"></em></i><small>仅在处理节点实际完成后推进，不按等待时间模拟。</small></div>
        <div class="detail-grid">
          <section class="timeline"><div class="section-head"><h3>执行时间线</h3><span>{{ selected.events?.length || 0 }} 个事件</span></div><div v-for="event in selected.events" :key="event.id" class="event" :class="event.status"><i></i><div><b>{{ event.label }}</b><small>{{ event.node_code }}<template v-if="event.duration_ms"> · {{ duration(event.duration_ms) }}</template></small></div><em>{{ eventText[event.status] || event.status }}</em></div><p v-if="!selected.events?.length" class="empty">等待任务进程接收</p></section>
          <section class="quality"><div class="section-head"><h3>质量报告</h3><span>{{ qualityStatus }}</span></div><div class="quality-grid"><article v-for="item in qualityMetrics" :key="item.label"><b>{{ item.value }}</b><small>{{ item.label }}</small></article></div><p class="summary">{{ quality.verification_summary || qualitySummary }}</p><div class="evidence-list"><div class="section-head"><h3>证据摘要</h3><span>{{ evidenceItems.length }} 条</span></div><article v-for="(item,index) in evidenceItems.slice(0,8)" :key="item.evidence_id || item.chunk_id || index"><b>{{ item.field || item.filename || `证据 ${index+1}` }}</b><p>{{ evidenceText(item) }}</p><small>{{ evidenceLocation(item) }}</small></article><p v-if="!evidenceItems.length" class="empty">当前任务暂无证据摘要</p></div></section>
        </div>
      </main>
      <main v-else class="main-empty"><span>⌁</span><b>选择一条任务查看真实执行过程</b></main>
    </section>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { cancelTask, downloadTask, getTask, getTasks, retryTask } from '../../api/tasks'

const tasks=ref([]),selected=ref(null),timer=ref(null)
const route=useRoute()
const kindNames={document_edit:'文档智能编辑',document_extract:'文档信息提取',table_fill:'多文档复杂填表'}
const eventText={running:'执行中',completed:'已完成',failed:'失败',skipped:'跳过'}
const activeStatuses=new Set(['queued','running','retrying'])
const metrics=computed(()=>[
  {label:'执行中',value:tasks.value.filter(i=>activeStatuses.has(i.status)).length},
  {label:'已完成',value:tasks.value.filter(i=>i.status==='succeeded').length},
  {label:'需关注',value:tasks.value.filter(i=>i.status==='failed').length},
  {label:'平均进度',value:`${tasks.value.length?Math.round(tasks.value.reduce((s,i)=>s+i.progress,0)/tasks.value.length):0}%`}
])
const quality=computed(()=>selected.value?.quality_report||{}),evidenceItems=computed(()=>selected.value?.evidence_summary?.items||[])
const qualityMetrics=computed(()=>[
  {label:'完整率',value:percent(quality.value.completeness)},
  {label:'证据覆盖',value:percent(quality.value.evidence_coverage)},
  {label:'平均置信度',value:percent(quality.value.average_confidence)},
  {label:'校验异常',value:quality.value.checks_failed??quality.value.errors??0}
])
const qualityStatus=computed(()=>quality.value.requires_review?'建议复核':selected.value?.status==='succeeded'?'检查通过':'等待结果')
const qualitySummary=computed(()=>quality.value.kind?'质量指标由本次真实执行结果计算。':'任务完成后将自动生成质量报告。')
const canCancel=computed(()=>selected.value&&activeStatuses.has(selected.value.status)),canRetry=computed(()=>selected.value&&['failed','cancelled'].includes(selected.value.status))
const percent=value=>value===undefined||value===null?'-':`${Math.round(Number(value)*100)}%`
const duration=ms=>ms<1000?`${ms} ms`:`${(ms/1000).toFixed(1)} s`
const evidenceText=item=>item.snippet||item.evidence||item.content?.text||JSON.stringify(item.content||'')
const evidenceLocation=item=>{const loc=item.citation||item.location||{};return [item.source_page?`第 ${item.source_page} 页`:'',loc.filename||'',loc.sheet?`${loc.sheet} 表`:'',loc.row_index!==undefined?`第 ${loc.row_index+1} 行`:''].filter(Boolean).join(' · ')||'来源位置已记录'}
const load=async()=>{const data=await getTasks({limit:50});tasks.value=data.items;if(selected.value){const match=tasks.value.find(i=>i.id===selected.value.id);if(match)await select(match)}else if(tasks.value.length){const requested=tasks.value.find(i=>i.id===route.query.task);await select(requested||tasks.value[0])}}
const select=async item=>{selected.value=await getTask(item.id)}
const refreshActive=async()=>{if(selected.value&&activeStatuses.has(selected.value.status)){selected.value=await getTask(selected.value.id);const index=tasks.value.findIndex(i=>i.id===selected.value.id);if(index>=0)tasks.value[index]=selected.value}}
const cancel=async()=>{if(confirm('确定取消当前任务吗？'))selected.value=await cancelTask(selected.value.id)}
const retry=async()=>{selected.value=await retryTask(selected.value.id)}
const download=async()=>{const blob=await downloadTask(selected.value.id),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=selected.value.filename||'result';a.click();URL.revokeObjectURL(url)}
onMounted(async()=>{try{await load()}catch(e){alert(e.message)}timer.value=window.setInterval(()=>refreshActive().catch(()=>{}),1500)})
onBeforeUnmount(()=>window.clearInterval(timer.value))
</script>

<style scoped>
.execution-view{display:grid;gap:18px;color:#37332e}.hero,.metrics article,.cockpit{background:#f8f8f8;border:1px solid #e4e0d9;border-radius:17px;box-shadow:0 8px 24px rgba(0,0,0,.035)}.hero{padding:27px 30px;display:flex;justify-content:space-between;align-items:center;background:linear-gradient(135deg,#faf7f1,#f4eadb);border-color:#e4d5be}.hero span{font:700 11px system-ui;letter-spacing:1.6px;color:#b18140}.hero h1{font-size:28px;margin:7px 0 5px}.hero p{margin:0;color:#918a81;font-size:13px}.hero button,.task-actions button{border:0;border-radius:19px;padding:10px 16px;background:#ece6dd;color:#6b6259;cursor:pointer}.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.metrics article{padding:17px 20px;display:flex;align-items:baseline;gap:9px}.metrics b{font:700 23px system-ui}.metrics span{color:#999;font-size:12px}.cockpit{min-height:680px;display:grid;grid-template-columns:310px minmax(0,1fr);overflow:hidden}.cockpit>aside{background:#f3f0eb;border-right:1px solid #e2ddd5}.aside-head,.section-head{display:flex;justify-content:space-between;align-items:center}.aside-head{padding:18px}.aside-head small,.section-head span{color:#999;font-size:11px}.cockpit>aside>button{width:100%;border:0;border-top:1px solid #e3ded7;background:transparent;padding:15px;display:grid;grid-template-columns:8px 1fr auto;gap:11px;text-align:left;align-items:start;cursor:pointer}.cockpit>aside>button.active{background:#fff;box-shadow:inset 3px 0 #cfa766}.cockpit>aside i{width:8px;height:8px;border-radius:50%;background:#aaa;margin-top:5px}.cockpit>aside i.running,.cockpit>aside i.retrying{background:#d29b45;box-shadow:0 0 0 4px #f1e1c8}.cockpit>aside i.succeeded{background:#58a370}.cockpit>aside i.failed{background:#cc6d60}.cockpit>aside span{min-width:0;display:grid;gap:5px}.cockpit>aside b,.cockpit>aside small{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.cockpit>aside b{font-size:13px}.cockpit>aside small{color:#999}.cockpit>aside em{font:11px system-ui;color:#99713c}.cockpit>main{padding:24px;min-width:0}.task-head{display:flex;justify-content:space-between;border-bottom:1px solid #ebe7e1;padding-bottom:17px}.task-head small{color:#aaa;font:10px system-ui}.task-head h2{margin:5px 0;font-size:21px}.task-head p{margin:0;color:#8f877f;font-size:13px}.task-actions{display:flex;gap:7px}.task-actions .primary{background:#d2aa6e;color:#fff}.real-progress{margin:18px 0;padding:16px;background:#f6f1e9;border-radius:11px}.real-progress>div{display:flex;justify-content:space-between;font-size:12px}.real-progress>i{display:block;height:8px;background:#e5ddd2;border-radius:5px;margin:10px 0;overflow:hidden}.real-progress>i em{display:block;height:100%;background:linear-gradient(90deg,#c99b56,#e0bf8b);transition:width .3s}.real-progress small{color:#999}.detail-grid{display:grid;grid-template-columns:1.1fr .9fr;gap:17px}.timeline,.quality{border:1px solid #e7e2dc;border-radius:13px;padding:17px;background:#fdfdfd}.section-head h3{font-size:16px;margin:0}.event{display:grid;grid-template-columns:12px 1fr auto;gap:9px;padding:13px 0;border-top:1px solid #eee9e3;align-items:start}.event>i{width:9px;height:9px;margin-top:4px;border-radius:50%;background:#c6beb4}.event.running>i{background:#d39e4d;box-shadow:0 0 0 4px #f5e8d3}.event.completed>i{background:#63a77a}.event.failed>i{background:#cf7063}.event>div{display:grid;gap:4px}.event b{font-size:12px}.event small,.event>em{font:10px system-ui;color:#aaa}.quality-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:14px 0}.quality-grid article{background:#f4efe7;border-radius:9px;padding:12px;display:grid}.quality-grid b{font:700 19px system-ui}.quality-grid small{color:#999}.summary{font-size:12px;color:#777;line-height:1.7}.evidence-list{margin-top:18px}.evidence-list article{padding:11px 0;border-top:1px solid #eee9e3}.evidence-list article b{font-size:12px}.evidence-list article p{font-size:11px;line-height:1.55;color:#746e67;margin:5px 0}.evidence-list article small{color:#aa8a5d;font-size:10px}.empty,.main-empty{color:#aaa;text-align:center;padding:35px}.main-empty{display:grid;place-content:center;gap:8px}.main-empty span{font-size:40px}@media(max-width:1050px){.detail-grid{grid-template-columns:1fr}}@media(max-width:760px){.metrics{grid-template-columns:1fr 1fr}.cockpit{grid-template-columns:1fr}.cockpit>aside{max-height:260px;overflow:auto;border-right:0}.hero{align-items:flex-start;gap:15px;flex-direction:column}.task-head{gap:15px;flex-direction:column}}
</style>
