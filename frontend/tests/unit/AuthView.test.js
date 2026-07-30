import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createApp, defineComponent, h, nextTick } from 'vue'
import { createPinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'

import AuthView from '../../src/views/AuthView.vue'

const EmptyPage = defineComponent({
  render: () => h('div'),
})

describe('AuthView', () => {
  let app
  let container

  beforeEach(async () => {
    localStorage.clear()
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/', component: EmptyPage },
        { path: '/auth', component: AuthView },
      ],
    })
    await router.push('/auth')
    await router.isReady()

    container = document.createElement('div')
    document.body.appendChild(container)
    app = createApp(AuthView)
    app.use(createPinia())
    app.use(router)
    app.mount(container)
  })

  afterEach(() => {
    app?.unmount()
    container?.remove()
    vi.restoreAllMocks()
  })

  it('可以在登录和注册表单间切换', async () => {
    const card = container.querySelector('.auth-card')
    expect(card.classList.contains('show-register')).toBe(false)

    const registerButton = [...container.querySelectorAll('.switch-btn')]
      .find((button) => button.textContent.includes('去注册'))
    registerButton.click()
    await nextTick()

    expect(card.classList.contains('show-register')).toBe(true)
    expect(container.querySelector('input[placeholder="用户名"]')).not.toBeNull()
  })

  it('未填写邮箱时给出明确提示', async () => {
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})
    const loginButton = [...container.querySelectorAll('.primary-btn')]
      .find((button) => button.textContent.trim() === '登录')

    loginButton.click()
    await nextTick()

    expect(alertSpy).toHaveBeenCalledWith('请输入邮箱')
  })
})
