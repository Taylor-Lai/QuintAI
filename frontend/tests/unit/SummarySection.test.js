import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createApp, defineComponent, h } from 'vue'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'

import SummarySection from '../../src/components/SummarySection.vue'
import { useUserStore } from '../../src/stores/user'

const EmptyPage = defineComponent({
  render: () => h('div'),
})

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: EmptyPage },
      { path: '/auth', component: EmptyPage },
      { path: '/guide', component: EmptyPage },
      { path: '/feature/doc-chat', component: EmptyPage },
    ],
  })
}

describe('SummarySection', () => {
  let app
  let container
  let router

  beforeEach(async () => {
    localStorage.clear()
    const pinia = createPinia()
    setActivePinia(pinia)
    router = createTestRouter()
    await router.push('/')
    await router.isReady()

    container = document.createElement('div')
    document.body.appendChild(container)
    app = createApp(SummarySection)
    app.use(pinia)
    app.use(router)
    app.mount(container)
  })

  afterEach(() => {
    app?.unmount()
    container?.remove()
    localStorage.clear()
  })

  it('展示三项核心能力和产品名称', () => {
    expect(container.querySelectorAll('.feature-card')).toHaveLength(3)
    expect(container.textContent).toContain('智能理解')
    expect(container.textContent).toContain('精准提取')
    expect(container.textContent).toContain('高效处理')
    expect(container.textContent).toContain('慧文融通')
  })

  it('根据登录状态进入登录页或文档能力页', async () => {
    const startButton = container.querySelector('.primary-btn')

    startButton.click()
    await vi.waitFor(() => {
      expect(router.currentRoute.value.path).toBe('/auth')
    })

    const userStore = useUserStore()
    userStore.setToken('test-token')
    await router.push('/')
    startButton.click()
    await vi.waitFor(() => {
      expect(router.currentRoute.value.path).toBe('/feature/doc-chat')
    })
  })

  it('可以进入上手指南', async () => {
    container.querySelector('.secondary-btn').click()
    await vi.waitFor(() => {
      expect(router.currentRoute.value.path).toBe('/guide')
    })
  })
})
