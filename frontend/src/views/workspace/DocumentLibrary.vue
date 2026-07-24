<template>
  <div class="library-view">
    <header class="page-heading">
      <div><div class="eyebrow">DOCUMENT LIBRARY</div><h1>文档库</h1><p>统一保存、分类和追踪进入 QuintAI 的业务材料。</p></div>
      <button class="primary-btn" @click="showUploader = true">＋ 导入文档</button>
    </header>

    <section class="toolbar">
      <div class="search-box"><span>⌕</span><input v-model.trim="filters.keyword" placeholder="搜索文件名或文档内容" @keyup.enter="loadDocuments" /></div>
      <select v-model="filters.status" @change="loadDocuments"><option value="">全部状态</option><option v-for="(label,key) in statusText" :key="key" :value="key">{{ label }}</option></select>
      <button class="secondary-btn" @click="loadDocuments">查询</button>
      <span class="total">共 {{ total }} 份文档</span>
    </section>

    <section class="table-card">
      <div v-if="loading" class="empty">正在加载文档...</div>
      <div v-else-if="!documents.length" class="empty"><div class="empty-icon">▤</div><strong>文档库还是空的</strong><span>导入材料后，即可在这里统一管理和追踪。</span><button class="text-btn" @click="showUploader = true">立即导入</button></div>
      <div v-else class="document-table">
        <div class="table-head"><span>文件</span><span>分类与标签</span><span>状态</span><span>导入时间</span><span>操作</span></div>
        <div v-for="item in documents" :key="item.id" class="table-row">
          <div class="file-cell"><div class="file-mark">{{ item.file_type?.toUpperCase() }}</div><div><strong :title="item.filename">{{ item.filename }}</strong><small>{{ formatSize(item.size_bytes) }} · {{ sourceText[item.source] || item.source }}</small></div></div>
          <div class="tag-cell"><span class="category">{{ item.category }}</span><small v-if="item.tags?.length">{{ item.tags.join('、') }}</small></div>
          <div><span class="status" :class="item.status">{{ statusText[item.status] || item.status }}</span></div>
          <div class="date-cell">{{ formatDate(item.created_at) }}</div>
          <div class="actions"><button v-if="canProcess(item) && item.status !== 'archived'" @click="openRunner(item)">运行流程</button><button @click="download(item)">下载</button><button v-if="item.status !== 'archived'" @click="archive(item)">归档</button><button class="danger" @click="remove(item)">删除</button></div>
        </div>
      </div>
    </section>

    <div v-if="showUploader" class="modal-mask" @click.self="showUploader = false">
      <div class="modal-card">
        <div class="modal-head"><div><h2>导入业务文档</h2><p>支持 Word、Excel、PDF、文本和 CSV，单次最多 10 个文件。</p></div><button @click="showUploader=false">×</button></div>
        <label class="drop-zone" :class="{ active: uploadFiles.length }">
          <input type="file" multiple accept=".docx,.xlsx,.xls,.pdf,.txt,.md,.csv" @change="selectFiles" />
          <span class="upload-icon">⇧</span><strong>{{ uploadFiles.length ? `已选择 ${uploadFiles.length} 个文件` : '点击选择或拖入文档' }}</strong><small>每个文件不超过 25 MB</small>
        </label>
        <div v-if="uploadFiles.length" class="selected-files"><span v-for="file in uploadFiles" :key="file.name">{{ file.name }}</span></div>
        <div class="form-grid"><label><span>业务分类</span><input v-model="uploadForm.category" placeholder="例如：采购合同" /></label><label><span>标签</span><input v-model="uploadForm.tags" placeholder="多个标签用逗号分隔" /></label></div>
        <div class="modal-actions"><button class="secondary-btn" @click="showUploader=false">取消</button><button class="primary-btn" :disabled="!uploadFiles.length || uploading" @click="submitUpload">{{ uploading ? '正在导入...' : '确认导入' }}</button></div>
      </div>
    </div>
    <div v-if="showRunner" class="modal-mask" @click.self="showRunner = false">
      <div class="modal-card runner-card">
        <div class="modal-head"><div><h2>运行工作流</h2><p>选择一个已启用的流程处理“{{ selectedDocument?.filename }}”。</p></div><button @click="showRunner=false">×</button></div>
        <label class="runner-select"><span>工作流</span><select v-model="selectedWorkflowId"><option value="">请选择工作流</option><option v-for="item in activeWorkflows" :key="item.id" :value="item.id">{{ item.name }}</option></select></label>
        <div v-if="!activeWorkflows.length" class="runner-empty">还没有可运行的工作流，请先在工作流页面配置提取字段并启用流程。</div>
        <div class="modal-actions"><button class="secondary-btn" @click="showRunner=false">取消</button><button class="primary-btn" :disabled="!selectedWorkflowId || running" @click="submitRun">{{ running ? '正在启动...' : '启动处理' }}</button></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { deleteDocument, downloadDocument, getDocuments, getWorkflows, runWorkflow, updateDocument, uploadDocuments } from '../../api/workspace'

