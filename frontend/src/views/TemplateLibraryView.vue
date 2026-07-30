<template>
  <div class="template-page">
    <AppHeader />

    <div class="container template-container">
      <section class="hero-card">
        <div class="hero-content">
          <div class="hero-badge">模板库</div>
          <h1 class="hero-title">支持预览与 Excel 下载</h1>
          <p class="hero-desc">
            提供合同、审批、财务、人事、采购、登记、教育、医疗、项目等多场景模板；
            支持模板预览、查看字段、下载 Excel 表头模板，以及在线编辑
          </p>

          <div class="hero-actions">
            <button class="primary-btn" @click="openAllTemplates()">查看全部模板</button>
            <button class="secondary-btn" @click="goEditor">在线编辑</button>
          </div>
        </div>

        <div class="hero-stat-list">
          <div class="hero-stat-card">
            <div class="stat-value">{{ templateList.length }}</div>
            <div class="stat-label">模板总数</div>
          </div>
          <div class="hero-stat-card">
            <div class="stat-value">{{ categories.length }}</div>
            <div class="stat-label">模板分类</div>
          </div>
          <div class="hero-stat-card">
            <div class="stat-value">Excel</div>
            <div class="stat-label">支持导出</div>
          </div>
        </div>
      </section>

      <section class="recommend-card">
        <div class="section-head">
          <div>
            <div class="section-title">推荐模板</div>
            <div class="section-subtitle">精选高频业务模板，点击即可预览</div>
          </div>
          <button class="text-btn" @click="openAllTemplates()">查看全部</button>
        </div>

        <div class="recommend-grid">
          <div
            v-for="item in recommendedTemplates"
            :key="item.id"
            class="recommend-item"
          >
            <div class="recommend-top">
              <span class="recommend-tag">{{ item.category }}</span>
            </div>

            <div class="recommend-name">{{ item.name }}</div>
            <div class="recommend-desc">{{ item.description }}</div>

            <div class="recommend-footer">
              <span>{{ item.fields }} 项字段</span>
              <span>适用：{{ item.scene }}</span>
            </div>

            <div class="recommend-actions">
              <button class="preview-btn" @click.stop="previewTemplate(item)">
                预览模板
              </button>
              <button class="use-btn" @click.stop="downloadTemplateExcel(item)">
                下载 Excel
              </button>
            </div>
          </div>
        </div>
      </section>

      <section class="category-card">
        <div class="section-head">
          <div>
            <div class="section-title">模板分类</div>
            <div class="section-subtitle">覆盖通用办公与行业场景</div>
          </div>
        </div>

        <div class="category-overview">
          <div
            v-for="item in categorySummary"
            :key="item.name"
            class="category-overview-item"
            @click="openAllTemplates(item.name)"
          >
            <div class="category-overview-name">{{ item.name }}</div>
            <div class="category-overview-count">{{ item.count }} 个模板</div>
          </div>
        </div>
      </section>

      <section class="guide-card">
        <div class="section-title">使用流程</div>

        <div class="guide-grid">
          <div class="guide-item">
            <div class="guide-index">01</div>
            <div class="guide-name">查看推荐</div>
            <div class="guide-desc">
              首页先展示推荐模板，减少信息过载，方便快速定位常用模板
            </div>
          </div>

          <div class="guide-item">
            <div class="guide-index">02</div>
            <div class="guide-name">查看全部</div>
            <div class="guide-desc">
              点击“查看全部”弹出完整模板库，可按分类、关键词和排序筛选
            </div>
          </div>

          <div class="guide-item">
            <div class="guide-index">03</div>
            <div class="guide-name">预览模板</div>
            <div class="guide-desc">
              支持查看模板说明、字段列表、适用场景与标签信息
            </div>
          </div>

          <div class="guide-item">
            <div class="guide-index">04</div>
            <div class="guide-name">使用或编辑</div>
            <div class="guide-desc">
              在全部模板中可直接编辑模板，或跳转到表格自定义数据填写模块使用
            </div>
          </div>
        </div>
      </section>
    </div>

    <!-- 全部模板弹窗 -->
    <div v-if="allTemplatesVisible" class="preview-mask" @click="closeAllTemplates">
      <div class="all-dialog" @click.stop>
        <div class="preview-head">
          <div>
            <div class="preview-title">全部模板</div>
            <div class="preview-subtitle">
              共 {{ filteredTemplates.length }} / {{ templateList.length }} 个模板
            </div>
          </div>
          <button class="close-btn" @click="closeAllTemplates">×</button>
        </div>

        <div class="filter-panel popup-filter-panel">
          <div class="search-box">
            <input
              v-model.trim="keyword"
              class="search-input"
              type="text"
              placeholder="搜索模板名称、用途、关键词"
            />
          </div>

          <div class="category-list">
            <button
              class="category-btn"
              :class="{ active: activeCategory === '全部' }"
              @click="activeCategory = '全部'"
            >
              全部
            </button>

            <button
              v-for="item in categories"
              :key="item"
              class="category-btn"
              :class="{ active: activeCategory === item }"
              @click="activeCategory = item"
            >
              {{ item }}
            </button>
          </div>

        </div>

        <div v-if="filteredTemplates.length" class="popup-template-grid">
          <div
            v-for="item in filteredTemplates"
            :key="item.id"
            class="template-item"
          >
            <div class="template-cover">
              <div class="cover-badge">{{ item.category }}</div>
              <div class="cover-icon">{{ item.shortName }}</div>
            </div>

            <div class="template-body">
              <div class="template-title-row">
                <div class="template-name-row">
                  <div class="template-name">{{ item.name }}</div>
                  <span v-if="item.source === 'custom'" class="local-badge">团队模板</span>
                </div>
                <span class="template-scene">{{ item.scene }}</span>
              </div>

              <div class="template-desc">
                {{ item.description }}
              </div>

              <div class="template-meta">
                <span>字段数：{{ item.fields }}</span>
                <span>格式：{{ item.format }}</span>
              </div>

              <div class="template-tags">
                <span
                  v-for="tag in item.tags"
                  :key="tag"
                  class="template-tag"
                >
                  {{ tag }}
                </span>
              </div>

              <div class="template-actions">
                <button class="preview-btn" @click="previewTemplate(item)">
                  预览模板
                </button>
                <button class="secondary-btn inline-btn" @click="downloadTemplateExcel(item)">
                  下载 Excel
                </button>
                <button class="secondary-btn inline-btn" @click="editTemplate(item)">
                  编辑
                </button>
                <button class="use-btn" @click="useTemplate(item)">
                  使用
                </button>

              </div>
            </div>
          </div>
        </div>

        <div v-else class="empty-box">
          未找到符合条件的模板，请尝试更换关键词或分类
        </div>
      </div>
    </div>

    <!-- 预览弹窗 -->
    <div v-if="previewVisible" class="preview-mask" @click="closePreview">
      <div class="preview-dialog" @click.stop>
        <div class="preview-head">
          <div>
            <div class="preview-title">{{ currentTemplate?.name }}</div>
            <div class="preview-subtitle">
              {{ currentTemplate?.category }} ｜ {{ currentTemplate?.scene }}
            </div>
          </div>
          <button class="close-btn" @click="closePreview">×</button>
        </div>

        <div class="preview-content">
          <div class="preview-block">
            <div class="preview-label">模板说明</div>
            <div class="preview-text">{{ currentTemplate?.description }}</div>
          </div>

          <div class="preview-grid">
            <div class="preview-block">
              <div class="preview-label">基础信息</div>
              <div class="info-line"><span>字段数：</span>{{ currentTemplate?.fields }}</div>
              <div class="info-line"><span>输出格式：</span>{{ currentTemplate?.format }}</div>
              <div class="info-line"><span>适用场景：</span>{{ currentTemplate?.scene }}</div>
              <div class="info-line"><span>来源：</span>{{ currentTemplate?.source === 'custom' ? '团队模板' : '系统内置' }}</div>
            </div>

            <div class="preview-block">
              <div class="preview-label">适用标签</div>
              <div class="preview-tags">
                <span
                  v-for="tag in currentTemplate?.tags || []"
                  :key="tag"
                  class="template-tag"
                >
                  {{ tag }}
                </span>
              </div>
            </div>
          </div>

          <div class="preview-block">
            <div class="preview-label">包含字段</div>
            <div class="field-list">
              <span
                v-for="field in currentTemplate?.fieldList || []"
                :key="field"
                class="field-item"
              >
                {{ field }}
              </span>
            </div>
          </div>
        </div>

        <div class="preview-actions">
          <button class="preview-btn" @click="closePreview">关闭</button>
          <button class="secondary-btn inline-btn" @click="downloadTemplateExcel(currentTemplate)">
            下载 Excel
          </button>
          <button class="secondary-btn inline-btn" @click="editTemplate(currentTemplate)">
            编辑
          </button>
          <button class="use-btn" @click="useTemplate(currentTemplate)">
            使用该模板
          </button>

        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { downloadExcel } from '../utils/excel'
