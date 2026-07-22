<template>
  <div class="guide-page">
    <AppHeader />

    <div class="container guide-container">
      <!-- 主内容区域 -->
      <section class="guide-card">
        <div class="card-head">
          <div>
            <div class="section-title">快速上手说明</div>
            <div class="section-subtitle">
              你可以通过左侧摘要快速跳转到对应内容位置
            </div>
          </div>
        </div>

        <div class="guide-content">
          <!-- 左侧摘要目录 -->
          <aside class="guide-sidebar">
            <div class="sidebar-title">内容摘要</div>
            <div class="sidebar-list">
              <div
                v-for="item in tocList"
                :key="item.id"
                class="sidebar-item"
                :class="{ active: activeAnchor === item.id }"
                @click="scrollToAnchor(item.id)"
              >
                {{ item.title }}
              </div>
            </div>
          </aside>

          <!-- 右侧正文 -->
          <div class="markdown-wrap">
            <article class="markdown-body">
              <section id="intro" class="anchor-section">
                <h1>欢迎使用 智汇文枢</h1>
                <p>
                  智汇文枢 是一个面向智能文档处理的综合平台，支持文档理解、
                  信息提取、模板使用与在线编辑等功能。
                </p>
              </section>

              <hr />

              <section id="features" class="anchor-section">
                <h2>一、平台主要功能</h2>

                <h3>1. 文档智能操作交互</h3>
                <p>
                  你可以上传文档，并围绕文档内容进行智能问答、分析和交互。
                </p>
                <p><strong>适用场景：</strong></p>
                <ul>
                  <li>合同内容快速问答</li>
                  <li>制度文件摘要提取</li>
                  <li>长文档重点定位</li>
                  <li>文档内容智能分析</li>
                </ul>

                <h3>2. 非结构化文档信息提取</h3>
                <p>
                  适用于从复杂文本中抽取关键信息，例如姓名、日期、金额、编号等。
                </p>
                <p><strong>适用场景：</strong></p>
                <ul>
                  <li>发票信息提取</li>
                  <li>合同字段识别</li>
                  <li>申请表结构化提取</li>
                  <li>报表内容关键信息抽取</li>
                </ul>

                <h3>3. 表格自定义数据填写</h3>
                <p>
                  支持根据业务需求，将识别后的内容填写到指定表格或模板中。
                </p>
                <p><strong>适用场景：</strong></p>
                <ul>
                  <li>表单自动填写</li>
                  <li>模板化数据录入</li>
                  <li>批量文档信息映射</li>
                  <li>数据归档整理</li>
                </ul>

                <h3>4. 在线编辑</h3>
                <p>
                  支持用户在线修改、整理和完善文档内容，提高处理效率。
                </p>
                <p><strong>适用场景：</strong></p>
                <ul>
                  <li>文档二次修订</li>
                  <li>模板内容补充</li>
                  <li>结果人工校验</li>
                  <li>内容标准化整理</li>
                </ul>
              </section>

              <hr />

              <section id="steps" class="anchor-section">
                <h2>二、快速使用流程</h2>

                <h3>第一步：注册或登录账号</h3>
                <p>
                  点击页面右上角的 <strong>登录/注册</strong> 按钮完成账号登录。
                </p>

                <h3>第二步：进入功能模块</h3>
                <p>你可以从导航栏中选择：</p>
                <ul>
                  <li><strong>功能</strong></li>
                  <li><strong>模板库</strong></li>
                  <li><strong>在线编辑</strong></li>
                </ul>

                <h3>第三步：上传或选择文档</h3>
                <p>
                  根据功能页面提示上传文档，或从模板库中选择现有模板。
                </p>

                <h3>第四步：查看处理结果</h3>
                <p>
                  系统会根据你的操作返回识别结果、提取内容或编辑后的文档数据。
                </p>

                <h3>第五步：进一步修改与导出</h3>
                <p>
                  你可以结合在线编辑功能对结果进行调整、保存或后续处理。
                </p>
              </section>

              <hr />

              <section id="notice" class="anchor-section">
                <h2>三、使用注意事项</h2>
                <ul>
                  <li>请优先上传清晰、完整的文件内容，以获得更好的识别效果。</li>
                  <li>若文档较复杂，建议分步骤处理，便于校验结果。</li>
                  <li>涉及敏感信息时，请遵循你的业务安全规范。</li>
                  <li>
                    如遇页面异常、接口失败、识别结果偏差等问题，可通过
                    <strong>问题反馈</strong> 页面提交说明。
                  </li>
                </ul>
              </section>

              <hr />

              <section id="faq" class="anchor-section">
                <h2>四、常见问题</h2>

                <h3>Q1：为什么某些功能需要登录后才能使用？</h3>
                <p>
                  为了保护你的数据、保存使用记录，并提供个性化服务，部分功能仅对登录用户开放。
                </p>

                <h3>Q2：上传文档后没有得到预期结果怎么办？</h3>
                <p>建议检查以下内容：</p>
                <ul>
                  <li>文件是否完整</li>
                  <li>文件格式是否正确</li>
                  <li>文档内容是否清晰</li>
                  <li>当前功能是否匹配你的使用场景</li>
                </ul>

                <h3>Q3：模板库和在线编辑有什么区别？</h3>
                <ul>
                  <li><strong>模板库</strong>：用于选择已有模板</li>
                  <li><strong>在线编辑</strong>：用于直接编辑和修改文档内容</li>
                </ul>
              </section>

              <hr />

              <section id="start" class="anchor-section">
                <h2>五、继续体验</h2>
                <p>你可以从以下入口开始：</p>
                <ul>
                  <li>进入 <strong>功能</strong> 页面体验智能文档处理</li>
                  <li>打开 <strong>模板库</strong> 查找可用模板</li>
                  <li>进入 <strong>在线编辑</strong> 处理文档内容</li>
                  <li>如有建议或问题，前往 <strong>问题反馈</strong></li>
                </ul>

                <blockquote>
                  感谢使用 智汇文枢，祝你体验顺利。
                </blockquote>
              </section>
            </article>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref } from 'vue'