const documents=ref([]), total=ref(0), loading=ref(true), showUploader=ref(false), uploading=ref(false), uploadFiles=ref([])
const showRunner=ref(false), running=ref(false), activeWorkflows=ref([]), selectedDocument=ref(null), selectedWorkflowId=ref('')
const filters=reactive({keyword:'',status:''}), uploadForm=reactive({category:'未分类',tags:''})
const statusText={ready:'待处理',processing:'处理中',needs_review:'待复核',completed:'已完成',archived:'已归档'}
const sourceText={upload:'手动导入',extraction:'信息提取'}
const loadDocuments=async()=>{loading.value=true;try{const data=await getDocuments(filters);documents.value=data.items;total.value=data.total}catch(e){alert(e.message)}finally{loading.value=false}}
const selectFiles=(event)=>{uploadFiles.value=Array.from(event.target.files||[]).slice(0,10)}
const submitUpload=async()=>{if(!uploadFiles.value.length)return;uploading.value=true;try{const body=new FormData();uploadFiles.value.forEach(file=>body.append('files',file));body.append('category',uploadForm.category);body.append('tags',uploadForm.tags);await uploadDocuments(body);showUploader.value=false;uploadFiles.value=[];await loadDocuments()}catch(e){alert(e.message)}finally{uploading.value=false}}
const archive=async(item)=>{await updateDocument(item.id,{status:'archived'});await loadDocuments()}
const remove=async(item)=>{if(!confirm(`确定删除“${item.filename}”吗？删除后无法恢复。`))return;try{await deleteDocument(item.id);await loadDocuments()}catch(e){alert(e.message)}}
const download=async(item)=>{try{const response=await downloadDocument(item.id);const url=URL.createObjectURL(response.data);const link=document.createElement('a');link.href=url;link.download=item.filename;link.click();URL.revokeObjectURL(url)}catch(e){alert(e.message)}}
const canProcess=(item)=>['docx','xlsx','txt','md'].includes(item.file_type)
const openRunner=async(item)=>{selectedDocument.value=item;selectedWorkflowId.value='';showRunner.value=true;try{activeWorkflows.value=(await getWorkflows()).items.filter(workflow=>workflow.status==='active')}catch(e){alert(e.message)}}
const submitRun=async()=>{if(!selectedDocument.value||!selectedWorkflowId.value)return;running.value=true;try{await runWorkflow(selectedWorkflowId.value,selectedDocument.value.id);showRunner.value=false;await loadDocuments();alert('工作流已启动，可在任务状态和复核中心查看进度')}catch(e){alert(e.message)}finally{running.value=false}}
const formatSize=(size=0)=>size<1048576?`${Math.max(1,Math.round(size/1024))} KB`:`${(size/1048576).toFixed(1)} MB`
const formatDate=(value)=>value?new Date(value).toLocaleString('zh-CN',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'}):'-'
onMounted(loadDocuments)
</script>

<style scoped>
.library-view{display:grid;gap:18px}.page-heading,.toolbar,.table-card{background:#f8f8f8;border:1px solid #e4e1dc;border-radius:17px;box-shadow:0 8px 24px rgba(0,0,0,.035)}.page-heading{padding:27px 30px;display:flex;justify-content:space-between;align-items:center;background:linear-gradient(135deg,#f9f7f2,#f5ede0);border-color:#e4d6c0}.eyebrow{font:700 11px system-ui;letter-spacing:1.7px;color:#b78a49}h1{font-size:28px;margin:7px 0 5px}.page-heading p,.modal-head p{margin:0;color:#918a81;font-size:14px}.primary-btn,.secondary-btn{height:42px;padding:0 20px;border:0;border-radius:21px;cursor:pointer;font-family:inherit}.primary-btn{background:#d5b076;color:#fff}.primary-btn:disabled{opacity:.55;cursor:not-allowed}.secondary-btn{background:#eee9e2;color:#5f5952}.toolbar{padding:14px 17px;display:flex;align-items:center;gap:12px}.search-box{flex:1;height:40px;border:1px solid #ddd8d0;border-radius:10px;background:#fff;display:flex;align-items:center;padding:0 12px;gap:8px}.search-box span{font:22px system-ui;color:#aaa}.search-box input{flex:1;border:0;outline:0;font-size:14px;background:transparent}.toolbar select{height:40px;border:1px solid #ddd8d0;background:#fff;border-radius:10px;padding:0 12px;color:#666}.total{font-size:13px;color:#999;margin-left:auto}.table-card{overflow:hidden}.document-table{min-width:900px}.table-head,.table-row{display:grid;grid-template-columns:minmax(250px,1.5fr) minmax(150px,.8fr) 100px 130px 225px;align-items:center;gap:16px;padding:0 20px}.table-head{height:48px;background:#f3f0eb;color:#8e877e;font-size:12px}.table-row{min-height:76px;background:#fff;border-top:1px solid #ece9e4}.file-cell{min-width:0;display:flex;align-items:center;gap:11px}.file-cell>div:last-child{min-width:0;display:grid;gap:5px}.file-cell strong{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:14px}.file-cell small,.tag-cell small{color:#a29b92;font-size:12px}.file-mark{flex:0 0 42px;height:42px;border-radius:10px;background:#f0e8dc;color:#a77634;display:grid;place-items:center;font:700 10px system-ui}.tag-cell{display:grid;justify-items:start;gap:6px}.category{font-size:13px;color:#625c55}.status{font-size:12px;padding:5px 10px;border-radius:12px;background:#eee;color:#777}.status.needs_review{background:#fff0d8;color:#a86b18}.status.completed{background:#e5f4eb;color:#48805b}.status.processing{background:#e7effa;color:#547aa8}.status.archived{background:#eee;color:#888}.date-cell{font-size:13px;color:#7d766e}.actions{display:flex;gap:10px}.actions button,.text-btn{border:0;background:none;color:#a87836;cursor:pointer;font-family:inherit;padding:0}.actions .danger{color:#c76e66}.empty{min-height:360px;display:grid;place-content:center;justify-items:center;gap:9px;color:#a19a91}.empty strong{color:#57524d}.empty-icon{font:36px system-ui;color:#caaa79}.modal-mask{position:fixed;inset:0;background:rgba(30,27,23,.45);z-index:200;display:grid;place-items:center;padding:20px}.modal-card{width:620px;max-width:100%;max-height:90vh;overflow:auto;background:#fafafa;border-radius:20px;padding:26px;box-shadow:0 25px 70px rgba(0,0,0,.22)}.modal-head{display:flex;justify-content:space-between;align-items:flex-start}.modal-head h2{margin:0 0 6px;font-size:22px}.modal-head button{border:0;background:#eee8df;border-radius:50%;width:34px;height:34px;font-size:22px;color:#777;cursor:pointer}.drop-zone{height:170px;margin:22px 0 12px;border:1.5px dashed #d6c3a6;border-radius:14px;background:#faf6ef;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;cursor:pointer;color:#615a52}.drop-zone.active{background:#f6eedf;border-style:solid}.drop-zone input{display:none}.drop-zone small{color:#aaa}.upload-icon{font:29px system-ui;color:#bd8b47}.selected-files{max-height:90px;overflow:auto;display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px}.selected-files span{font-size:12px;background:#eee9e1;padding:6px 9px;border-radius:7px;color:#6f675f}.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.form-grid label{display:grid;gap:7px;font-size:13px;color:#6e675f}.form-grid input{height:42px;border:1px solid #ddd6cd;border-radius:9px;padding:0 12px;outline:0}.runner-card{width:520px}.runner-select{display:grid;gap:8px;margin-top:22px;color:#655f58;font-size:13px}.runner-select select{height:44px;border:1px solid #ddd6cd;border-radius:9px;background:#fff;padding:0 12px;font-family:inherit}.runner-empty{margin-top:15px;padding:14px;border-radius:9px;background:#f5eee3;color:#8a7353;font-size:13px;line-height:1.7}.modal-actions{display:flex;justify-content:flex-end;gap:10px;margin-top:24px}@media(max-width:900px){.table-card{overflow:auto}.toolbar{flex-wrap:wrap}.search-box{flex-basis:100%}}@media(max-width:600px){.page-heading{align-items:flex-start;gap:17px;flex-direction:column}.form-grid{grid-template-columns:1fr}}
</style>