import { getTemplates } from '../api/enterprise'
import AppHeader from '../components/AppHeader.vue'

const router = useRouter()

const ACTIVE_TEMPLATE_STORAGE_KEY = 'active_template_for_table_fill_v1'
const EDIT_TEMPLATE_STORAGE_KEY = 'active_template_for_editor_v1'

const keyword = ref('')
const activeCategory = ref('全部')
const previewVisible = ref(false)
const allTemplatesVisible = ref(false)
const currentTemplate = ref(null)
const uploadedTemplates = ref([])

const builtinTemplates = ref([])
const getShortName = (name = '') => {
  return String(name).trim().slice(0, 1) || '模'
}

const normalizeTemplate = (item, index = 0) => {
  const rawFields = Array.isArray(item.fields) ? item.fields : []
  const fieldList = rawFields.map((field, i) => {
    if (typeof field === 'string') return field
    return field.label || field.name || field.key || `字段${i + 1}`
  })

  return {
    id: item.id || `template_${Date.now()}_${index}`,
    name: item.name || '未命名模板',
    shortName: getShortName(item.name),
    category: item.category || '自定义分类',
    scene: item.scene || '在线编辑',
    description: item.description || `团队模板：${item.name || '未命名模板'}`,
    fields: fieldList.length,
    format: item.format || 'Excel / 在线表单',
    tags: Array.isArray(item.tags) && item.tags.length ? item.tags : ['团队模板'],
    source: item.source || 'custom',
    editable: Boolean(item.editable),
    fieldList,
    rawFields,
    createdAt: item.createdAt || Date.now()
  }
}

