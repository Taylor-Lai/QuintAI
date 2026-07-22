<template>
  <div class="editor-page">
    <AppHeader />

    <div class="container editor-container">
      <section class="editor-hero">
        <div class="hero-left">
          <div class="hero-badge">在线编辑</div>
          <h1 class="hero-title">自定义模板并上传到模板库</h1>
          <p class="hero-desc">
            你可以自定义模板名称、分类、场景、字段、标签等信息，
            支持上传至模板库，也支持下载到本地保存。
          </p>
        </div>

        <div class="hero-actions">
          <button class="secondary-btn" @click="goTemplateLibrary">
            返回模板库
          </button>
          <button class="secondary-btn" @click="downloadTemplateAsJson">
            下载 JSON
          </button>
          <button class="secondary-btn" @click="downloadTemplateAsExcel">
            下载 Excel
          </button>
          <button
            class="primary-btn"
            :disabled="uploading"
            @click="uploadTemplateToLibrary"
          >
            {{
              uploading
                ? (isEditMode ? '保存中...' : '上传中...')
                : (isEditMode ? '保存' : '上传至模板库')
            }}
          </button>
        </div>
      </section>

      <section class="editor-card">
        <div class="section-title">模板基础信息</div>

        <div class="form-grid">
          <div class="form-item">
            <label>模板名称</label>
            <input
              v-model.trim="templateForm.name"
              type="text"
              placeholder="例如：项目验收登记表"
            />
          </div>

          <div class="form-item">
            <label>模板分类</label>
            <input
              v-model.trim="templateForm.category"
              type="text"
              placeholder="例如：项目管理 / 行政办公 / 财务管理"
            />
          </div>

          <div class="form-item">
            <label>适用场景</label>
            <input
              v-model.trim="templateForm.scene"
              type="text"
              placeholder="例如：项目验收 / 采购审批 / 入职登记"
            />
          </div>

          <div class="form-item">
            <label>输出格式</label>
            <input
              v-model.trim="templateForm.format"
              type="text"
              placeholder="例如：Excel / 在线表单"
            />
          </div>

          <div class="form-item full">
            <label>模板描述</label>
            <textarea
              v-model.trim="templateForm.description"
              rows="4"
              placeholder="请输入模板说明，例如该模板适用于什么场景、有什么用途"
            />
          </div>

          <div class="form-item full">
            <label>模板标签（用逗号分隔）</label>
            <input
              v-model.trim="tagsInput"
              type="text"
              placeholder="例如：项目, 验收, 登记"
            />
          </div>
        </div>
      </section>

      <section class="editor-card">
        <div class="field-header">
          <div class="section-title">字段配置</div>
          <div class="field-header-actions">
            <button class="secondary-btn" @click="addField">新增字段</button>
            <button class="secondary-btn" @click="resetTemplate">重置模板</button>
          </div>
        </div>

        <div v-if="templateForm.fields.length" class="field-list">
          <div
            v-for="(field, index) in templateForm.fields"
            :key="field.id"
            class="field-row"
          >
            <div class="field-index">{{ String(index + 1).padStart(2, '0') }}</div>

            <div class="field-form-grid">
              <div class="form-item">
                <label>字段名称</label>
                <input
                  v-model.trim="field.label"
                  type="text"
                  placeholder="例如：姓名 / 合同编号 / 联系电话"
                />
              </div>

              <div class="form-item">
                <label>字段标识</label>
                <input
                  v-model.trim="field.key"
                  type="text"
                  placeholder="例如：name / contractNo / phone"
                />
              </div>

              <div class="form-item">
                <label>字段类型</label>
                <select v-model="field.type">
                  <option value="text">文本</option>
                  <option value="number">数字</option>
                  <option value="date">日期</option>
                  <option value="textarea">多行文本</option>
                  <option value="select">下拉选项</option>
                </select>
              </div>

              <div class="form-item checkbox-item">
                <label>是否必填</label>
                <div class="checkbox-wrap">
                  <input v-model="field.required" type="checkbox" />
                  <span>{{ field.required ? '是' : '否' }}</span>
                </div>
              </div>
            </div>

            <button class="danger-btn" @click="removeField(index)">删除</button>
          </div>
        </div>

        <div v-else class="empty-box">
          暂无字段，请点击“新增字段”
        </div>
      </section>

      <section class="editor-card">
        <div class="section-title">模板预览</div>

        <div class="preview-panel">
          <div class="preview-title">
            {{ previewData.name || '未命名模板' }}
          </div>

          <div class="preview-meta">
            <span>{{ previewData.category || '自定义分类' }}</span>
            <span>{{ previewData.scene || '在线编辑' }}</span>
            <span>{{ previewData.format || 'Excel / 在线表单' }}</span>
            <span>{{ previewData.fields.length }} 个字段</span>
          </div>

          <div class="preview-desc">
            {{ previewData.description || '暂无模板描述' }}
          </div>

          <div class="preview-block">
            <div class="preview-label">模板标签</div>
            <div class="preview-tags">
              <span
                v-for="tag in previewData.tags"
                :key="tag"
                class="tag-item"
              >
                {{ tag }}
              </span>
            </div>
          </div>

          <div class="preview-block">
            <div class="preview-label">字段列表</div>
            <div class="preview-fields">
              <span
                v-for="field in previewData.fields"
                :key="field.id"
                class="field-tag"
              >
                {{ field.label || field.key || '未命名字段' }}
              </span>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import * as XLSX from 'xlsx'