import AppHeader from '../components/AppHeader.vue'

const tocList = [
  { id: 'intro', title: '欢迎使用智汇文枢' },
  { id: 'features', title: '一、平台主要功能' },
  { id: 'steps', title: '二、快速使用流程' },
  { id: 'notice', title: '三、使用注意事项' },
  { id: 'faq', title: '四、常见问题' },
  { id: 'start', title: '五、继续体验' }
]

const activeAnchor = ref('intro')

const scrollToAnchor = (id) => {
  activeAnchor.value = id
  const el = document.getElementById(id)
  if (el) {
    el.scrollIntoView({
      behavior: 'smooth',
      block: 'start'
    })
  }
}

const updateActiveAnchor = () => {
  let currentId = tocList[0].id

  for (const item of tocList) {
    const el = document.getElementById(item.id)
    if (!el) continue

    const rect = el.getBoundingClientRect()
    if (rect.top <= 140) {
      currentId = item.id
    }
  }

  activeAnchor.value = currentId
}

onMounted(() => {
  window.addEventListener('scroll', updateActiveAnchor)
  updateActiveAnchor()
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', updateActiveAnchor)
})
</script>

<style scoped>
.guide-page {
  min-height: 100vh;
  background: #ececec;
}

.container {
  width: 1280px;
  max-width: calc(100% - 48px);
  margin: 0 auto;
}

.guide-container {
  padding: 32px 0 48px;
}

.guide-card {
  background: #f8f8f8;
  border-radius: 20px;
  padding: 28px;
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.05);
}

.card-head {
  margin-bottom: 22px;
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

.guide-content {
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 24px;
  align-items: start;
}

.guide-sidebar {
  position: sticky;
  top: 96px;
  background: #fff;
  border: 1px solid #ececec;
  border-radius: 18px;
  padding: 20px;
}

.sidebar-title {
  font-size: 18px;
  font-weight: 700;
  color: #2d2d2d;
  margin-bottom: 16px;
}

.sidebar-list {
  display: grid;
  gap: 10px;
}

.sidebar-item {
  padding: 12px 14px;
  border-radius: 12px;
  color: #666;
  font-size: 14px;
  line-height: 1.6;
  cursor: pointer;
  transition: all 0.2s ease;
  background: #fafafa;
  border: 1px solid transparent;
}

.sidebar-item:hover {
  background: #faf6ef;
  color: #b88c47;
}

.sidebar-item.active {
  background: rgba(213, 176, 118, 0.12);
  color: #9c6a1f;
  font-weight: 700;
  border-color: rgba(213, 176, 118, 0.22);
}

.markdown-wrap {
  background: #fff;
  border: 1px solid #ececec;
  border-radius: 18px;
  padding: 28px;
}

.anchor-section {
  scroll-margin-top: 100px;
}

.markdown-body {
  color: #444;
  font-size: 15px;
  line-height: 1.9;
}

.markdown-body h1 {
  font-size: 30px;
  color: #2d2d2d;
  margin: 0 0 18px;
  line-height: 1.35;
}

.markdown-body h2 {
  font-size: 24px;
  color: #2d2d2d;
  margin: 30px 0 14px;
  line-height: 1.4;
}

.markdown-body h3 {
  font-size: 18px;
  color: #9c6a1f;
  margin: 22px 0 10px;
  line-height: 1.5;
}

.markdown-body p {
  margin: 10px 0;
  color: #555;
}

.markdown-body ul {
  margin: 10px 0 10px 22px;
  padding: 0;
}

.markdown-body li {
  margin: 8px 0;
  color: #555;
}

.markdown-body hr {
  border: none;
  border-top: 1px solid #ece3d5;
  margin: 24px 0;
}

.markdown-body strong {
  color: #2d2d2d;
  font-weight: 700;
}

.markdown-body code {
  display: inline-block;
  padding: 2px 8px;
  margin: 0 2px;
  border-radius: 8px;
  background: #f6efe4;
  color: #8a611d;
  font-size: 13px;
}

.markdown-body blockquote {
  margin: 18px 0;
  padding: 14px 18px;
  background: #faf6ef;
  border-left: 4px solid #d5b076;
  border-radius: 12px;
}

.markdown-body blockquote p {
  margin: 0;
  color: #7a5b2b;
}

@media (max-width: 992px) {
  .container {
    max-width: calc(100% - 24px);
  }

  .guide-content {
    grid-template-columns: 1fr;
  }

  .guide-sidebar {
    position: static;
  }
}

@media (max-width: 768px) {
  .guide-card {
    padding: 20px;
  }

  .section-title {
    font-size: 20px;
  }

  .markdown-wrap {
    padding: 20px;
  }

  .markdown-body h1 {
    font-size: 24px;
  }

  .markdown-body h2 {
    font-size: 20px;
  }

  .markdown-body h3 {
    font-size: 17px;
  }
}
</style>