const loadUploadedTemplates = async () => {
  try {
    const response = await getTemplates()
    const templates = Array.isArray(response.items) ? response.items.map((item, index) => normalizeTemplate(item, index)) : []
    builtinTemplates.value = templates.filter((item) => item.source === 'builtin')
    uploadedTemplates.value = templates.filter((item) => item.source === 'custom')
  } catch (error) {
    console.error('读取服务端模板库失败：', error)
    builtinTemplates.value = []
    uploadedTemplates.value = []
  }
}

const templateList = computed(() => {
  return [...builtinTemplates.value, ...uploadedTemplates.value]
})

const categories = computed(() => {
  return [...new Set(templateList.value.map(item => item.category))]
})

const filteredTemplates = computed(() => {
  const key = keyword.value.toLowerCase()

  let list = templateList.value.filter(item => {
    const matchCategory =
      activeCategory.value === '全部' || item.category === activeCategory.value

    const matchKeyword =
      !key ||
      item.name.toLowerCase().includes(key) ||
      item.description.toLowerCase().includes(key) ||
      item.scene.toLowerCase().includes(key) ||
      item.tags.some(tag => String(tag).toLowerCase().includes(key))

    return matchCategory && matchKeyword
  })

  return list
})

const recommendedTemplates = computed(() => {
  return templateList.value.slice(0, 6)
})

const categorySummary = computed(() => {
  return categories.value.map(name => ({
    name,
    count: templateList.value.filter(item => item.category === name).length
  }))
})

const openAllTemplates = (category = '全部') => {
  activeCategory.value = category
  keyword.value = ''
  allTemplatesVisible.value = true
}

const closeAllTemplates = () => {
  allTemplatesVisible.value = false
}

const previewTemplate = (item) => {
  currentTemplate.value = item
  previewVisible.value = true
}

const closePreview = () => {
  previewVisible.value = false
}

