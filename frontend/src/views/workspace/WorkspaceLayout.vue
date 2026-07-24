<template>
  <div class="workspace-page">
    <AppHeader />
    <div class="workspace-frame">
      <aside class="workspace-sidebar">
        <div class="sidebar-title">智能工作台</div>
        <div class="sidebar-subtitle">让文档处理形成完整闭环</div>
        <nav class="sidebar-nav">
          <RouterLink v-for="item in navigation" :key="item.to" :to="item.to" class="sidebar-link">
            <span class="nav-icon">{{ item.icon }}</span>
            <span>{{ item.label }}</span>
          </RouterLink>
        </nav>
        <div class="sidebar-capability">
          <div class="capability-label">AI 能力入口</div>
          <RouterLink to="/feature/doc-extract">信息提取</RouterLink>
          <RouterLink to="/feature/table-fill">复杂填表</RouterLink>
          <RouterLink to="/feature/doc-chat">文档操作</RouterLink>
        </div>
      </aside>
      <main class="workspace-main"><RouterView /></main>
    </div>
  </div>
</template>

<script setup>
import AppHeader from '../../components/AppHeader.vue'

const navigation = [
  { to: '/workspace', label: '工作台概览', icon: '◫' },
  { to: '/workspace/documents', label: '文档库', icon: '▤' },
  { to: '/workspace/reviews', label: '人工复核', icon: '✓' },
  { to: '/workspace/workflows', label: '工作流', icon: '⌘' },
  { to: '/workspace/enterprise', label: '企业控制台', icon: '企' }
]
</script>

<style scoped>
.workspace-page { min-height: 100vh; background: #ececec; }
.workspace-frame { width: 1440px; max-width: calc(100% - 40px); margin: 24px auto 48px; display: grid; grid-template-columns: 238px minmax(0, 1fr); gap: 22px; align-items: start; }
.workspace-sidebar { position: sticky; top: 96px; min-height: calc(100vh - 120px); background: #f8f8f8; border: 1px solid #e5e0d8; border-radius: 18px; padding: 24px 16px; box-shadow: 0 10px 28px rgba(0,0,0,.04); }
.sidebar-title { padding: 0 10px; font-size: 21px; font-weight: 700; color: #292929; }
.sidebar-subtitle { padding: 7px 10px 22px; font-size: 12px; color: #9a9388; line-height: 1.6; }
.sidebar-nav { display: grid; gap: 7px; }
.sidebar-link { display: flex; align-items: center; gap: 12px; min-height: 46px; padding: 0 14px; border-radius: 11px; color: #65615b; font-size: 15px; transition: .2s ease; }
.sidebar-link:hover { background: #f3eee5; color: #a47432; }
.sidebar-link.router-link-exact-active { background: linear-gradient(135deg, #d9b77f, #c99c58); color: #fff; box-shadow: 0 8px 18px rgba(190,143,73,.2); }
.nav-icon { width: 22px; text-align: center; font-family: system-ui, sans-serif; font-size: 18px; }
.sidebar-capability { margin-top: 28px; padding: 18px 12px 8px; border-top: 1px solid #e8e2d9; display: grid; gap: 11px; }
.capability-label { color: #aaa198; font-size: 12px; margin-bottom: 3px; }
.sidebar-capability a { color: #77716a; font-size: 14px; }
.sidebar-capability a:hover { color: #b88640; }
.workspace-main { min-width: 0; }
@media (max-width: 900px) { .workspace-frame { max-width: calc(100% - 24px); grid-template-columns: 1fr; margin-top: 12px; } .workspace-sidebar { position: static; min-height: auto; } .sidebar-nav { grid-template-columns: repeat(4, 1fr); } .sidebar-link { justify-content: center; padding: 0 8px; } .nav-icon, .sidebar-capability, .sidebar-subtitle { display: none; } }
@media (max-width: 600px) { .sidebar-nav { grid-template-columns: repeat(2, 1fr); } }
</style>
