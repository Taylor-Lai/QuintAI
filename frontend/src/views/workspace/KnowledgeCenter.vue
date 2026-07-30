<template>
  <div class="knowledge-view">
    <header class="hero">
      <div><span>EVIDENCE KNOWLEDGE</span><h1>知识与证据中心</h1><p>将原始文档、结构化字段、实体关系与可核验证据统一管理。</p></div>
      <button @click="creating = !creating">＋ 新建知识库</button>
    </header>
    <section v-if="creating" class="create-bar">
      <input v-model.trim="form.name" placeholder="知识库名称">
      <input v-model.trim="form.description" placeholder="用途说明">
      <select v-model="form.retrieval_mode"><option value="hybrid">混合检索</option><option value="keyword">关键词检索</option><option value="vector">特征向量检索</option></select>
      <button @click="create">创建</button>
    </section>
    <section class="workspace">
      <aside>
        <div class="aside-head"><b>知识库</b><small>{{ collections.length }}</small></div>
        <button v-for="item in collections" :key="item.id" :class="{ active: item.id === selectedId }" @click="choose(item.id)">
          <span><b>{{ item.name }}</b><small>{{ item.documents }} 份文档 · {{ modeNames[item.retrieval_mode] }}</small></span><em>›</em>
        </button>
        <p v-if="!collections.length" class="empty">请先创建知识库</p>
      </aside>
      <main v-if="selected">
        <div class="library-head">
          <div><h2>{{ selected.name }}</h2><p>{{ selected.description || '用于组织材料并提供可追溯检索。' }}</p></div>
          <div class="add-doc"><select v-model="documentId"><option value="">选择工作台文档</option><option v-for="doc in availableDocuments" :key="doc.id" :value="doc.id">{{ doc.filename }}</option></select><button :disabled="!documentId" @click="addDocument">加入知识库</button></div>
        </div>
        <div class="library-meta"><span v-for="doc in indexedDocuments" :key="doc.id">{{ doc.filename }}<small>{{ doc.chunk_count }} 段</small></span><i v-if="!indexedDocuments.length">暂未加入文档</i></div>
        <div class="view-tabs"><button :class="{ active: view === 'search' }" @click="view = 'search'">证据检索</button><button :class="{ active: view === 'graph' }" @click="showGraph">知识图谱</button></div>

        <section v-if="view === 'search'" class="search-view">
          <div class="search-box"><input v-model.trim="query" placeholder="输入问题或关键词，例如：项目负责人和预算是多少？" @keyup.enter="search"><button :disabled="query.length < 2" @click="search">检索</button></div>
          <div class="search-note">结果由关键词匹配、本地特征向量与证据图谱路径共同排序；所有图谱结论均保留原文来源。</div>
          <div v-if="retrieval.graph_paths?.length" class="graph-paths"><b>关联路径</b><span v-for="path in retrieval.graph_paths" :key="path">{{ path }}</span></div>
          <article v-for="(item, index) in results" :key="item.chunk_id">
            <div class="rank">{{ index + 1 }}</div>
            <div><h3>{{ item.filename }}</h3><p>{{ item.snippet }}</p><span>综合 {{ score(item.score) }} · 关键词 {{ score(item.keyword_score) }} · 特征向量 {{ score(item.vector_score) }}<template v-if="item.graph_score"> · 图谱增强 {{ score(item.graph_score) }}</template></span><small v-for="path in item.graph_paths" :key="path" class="result-path">{{ path }}</small></div>
            <small>片段 {{ (item.citation?.chunk_index ?? 0) + 1 }}</small>
          </article>
          <p v-if="searched && !results.length" class="empty">没有检索到相关内容</p>
        </section>

        <section v-else>
          <div class="graph-toolbar"><input v-model.trim="graphQuery" placeholder="筛选实体名称"><select v-model="entityType"><option value="">全部类型</option><option v-for="type in entityTypes" :key="type" :value="type">{{ type }}</option></select><span>{{ graphNodes.length }} / {{ graph.metadata?.entity_count || 0 }} 个实体</span><button @click="rebuildGraph">重新构建</button></div>
          <div class="graph-view">
            <div class="graph-stage"><svg viewBox="0 0 900 520" preserveAspectRatio="xMidYMid meet"><line v-for="edge in graphEdges" :key="edge.id" :x1="edge.x1" :y1="edge.y1" :x2="edge.x2" :y2="edge.y2"/><g v-for="node in graphNodes" :key="node.id" :transform="`translate(${node.x},${node.y})`" @click="focus = node.raw"><circle :r="node.document ? 34 : 24" :class="{ document: node.document, active: focus?.entity_id === node.id }"/><text text-anchor="middle" dy="4">{{ node.label }}</text></g></svg><div v-if="!graphNodes.length" class="empty graph-empty">加入并提取文档后即可生成图谱</div></div>
            <aside class="node-detail">
              <template v-if="focus">
                <span>{{ focus.entity_type }} · 置信度 {{ score(focus.confidence) }} · {{ reviewNames[focus.review_status] || '待复核' }}</span><h3>{{ focus.name }}</h3>
                <div class="review-actions"><button @click="reviewEntity('confirmed')">确认实体</button><button @click="reviewEntity('questioned')">标记存疑</button></div>
                <p v-if="focus.attributes?.field_names?.length">字段：{{ focus.attributes.field_names.join('、') }}</p><p>关联来源：{{ focus.source_ids?.length || 0 }} 份文档</p>
                <div v-if="focusedRelations.length" class="relations"><b>实体关系</b><small v-for="item in focusedRelations" :key="item.relation_id">{{ item.label }}</small></div>
                <div class="evidence-list"><b>原文证据</b><article v-for="item in focus.evidence" :key="item.id"><strong>{{ item.filename }}</strong><p>{{ item.snippet || '已关联原始文档' }}</p><small>{{ item.field_name || '文档来源' }} · {{ score(item.confidence) }}</small></article></div>
              </template>
              <p v-else>点击节点查看关系、来源文档和原文证据</p>
            </aside>
          </div>
        </section>
      </main>
      <main v-else class="main-empty">选择或创建知识库后开始</main>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { getDocuments } from '../../api/workspace'