const buildTemplatePayloadForUse = (item) => {
  if (!item) return null

  const fieldList = Array.isArray(item.fieldList) ? item.fieldList : []
  const normalizedFields = fieldList.map((field, index) => ({
    id: `field_${index + 1}`,
    label: field,
    key: `field_${index + 1}`,
    type: 'text',
    required: false
  }))

  return {
    id: item.id,
    name: item.name,
    category: item.category,
    scene: item.scene,
    description: item.description,
    format: item.format,
    tags: item.tags || [],
    source: item.source || 'builtin',
    fields: normalizedFields,
    fieldList
  }
}

const buildTemplatePayloadForEdit = (item) => {
  if (!item) return null

  const localRawFields = Array.isArray(item.rawFields) ? item.rawFields : null

  let fields

  if (localRawFields && localRawFields.length) {
    fields = localRawFields.map((field, index) => {
      if (typeof field === 'string') {
        return {
          id: `field_${index + 1}`,
          label: field,
          key: `field_${index + 1}`,
          type: 'text',
          required: false
        }
      }

      return {
        id: field.id || `field_${index + 1}`,
        label: field.label || field.name || `字段${index + 1}`,
        key: field.key || `field_${index + 1}`,
        type: field.type || 'text',
        required: Boolean(field.required)
      }
    })
  } else {
    fields = (item.fieldList || []).map((field, index) => ({
      id: `field_${index + 1}`,
      label: field,
      key: `field_${index + 1}`,
      type: 'text',
      required: false
    }))
  }

  return {
    id: item.source === 'custom' ? item.id : `tpl_${Date.now()}`,
    originalTemplateId: item.id,
    name: item.name || '',
    category: item.category || '自定义分类',
    scene: item.scene || '在线编辑',
    description: item.description || '',
    format: item.format || 'Excel / 在线表单',
    tags: item.tags || [],
    createdAt: item.createdAt || Date.now(),
    editMode: true,
    source: item.source || 'builtin',
    fields
  }
}

const useTemplate = (item) => {
  if (!item) return

  const payload = buildTemplatePayloadForUse(item)
  localStorage.setItem(ACTIVE_TEMPLATE_STORAGE_KEY, JSON.stringify(payload))
  router.push({ name: 'tableFill' })
}

const editTemplate = (item) => {
  if (!item) return

  const payload = buildTemplatePayloadForEdit(item)
  localStorage.setItem(EDIT_TEMPLATE_STORAGE_KEY, JSON.stringify(payload))
  router.push({ name: 'editor' })
}

const goEditor = () => {
  localStorage.removeItem(EDIT_TEMPLATE_STORAGE_KEY)
  router.push({ name: 'editor' })
}

const downloadTemplateExcel = async (item) => {
  if (!item) return
  const headers = item.fieldList || []
  await downloadExcel(headers, `${item.name || '模板'}.xlsx`)
}

onMounted(loadUploadedTemplates)
</script>

<style scoped>
.template-page {
  min-height: 100vh;
  background: #ececec;
}

.container {
  width: 1200px;
  max-width: calc(100% - 48px);
  margin: 0 auto;
}

.template-container {
  padding: 32px 0 48px;
  display: grid;
  gap: 24px;
}

.hero-card,
.recommend-card,
.category-card,
.guide-card {
  background: #f8f8f8;
  border-radius: 18px;
  padding: 28px 28px 30px;
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.05);
}

.hero-card {
  display: grid;
  grid-template-columns: 1.3fr 0.9fr;
  gap: 24px;
  align-items: stretch;
}

.hero-content {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  height: 32px;
  padding: 0 14px;
  border-radius: 16px;
  background: rgba(213, 176, 118, 0.16);
  color: #b48742;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 16px;
}

.hero-title {
  font-size: 32px;
  line-height: 1.3;
  color: #2d2d2d;
  margin: 0 0 14px;
}

.hero-desc {
  font-size: 15px;
  line-height: 1.9;
  color: #666;
  margin: 0;
  max-width: 720px;
}

.hero-actions {
  margin-top: 24px;
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
}

.primary-btn,
.secondary-btn,
.preview-btn,
.use-btn {
  height: 40px;
  padding: 0 18px;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
  box-sizing: border-box;
}

