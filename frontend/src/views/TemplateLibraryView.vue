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
            <div class="section-title">热门推荐</div>
            <div class="section-subtitle">精选高频业务模板，点击即可预览</div>
          </div>
          <button class="text-btn" @click="openAllTemplates()">查看全部</button>
        </div>

        <div class="recommend-grid">
          <div
            v-for="item in hotTemplates"
            :key="item.id"
            class="recommend-item"
          >
            <div class="recommend-top">
              <span class="recommend-tag">{{ item.category }}</span>
              <span class="recommend-hot">{{ item.isHot ? '最热' : '热门' }}</span>
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

          <div class="sort-list">
            <button
              class="sort-btn"
              :class="{ active: sortType === 'default' }"
              @click="sortType = 'default'"
            >
              默认排序
            </button>
            <button
              class="sort-btn"
              :class="{ active: sortType === 'hot' }"
              @click="sortType = 'hot'"
            >
              最热
            </button>
            <button
              class="sort-btn"
              :class="{ active: sortType === 'likes' }"
              @click="sortType = 'likes'"
            >
              点赞数最多
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
                  <span v-if="item.isHot" class="top-hot-badge">最热</span>
                  <span v-if="item.source === 'local'" class="local-badge">本地上传</span>
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

                <div class="action-stats">
                  <button
                    class="stat-icon-btn like-btn"
                    title="点赞"
                    @click="increaseLikes(item)"
                  >
                    <span class="stat-icon">👍</span>
                    <span class="stat-count">{{ item.likes }}</span>
                  </button>
                  <span class="stat-icon-btn comment-btn" title="评论">
                    <span class="stat-icon">💬</span>
                    <span class="stat-count">{{ item.comments }}</span>
                  </span>
                </div>
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
              <div class="info-line"><span>点赞数：</span>{{ currentTemplate?.likes }}</div>
              <div class="info-line"><span>评论数：</span>{{ currentTemplate?.comments }}</div>
              <div class="info-line"><span>来源：</span>{{ currentTemplate?.source === 'local' ? '本地上传' : '系统内置' }}</div>
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

          <div class="action-stats preview-action-stats">
            <button
              class="stat-icon-btn like-btn"
              title="点赞"
              @click="increaseLikes(currentTemplate)"
            >
              <span class="stat-icon">👍</span>
              <span class="stat-count">{{ currentTemplate?.likes || 0 }}</span>
            </button>
            <span class="stat-icon-btn comment-btn" title="评论">
              <span class="stat-icon">💬</span>
              <span class="stat-count">{{ currentTemplate?.comments || 0 }}</span>
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { downloadExcel } from '../utils/excel'
import AppHeader from '../components/AppHeader.vue'

const router = useRouter()

const TEMPLATE_LIBRARY_STORAGE_KEY = 'local_template_library_v1'
const ACTIVE_TEMPLATE_STORAGE_KEY = 'active_template_for_table_fill_v1'
const EDIT_TEMPLATE_STORAGE_KEY = 'active_template_for_editor_v1'

const keyword = ref('')
const activeCategory = ref('全部')
const sortType = ref('default')
const previewVisible = ref(false)
const allTemplatesVisible = ref(false)
const currentTemplate = ref(null)
const uploadedTemplates = ref([])