import { addKnowledgeDocument, createKnowledge, getKnowledge, getKnowledgeDocuments, getKnowledgeGraph, rebuildKnowledgeGraph, reviewKnowledgeEntity, searchKnowledge } from '../../api/enterprise'

const collections = ref([]), documents = ref([]), indexedDocuments = ref([]), selectedId = ref(''), documentId = ref(''), query = ref(''), results = ref([]), searched = ref(false), view = ref('search'), creating = ref(false), graph = ref({ entities: [], relations: [], metadata: {} }), focus = ref(null), graphQuery = ref(''), entityType = ref(''), retrieval = ref({})
const form = reactive({ name: '', description: '', retrieval_mode: 'hybrid' })
const modeNames = { hybrid: '混合', keyword: '关键词', vector: '特征向量' }
const reviewNames = { unreviewed: '待复核', confirmed: '已确认', questioned: '存疑' }
const selected = computed(() => collections.value.find(item => item.id === selectedId.value))
const availableDocuments = computed(() => { const used = new Set(indexedDocuments.value.map(item => item.document_id)); return documents.value.filter(item => !used.has(item.id)) })
const entityTypes = computed(() => Object.keys(graph.value.metadata?.entity_types || {}))
const filteredEntities = computed(() => { const keyword = graphQuery.value.toLowerCase(); return (graph.value.entities || []).filter(item => (!entityType.value || item.entity_type === entityType.value) && (!keyword || String(item.name).toLowerCase().includes(keyword))).slice(0, 80) })
const graphNodes = computed(() => { const nodes = filteredEntities.value, center = { x: 450, y: 260 }; return nodes.map((raw, index) => { const document = raw.entity_type === '文档', angle = (Math.PI * 2 * index) / Math.max(1, nodes.length), radius = document ? 75 : 165 + (index % 3) * 55; return { id: raw.entity_id, raw, document, x: center.x + Math.cos(angle) * radius, y: center.y + Math.sin(angle) * radius, label: String(raw.name || '节点').slice(0, 10) } }) })
const graphEdges = computed(() => { const points = new Map(graphNodes.value.map(item => [item.id, item])); return (graph.value.relations || []).map(raw => { const source = points.get(raw.source_entity_id), target = points.get(raw.target_entity_id); return source && target ? { id: raw.relation_id, x1: source.x, y1: source.y, x2: target.x, y2: target.y } : null }).filter(Boolean) })
const focusedRelations = computed(() => { if (!focus.value) return []; const names = new Map((graph.value.entities || []).map(item => [item.entity_id, item.name])); return (graph.value.relations || []).filter(item => item.source_entity_id === focus.value.entity_id || item.target_entity_id === focus.value.entity_id).map(item => ({ ...item, label: `${names.get(item.source_entity_id) || '实体'} —${item.relation_type}→ ${names.get(item.target_entity_id) || '实体'}` })).slice(0, 12) })
const load = async () => { const [knowledge, workspaceDocuments] = await Promise.all([getKnowledge(), getDocuments({ limit: 100 })]); collections.value = knowledge.items; documents.value = workspaceDocuments.items; if (!selectedId.value && collections.value.length) await choose(collections.value[0].id) }
const choose = async id => { selectedId.value = id; results.value = []; retrieval.value = {}; searched.value = false; focus.value = null; indexedDocuments.value = (await getKnowledgeDocuments(id)).items }
const create = async () => { if (!form.name) return; const item = await createKnowledge(form); creating.value = false; Object.assign(form, { name: '', description: '', retrieval_mode: 'hybrid' }); await load(); await choose(item.id) }
const addDocument = async () => { await addKnowledgeDocument(selectedId.value, documentId.value); documentId.value = ''; await choose(selectedId.value); await load() }
const search = async () => { if (query.value.length < 2) return; const data = await searchKnowledge(selectedId.value, query.value); results.value = data.items; retrieval.value = data.retrieval || {}; searched.value = true }
const showGraph = async () => { view.value = 'graph'; graph.value = await getKnowledgeGraph(selectedId.value); focus.value = null }
const rebuildGraph = async () => { await rebuildKnowledgeGraph(selectedId.value); await showGraph() }
const reviewEntity = async reviewStatus => { if (!focus.value) return; const entityId = focus.value.entity_id; await reviewKnowledgeEntity(selectedId.value, entityId, reviewStatus); graph.value = await getKnowledgeGraph(selectedId.value); focus.value = graph.value.entities.find(item => item.entity_id === entityId) || null }
const score = value => `${Math.round(Number(value || 0) * 100)}%`
onMounted(() => load().catch(error => alert(error.message)))
</script>

