<template>
  <div class="upload-page">
    <section class="page-header">
      <div class="container">
        <h1 class="page-title">{{ title }}</h1>
        <p class="page-desc">{{ description }}</p>
      </div>
    </section>

    <section class="tabs-section">
      <div class="container">
        <div class="tab active">上传处理</div>
      </div>
    </section>

    <!-- doc-chat 三栏布局 -->
    <section v-if="props.type === 'doc-chat'" class="upload-section">
      <div class="container">
        <div class="doc-chat-workbench">
          <!-- 左侧来源 -->
          <div class="panel source-panel compact-panel">
            <div class="panel-header">
              <h3>来源文档</h3>
              <button class="small-action-btn" @click="triggerSelectFile">
                + 添加来源
              </button>
            </div>

            <div class="source-upload-box">
              <div class="source-upload-text">
                支持上传 Word / Markdown / TXT 等文档
              </div>

              <button class="browse-btn" @click="triggerSelectFile">
                浏览文件
              </button>
            </div>

            <div class="source-list">
              <div v-if="selectedFile" class="source-item active">
                <div class="source-file-meta">
                  <div class="file-icon">文</div>
                  <div class="file-info">
                    <div class="file-name">{{ fileName }}</div>
                    <div class="file-status">已上传文件</div>
                  </div>
                </div>
                <div class="file-tag">当前</div>
              </div>

              <div v-else class="empty-source">
                暂未添加文档，先上传文件开始处理
              </div>
            </div>
          </div>

          <!-- 中间结果 -->
          <div class="panel note-panel compact-panel">
            <div class="panel-header panel-header-with-actions">
              <h3>处理结果</h3>

              <div
                v-if="resultData && !loading && isFileResult()"
                class="result-action-buttons"
              >
              </div>
            </div>

            <div v-if="loading" class="loading-panel">
              <div class="loading-visual">
                <div class="loading-orbit orbit-1"></div>
                <div class="loading-orbit orbit-2"></div>
                <div class="loading-core">
                  <div class="loading-percent">{{ progress }}%</div>
                </div>
              </div>

              <div class="loading-title">{{ getLoadingTitle() }}</div>
              <div class="loading-subtitle">{{ progressText }}</div>

              <div class="progress-track">
                <div
                  class="progress-fill"
                  :style="{ width: `${progress}%` }"
                ></div>
              </div>

              <div class="progress-meta">
                <span>{{ getLoadingStageLabel() }}</span>
                <span>{{ progress }}%</span>
              </div>
            </div>

            <div v-else-if="resultData" class="note-content">
              <div class="result-summary-card nice-summary-card">
                <div class="summary-label">结果摘要</div>
                <div class="summary-text">
                  {{ getResultSummary() }}
                </div>
              </div>

              <div class="result-box result-box-pretty">
                <div class="result-title">
                  {{ getResultTitle() }}
                </div>

                <template v-if="isFileResult()">
                  <div class="pretty-result-card">
                    <div class="pretty-result-hero">
                      <div class="hero-graphic">
                        <div class="hero-circle hero-circle-lg"></div>
                        <div class="hero-circle hero-circle-sm"></div>
                        <div class="hero-main-icon">
                          <span>✓</span>
                        </div>
                      </div>

                      <div class="hero-texts">
                        <div class="hero-title">结果文件已生成</div>
                        <div class="hero-desc">
                          文件已经准备完成，可直接下载查看内容。
                        </div>
                      </div>
                    </div>

                    <div class="result-file-card modern-file-card">
                      <div class="result-file-top">
                        <div class="result-file-icon result-file-icon-fancy">文件</div>
                        <div class="result-file-main">
                          <div class="result-file-name">
                            {{ getResultFileName() }}
                          </div>
                          <div class="result-file-meta">
                            {{ getResultFileTypeText() }} · {{ formatFileSize(getResultFileSize()) }}
                          </div>
                        </div>
                      </div>

                      <div class="result-file-desc">
                        已输出新的文档结果，可下载到本地继续查看、流转或存档。
                      </div>

                      <div class="result-file-actions">
                        <button
                          class="upload-btn result-download-btn"
                          type="button"
                          @click="handleDownload"
                        >
                          下载结果文件
                        </button>
                      </div>
                    </div>
                  </div>
                </template>

                <ul
                  v-else-if="Array.isArray(getResultContent())"
                  class="result-list"
                >
                  <li
                    v-for="(item, index) in getResultContent()"
                    :key="index"
                  >
                    {{ item }}
                  </li>
                </ul>

                <div v-else class="result-plain-text">
                  {{ getResultContent() }}
                </div>
              </div>
            </div>

            <div v-else class="note-placeholder">
              <div class="placeholder-graphic">
                <div class="placeholder-doc"></div>
                <div class="placeholder-dot"></div>
              </div>
              <div class="placeholder-main">暂无结果</div>
              <div class="placeholder-sub">
                上传文档后，在右侧输入自然语言指令再开始处理
              </div>
            </div>
          </div>

          <!-- 右侧操作 -->
          <div class="panel command-panel compact-panel">
            <div class="panel-header">
              <h3>智能操作指令</h3>
            </div>

            <div class="command-desc">
              基于自然语言处理与文档结构理解技术，能够将用户对文档的编辑、排版、格式调整、内容提取等操作需求，通过自然语言指令进行解析与转化，自动执行相应操作。
            </div>

            <div class="field-label input-label">请输入处理需求</div>

            <textarea
              v-model="commandText"
              class="command-textarea compact-textarea"
              placeholder="例如：