import AppHeader from '../components/AppHeader.vue'

const router = useRouter()

const TEMPLATE_LIBRARY_STORAGE_KEY = 'local_template_library_v1'
const EDIT_TEMPLATE_STORAGE_KEY = 'active_template_for_editor_v1'

const uploading = ref(false)
const isEditMode = ref(false)

const createField = () => ({
  id: `field_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
  label: '',
  key: '',
  type: 'text',
  required: false
})

const createFieldFromData = (field = {}, index = 0) => ({
  id: field.id || `field_${Date.now()}_${index}_${Math.random().toString(36).slice(2, 8)}`,
  label: field.label || field.name || '',
  key: field.key || `field_${index + 1}`,
  type: field.type || 'text',
  required: Boolean(field.required)
})

const createDefaultTemplate = () => ({
  id: `tpl_${Date.now()}`,
  name: '',
  category: '自定义分类',
  scene: '在线编辑',
  description: '',
  format: 'Excel / 在线表单',
  fields: [createField(), createField()]
})

const templateForm = ref(createDefaultTemplate())
const tagsInput = ref('本地上传, 自定义模板')

const parsedTags = computed(() => {
  return tagsInput.value
    .split(/[,，]/)
    .map(item => item.trim())
    .filter(Boolean)
})

const previewData = computed(() => {
  return {
    ...templateForm.value,
    tags: parsedTags.value
  }
})

const addField = () => {
  templateForm.value.fields.push(createField())
}

const removeField = (index) => {
  templateForm.value.fields.splice(index, 1)
}

const resetTemplate = () => {
  localStorage.removeItem(EDIT_TEMPLATE_STORAGE_KEY)
  isEditMode.value = false
  templateForm.value = createDefaultTemplate()
  tagsInput.value = '本地上传, 自定义模板'
}

const buildUploadPayload = () => {
  return {
    id: templateForm.value.id,
    originalTemplateId: templateForm.value.originalTemplateId || '',
    name: templateForm.value.name || '未命名模板',
    category: templateForm.value.category || '自定义分类',
    scene: templateForm.value.scene || '在线编辑',
    description:
      templateForm.value.description ||
      `本地上传模板：${templateForm.value.name || '未命名模板'}`,
    format: templateForm.value.format || 'Excel / 在线表单',
    tags: parsedTags.value.length ? parsedTags.value : ['本地上传'],
    likes: Number(templateForm.value.likes || 0),
    comments: Number(templateForm.value.comments || 0),
    isHot: Boolean(templateForm.value.isHot),
    fields: templateForm.value.fields.map((field, index) => ({
      id: field.id || `field_${index + 1}`,
      label: field.label || `字段${index + 1}`,
      key: field.key || `field_${index + 1}`,
      type: field.type || 'text',
      required: Boolean(field.required)
    })),
    createdAt: templateForm.value.createdAt || Date.now()
  }
}

const validateForm = () => {
  if (!templateForm.value.name.trim()) {
    alert('请填写模板名称')
    return false
  }

  if (!templateForm.value.fields.length) {
    alert('请至少添加一个字段')
    return false
  }

  const invalidField = templateForm.value.fields.find(
    field => !String(field.label || '').trim() && !String(field.key || '').trim()
  )

  if (invalidField) {
    alert('每个字段至少填写“字段名称”或“字段标识”其中一个')
    return false
  }

  return true
}

const triggerDownload = (blob, fileName) => {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = fileName
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

const downloadTemplateAsJson = () => {
  const payload = buildUploadPayload()
  const blob = new Blob([JSON.stringify(payload, null, 2)], {
    type: 'application/json;charset=utf-8'
  })
  const fileName = `${payload.name || '未命名模板'}.json`
  triggerDownload(blob, fileName)
}

const downloadTemplateAsExcel = () => {
  const payload = buildUploadPayload()
  const headers = payload.fields.map(field => field.label || field.key || '未命名字段')

  if (!headers.length) {
    alert('当前没有可导出的字段')
    return
  }

  const worksheet = XLSX.utils.aoa_to_sheet([headers])
  const workbook = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(workbook, worksheet, '模板')

  XLSX.writeFile(workbook, `${payload.name || '未命名模板'}.xlsx`)
}

const uploadTemplateToLibrary = async () => {
  if (uploading.value) return
  if (!validateForm()) return

  try {
    uploading.value = true

    const uploadItem = buildUploadPayload()
    const raw = localStorage.getItem(TEMPLATE_LIBRARY_STORAGE_KEY)

    let libraryList = []

    try {
      const parsed = raw ? JSON.parse(raw) : []
      libraryList = Array.isArray(parsed) ? parsed : []
    } catch {
      libraryList = []
    }

    const existedIndex = libraryList.findIndex(item => item.id === uploadItem.id)

    if (existedIndex > -1) {
      const oldItem = libraryList[existedIndex] || {}
      libraryList.splice(existedIndex, 1, {
        ...oldItem,
        ...uploadItem,
        id: oldItem.id || uploadItem.id,
        likes: Number(oldItem.likes || uploadItem.likes || 0),
        comments: Number(oldItem.comments || uploadItem.comments || 0),
        isHot: Boolean(oldItem.isHot ?? uploadItem.isHot)
      })
    } else {
      libraryList.unshift(uploadItem)
    }

    localStorage.setItem(
      TEMPLATE_LIBRARY_STORAGE_KEY,
      JSON.stringify(libraryList)
    )

    localStorage.removeItem(EDIT_TEMPLATE_STORAGE_KEY)

    alert(isEditMode.value ? '保存成功，正在跳转到模板库...' : '上传成功，正在跳转到模板库...')
    router.push({ name: 'template' })
  } catch (error) {
    console.error('上传模板失败：', error)
    alert(isEditMode.value ? '保存失败，请稍后重试' : '上传失败，请稍后重试')
  } finally {
    uploading.value = false
  }
}

const goTemplateLibrary = () => {
  router.push({ name: 'template' })
}

const fillEditorFromTemplate = (template) => {
  if (!template || typeof template !== 'object') return

  const rawFields = Array.isArray(template.fields) ? template.fields : []
  const normalizedFields = rawFields.length
    ? rawFields.map((field, index) => {
        if (typeof field === 'string') {
          return createFieldFromData(
            {
              label: field,
              key: `field_${index + 1}`,
              type: 'text',
              required: false
            },
            index
          )
        }

        return createFieldFromData(field, index)
      })
    : [createField(), createField()]

  isEditMode.value = Boolean(template.editMode)

  templateForm.value = {
    id: template.id || `tpl_${Date.now()}`,
    originalTemplateId: template.originalTemplateId || '',
    name: template.name || '',
    category: template.category || '自定义分类',
    scene: template.scene || '在线编辑',
    description: template.description || '',
    format: template.format || 'Excel / 在线表单',
    likes: Number(template.likes || 0),
    comments: Number(template.comments || 0),
    isHot: Boolean(template.isHot),
    createdAt: template.createdAt || Date.now(),
    fields: normalizedFields
  }

  tagsInput.value = Array.isArray(template.tags) && template.tags.length
    ? template.tags.join(', ')
    : '本地上传, 自定义模板'
}

const loadEditingTemplate = () => {
  const raw = localStorage.getItem(EDIT_TEMPLATE_STORAGE_KEY)
  if (!raw) return

  try {
    const parsed = JSON.parse(raw)
    fillEditorFromTemplate(parsed)
  } catch (error) {
    console.error('读取待编辑模板失败：', error)
  }
}

onMounted(() => {
  loadEditingTemplate()
})
</script>

<style scoped>
.editor-page {
  min-height: 100vh;
  background: #ececec;
}

.container {
  width: 1200px;
  max-width: calc(100% - 48px);
  margin: 0 auto;
}

.editor-container {
  padding: 32px 0 48px;
  display: grid;
  gap: 24px;
}

.editor-hero,
.editor-card {
  background: #f8f8f8;
  border-radius: 18px;
  padding: 28px;
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.05);
}

.editor-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.hero-left {
  flex: 1;
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
  font-size: 30px;
  line-height: 1.3;
  color: #2d2d2d;
  margin: 0 0 12px;
}

.hero-desc {
  margin: 0;
  color: #666;
  font-size: 15px;
  line-height: 1.8;
  max-width: 760px;
}

.hero-actions {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
}

.primary-btn,
.secondary-btn,
.danger-btn {
  height: 40px;
  padding: 0 18px;
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
  box-sizing: border-box;
}

.primary-btn {
  border: none;
  background: #d5b076;
  color: #fff;
}

.primary-btn:hover {
  background: #c59d60;
}

.primary-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.secondary-btn {
  background: #fff;
  color: #b48742;
  border: 1px solid #e8d6b4;
}

.secondary-btn:hover {
  background: #faf6ef;
}

.danger-btn {
  border: none;
  background: #fbe7e7;
  color: #d84f4f;
  min-width: 72px;
}

.danger-btn:hover {
  background: #f7d6d6;
}

.section-title {
  font-size: 22px;
  font-weight: 700;
  color: #2d2d2d;
  margin-bottom: 18px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-item.full {
  grid-column: 1 / -1;
}

.form-item label {
  font-size: 14px;
  color: #666;
  font-weight: 600;
}

.form-item input,
.form-item textarea,
.form-item select {
  width: 100%;
  border: 1px solid #ddd;
  border-radius: 12px;
  background: #fff;
  padding: 12px 14px;
  font-size: 14px;
  color: #333;
  box-sizing: border-box;
  outline: none;
}

.form-item input:focus,
.form-item textarea:focus,
.form-item select:focus {
  border-color: #d5b076;
}

.field-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.field-header-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.field-list {
  display: grid;
  gap: 16px;
}

.field-row {
  background: #fff;
  border: 1px solid #ececec;
  border-radius: 16px;
  padding: 18px;
  display: grid;
  grid-template-columns: 64px 1fr auto;
  gap: 18px;
  align-items: start;
}

.field-index {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  background: #faf6ef;
  color: #b48742;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}

.field-form-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.checkbox-item .checkbox-wrap {
  height: 46px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.preview-panel {
  background: #fff;
  border: 1px solid #ececec;
  border-radius: 16px;
  padding: 22px;
}

.preview-title {
  font-size: 24px;
  font-weight: 700;
  color: #2d2d2d;
}

.preview-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 12px;
}

.preview-meta span {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 0 12px;
  border-radius: 15px;
  background: #faf6ef;
  border: 1px solid #ead8ba;
  color: #b48742;
  font-size: 13px;
}

.preview-desc {
  margin-top: 16px;
  color: #666;
  font-size: 14px;
  line-height: 1.8;
}

.preview-block {
  margin-top: 18px;
}

.preview-label {
  font-size: 14px;
  font-weight: 700;
  color: #2d2d2d;
  margin-bottom: 10px;
}

.preview-tags,
.preview-fields {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.tag-item,
.field-tag {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 0 12px;
  border-radius: 15px;
  background: #f6f6f6;
  color: #777;
  font-size: 13px;
  border: 1px solid #ededed;
}

.empty-box {
  min-height: 120px;
  background: #fff;
  border: 1px dashed #ddd;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
}

@media (max-width: 960px) {
  .editor-hero,
  .field-row,
  .form-grid,
  .field-form-grid {
    grid-template-columns: 1fr;
    display: grid;
  }

  .editor-hero {
    align-items: flex-start;
  }
}
</style>