.primary-btn,
.use-btn {
  background: #d5b076;
  color: #fff;
}

.primary-btn:hover,
.use-btn:hover {
  background: #c59d60;
}

.secondary-btn,
.preview-btn {
  background: #fff;
  color: #b48742;
  border: 1px solid #e8d6b4;
}

.secondary-btn:hover,
.preview-btn:hover {
  background: #faf6ef;
}

.inline-btn {
  height: 40px;
}

.hero-stat-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}

.hero-stat-card {
  background: #fff;
  border-radius: 16px;
  padding: 22px 20px;
  border: 1px solid #ececec;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #2d2d2d;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #888;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 22px;
  gap: 16px;
}

.section-title {
  font-size: 24px;
  font-weight: 700;
  color: #2d2d2d;
}

.section-subtitle {
  margin-top: 4px;
  font-size: 14px;
  color: #999;
}

.text-btn {
  border: none;
  background: transparent;
  color: #b48742;
  cursor: pointer;
  font-size: 14px;
  padding: 0;
}

.recommend-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.recommend-item {
  background: #fff;
  border-radius: 14px;
  padding: 18px;
  border: 1px solid #ececec;
  transition: all 0.2s ease;
}

.recommend-item:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 22px rgba(0, 0, 0, 0.06);
}

.recommend-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.recommend-tag {
  display: inline-flex;
  align-items: center;
  height: 28px;
  padding: 0 10px;
  border-radius: 14px;
  background: rgba(213, 176, 118, 0.14);
  color: #b48742;
  font-size: 12px;
  font-weight: 600;
}

.recommend-name {
  font-size: 17px;
  font-weight: 700;
  color: #2d2d2d;
  margin-bottom: 10px;
}

.recommend-desc {
  font-size: 14px;
  line-height: 1.7;
  color: #666;
  min-height: 72px;
}

.recommend-footer {
  margin-top: 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  color: #999;
}

.recommend-actions {
  margin-top: 18px;
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

.category-overview {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 18px;
}

.category-overview-item {
  background: #fff;
  border: 1px solid #ececec;
  border-radius: 16px;
  padding: 20px 18px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.category-overview-item:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 22px rgba(0, 0, 0, 0.06);
}

.category-overview-name {
  font-size: 17px;
  font-weight: 700;
  color: #2d2d2d;
  margin-bottom: 8px;
}

.category-overview-count {
  font-size: 14px;
  color: #999;
}

.guide-grid {
  margin-top: 20px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 18px;
}

.guide-item {
  background: #fff;
  border-radius: 14px;
  border: 1px solid #ececec;
  padding: 22px 18px;
}

.guide-index {
  font-size: 24px;
  font-weight: 700;
  color: #d5b076;
  margin-bottom: 14px;
}

.guide-name {
  font-size: 17px;
  font-weight: 700;
  color: #2d2d2d;
  margin-bottom: 10px;
}

.guide-desc {
  font-size: 14px;
  line-height: 1.8;
  color: #666;
}

.preview-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.32);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  z-index: 999;
}

.preview-dialog {
  width: 760px;
  max-width: 100%;
  background: #f8f8f8;
  border-radius: 18px;
  padding: 24px;
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.12);
}

.all-dialog {
  width: 1180px;
  max-width: 100%;
  max-height: calc(100vh - 40px);
  overflow: auto;
  background: #f8f8f8;
  border-radius: 18px;
  padding: 24px;
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.12);
}

.preview-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.preview-title {
  font-size: 24px;
  font-weight: 700;
  color: #2d2d2d;
  margin-bottom: 6px;
}

.preview-subtitle {
  font-size: 14px;
  color: #999;
}

.close-btn {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 18px;
  background: #fff;
  color: #666;
  cursor: pointer;
  font-size: 22px;
  line-height: 1;
  flex-shrink: 0;
}

.filter-panel {
  display: grid;
  gap: 18px;
}

.popup-filter-panel {
  margin-bottom: 20px;
}

.search-box {
  width: 100%;
}

.search-input {
  width: 100%;
  height: 46px;
  border: 1px solid #ddd;
  border-radius: 12px;
  padding: 0 16px;
  font-size: 14px;
  color: #333;
  background: #fff;
  outline: none;
  box-sizing: border-box;
}

