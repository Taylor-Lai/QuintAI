import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { createApp, nextTick } from 'vue'

import UploadPanel from '../../src/components/UploadPanel.vue'

describe('UploadPanel extraction result', () => {
  let app
  let container
  let setupState

  beforeEach(() => {
    localStorage.clear()
    sessionStorage.clear()
    container = document.createElement('div')
    document.body.appendChild(container)
    app = createApp(UploadPanel, { type: 'doc-extract' })
    app.mount(container)
    setupState = app._instance.setupState
  })

  afterEach(() => {
    app?.unmount()
    container?.remove()
  })

  it('does not render an empty status pill', async () => {
    setupState.resultData = { status: '', extracted_data: { 项目名称: '海岸项目' } }
    await nextTick()
    expect(container.querySelector('.extract-status-badge')).toBeNull()
  })

  it('renders a readable completed status', async () => {
    setupState.resultData = { status: 'succeeded', extracted_data: { 项目名称: '海岸项目' } }
    await nextTick()
    expect(container.querySelector('.extract-status-badge')?.textContent.trim()).toBe('已整理')
  })

  it('does not expose extraction metadata as a business field', async () => {
    setupState.resultData = {
      status: 'succeeded',
      extracted_data: { 项目名称: '海岸项目', _meta: { confidence: 0.9 } }
    }
    await nextTick()
    expect(container.querySelectorAll('.extract-item-card')).toHaveLength(1)
    expect(container.textContent).not.toContain('_meta')
  })

  it('shows readable extraction steps instead of an internal node label', async () => {
    setupState.loading = true
    setupState.completedSteps = 1
    setupState.totalSteps = 5
    await nextTick()

    expect(container.querySelector('.progress-meta')?.textContent).toContain('处理步骤 2 / 5')
    expect(container.querySelector('.progress-steps')?.textContent).toContain('读取文档')
    expect(container.querySelector('.progress-steps')?.textContent).toContain('完成交付')
    expect(container.textContent).not.toContain('真实节点')
  })

  it('shows every real table filling stage in execution order', async () => {
    app.unmount()
    app = createApp(UploadPanel, { type: 'table-fill' })
    app.mount(container)
    setupState = app._instance.setupState
    setupState.loading = true
    setupState.completedSteps = 7
    setupState.totalSteps = 12
    await nextTick()

    const steps = container.querySelector('.progress-steps')?.textContent || ''
    expect(container.querySelector('.progress-meta')?.textContent).toContain('处理步骤 8 / 12')
    expect(steps).toContain('准备任务')
    expect(steps).toContain('计算并写入')
    expect(steps).toContain('生成报告')
    expect(steps).toContain('完成交付')
  })
})
