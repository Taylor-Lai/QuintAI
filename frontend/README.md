# 慧文融通 Web 前端

Web 客户端基于 Vue 3、Pinia、Vue Router、Axios、fflate 和 Vite，覆盖认证、三类文档能力、任务中心、文档工作台和企业管理功能。

桌面端采用完整顶部导航；视口宽度低于 900px 时启用独立移动导航，覆盖首页、工作台、三类文档能力、模板库、在线编辑和上手指南。公共导航或响应式样式发生变更后，至少应在 390×844 与 1280×720 两种视口下完成回归验证。

## 开发

```powershell
npm install
npm run dev
```

开发环境通过 `vite.config.js` 中的 `/api` 代理访问本地后端。生产环境由 FastAPI 提供编译后的单页应用，因此浏览器与 API 使用同源请求。

## 质量检查

```powershell
npm run lint
npm run test:unit
npm run build
npm audit
npx playwright install chromium
npm run test:e2e
```

组件测试使用 Vitest 和 jsdom，覆盖组件渲染、表单交互、路由与登录状态分支。浏览器测试使用 Playwright，在桌面 Chromium 和 Pixel 7 移动视口中验证首页、指南、路由保护和登录流程；GitHub CI 会在每次推送和拉取请求中持续执行。

首次执行浏览器测试前，须通过 `npx playwright install chromium` 安装测试浏览器。自动化测试不替代涉及真实模型、文件交付物与发布环境的[真实材料验收](../tests/manual/README.md)和客户端人工核验。依赖安装与安全审计会向 npm registry 提交依赖元数据，应在获准联网的受控环境中执行。

## 目录约定

- `src/views`：路由页面，文件名以 `View.vue` 结尾；
- `src/components`：可复用界面组件；
- `src/stores`：Pinia 状态与业务动作；
- `src/api`：HTTP 客户端和接口封装；
- `src/router`：路由、鉴权与页面入口。
- `tests/unit`：无需后端的组件级测试；
- `tests/e2e`：由 Playwright 执行的核心浏览器流程。

页面组件不得分散维护请求地址或令牌处理逻辑。公开接口发生变更时，必须同步验证 Android 调用方与后端契约测试。

更多内容见[仓库工程规范](../docs/development/conventions.md)和[系统架构](../docs/architecture/overview.md)。
