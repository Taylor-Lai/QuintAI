# 慧文融通 Web 前端

Web 客户端基于 Vue 3、Pinia、Vue Router、Axios、ECharts、fflate 和 Vite，覆盖认证、三类文档能力、任务中心、文档工作台和企业管理功能。

桌面端使用完整顶部导航；900px 以下提供独立移动导航菜单，覆盖首页、工作台、三类文档能力、模板库、在线编辑和上手指南。修改公共导航或响应式样式后，应至少在 390×844 和 1280×720 两种视口回归。

## 开发

```powershell
npm install
npm run dev
```

开发环境通过 `vite.config.js` 中的 `/api` 代理访问本地后端。生产环境由 FastAPI 提供编译后的单页应用，因此浏览器与 API 使用同源请求。

## 质量检查

```powershell
npm run lint
npm run build
npm audit --omit=dev
```

当前仓库尚未引入 Web 组件测试框架，发布前除 lint 和生产构建外，还必须按[人工验收套件](../tests/manual/README.md)在真实浏览器中执行核心流程。依赖审计会向 npm registry 发送依赖清单，应在允许联网的受控环境中运行。

## 目录约定

- `src/views`：路由页面，文件名以 `View.vue` 结尾；
- `src/components`：可复用界面组件；
- `src/stores`：Pinia 状态与业务动作；
- `src/api`：HTTP 客户端和接口封装；
- `src/router`：路由、鉴权与页面入口。

页面不应直接散落请求地址或令牌逻辑。公开接口变更必须同步检查 Android 调用方和后端契约测试。

更多内容见[仓库工程规范](../docs/development/conventions.md)和[系统架构](../docs/architecture/overview.md)。
