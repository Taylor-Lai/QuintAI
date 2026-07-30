import { expect, test } from '@playwright/test'

test('首页可以进入用户指南', async ({ page }) => {
  await page.route('**/api/user/profile', (route) => route.fulfill({ status: 401, contentType: 'application/json', body: '{"detail":"unauthorized"}' }))
  await page.goto('/')

  await expect(page).toHaveTitle('慧文融通 - 首页')
  await expect(page.getByText('让复杂文档处理变得简单高效')).toBeVisible()
  await page.getByRole('button', { name: '查看上手指南' }).click()

  await expect(page).toHaveURL(/\/guide$/)
  await expect(page.getByRole('heading', { name: '欢迎使用 慧文融通' })).toBeVisible()
})

test('受保护页面要求登录，登录后返回首页', async ({ page }) => {
  await page.route('**/api/user/profile', (route) => route.fulfill({ status: 401, contentType: 'application/json', body: '{"detail":"unauthorized"}' }))
  await page.route('**/api/auth/login', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        access_token: 'e2e-token',
        token_type: 'bearer',
        user_info: {
          id: 'e2e-user',
          username: '验收用户',
          email: 'e2e@example.com',
          role: '普通用户',
        },
      }),
    })
  })
  await page.route('**/api/auth/heartbeat', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' })
  })

  await page.goto('/workspace')
  await expect(page).toHaveURL(/\/auth$/)

  await page.getByPlaceholder('邮箱').first().fill('e2e@example.com')
  await page.getByPlaceholder('密码').first().fill('test-password')
  await page.getByRole('button', { name: '登录', exact: true }).click()

  await expect(page).toHaveURL(/\/$/)
  await expect(page.getByText('让复杂文档处理变得简单高效')).toBeVisible()
  await expect(page.evaluate(() => localStorage.getItem('sc_token'))).resolves.toBeNull()
})