.search-input:focus {
  border-color: #d5b076;
}

.category-list,
.sort-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.category-btn,
.sort-btn {
  height: 38px;
  padding: 0 16px;
  border: 1px solid #e6e6e6;
  border-radius: 19px;
  background: #fff;
  color: #666;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.category-btn:hover,
.sort-btn:hover {
  background: #faf6ef;
  color: #b48742;
  border-color: #ead8ba;
}

.category-btn.active,
.sort-btn.active {
  background: #d5b076;
  color: #fff;
  border-color: #d5b076;
}

.popup-template-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}

.template-item {
  background: #fff;
  border-radius: 16px;
  border: 1px solid #ececec;
  overflow: hidden;
  transition: all 0.2s ease;
}

.template-item:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.06);
}

.template-cover {
  height: 132px;
  background: linear-gradient(135deg, #f2e4cf, #ead3ac);
  padding: 18px 20px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.cover-badge {
  display: inline-flex;
  align-items: center;
  height: 28px;
  padding: 0 10px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.72);
  color: #9a6d2f;
  font-size: 12px;
  font-weight: 600;
}

.cover-icon {
  width: 54px;
  height: 54px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.78);
  color: #9a6d2f;
  font-size: 26px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.template-body {
  padding: 20px;
}

.template-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.template-name-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.template-name {
  font-size: 18px;
  font-weight: 700;
  color: #2d2d2d;
}

.top-hot-badge {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 10px;
  border-radius: 12px;
  background: rgba(216, 79, 79, 0.12);
  color: #d84f4f;
  font-size: 12px;
  font-weight: 700;
}

.local-badge {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 10px;
  border-radius: 12px;
  background: rgba(74, 144, 226, 0.12);
  color: #4a90e2;
  font-size: 12px;
  font-weight: 700;
}

.template-scene {
  flex-shrink: 0;
  font-size: 12px;
  color: #b48742;
  background: #faf6ef;
  border: 1px solid #ead8ba;
  border-radius: 12px;
  padding: 4px 8px;
}

.template-desc {
  font-size: 14px;
  line-height: 1.8;
  color: #666;
  min-height: 76px;
}

.template-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  font-size: 13px;
  color: #999;
  margin-top: 14px;
}

.template-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 16px;
}

.template-tag {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 14px;
  background: #f6f6f6;
  color: #777;
  font-size: 12px;
  border: 1px solid #ededed;
}

.template-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 20px;
  flex-wrap: nowrap;
  overflow-x: auto;
}

.action-stats {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  margin-left: 4px;
  flex-shrink: 0;
}

.preview-action-stats {
  margin-left: 0;
}

.preview-content {
  display: grid;
  gap: 18px;
}

.preview-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}

.preview-block {
  background: #fff;
  border-radius: 12px;
  padding: 18px;
  border: 1px solid #ececec;
}

.preview-label {
  font-size: 14px;
  font-weight: 700;
  color: #2d2d2d;
  margin-bottom: 12px;
}

.preview-text {
  font-size: 14px;
  line-height: 1.8;
  color: #666;
}

.info-line {
  font-size: 14px;
  color: #666;
  line-height: 1.9;
}

.info-line span {
  color: #999;
}

.preview-tags,
.field-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.field-item {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 0 12px;
  border-radius: 15px;
  background: #faf6ef;
  color: #b48742;
  font-size: 13px;
  border: 1px solid #ead8ba;
}

.preview-actions {
  margin-top: 22px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  flex-wrap: nowrap;
  overflow-x: auto;
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

@media (max-width: 1100px) {
  .hero-card,
  .recommend-grid,
  .guide-grid,
  .category-overview,
  .popup-template-grid,
  .preview-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .template-container {
    padding: 24px 0 40px;
  }

  .hero-title {
    font-size: 26px;
  }

  .section-head,
  .template-title-row,
  .preview-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .preview-dialog,
  .all-dialog {
    padding: 18px;
  }

  .template-actions,
  .preview-actions,
  .recommend-actions,
  .hero-actions {
    flex-wrap: wrap;
  }
}
</style>
