<template>
  <div class="feedback-page">
    <AppHeader />

    <div class="container feedback-container">
      <!-- 反馈表单 -->
      <section class="form-card">
        <div class="card-head">
          <div>
            <div class="section-title">填写反馈内容</div>
            <div class="section-subtitle">
              请尽可能详细描述你遇到的问题，便于我们快速定位与处理
            </div>
          </div>
        </div>

        <div class="form-grid">
          <div class="form-item">
            <label class="form-label">问题类型</label>
            <select v-model="form.type" class="form-select">
              <option value="">请选择问题类型</option>
              <option value="功能异常">功能异常</option>
              <option value="页面显示问题">页面显示问题</option>
              <option value="文档处理问题">文档处理问题</option>
              <option value="账号登录问题">账号登录问题</option>
              <option value="功能建议">功能建议</option>
              <option value="其他">其他</option>
            </select>
          </div>

          <div class="form-item">
            <label class="form-label">联系方式</label>
            <input
              v-model.trim="form.contact"
              type="text"
              class="form-input"
              placeholder="请输入邮箱或手机号，便于我们联系你"
            />
          </div>

          <div class="form-item full">
            <label class="form-label">问题标题</label>
            <input
              v-model.trim="form.title"
              type="text"
              class="form-input"
              placeholder="请输入问题标题，例如：文档上传后无法解析"
            />
          </div>

          <div class="form-item full">
            <label class="form-label">问题描述</label>
            <textarea
              v-model.trim="form.content"
              class="form-textarea"
              placeholder="请详细描述问题出现的场景、操作步骤、报错提示等内容..."
            ></textarea>
          </div>

          <div class="form-item full">
            <label class="form-label">补充说明</label>
            <input
              v-model.trim="form.remark"
              type="text"
              class="form-input"
              placeholder="可填写设备信息、浏览器版本、复现频率等"
            />
          </div>
        </div>

        <div class="check-row">
          <label class="checkbox-wrap">
            <input v-model="form.allowContact" type="checkbox" />
            <span>允许工作人员通过联系方式与我进一步沟通</span>
          </label>
        </div>

        <div class="form-actions">
          <button
            class="primary-btn"
            :disabled="submitting"
            @click="handleSubmit"
          >
            {{ submitting ? '提交中...' : '提交反馈' }}
          </button>
          <button class="secondary-btn" @click="handleReset">重置内容</button>
        </div>
      </section>

      <!-- 底部提示 -->
      <section class="tips-card">
        <div class="section-title">反馈说明</div>
        <div class="tips-list">
          <div class="tip-item">1. 问题描述越详细，我们越容易快速定位并处理。</div>
          <div class="tip-item">2. 如果涉及文档解析错误，建议说明文档类型与操作步骤。</div>
          <div class="tip-item">3. 如填写联系方式，我们可能会与你进一步确认问题细节。</div>
          <div class="tip-item">4. 产品建议同样欢迎提交，我们会纳入后续优化评估。</div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import AppHeader from '../components/AppHeader.vue'

const submitting = ref(false)

const createDefaultForm = () => ({
  type: '',
  contact: '',
  title: '',
  content: '',
  remark: '',
  allowContact: true
})

const form = reactive(createDefaultForm())

const validateForm = () => {
  if (!form.type) {
    alert('请选择问题类型')
    return false
  }

  if (!form.title) {
    alert('请输入问题标题')
    return false
  }

  if (!form.content) {
    alert('请输入问题描述')
    return false
  }

  if (form.content.length < 10) {
    alert('问题描述不能少于10个字')
    return false
  }

  return true
}

const handleSubmit = async () => {
  if (submitting.value) return
  if (!validateForm()) return

  submitting.value = true

  try {
    // 前端演示提交，后续可替换为实际接口
    console.log('提交的问题反馈：', {
      type: form.type,
      contact: form.contact,
      title: form.title,
      content: form.content,
      remark: form.remark,
      allowContact: form.allowContact
    })

    await new Promise((resolve) => setTimeout(resolve, 800))

    alert('反馈提交成功，感谢你的建议与支持！')

    Object.assign(form, createDefaultForm())
  } catch (error) {
    console.error('提交反馈失败：', error)
    alert('提交失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}

const handleReset = () => {
  const confirmed = window.confirm('确定要清空当前填写的内容吗？')
  if (!confirmed) return

  Object.assign(form, createDefaultForm())
}
</script>

<style scoped>
.feedback-page {
  min-height: 100vh;
  background: #ececec;
}

.container {
  width: 1280px;
  max-width: calc(100% - 48px);
  margin: 0 auto;
}

.feedback-container {
  padding: 32px 0 48px;
  display: grid;
  gap: 24px;
}

.form-card,
.tips-card {
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

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.form-item.full {
  grid-column: 1 / -1;
}

.form-label {
  font-size: 14px;
  font-weight: 600;
  color: #555;
}

.form-input,
.form-select,
.form-textarea {
  width: 100%;
  border: 1px solid #e5e5e5;
  border-radius: 16px;
  background: #fff;
  font-size: 15px;
  color: #333;
  outline: none;
  transition: all 0.2s ease;
  box-sizing: border-box;
  font-family: serif;
}

.form-input,
.form-select {
  height: 54px;
  padding: 0 16px;
}

.form-textarea {
  min-height: 180px;
  padding: 16px;
  resize: vertical;
  line-height: 1.8;
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  border-color: #d5b076;
  box-shadow: 0 0 0 3px rgba(213, 176, 118, 0.12);
}

.check-row {
  margin-top: 22px;
}

.checkbox-wrap {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: #666;
  font-size: 14px;
  cursor: pointer;
}

.checkbox-wrap input {
  width: 16px;
  height: 16px;
  accent-color: #d5b076;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 28px;
  flex-wrap: wrap;
}

.primary-btn,
.secondary-btn {
  height: 42px;
  padding: 0 20px;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}

.primary-btn {
  background: #d5b076;
  color: #fff;
}

.secondary-btn {
  background: #f3f3f3;
  color: #444;
}

.primary-btn:hover,
.secondary-btn:hover {
  transform: translateY(-1px);
}

.primary-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.tips-list {
  margin-top: 18px;
  display: grid;
  gap: 12px;
}

.tip-item {
  padding: 14px 16px;
  background: #fff;
  border: 1px solid #eeeeee;
  border-radius: 14px;
  color: #666;
  font-size: 14px;
  line-height: 1.8;
}

@media (max-width: 992px) {
  .form-grid {
    grid-template-columns: 1fr;
  }

  .container {
    max-width: calc(100% - 24px);
  }
}

@media (max-width: 768px) {
  .form-card,
  .tips-card {
    padding: 20px;
  }

  .section-title {
    font-size: 20px;
  }

  .form-actions {
    flex-direction: column;
  }

  .primary-btn,
  .secondary-btn {
    width: 100%;
  }
}
</style>