const builtinTemplates = ref([
  {
    id: 1,
    name: '合同信息登记表',
    shortName: '合',
    category: '行政办公',
    scene: '合同管理',
    description: '适用于合同基础信息登记、审批流转及归档管理，便于统一维护合同状态和关键条款。',
    fields: 12,
    format: 'Excel / 在线表单',
    tags: ['合同', '登记', '审批'],
    likes: 128,
    comments: 26,
    isHot: true,
    source: 'builtin',
    fieldList: ['合同编号', '合同名称', '甲方', '乙方', '签订日期', '到期日期', '金额', '负责人', '审批状态', '归档编号', '备注', '附件说明']
  },
  {
    id: 2,
    name: '员工入职信息表',
    shortName: '入',
    category: '人事管理',
    scene: '员工档案',
    description: '用于员工入职基础信息采集，支持身份信息、岗位信息和联系方式统一录入。',
    fields: 15,
    format: 'Excel / 在线表单',
    tags: ['人事', '入职', '员工'],
    likes: 165,
    comments: 35,
    isHot: true,
    source: 'builtin',
    fieldList: ['姓名', '性别', '身份证号', '手机号', '邮箱', '部门', '岗位', '入职日期', '工号', '紧急联系人', '联系地址', '学历', '毕业院校', '开户行', '银行卡号']
  },
  {
    id: 3,
    name: '费用报销申请表',
    shortName: '报',
    category: '财务管理',
    scene: '费用报销',
    description: '适合日常差旅、办公采购、项目支出等报销场景，支持票据和说明字段配置。',
    fields: 10,
    format: 'Excel / 在线表单',
    tags: ['财务', '报销', '审批'],
    likes: 186,
    comments: 40,
    isHot: true,
    source: 'builtin',
    fieldList: ['申请人', '部门', '报销事由', '费用类型', '金额', '发生日期', '票据数量', '审批人', '支付方式', '备注']
  },
  {
    id: 4,
    name: '采购申请汇总表',
    shortName: '采',
    category: '供应链',
    scene: '采购审批',
    description: '用于物资、设备、耗材等采购需求申请和汇总，便于采购流程标准化管理。',
    fields: 11,
    format: 'Excel / 在线表单',
    tags: ['采购', '审批', '物资'],
    likes: 96,
    comments: 18,
    isHot: false,
    source: 'builtin',
    fieldList: ['申请部门', '申请人', '物品名称', '规格型号', '数量', '预算金额', '用途说明', '申请日期', '供应商建议', '到货日期', '审批意见']
  },
  {
    id: 5,
    name: '会议签到登记表',
    shortName: '会',
    category: '行政办公',
    scene: '活动签到',
    description: '适用于会议、培训、活动现场签到，支持参会人信息快速采集与统计。',
    fields: 8,
    format: 'Excel / 在线表单',
    tags: ['会议', '签到', '统计'],
    likes: 78,
    comments: 12,
    isHot: false,
    source: 'builtin',
    fieldList: ['会议名称', '姓名', '单位', '部门', '职务', '手机号', '签到时间', '签字']
  },
  {
    id: 6,
    name: '学生成绩登记表',
    shortName: '成',
    category: '教育场景',
    scene: '成绩管理',
    description: '适用于课程成绩录入与汇总，支持多维度字段扩展和期末成绩导出。',
    fields: 9,
    format: 'Excel / 在线表单',
    tags: ['教育', '成绩', '登记'],
    likes: 88,
    comments: 16,
    isHot: false,
    source: 'builtin',
    fieldList: ['学号', '姓名', '班级', '课程名称', '平时成绩', '期中成绩', '期末成绩', '总评成绩', '教师评语']
  },
  {
    id: 7,
    name: '病历信息采集表',
    shortName: '病',
    category: '医疗场景',
    scene: '病历整理',
    description: '用于从病历文档中提取患者基本信息、诊断结果及检查信息并完成结构化填写。',
    fields: 14,
    format: 'Excel / 在线表单',
    tags: ['医疗', '病历', '采集'],
    likes: 110,
    comments: 22,
    isHot: true,
    source: 'builtin',
    fieldList: ['姓名', '性别', '年龄', '住院号', '科室', '主诉', '既往史', '诊断结果', '检查结论', '治疗方案', '入院日期', '出院日期', '主治医生', '备注']
  },
  {
    id: 8,
    name: '项目进度跟踪表',
    shortName: '项',
    category: '项目管理',
    scene: '进度管理',
    description: '适合团队项目的阶段任务跟踪、负责人分配与完成状态记录。',
    fields: 13,
    format: 'Excel / 在线表单',
    tags: ['项目', '进度', '跟踪'],
    likes: 154,
    comments: 30,
    isHot: true,
    source: 'builtin',
    fieldList: ['项目名称', '阶段名称', '任务名称', '负责人', '开始时间', '截止时间', '完成状态', '优先级', '风险说明', '依赖项', '成果物', '更新时间', '备注']
  },
  {
    id: 9,
    name: '固定资产登记表',
    shortName: '资',
    category: '财务管理',
    scene: '资产管理',
    description: '用于办公设备、固定资产统一编号、入库、领用和盘点管理。',
    fields: 12,
    format: 'Excel / 在线表单',
    tags: ['资产', '登记', '盘点'],
    likes: 99,
    comments: 19,
    isHot: false,
    source: 'builtin',
    fieldList: ['资产编号', '资产名称', '类别', '规格型号', '购置日期', '原值', '使用部门', '责任人', '存放地点', '状态', '盘点日期', '备注']
  },
  {
    id: 10,
    name: '请假申请单',
    shortName: '假',
    category: '人事管理',
    scene: '请假审批',
    description: '适用于事假、病假、年假等请假申请及审批流程管理。',
    fields: 9,
    format: 'Excel / 在线表单',
    tags: ['请假', '审批', '考勤'],
    likes: 142,
    comments: 28,
    isHot: true,
    source: 'builtin',
    fieldList: ['申请人', '部门', '请假类型', '开始时间', '结束时间', '请假天数', '请假事由', '审批人', '审批结果']
  },
  {
    id: 11,
    name: '加班申请表',
    shortName: '班',
    category: '人事管理',
    scene: '加班管理',
    description: '适合员工加班登记、审核与统计汇总。',
    fields: 8,
    format: 'Excel / 在线表单',
    tags: ['加班', '考勤', '审批'],
    likes: 93,
    comments: 17,
    isHot: false,
    source: 'builtin',
    fieldList: ['申请人', '部门', '加班日期', '开始时间', '结束时间', '加班时长', '加班事由', '审批意见']
  },
  {
    id: 12,
    name: '客户拜访记录表',
    shortName: '客',
    category: '市场销售',
    scene: '客户跟进',
    description: '用于销售、商务人员进行客户拜访、回访与商机跟踪记录。',
    fields: 11,
    format: 'Excel / 在线表单',
    tags: ['客户', '销售', '拜访'],
    likes: 131,
    comments: 25,
    isHot: false,
    source: 'builtin',
    fieldList: ['客户名称', '联系人', '联系电话', '拜访日期', '拜访地点', '拜访人', '沟通主题', '客户需求', '下步计划', '合作意向', '备注']
  },
  {
    id: 13,
    name: '售后服务登记表',
    shortName: '售',
    category: '市场销售',
    scene: '售后处理',
    description: '适用于售后问题登记、跟踪处理和满意度回访。',
    fields: 10,
    format: 'Excel / 在线表单',
    tags: ['售后', '服务', '登记'],
    likes: 84,
    comments: 13,
    isHot: false,
    source: 'builtin',
    fieldList: ['客户名称', '产品名称', '问题描述', '报修时间', '处理人员', '处理进度', '解决时间', '处理结果', '满意度', '备注']
  },
  {
    id: 14,
    name: '来访人员登记表',
    shortName: '访',
    category: '行政办公',
    scene: '访客管理',
    description: '适合前台访客登记、安全管理和来访信息留存。',
    fields: 9,
    format: 'Excel / 在线表单',
    tags: ['来访', '登记', '安保'],
    likes: 69,
    comments: 10,
    isHot: false,
    source: 'builtin',
    fieldList: ['姓名', '单位', '来访事由', '被访人', '联系电话', '证件号码', '到访时间', '离开时间', '备注']
  },
  {
    id: 15,
    name: '培训签到反馈表',
    shortName: '训',
    category: '教育场景',
    scene: '培训管理',
    description: '适用于企业内训、课程签到及培训反馈收集。',
    fields: 10,
    format: 'Excel / 在线表单',
    tags: ['培训', '签到', '反馈'],
    likes: 105,
    comments: 21,
    isHot: false,
    source: 'builtin',
    fieldList: ['培训主题', '讲师', '参训人', '部门', '签到时间', '课程评分', '内容评价', '意见建议', '是否通过', '备注']
  },
  {
    id: 16,
    name: '门诊登记信息表',
    shortName: '诊',
    category: '医疗场景',
    scene: '门诊登记',
    description: '适用于门诊患者基础信息登记和挂号信息留档。',
    fields: 11,
    format: 'Excel / 在线表单',
    tags: ['门诊', '挂号', '登记'],
    likes: 117,
    comments: 23,
    isHot: false,
    source: 'builtin',
    fieldList: ['姓名', '性别', '年龄', '身份证号', '联系方式', '挂号科室', '医生姓名', '就诊日期', '病情描述', '诊疗建议', '备注']
  },
  {
    id: 17,
    name: '仓库出入库登记表',
    shortName: '库',
    category: '供应链',
    scene: '库存管理',
    description: '适用于仓储物资出库、入库、盘点及库存台账维护。',
    fields: 12,
    format: 'Excel / 在线表单',
    tags: ['仓库', '库存', '出入库'],
    likes: 136,
    comments: 24,
    isHot: true,
    source: 'builtin',
    fieldList: ['单据编号', '物料名称', '规格型号', '单位', '入库数量', '出库数量', '库存结余', '操作类型', '仓库位置', '经办人', '日期', '备注']
  },
  {
    id: 18,
    name: '招标报名信息表',
    shortName: '招',
    category: '供应链',
    scene: '招标管理',
    description: '用于供应商报名、资格初审和招标项目台账管理。',
    fields: 10,
    format: 'Excel / 在线表单',
    tags: ['招标', '供应商', '报名'],
    likes: 82,
    comments: 14,
    isHot: false,
    source: 'builtin',
    fieldList: ['项目名称', '供应商名称', '联系人', '联系电话', '邮箱', '报名时间', '资质情况', '投标状态', '审核结果', '备注']
  },
  {
    id: 19,
    name: '预算编制汇总表',
    shortName: '预',
    category: '财务管理',
    scene: '预算管理',
    description: '适合部门年度预算、项目预算及费用预测汇总。',
    fields: 11,
    format: 'Excel / 在线表单',
    tags: ['预算', '财务', '汇总'],
    likes: 123,
    comments: 22,
    isHot: false,
    source: 'builtin',
    fieldList: ['年度', '部门', '项目名称', '费用类别', '预算金额', '实际金额', '差异金额', '编制人', '审核人', '更新时间', '备注']
  },
  {
    id: 20,
    name: '任务派发表',
    shortName: '任',
    category: '项目管理',
    scene: '任务分配',
    description: '适用于团队任务拆解、责任到人和协作执行。',
    fields: 10,
    format: 'Excel / 在线表单',
    tags: ['任务', '分配', '执行'],
    likes: 147,
    comments: 29,
    isHot: true,
    source: 'builtin',
    fieldList: ['任务编号', '任务名称', '所属项目', '负责人', '参与人', '开始时间', '截止时间', '优先级', '状态', '备注']
  }
])

