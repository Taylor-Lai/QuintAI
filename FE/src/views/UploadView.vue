<template>
  <div class="upload-view">
    <AppHeader />
    <UploadPanel
      :title="pageConfig.title"
      :description="pageConfig.description"
      :type="pageConfig.type"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import UploadPanel from '../components/UploadPanel.vue'

const route = useRoute()

const pageConfig = computed(() => {
  const configMap = {
    '/feature/doc-chat': {
      type: 'doc-chat',
      title: '文档智能操作交互',
      description: '上传文件后，系统将进行文档理解、问答与内容智能处理'
    },
    '/feature/doc-extract': {
      type: 'doc-extract',
      title: '非结构化文档信息提取',
      description: '上传文件后，系统将自动提取非结构化文档中的关键信息'
    },
    '/feature/table-fill': {
      type: 'table-fill',
      title: '表格自定义数据填写',
      description: '上传表格文件后，系统将提供智能填写与数据补全建议'
    }
  }

  return configMap[route.path] || {
    type: 'doc-chat',
    title: '文件上传',
    description: '上传文件后，系统将进行智能处理'
  }
})
</script>

<style scoped>
.upload-view {
  min-height: 100vh;
  background: #ececec;
}
</style>