<style scoped>
.knowledge-view{display:grid;gap:18px;color:#38342f}.hero,.create-bar,.workspace{background:#f8f8f8;border:1px solid #e4e0d9;border-radius:17px;box-shadow:0 8px 24px rgba(0,0,0,.035)}.hero{padding:27px 30px;display:flex;justify-content:space-between;align-items:center;background:linear-gradient(135deg,#faf7f1,#f4eadb);border-color:#e4d5be}.hero span{font:700 11px system-ui;letter-spacing:1.6px;color:#b18140}.hero h1{font-size:28px;margin:7px 0 5px}.hero p{margin:0;color:#918a81;font-size:13px}.hero button,.create-bar button,.add-doc button,.search-box button,.graph-toolbar button{border:0;border-radius:19px;padding:10px 16px;background:#d2aa6e;color:#fff;cursor:pointer}.create-bar{padding:14px;display:grid;grid-template-columns:1fr 1.4fr 150px auto;gap:9px}.create-bar input,.create-bar select,.add-doc select,.search-box input,.graph-toolbar input,.graph-toolbar select{height:40px;border:1px solid #ddd6cc;border-radius:9px;padding:0 11px;background:#fff}.workspace{min-height:670px;display:grid;grid-template-columns:260px minmax(0,1fr);overflow:hidden}.workspace>aside{background:#f2efe9;border-right:1px solid #e2ddd5}.aside-head{padding:18px;display:flex;justify-content:space-between}.aside-head small{color:#999}.workspace>aside>button{width:100%;min-height:72px;border:0;border-top:1px solid #e2ddd5;background:transparent;padding:14px 16px;display:flex;justify-content:space-between;text-align:left;cursor:pointer}.workspace>aside>button.active{background:#fff;box-shadow:inset 3px 0 #cda566}.workspace>aside button span{display:grid;gap:5px}.workspace>aside small{color:#999}.workspace>aside em{font:20px system-ui;color:#b8aa96}.workspace>main{padding:23px;min-width:0}.library-head{display:flex;justify-content:space-between;gap:15px}.library-head h2{margin:0 0 5px}.library-head p{margin:0;color:#999;font-size:12px}.add-doc{display:flex;gap:7px}.add-doc button:disabled,.search-box button:disabled{opacity:.5}.library-meta{display:flex;gap:7px;overflow:auto;padding:14px 0}.library-meta span{white-space:nowrap;padding:7px 10px;border-radius:15px;background:#efe9df;font-size:11px}.library-meta small{margin-left:6px;color:#a88a62}.library-meta i{font-style:normal;color:#aaa;font-size:12px}.view-tabs{display:flex;border-bottom:1px solid #e7e2db}.view-tabs button{border:0;background:none;padding:12px 18px;color:#888;cursor:pointer}.view-tabs button.active{color:#9b6b2a;border-bottom:2px solid #d0a564}.search-box{margin-top:18px;display:flex;gap:8px}.search-box input{flex:1}.search-note{font-size:11px;color:#999;margin:9px 3px 14px}.search-view>article{display:grid;grid-template-columns:34px 1fr auto;gap:12px;padding:15px 3px;border-top:1px solid #ebe6df}.rank{width:28px;height:28px;border-radius:8px;background:#eadcc7;color:#9a6c2f;display:grid;place-items:center;font:12px system-ui}.search-view h3{font-size:14px;margin:0}.search-view p{font-size:12px;line-height:1.65;color:#716b64;margin:6px 0}.search-view span,.search-view article>small{font-size:10px;color:#a78d69}.graph-paths{display:grid;gap:5px;padding:10px 13px;background:#f5eee3;border-radius:10px;margin-bottom:12px;font-size:11px}.result-path{display:block;margin-top:4px;color:#9a6c2f!important}.graph-toolbar{display:flex;gap:8px;align-items:center;margin-top:15px}.graph-toolbar input{flex:1}.graph-toolbar span{font-size:11px;color:#999;white-space:nowrap}.graph-view{display:grid;grid-template-columns:minmax(0,1fr) 240px;gap:12px;margin-top:12px}.graph-stage{position:relative;min-height:480px;background:radial-gradient(circle at center,#fff,#f4f0e9);border:1px solid #e5dfd6;border-radius:13px;overflow:hidden}.graph-stage svg{width:100%;height:100%;min-height:480px}.graph-stage line{stroke:#d4c7b6;stroke-width:1}.graph-stage circle{fill:#e2c79e;stroke:#fff;stroke-width:3;cursor:pointer}.graph-stage circle.document{fill:#aa7a3c}.graph-stage circle.active{stroke:#67491f;stroke-width:4}.graph-stage text{font-size:9px;fill:#4d4439;pointer-events:none}.node-detail{border:1px solid #e5dfd6;border-radius:13px;padding:16px;background:#faf8f4;max-height:480px;overflow:auto}.node-detail span{font-size:10px;color:#a27132}.node-detail h3{font-size:17px}.node-detail p,.node-detail small{font-size:11px;line-height:1.6;color:#777}.relations,.evidence-list{display:grid;gap:6px;margin-top:14px}.relations small{padding:6px;background:#f1ece4;border-radius:6px}.evidence-list article{padding:9px;border:1px solid #e5dfd6;border-radius:8px;background:#fff}.evidence-list article p{margin:4px 0}.evidence-list strong{font-size:11px}.empty,.main-empty{padding:35px;text-align:center;color:#aaa}.graph-empty{position:absolute;inset:0;display:grid;place-content:center}@media(max-width:850px){.workspace{grid-template-columns:1fr}.workspace>aside{max-height:220px;overflow:auto}.graph-view{grid-template-columns:1fr}.create-bar{grid-template-columns:1fr}.hero,.library-head,.graph-toolbar{align-items:stretch;flex-direction:column}.add-doc{width:100%}.add-doc select{flex:1}.graph-toolbar input,.graph-toolbar select{width:100%}}
.review-actions{display:flex;gap:6px}.review-actions button{border:1px solid #d7c7b0;border-radius:15px;padding:6px 9px;background:#fff;color:#805c2d;font-size:10px;cursor:pointer}
</style>