const getShortName = (name = '') => {
  return String(name).trim().slice(0, 1) || '模'
}

const normalizeLocalTemplate = (item, index = 0) => {
  const rawFields = Array.isArray(item.fields) ? item.fields : []
  const fieldList = rawFields.map((field, i) => {
    if (typeof field === 'string') return field
    return field.label || field.name || field.key || `字段${i + 1}`
  })

  return {
    id: item.id || `local_${Date.now()}_${index}`,
    name: item.name || '未命名模板',
    shortName: getShortName(item.name),
    category: item.category || '自定义分类',
    scene: item.scene || '在线编辑',
    description: item.description || `本地上传模板：${item.name || '未命名模板'}`,
    fields: fieldList.length,
    format: item.format || 'Excel / 在线表单',
    tags: Array.isArray(item.tags) && item.tags.length ? item.tags : ['本地上传'],
    likes: Number(item.likes || 0),
    comments: Number(item.comments || 0),
    isHot: Boolean(item.isHot),
    source: 'local',
    fieldList,
    rawFields,
    createdAt: item.createdAt || Date.now()
  }
}

const loadUploadedTemplates = () => {
  const raw = localStorage.getItem(TEMPLATE_LIBRARY_STORAGE_KEY)
  if (!raw) {
    uploadedTemplates.value = []
    return
  }

  try {
    const parsed = JSON.parse(raw)
    uploadedTemplates.value = Array.isArray(parsed)
      ? parsed.map((item, index) => normalizeLocalTemplate(item, index))
      : []
  } catch (error) {
    console.error('读取模板库失败：', error)
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

  if (sortType.value === 'hot') {
    list = [...list].sort((a, b) => Number(b.isHot) - Number(a.isHot) || b.likes - a.likes)
  } else if (sortType.value === 'likes') {
    list = [...list].sort((a, b) => b.likes - a.likes)
  }

  return list
})