1. 提取文档摘要
2. 调整标题格式
3. 优化排版
4. 提取表格内容"
            />

            <div class="selected-file-box">
              <div class="selected-file-label">当前文件</div>
              <div class="selected-file-name">
                {{ fileName || '未选择文件' }}
              </div>
            </div>

            <div class="action-row chat-action-row">
              <button class="upload-btn secondary" @click="resetDocChat">
                重置
              </button>

              <button
                class="upload-btn"
                :disabled="loading || !selectedFile"
                @click="handleUpload"
              >
                {{ loading ? '处理中...' : '开始处理' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- doc-extract / table-fill -->
    <section v-else class="upload-section">
      <div class="container upload-layout-advanced">
        <!-- 左侧操作区 -->
        <div class="upload-card large-card compact-card">
          <!-- doc-extract -->
          <template v-if="props.type === 'doc-extract'">
            <div class="field-block">
              <div class="field-label">选择文件</div>

              <div class="multi-upload-box">
                <div
                  v-if="!extractFile"
                  class="multi-upload-empty"
                >
                  暂未选择文件
                </div>

                <div v-else class="selected-file-list">
                  <div class="selected-file-item">
                    <div class="selected-file-item-left">
                      <div class="mini-file-icon">文</div>
                      <div class="selected-file-info">
                        <div class="selected-file-title">{{ extractFile.name }}</div>
                        <div class="selected-file-size">
                          {{ formatFileSize(extractFile.size) }}
                        </div>
                      </div>
                    </div>

                    <button
                      class="delete-file-btn"
                      type="button"
                      @click="removeExtractFile"
                    >
                      删除
                    </button>
                  </div>
                </div>

                <div class="upload-row upload-row-bottom">
                  <button class="browse-btn" type="button" @click="triggerExtractSelectFile">
                    浏览文件
                  </button>
                </div>
              </div>
            </div>

            <div class="field-block">
              <div class="field-label">提取字段</div>
              <div class="text-input-box">
                <input
                  v-model="fieldsText"
                  class="text-input"
                  placeholder="例如：姓名,身份证号,学校,联系方式"
                />
              </div>
            </div>

            <div class="action-row action-row-left">
              <button
                class="upload-btn secondary"
                type="button"
                @click="resetDocExtract"
              >
                重置
              </button>
              <button
                class="upload-btn"
                :disabled="loading || !extractFile || !fieldsText.trim()"
                @click="handleUpload"
              >
                {{ loading ? '处理中...' : '处理' }}
              </button>
            </div>

            <div class="bottom-tip">
              上传源文件并填写提取字段后，即可进行信息提取
            </div>
          </template>

          <!-- table-fill -->
          <template v-else>
            <div class="field-block">
              <div class="field-label">信息汇总模板</div>

              <div v-if="activeTemplateMeta" class="active-template-box">
                <div class="active-template-header">
                  <div class="active-template-badge">当前使用模板</div>
                  <button
                    class="small-clear-btn"
                    type="button"
                    @click="clearActiveTemplate"
                  >
                    清除模板
                  </button>
                </div>

                <div class="active-template-name">
                  {{ activeTemplateMeta.name || '未命名模板' }}
                </div>

                <div class="active-template-meta">
                  <span>{{ activeTemplateMeta.category || '自定义分类' }}</span>
                  <span>{{ activeTemplateMeta.scene || '在线编辑' }}</span>
                  <span>{{ activeTemplateFieldLabels.length }} 个字段</span>
                </div>

                <div class="active-template-desc">
                  {{ activeTemplateMeta.description || '已从模板库带入当前模板' }}
                </div>

                <div v-if="activeTemplateFieldLabels.length" class="active-template-fields">
                  <span
                    v-for="(field, index) in activeTemplateFieldLabels"
                    :key="`${field}-${index}`"
                    class="active-template-field-tag"
                  >
                    {{ field }}
                  </span>
                </div>
              </div>

              <div class="template-upload-box" :class="{ 'with-active-template': activeTemplateMeta }">
                <div v-if="selectedTemplateFile" class="template-file-card">
                  <div class="template-file-left">
                    <div class="mini-file-icon">模</div>
                    <div class="selected-file-info">
                      <div class="selected-file-title">{{ selectedTemplateFile.name }}</div>
                      <div class="selected-file-size">
                        {{ formatFileSize(selectedTemplateFile.size) }}
                      </div>
                    </div>
                  </div>

                  <button
                    class="delete-file-btn"
                    type="button"
                    @click="removeTemplateFile"
                  >
                    删除
                  </button>
                </div>

                <div v-else-if="activeTemplateMeta" class="template-upload-empty template-upload-empty-active">
                  <div class="template-auto-title">已选择模板库模板</div>
                  <div class="template-auto-desc">
                    处理时将自动根据当前模板生成 Excel 模板文件，无需手动上传
                  </div>
                </div>

                <div v-else class="template-upload-empty">
                  暂未上传模板文件
                </div>

                <div class="upload-row upload-row-bottom">
                  <button class="browse-btn" type="button" @click="triggerTemplateSelectFile">
                    上传模板
                  </button>
                </div>
              </div>
            </div>

            <div class="field-block">
              <div class="field-label">选择文件</div>

              <div class="multi-upload-box">
                <div v-if="!tableFillDocumentFiles.length" class="multi-upload-empty">
                  暂未选择文件
                </div>

                <div v-else class="selected-file-list">
                  <div
                    v-for="(documentFile, index) in tableFillDocumentFiles"
                    :key="`${documentFile.name}-${documentFile.size}-${index}`"
                    class="selected-file-item"
                  >
                    <div class="selected-file-item-left">
                      <div class="mini-file-icon">文</div>
                      <div class="selected-file-info">
                        <div class="selected-file-title">{{ documentFile.name }}</div>
                        <div class="selected-file-size">
                          {{ formatFileSize(documentFile.size) }}
                        </div>
                      </div>
                    </div>

                    <button
                      class="delete-file-btn"
                      type="button"
                      @click="removeTableFillDocumentFile(index)"
                    >
                      删除
                    </button>
                  </div>
                </div>

                <div class="upload-row upload-row-bottom">
                  <button class="browse-btn" type="button" @click="triggerTableFillDocumentSelectFile">
                    浏览文件
                  </button>
                </div>
              </div>
            </div>

            <div class="field-block">
              <div class="field-label">填写要求（可选）</div>
              <textarea
                v-model="tableFillUserRequest"
                class="command-textarea compact-textarea"
                placeholder="例如：筛选 2020 年 7 月中国每日数据，按国家和日期排序"
              ></textarea>
            </div>

            <div class="action-row action-row-left">
              <button
                class="upload-btn secondary"
                type="button"
                @click="resetTableFill"
              >
                重置
              </button>
              <button
                class="upload-btn"
                :disabled="loading || !canSubmitTableFill"
                @click="handleUpload"
              >
                {{ loading ? '处理中...' : '处理' }}
              </button>
            </div>

            <div class="bottom-tip">
              上传 Excel 模板和源文档后，即可进行自动表格填写；支持直接使用模板库中的模板
            </div>
          </template>
        </div>

        <!-- 右侧结果区 -->
        <div class="result-card large-card compact-card">
          <div class="result-header result-header-with-actions">
            <h3>处理结果</h3>

            <div v-if="resultData && !loading" class="result-action-buttons">
              <button
                v-if="showPreviewButton()"
                class="small-action-btn"
                type="button"
                @click="handlePreview"
              >
                预览
              </button>
            </div>
          </div>

          <div v-if="loading" class="loading-panel result-loading-panel">
            <div class="loading-visual">
              <div class="loading-orbit orbit-1"></div>
              <div class="loading-orbit orbit-2"></div>
              <div class="loading-core">
                <div class="loading-percent">{{ progress }}%</div>
              </div>
            </div>

            <div class="loading-title">{{ getLoadingTitle() }}</div>
            <div class="loading-subtitle">{{ progressText }}</div>

            <div class="progress-track">
              <div
                class="progress-fill"
                :style="{ width: `${progress}%` }"
              ></div>
            </div>

            <div class="progress-meta">
              <span>{{ getLoadingStageLabel() }}</span>
              <span>{{ progress }}%</span>
            </div>
          </div>

          <div v-else-if="resultData" class="result-content">
            <div class="result-summary">
              <div class="summary-label">结果摘要</div>
              <div class="summary-text">
                {{ getResultSummary() }}
              </div>
            </div>

            <div class="result-box result-box-pretty">
              <div class="result-title">
                {{ getResultTitle() }}
              </div>

              <template v-if="isFileResult()">
                <div class="pretty-result-card">
                  <div class="pretty-result-hero">
                    <div class="hero-graphic">
                      <div class="hero-circle hero-circle-lg"></div>
                      <div class="hero-circle hero-circle-sm"></div>
                      <div class="hero-main-icon">
                        <span>✓</span>
                      </div>
                    </div>

                    <div class="hero-texts">
                      <div class="hero-title">结果文件已生成</div>
                      <div class="hero-desc">
                        内容已整理完成，可直接下载查看。
                      </div>
                    </div>
                  </div>

                  <div class="result-file-card modern-file-card">
                    <div class="result-file-top">
                      <div class="result-file-icon result-file-icon-fancy">文件</div>
                      <div class="result-file-main">
                        <div class="result-file-name">
                          {{ getResultFileName() }}
                        </div>
                        <div class="result-file-meta">
                          {{ getResultFileTypeText() }} · {{ formatFileSize(getResultFileSize()) }}
                        </div>
                      </div>
                    </div>

                    <div class="result-file-desc">
                      已输出新的结果文件，适合继续下载、查看和后续流转。
                    </div>

                    <div class="result-file-actions">
                      <button class="upload-btn result-download-btn" type="button" @click="handleDownload">
                        下载结果文件
                      </button>
                    </div>
                  </div>
                </div>
              </template>

              <template v-else-if="props.type === 'doc-extract'">
                <div class="extract-result-wrapper">
                  <div class="extract-hero-card">
                    <div class="extract-hero-left">
                      <div class="extract-hero-icon">
                        <span>◎</span>
                      </div>
                      <div>
                        <div class="extract-hero-title">字段内容已整理</div>
                        <div class="extract-hero-desc">
                          本次共识别 {{ getExtractEntries().length }} 项内容
                        </div>
                      </div>
                    </div>

                    <div class="extract-status-badge soft-badge">
                      {{ getExtractStatusText() }}
                    </div>
                  </div>

                  <div v-if="getExtractEntries().length" class="extract-grid">
                    <div
                      v-for="(item, index) in getExtractEntries()"
                      :key="`${item.label}-${index}`"
                      class="extract-item-card extract-item-card-pretty"
                    >
                      <div class="extract-item-label">
                        {{ item.label }}
                      </div>
                      <div class="extract-item-value">
                        {{ item.value || '未识别到内容' }}
                      </div>
                    </div>
                  </div>

                  <div v-else class="extract-empty">
                    暂未识别到可展示的提取结果
                  </div>
                </div>
              </template>

              <ul
                v-else-if="Array.isArray(getResultContent())"
                class="result-list"
              >
                <li
                  v-for="(item, index) in getResultContent()"
                  :key="index"
                >
                  {{ item }}
                </li>
              </ul>

              <div v-else class="result-plain-text">
                {{ getResultContent() }}
              </div>
            </div>
          </div>

          <div v-else class="result-placeholder result-placeholder-pretty">
            <div class="placeholder-graphic">
              <div class="placeholder-doc"></div>
              <div class="placeholder-dot"></div>
            </div>
            <div>完成上传并点击处理后，这里会展示接口返回结果。</div>
          </div>
        </div>
      </div>
    </section>

    <!-- doc-chat 单文件 -->
    <input
      v-if="props.type === 'doc-chat'"
      ref="fileInputRef"
      type="file"
      class="hidden-input"
      @change="handleFileChange"
    />

    <!-- doc-extract 单文件 -->
    <input
      v-if="props.type === 'doc-extract'"
      ref="extractFileInputRef"
      type="file"
      class="hidden-input"
      @change="handleExtractFileChange"
    />

    <!-- table-fill 模板 -->
    <input
      v-if="props.type === 'table-fill'"
      ref="templateFileInputRef"
      type="file"
      class="hidden-input"
      accept=".xlsx,.docx"
      @change="handleTemplateFileChange"
    />

    <!-- table-fill 源文档 -->
    <input
      v-if="props.type === 'table-fill'"
      ref="tableFillDocumentInputRef"
      type="file"
      class="hidden-input"
      multiple
      accept=".docx,.xlsx,.txt,.md"
      @change="handleTableFillDocumentChange"
    />
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { createExcelBlob, XLSX_MIME_TYPE } from '../utils/excel'
import {
  uploadDocChatApi,
  uploadDocExtractApi,
  uploadTableFillApi,
  waitForTask,
  downloadTaskApi
} from '../api/feature'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()

const ACTIVE_TEMPLATE_STORAGE_KEY = 'active_template_for_table_fill_v1'

const props = defineProps({
  title: {
    type: String,
    default: '文件上传'
  },
  description: {
    type: String,
    default: '上传文件，我们将为您处理并生成新的文件内容'
  },
  type: {
    type: String,
    default: 'doc-chat'
  }
})

const fileInputRef = ref(null)
const extractFileInputRef = ref(null)
const templateFileInputRef = ref(null)
const tableFillDocumentInputRef = ref(null)

const selectedFile = ref(null)
const fileName = ref('')

const extractFile = ref(null)
const fieldsText = ref('')

const selectedTemplateFile = ref(null)
const tableFillDocumentFiles = ref([])
const tableFillUserRequest = ref('')
const activeTemplateMeta = ref(null)

const loading = ref(false)
const resultData = ref(null)
const commandText = ref('')
const resultFileBlob = ref(null)
const resultFileName = ref('')
const resultObjectUrl = ref('')

const progress = ref(0)
const progressText = ref('正在准备任务...')

const typeNameMap = {
  'doc-chat': '文档智能操作交互',
  'doc-extract': '非结构化文档信息提取',
  'table-fill': '表格自定义数据填写'
}


const activeTemplateFieldLabels = computed(() => {
  const template = activeTemplateMeta.value
  if (!template) return []

  if (Array.isArray(template.fieldList) && template.fieldList.length) {
    return template.fieldList.map(item => String(item))
  }

  if (Array.isArray(template.fields) && template.fields.length) {
    return template.fields.map((field, index) => {
      if (typeof field === 'string') return field
      return field.label || field.name || field.key || `字段${index + 1}`
    })
  }

  return []
})

const canSubmitTableFill = computed(() => {
  if (props.type !== 'table-fill') return false
  return Boolean(tableFillDocumentFiles.value.length && (selectedTemplateFile.value || activeTemplateMeta.value))
})

const clearResultFileState = () => {
  resultFileBlob.value = null
  resultFileName.value = ''

  if (resultObjectUrl.value) {
    URL.revokeObjectURL(resultObjectUrl.value)
    resultObjectUrl.value = ''
  }
}

const clearResultState = () => {
  clearResultFileState()
  resultData.value = null
}

const clearAllInputs = () => {
  selectedFile.value = null
  fileName.value = ''
  extractFile.value = null
  fieldsText.value = ''
  selectedTemplateFile.value = null
  tableFillDocumentFiles.value = []
  tableFillUserRequest.value = ''
  commandText.value = ''
}

const clearInputElements = () => {
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }

  if (extractFileInputRef.value) {
    extractFileInputRef.value.value = ''
  }

  if (templateFileInputRef.value) {
    templateFileInputRef.value.value = ''
  }

  if (tableFillDocumentInputRef.value) {
    tableFillDocumentInputRef.value.value = ''
  }
}

const resetProgressState = () => {
  progress.value = 0
  progressText.value = '正在准备任务...'
}

const resetPageState = () => {
  loading.value = false
  clearAllInputs()
  clearResultState()
  clearInputElements()
  resetProgressState()
  if (props.type === 'table-fill') {
    loadActiveTemplate()
  }
}

watch(
  () => props.type,
  (newType, oldType) => {
    if (oldType !== undefined && newType !== oldType) {
      resetPageState()
    }
  }
)

onMounted(() => {
  if (props.type === 'table-fill') {
    loadActiveTemplate()
  }
})

onBeforeUnmount(() => {
  clearResultFileState()
})

const triggerSelectFile = () => {
  fileInputRef.value?.click()
}

const triggerExtractSelectFile = () => {
  extractFileInputRef.value?.click()
}

const triggerTemplateSelectFile = () => {
  templateFileInputRef.value?.click()
}

const triggerTableFillDocumentSelectFile = () => {
  tableFillDocumentInputRef.value?.click()
}

const handleFileChange = (event) => {
  const file = event.target.files?.[0]
  selectedFile.value = file || null
  fileName.value = file ? file.name : ''
  clearResultState()

  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

const handleExtractFileChange = (event) => {
  const file = event.target.files?.[0]
  extractFile.value = file || null
  clearResultState()

  if (extractFileInputRef.value) {
    extractFileInputRef.value.value = ''
  }
}

const handleTemplateFileChange = (event) => {
  const file = event.target.files?.[0]
  selectedTemplateFile.value = file || null
  clearResultState()

  if (templateFileInputRef.value) {
    templateFileInputRef.value.value = ''
  }
}

const handleTableFillDocumentChange = (event) => {
  const files = Array.from(event.target.files || [])
  tableFillDocumentFiles.value = [...tableFillDocumentFiles.value, ...files]
  clearResultState()

  if (tableFillDocumentInputRef.value) {
    tableFillDocumentInputRef.value.value = ''
  }
}

const removeExtractFile = () => {
  extractFile.value = null
  clearResultState()

  if (extractFileInputRef.value) {
    extractFileInputRef.value.value = ''
  }
}

const removeTemplateFile = () => {
  selectedTemplateFile.value = null
  clearResultState()

  if (templateFileInputRef.value) {
    templateFileInputRef.value.value = ''
  }
}

const removeTableFillDocumentFile = (index) => {
  tableFillDocumentFiles.value.splice(index, 1)
  clearResultState()

  if (tableFillDocumentInputRef.value) {
    tableFillDocumentInputRef.value.value = ''
  }
}

const formatFileSize = (size) => {
  if (!size && size !== 0) return '--'
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

const getFileNameFromDisposition = (contentDisposition = '') => {
  if (!contentDisposition) return ''

  const utf8Match = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i)
  if (utf8Match?.[1]) {
    try {
      return decodeURIComponent(utf8Match[1])
    } catch {
      return utf8Match[1]
    }
  }

  const normalMatch = contentDisposition.match(/filename="?([^";]+)"?/i)
  return normalMatch?.[1] || ''
}

const isBlobLike = (value) => {
  return typeof Blob !== 'undefined' && value instanceof Blob
}

const parseJsonSafely = (value) => {
  if (typeof value !== 'string') return value

  try {
    return JSON.parse(value)
  } catch {
    return value
  }
}

const setResultFile = (blob, fallbackFileName = '') => {
  if (!isBlobLike(blob)) return

  clearResultFileState()

  resultFileBlob.value = blob
  resultFileName.value = fallbackFileName || `result_${Date.now()}`
  resultObjectUrl.value = URL.createObjectURL(blob)
}

const normalizeApiResponse = (rawResponse, fallbackFileName = '') => {
  if (rawResponse == null) {
    clearResultFileState()
    return null
  }

  const responseData = rawResponse?.data ?? rawResponse
  const responseHeaders = rawResponse?.headers || {}
  const contentDisposition =
    responseHeaders['content-disposition'] || responseHeaders['Content-Disposition'] || ''
  const serverFileName = getFileNameFromDisposition(contentDisposition)
  const finalFileName = serverFileName || fallbackFileName

  if (isBlobLike(responseData)) {
    setResultFile(responseData, finalFileName)

    return {
      status: '已完成',
      message: '已生成结果文件',
      filename: resultFileName.value,
      content_type: responseData.type || '',
      size: responseData.size,
      result_type: 'file',
      previewUrl: resultObjectUrl.value,
      downloadUrl: resultObjectUrl.value
    }
  }

  if (typeof ArrayBuffer !== 'undefined' && responseData instanceof ArrayBuffer) {
    const blob = new Blob([responseData])
    setResultFile(blob, finalFileName)

    return {
      status: '已完成',
      message: '已生成结果文件',
      filename: resultFileName.value,
      content_type: blob.type || '',
      size: blob.size,
      result_type: 'file',
      previewUrl: resultObjectUrl.value,
      downloadUrl: resultObjectUrl.value
    }
  }

  clearResultFileState()

  if (typeof responseData === 'string') {
    return parseJsonSafely(responseData)
  }

  return responseData
}

const waitForSubmittedTask = async (submission, fallbackFileName = '') => {
  const task = await waitForTask(submission.id, (current) => {
    progress.value = Math.max(0, Math.min(100, Number(current.progress) || 0))
    progressText.value = current.stage || '正在处理...'
  })
  if (task.has_file) {
    return normalizeApiResponse(await downloadTaskApi(task.id), task.filename || fallbackFileName)
  }
  return task.result || task
}

const getLoadingTitle = () => {
  if (props.type === 'doc-chat') return '文档内容处理中'
  if (props.type === 'doc-extract') return '字段内容提取中'
  return '表格数据写入中'
}

const getLoadingStageLabel = () => {
  if (progress.value < 25) return '准备阶段'
  if (progress.value < 50) return '解析阶段'
  if (progress.value < 80) return '执行阶段'
  return '整理阶段'
}

const loadActiveTemplate = () => {
  const raw = localStorage.getItem(ACTIVE_TEMPLATE_STORAGE_KEY)
  if (!raw) {
    activeTemplateMeta.value = null
    return
  }

  try {
    const parsed = JSON.parse(raw)
    activeTemplateMeta.value = parsed && typeof parsed === 'object' ? parsed : null
  } catch (error) {
    console.error('读取当前使用模板失败：', error)
    activeTemplateMeta.value = null
  }
}

const clearActiveTemplate = () => {
  localStorage.removeItem(ACTIVE_TEMPLATE_STORAGE_KEY)
  activeTemplateMeta.value = null
  clearResultState()
}

const buildExcelFileFromActiveTemplate = async () => {
  const template = activeTemplateMeta.value
  if (!template) return null

  const headers = activeTemplateFieldLabels.value
  if (!headers.length) {
    throw new Error('当前模板没有可用字段，无法生成 Excel 模板文件')
  }

  const blob = await createExcelBlob(headers)

  const safeName = (template.name || '模板').replace(/[\\/:*?"<>|]/g, '_')
  return new File([blob], `${safeName}.xlsx`, {
    type: XLSX_MIME_TYPE
  })
}

const handleDocChatUpload = async () => {
  if (!selectedFile.value) {
    alert('请先选择文档')
    return
  }

  if (!commandText.value.trim()) {
    alert('请输入操作指令')
    return
  }

  const formData = new FormData()
  formData.append('command', commandText.value.trim())
  formData.append('document', selectedFile.value)

  loading.value = true
  clearResultState()
  progress.value = 0
  progressText.value = '任务已提交，等待执行...'

  try {
    const fallbackFileName = selectedFile.value.name.replace(/(\.[^.]+)?$/, '_result.docx')
    const submission = await uploadDocChatApi(formData)
    const normalizedRes = await waitForSubmittedTask(submission, fallbackFileName)
    resultData.value = normalizedRes

    userStore.addHistoryRecord({
      fileName: selectedFile.value.name,
      type: typeNameMap[props.type],
      time: new Date().toLocaleString(),
      status: '已完成',
      summary: getSummaryFromResponse(normalizedRes) || commandText.value.trim()
    })
  } catch (error) {
    alert(error?.message || '上传失败')
  } finally {
    loading.value = false
    resetProgressState()
  }
}

const handleDocExtractUpload = async () => {
  if (!extractFile.value) {
    alert('请先选择文件')
    return
  }

  if (!fieldsText.value.trim()) {
    alert('请输入提取字段')
    return
  }

  const formData = new FormData()
  formData.append('file', extractFile.value)
  formData.append('fields', fieldsText.value.trim())

  loading.value = true
  clearResultState()
  progress.value = 0
  progressText.value = '任务已提交，等待执行...'

  try {
    const submission = await uploadDocExtractApi(formData)
    const normalizedRes = await waitForSubmittedTask(submission, extractFile.value.name)
    resultData.value = normalizedRes

    userStore.addHistoryRecord({
      fileName: extractFile.value.name,
      type: typeNameMap[props.type],
      time: new Date().toLocaleString(),
      status: '已完成',
      summary: getSummaryFromResponse(normalizedRes) || fieldsText.value.trim()
    })
  } catch (error) {
    alert(error?.message || '上传失败')
  } finally {
    loading.value = false
    resetProgressState()
  }
}

const handleTableFillUpload = async () => {
  const templateFile = selectedTemplateFile.value || await buildExcelFileFromActiveTemplate()

  if (!templateFile) {
    alert('请先上传模板文件或从模板库选择模板')
    return
  }

  if (!tableFillDocumentFiles.value.length) {
    alert('请先上传源文档')
    return
  }

  const formData = new FormData()
  formData.append('template', templateFile)
  tableFillDocumentFiles.value.forEach((documentFile) => {
    formData.append('documents', documentFile)
  })
  formData.append('user_request', tableFillUserRequest.value.trim())

  loading.value = true
  clearResultState()
  progress.value = 0
  progressText.value = '任务已提交，等待执行...'

  try {
    const fallbackFileName = `filled_${templateFile.name}`
    const submission = await uploadTableFillApi(formData)
    const normalizedRes = await waitForSubmittedTask(submission, fallbackFileName)
    resultData.value = normalizedRes

    const templateSourceName =
      selectedTemplateFile.value?.name ||
      activeTemplateMeta.value?.name ||
      templateFile.name

    userStore.addHistoryRecord({
      fileName: `${templateSourceName} / ${tableFillDocumentFiles.value.map((file) => file.name).join(', ')}`,
      type: typeNameMap[props.type],
      time: new Date().toLocaleString(),
      status: '已完成',
      summary: getSummaryFromResponse(normalizedRes) || '表格填写完成'
    })
  } catch (error) {
    alert(error?.message || '上传失败')
  } finally {
    loading.value = false
    resetProgressState()
  }
}

const handleUpload = async () => {
  if (props.type === 'doc-chat') {
    return handleDocChatUpload()
  }

  if (props.type === 'doc-extract') {
    return handleDocExtractUpload()
  }

  if (props.type === 'table-fill') {
    return handleTableFillUpload()
  }
}

const resetDocChat = () => {
  commandText.value = ''
  selectedFile.value = null
  fileName.value = ''
  clearResultState()
  resetProgressState()

  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

const resetDocExtract = () => {
  extractFile.value = null
  fieldsText.value = ''
  clearResultState()
  resetProgressState()

  if (extractFileInputRef.value) {
    extractFileInputRef.value.value = ''
  }
}

const resetTableFill = () => {
  selectedTemplateFile.value = null
  tableFillDocumentFiles.value = []
  tableFillUserRequest.value = ''
  clearResultState()
  resetProgressState()

  if (templateFileInputRef.value) {
    templateFileInputRef.value.value = ''
  }

  if (tableFillDocumentInputRef.value) {
    tableFillDocumentInputRef.value.value = ''
  }

  loadActiveTemplate()
}

const isFileResult = () => {
  return resultData.value?.result_type === 'file'
}

const normalizeStatusText = (status) => {
  if (!status) return ''
  const text = String(status).toLowerCase()
  if (text === 'success') return '已完成'
  if (text === 'ok') return '已完成'
  if (text === 'failed') return '失败'
  if (text === 'error') return '失败'
  return String(status)
}

const getSummaryFromResponse = (res) => {
  if (!res) return ''

  if (res?.result_type === 'file') {
    return `已生成结果文件：${res.filename || resultFileName.value || '结果文件'}`
  }

  if (props.type === 'doc-extract') {
    const count = getExtractEntriesFromData(res).length
    if (count > 0) {
      return `字段整理完成，共识别 ${count} 项内容`
    }
    return '字段整理完成'
  }

  return (
    res?.summary ||
    res?.message ||
    normalizeStatusText(res?.status) ||
    (res?.success === true ? '内容已生成' : '') ||
    ''
  )
}

const getResultSummary = () => {
  if (!resultData.value) return '暂无结果摘要'
  return getSummaryFromResponse(resultData.value) || '内容已整理完成'
}

const getResultTitle = () => {
  if (props.type === 'doc-chat') return '文档操作结果'
  if (props.type === 'doc-extract') return '提取结果详情'
  return '表格填写结果'
}

const getResultFileName = () => {
  return resultData.value?.filename || resultFileName.value || '结果文件'
}

const getResultFileSize = () => {
  return resultData.value?.size ?? resultFileBlob.value?.size ?? 0
}

const getResultFileTypeText = () => {
  const contentType = resultData.value?.content_type || resultFileBlob.value?.type || ''

  if (contentType.includes('wordprocessingml')) return 'Word 文档'
  if (contentType.includes('spreadsheetml')) return 'Excel 文档'
  if (contentType.includes('pdf')) return 'PDF 文档'
  if (contentType.includes('text/plain')) return '文本文件'
  if (contentType.includes('json')) return 'JSON 数据'

  const fileNameText = getResultFileName().toLowerCase()
  if (fileNameText.endsWith('.docx') || fileNameText.endsWith('.doc')) return 'Word 文档'
  if (fileNameText.endsWith('.xlsx') || fileNameText.endsWith('.xls')) return 'Excel 文档'
  if (fileNameText.endsWith('.pdf')) return 'PDF 文档'
  if (fileNameText.endsWith('.txt')) return '文本文件'
  if (fileNameText.endsWith('.md')) return 'Markdown 文件'

  return '结果文件'
}

const getExtractEntriesFromData = (res) => {
  if (!res) return []

  const source = res?.extracted_data && typeof res.extracted_data === 'object'
    ? res.extracted_data
    : null

  if (!source) return []

  return Object.entries(source)
    .filter(([key]) => key !== '_meta')
    .map(([key, value]) => ({
    label: key,
    value:
      value === null || value === undefined || value === ''
        ? '未识别到内容'
        : typeof value === 'object'
          ? JSON.stringify(value)
          : String(value)
    }))
}

const getExtractEntries = () => {
  return getExtractEntriesFromData(resultData.value)
}

const getExtractStatusText = () => {
  if (!resultData.value) return '已整理'
  const text = normalizeStatusText(resultData.value.status)
  return text === '已完成' ? '已整理' : text
}

const getResultContent = () => {
  const res = resultData.value
  if (!res) return '暂无详细结果内容'

  if (props.type === 'doc-chat') {
    if (typeof res.result === 'string') return res.result
    if (Array.isArray(res.result)) return res.result
    if (res.result && typeof res.result === 'object') {
      return JSON.stringify(res.result, null, 2)
    }
    return typeof res === 'string' ? res : JSON.stringify(res, null, 2)
  }

  if (props.type === 'doc-extract') {
    return '提取完成'
  }

  if (typeof res === 'string') return res
  if (res?.result && typeof res.result === 'string') return res.result
  return JSON.stringify(res, null, 2)
}

const showPreviewButton = () => {
  if (!resultData.value) return false
  if (isFileResult()) return false
  if (props.type === 'doc-extract') return false
  return Boolean(
    resultObjectUrl.value ||
    resultData.value?.previewUrl ||
    resultData.value?.result?.previewUrl ||
    resultData.value?.data?.previewUrl ||
    resultData.value?.query_url
  )
}

const handlePreview = () => {
  const previewUrl =
    resultObjectUrl.value ||
    resultData.value?.previewUrl ||
    resultData.value?.result?.previewUrl ||
    resultData.value?.data?.previewUrl ||
    resultData.value?.query_url

  if (previewUrl) {
    window.open(previewUrl, '_blank')
    return
  }

  alert('暂无可预览内容')
}

const handleDownload = () => {
  const downloadUrl =
    resultObjectUrl.value ||
    resultData.value?.downloadUrl ||
    resultData.value?.result?.downloadUrl ||
    resultData.value?.data?.downloadUrl

  if (downloadUrl) {
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = resultFileName.value || resultData.value?.filename || ''
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    return
  }

  alert('暂无可下载文件')
}
</script>

<style scoped>
.upload-page {
  min-height: calc(100vh - 72px);
  background: linear-gradient(180deg, #efefef 0%, #ebebeb 100%);
}

.container {
  width: 1200px;
  max-width: calc(100% - 48px);
  margin: 0 auto;
}

.page-header {
  padding: 30px 0 16px;
}

.page-title {
  margin: 0 0 12px;
  font-size: 40px;
  font-weight: 800;
  color: #2d2d2d;
}

.page-desc {
  margin: 0;
  font-size: 15px;
  color: #888;
  line-height: 1.8;
}

.tabs-section {
  padding-top: 8px;
}

.tab {
  display: inline-flex;
  align-items: center;
  height: 42px;
  padding: 0 6px;
  color: #d5b076;
  font-size: 15px;
  border-bottom: 2px solid #d5b076;
}

.upload-section {
  padding: 18px 0 44px;
}

.hidden-input {
  display: none;
}

/* doc-chat */
.doc-chat-workbench {
  display: grid;
  grid-template-columns: 292px 1fr 330px;
  gap: 20px;
}

.panel {
  background: #f8f8f8;
  border-radius: 16px;
  padding: 20px 18px;
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.05);
  min-height: 560px;
  display: flex;
  flex-direction: column;
}

.compact-panel {
  min-height: 560px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.panel-header h3 {
  margin: 0;
  font-size: 20px;
  color: #2d2d2d;
}

.panel-header-with-actions {
  align-items: flex-start;
}

.small-action-btn {
  height: 34px;
  padding: 0 14px;
  border: 1px solid #d5b076;
  border-radius: 18px;
  background: #fffaf2;
  color: #b88c47;
  font-size: 13px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s ease;
}

.small-action-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 18px rgba(213, 176, 118, 0.16);
}

.small-action-btn.solid {
  background: #d5b076;
  color: #fff;
}

.small-action-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.small-clear-btn {
  height: 30px;
  padding: 0 12px;
  border: 1px solid #ead8ba;
  border-radius: 16px;
  background: #fff;
  color: #b48742;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.small-clear-btn:hover {
  background: #faf6ef;
}

.source-upload-box {
  border: 1px dashed #d8c29a;
  background: linear-gradient(180deg, #fffaf2 0%, #fff7ea 100%);
  border-radius: 14px;
  padding: 16px;
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.source-upload-text {
  color: #8a7a60;
  font-size: 14px;
  line-height: 1.8;
}

.source-list {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
}

.source-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  background: #fff;
  border: 1px solid #ececec;
  border-radius: 12px;
  padding: 14px;
}

.source-item.active {
  border-color: #d5b076;
  box-shadow: 0 8px 20px rgba(213, 176, 118, 0.12);
}

.source-file-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.file-icon,
.mini-file-icon {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: #f4ead8;
  color: #b88c47;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  flex-shrink: 0;
}

.file-info {
  min-width: 0;
}

.file-name {
  font-size: 14px;
  font-weight: 600;
  color: #2d2d2d;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-status {
  margin-top: 4px;
  font-size: 12px;
  color: #999;
}

.file-tag {
  font-size: 12px;
  color: #b88c47;
  background: #fff5e6;
  border-radius: 999px;
  padding: 4px 10px;
  flex-shrink: 0;
}

.empty-source {
  flex: 1;
  min-height: 180px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  text-align: center;
  line-height: 1.8;
  background: #fff;
  border-radius: 14px;
  border: 1px dashed #e7e1d7;
  padding: 20px;
}

.note-panel {
  overflow: hidden;
}

.note-placeholder {
  flex: 1;
  min-height: 340px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  color: #999;
  text-align: center;
  background: #fff;
  border: 1px dashed #e7e1d7;
  border-radius: 16px;
  padding: 28px;
}

.placeholder-graphic {
  position: relative;
  width: 82px;
  height: 82px;
  margin-bottom: 18px;
}

.placeholder-doc {
  position: absolute;
  left: 16px;
  top: 10px;
  width: 46px;
  height: 56px;
  border-radius: 12px;
  background: linear-gradient(180deg, #f6ebd7 0%, #ecd6af 100%);
  box-shadow: 0 10px 24px rgba(213, 176, 118, 0.2);
}

.placeholder-doc::before {
  content: '';
  position: absolute;
  right: 0;
  top: 0;
  width: 14px;
  height: 14px;
  background: rgba(255, 255, 255, 0.75);
  clip-path: polygon(0 0, 100% 0, 100% 100%);
  border-top-right-radius: 12px;
}

.placeholder-dot {
  position: absolute;
  right: 10px;
  bottom: 10px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #d5b076;
  box-shadow: 0 8px 18px rgba(213, 176, 118, 0.3);
}

.placeholder-main {
  font-size: 22px;
  font-weight: 700;
  color: #5a5a5a;
  margin-bottom: 10px;
}

.placeholder-sub {
  font-size: 14px;
  color: #999;
  line-height: 1.9;
}

.note-content {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.command-desc {
  font-size: 13px;
  color: #7d7d7d;
  line-height: 1.9;
  background: #fff;
  border: 1px solid #ececec;
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 18px;
}

.field-label {
  font-size: 22px;
  font-weight: 700;
  color: #2d2d2d;
  margin-bottom: 14px;
}

.input-label {
  font-size: 14px;
  font-weight: 400;
  color: #666;
  margin-bottom: 12px;
}

.command-textarea {
  width: 100%;
  min-height: 300px;
  resize: vertical;
  border: 1px solid #e2dfd8;
  border-radius: 14px;
  background: #fff;
  padding: 16px;
  font-size: 14px;
  line-height: 1.8;
  color: #333;
  outline: none;
  box-sizing: border-box;
  transition: all 0.2s ease;
}

.compact-textarea {
  min-height: 250px;
}

.command-textarea:focus,
.text-input:focus {
  border-color: #d5b076;
  box-shadow: 0 0 0 3px rgba(213, 176, 118, 0.12);
}

.selected-file-box {
  margin-top: 16px;
  background: #fff;
  border: 1px solid #ececec;
  border-radius: 12px;
  padding: 14px 16px;
}

.selected-file-label {
  font-size: 13px;
  color: #777;
  margin-bottom: 8px;
}

.selected-file-name {
  font-size: 14px;
  color: #333;
  word-break: break-all;
}

.chat-action-row {
  margin-top: auto;
  padding-top: 20px;
  gap: 12px;
  justify-content: flex-end;
}

/* doc-extract / table-fill */
.upload-layout-advanced {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.large-card {
  background: #f8f8f8;
  border-radius: 16px;
  padding: 24px 22px;
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.05);
  min-height: 560px;
}

.compact-card {
  min-height: 560px;
}

.field-block + .field-block {
  margin-top: 22px;
}

.active-template-box {
  background: linear-gradient(180deg, #fffdf9 0%, #fff7ec 100%);
  border: 1px solid #ecdaba;
  border-radius: 14px;
  padding: 16px;
  margin-bottom: 14px;
}

.active-template-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.active-template-badge {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 14px;
  background: rgba(213, 176, 118, 0.16);
  color: #b48742;
  font-size: 12px;
  font-weight: 700;
}

.active-template-name {
  margin-top: 12px;
  font-size: 18px;
  font-weight: 700;
  color: #2d2d2d;
}

.active-template-meta {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.active-template-meta span {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 14px;
  background: #fff;
  border: 1px solid #ead8ba;
  color: #b48742;
  font-size: 12px;
}

.active-template-desc {
  margin-top: 12px;
  font-size: 14px;
  color: #6e6254;
  line-height: 1.8;
}

.active-template-fields {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 14px;
}

.active-template-field-tag {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 14px;
  background: #fff;
  color: #777;
  font-size: 12px;
  border: 1px solid #ededed;
}

.multi-upload-box,
.template-upload-box,
.text-input-box {
  background: #fff;
  border: 1px solid #ececec;
  border-radius: 14px;
  padding: 16px;
}

.with-active-template {
  border-color: #ecdaba;
}

.multi-upload-empty,
.template-upload-empty {
  height: 110px;
  border: 1px dashed #e7e1d7;
  border-radius: 12px;
  background: #fcfcfc;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
}

.template-upload-empty-active {
  flex-direction: column;
  gap: 8px;
  text-align: center;
  padding: 12px;
}

.template-auto-title {
  font-size: 16px;
  font-weight: 700;
  color: #b48742;
}

.template-auto-desc {
  font-size: 13px;
  line-height: 1.8;
  color: #8a7a60;
}

.selected-file-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.selected-file-item,
.template-file-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  background: #fbfbfb;
  border: 1px solid #ececec;
  border-radius: 12px;
  padding: 12px 14px;
}

.selected-file-item-left,
.template-file-left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.selected-file-info {
  min-width: 0;
}

.selected-file-title {
  font-size: 14px;
  font-weight: 600;
  color: #2d2d2d;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.selected-file-size {
  margin-top: 4px;
  font-size: 12px;
  color: #999;
}

.delete-file-btn {
  border: none;
  background: transparent;
  color: #b88c47;
  font-size: 13px;
  cursor: pointer;
  flex-shrink: 0;
}

.upload-row {
  display: flex;
  align-items: center;
  gap: 16px;
}

.upload-row-bottom {
  margin-top: 16px;
  justify-content: flex-end;
}

.text-input {
  width: 100%;
  height: 46px;
  border: 1px solid #e2dfd8;
  border-radius: 10px;
  padding: 0 14px;
  background: #fff;
  color: #333;
  font-size: 14px;
  outline: none;
  box-sizing: border-box;
}

.action-row {
  display: flex;
  justify-content: flex-end;
  margin-top: 18px;
}

.action-row-left {
  gap: 12px;
  margin-top: 26px;
}

.upload-btn {
  min-width: 110px;
  height: 42px;
  border: none;
  border-radius: 24px;
  font-size: 14px;
  cursor: pointer;
  background: linear-gradient(180deg, #d9b57b 0%, #caa262 100%);
  color: #fff;
  box-shadow: 0 10px 18px rgba(213, 176, 118, 0.2);
  transition: all 0.2s ease;
}

.upload-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 12px 22px rgba(213, 176, 118, 0.24);
}

.upload-btn.secondary {
  background: linear-gradient(180deg, #9a9a9a 0%, #7f7f7f 100%);
  box-shadow: 0 10px 18px rgba(0, 0, 0, 0.12);
}

.upload-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.bottom-tip {
  text-align: center;
  color: #8d8d8d;
  font-size: 14px;
  margin-top: 30px;
}

.result-header h3 {
  margin: 0;
  font-size: 22px;
  color: #2d2d2d;
}

.result-header-with-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.result-action-buttons {
  display: flex;
  gap: 10px;
}

.result-placeholder {
  min-height: 360px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  text-align: center;
}

.result-placeholder-pretty {
  flex-direction: column;
  gap: 10px;
}

.result-content {
  margin-top: 18px;
}

.result-summary,
.result-summary-card {
  margin-bottom: 16px;
}

.summary-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.summary-text {
  background: #fff;
  border-radius: 12px;
  padding: 14px 16px;
  color: #444;
  line-height: 1.8;
  border: 1px solid #ececec;
  white-space: pre-wrap;
  word-break: break-word;
}

.nice-summary-card .summary-text {
  background: linear-gradient(180deg, #fffdf9 0%, #fff8ef 100%);
  border-color: #efe4d0;
}

.result-box {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  border: 1px solid #ececec;
  min-height: 220px;
}

.result-box-pretty {
  background: linear-gradient(180deg, #ffffff 0%, #fffdf9 100%);
}

.result-title {
  font-size: 16px;
  font-weight: 700;
  color: #2d2d2d;
  margin-bottom: 14px;
}

.result-list {
  margin: 0;
  padding-left: 20px;
  color: #555;
  line-height: 1.9;
}

.result-plain-text {
  color: #555;
  line-height: 1.9;
  white-space: pre-wrap;
  word-break: break-word;
}

/* loading */
.loading-panel {
  flex: 1;
  min-height: 360px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  background: linear-gradient(180deg, #fffdf9 0%, #fff8ef 100%);
  border: 1px solid #efe4d0;
  border-radius: 18px;
  padding: 32px 28px;
}

.result-loading-panel {
  margin-top: 18px;
}

.loading-visual {
  position: relative;
  width: 110px;
  height: 110px;
  margin: 0 auto 20px;
}

.loading-orbit {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 1px dashed rgba(213, 176, 118, 0.45);
  animation: spin 8s linear infinite;
}

.orbit-2 {
  inset: 10px;
  animation-duration: 5s;
  animation-direction: reverse;
}

.loading-core {
  position: absolute;
  inset: 24px;
  border-radius: 50%;
  background: radial-gradient(circle at 30% 30%, #ecd2a3 0%, #d5b076 70%, #c89b55 100%);
  box-shadow: 0 14px 28px rgba(213, 176, 118, 0.28);
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-percent {
  font-size: 22px;
  font-weight: 800;
  color: #fff;
}

.loading-title {
  text-align: center;
  font-size: 22px;
  font-weight: 700;
  color: #3a342b;
  margin-bottom: 8px;
}

.loading-subtitle {
  text-align: center;
  color: #8a7a60;
  font-size: 14px;
  line-height: 1.8;
  margin-bottom: 18px;
}

.progress-track {
  width: 100%;
  height: 12px;
  border-radius: 999px;
  background: #f1e8d9;
  overflow: hidden;
  position: relative;
}

.progress-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #d5b076 0%, #e8c996 100%);
  box-shadow: 0 4px 12px rgba(213, 176, 118, 0.25);
  transition: width 0.22s ease;
}

.progress-meta {
  margin-top: 10px;
  display: flex;
  justify-content: space-between;
  color: #8a7a60;
  font-size: 13px;
}

/* file result */
.pretty-result-card {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.pretty-result-hero {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 18px;
  border-radius: 16px;
  background: linear-gradient(135deg, #fff9ef 0%, #fff4df 100%);
  border: 1px solid #efdfc2;
}

.hero-graphic {
  position: relative;
  width: 90px;
  height: 90px;
  flex-shrink: 0;
}

.hero-circle {
  position: absolute;
  border-radius: 50%;
}

.hero-circle-lg {
  width: 78px;
  height: 78px;
  left: 6px;
  top: 6px;
  background: rgba(213, 176, 118, 0.18);
}

.hero-circle-sm {
  width: 26px;
  height: 26px;
  right: 0;
  bottom: 6px;
  background: rgba(213, 176, 118, 0.28);
}

.hero-main-icon {
  position: absolute;
  left: 18px;
  top: 18px;
  width: 54px;
  height: 54px;
  border-radius: 18px;
  background: linear-gradient(180deg, #d5b076 0%, #c89b55 100%);
  color: #fff;
  font-size: 28px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 14px 24px rgba(213, 176, 118, 0.25);
}

.hero-texts {
  min-width: 0;
}

.hero-title {
  font-size: 20px;
  font-weight: 800;
  color: #2d2d2d;
}

.hero-desc {
  margin-top: 8px;
  color: #7c6d57;
  line-height: 1.8;
  font-size: 14px;
}

.result-file-card {
  border: 1px solid #eadfcb;
  background: linear-gradient(180deg, #fffdf8 0%, #fff7ea 100%);
  border-radius: 16px;
  padding: 18px;
}

.modern-file-card {
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7);
}

.result-file-top {
  display: flex;
  align-items: center;
  gap: 14px;
}

.result-file-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  background: #f3e4c7;
  color: #a9782d;
  font-size: 14px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.result-file-icon-fancy {
  background: linear-gradient(180deg, #f5e6c9 0%, #ecd3a2 100%);
  box-shadow: 0 10px 18px rgba(213, 176, 118, 0.16);
}

.result-file-main {
  min-width: 0;
}

.result-file-name {
  font-size: 16px;
  font-weight: 700;
  color: #2d2d2d;
  line-height: 1.6;
  word-break: break-all;
}

.result-file-meta {
  margin-top: 6px;
  font-size: 13px;
  color: #8a7a60;
}

.result-file-desc {
  margin-top: 16px;
  font-size: 14px;
  color: #6e6254;
  line-height: 1.8;
  background: rgba(255, 255, 255, 0.75);
  border-radius: 12px;
  padding: 12px 14px;
}

.result-file-actions {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
}

.result-download-btn {
  min-width: 140px;
}

/* extract result */
.extract-result-wrapper {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.extract-hero-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 16px 18px;
  border-radius: 16px;
  background: linear-gradient(135deg, #fffaf1 0%, #fff4e2 100%);
  border: 1px solid #efdfc2;
}

.extract-hero-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.extract-hero-icon {
  width: 58px;
  height: 58px;
  border-radius: 16px;
  background: linear-gradient(180deg, #d5b076 0%, #c89b55 100%);
  color: #fff;
  font-size: 24px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 14px 24px rgba(213, 176, 118, 0.22);
}

.extract-hero-title {
  font-size: 18px;
  font-weight: 800;
  color: #2d2d2d;
}

.extract-hero-desc {
  margin-top: 6px;
  font-size: 14px;
  color: #7c6d57;
}

.extract-status-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 88px;
  height: 34px;
  padding: 0 16px;
  border-radius: 999px;
  background: #d5b076;
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  flex-shrink: 0;
}

.soft-badge {
  background: linear-gradient(180deg, #d9b57b 0%, #caa262 100%);
  box-shadow: 0 10px 18px rgba(213, 176, 118, 0.16);
}

.extract-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.extract-item-card {
  border: 1px solid #efe8de;
  border-radius: 14px;
  background: #fcfcfc;
  padding: 16px;
  min-height: 110px;
}

.extract-item-card-pretty {
  background: linear-gradient(180deg, #ffffff 0%, #fffdfa 100%);
  box-shadow: 0 8px 18px rgba(0, 0, 0, 0.03);
}

.extract-item-label {
  font-size: 13px;
  color: #9a7a45;
  margin-bottom: 10px;
  font-weight: 700;
}

.extract-item-value {
  font-size: 15px;
  color: #333;
  line-height: 1.8;
  word-break: break-word;
  white-space: pre-wrap;
}

.extract-empty {
  min-height: 180px;
  border: 1px dashed #e7e1d7;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  background: #fafafa;
}

.browse-btn {
  min-width: 108px;
  height: 42px;
  border: none;
  border-radius: 10px;
  background: linear-gradient(180deg, #767676 0%, #5f5f5f 100%);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.2s ease;
}

.browse-btn:hover {
  transform: translateY(-1px);
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 1200px) {
  .doc-chat-workbench,
  .upload-layout-advanced {
    grid-template-columns: 1fr;
  }

  .panel,
  .large-card,
  .compact-panel,
  .compact-card {
    min-height: auto;
  }

  .note-placeholder,
  .result-placeholder,
  .loading-panel {
    min-height: 240px;
  }
}

@media (max-width: 900px) {
  .container {
    max-width: calc(100% - 32px);
  }

  .page-title {
    font-size: 32px;
  }

  .result-header-with-actions,
  .panel-header-with-actions,
  .extract-hero-card,
  .pretty-result-hero,
  .active-template-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .extract-grid {
    grid-template-columns: 1fr;
  }

  .selected-file-item,
  .template-file-card {
    flex-direction: column;
    align-items: flex-start;
  }

  .delete-file-btn {
    padding-left: 50px;
  }

  .result-file-actions {
    justify-content: flex-start;
  }

  .loading-visual {
    width: 96px;
    height: 96px;
  }

  .loading-core {
    inset: 22px;
  }

  .loading-percent {
    font-size: 20px;
  }
}
</style>