const hotTemplates = computed(() => {
  return [...templateList.value]
    .sort((a, b) => Number(b.isHot) - Number(a.isHot) || b.likes - a.likes)
    .slice(0, 6)
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
  sortType.value = 'default'
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
    id: item.source === 'local' ? item.id : `tpl_${Date.now()}`,
    originalTemplateId: item.id,
    name: item.name || '',
    category: item.category || '自定义分类',
    scene: item.scene || '在线编辑',
    description: item.description || '',
    format: item.format || 'Excel / 在线表单',
    tags: item.tags || [],
    likes: Number(item.likes || 0),
    comments: Number(item.comments || 0),
    isHot: Boolean(item.isHot),
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

const increaseLikes = (item) => {
  if (!item) return
  item.likes = Number(item.likes || 0) + 1
}

onMounted(() => {
  loadUploadedTemplates()
})
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

.recommend-hot {
  font-size: 12px;
  color: #d84f4f;
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

.stat-icon-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 36px;
  padding: 0;
  background: transparent;
  border: none;
  color: #8b6a32;
  font-size: 13px;
  line-height: 1;
  white-space: nowrap;
}

.like-btn {
  cursor: pointer;
}

.comment-btn {
  cursor: default;
}

.like-btn:hover {
  color: #d84f4f;
}

.stat-icon {
  font-size: 16px;
}

.stat-count {
  font-weight: 600;
  color: #7a6a55;
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
