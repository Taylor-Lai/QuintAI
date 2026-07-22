# QuintAI 前端

基于 Vue 3、Pinia、Vue Router、Axios、ECharts 和 Vite 构建的 Web 前端。

```powershell
npm install
npm run dev
npm run lint
npm run build
```

开发环境通过 `vite.config.js` 中配置的 `/api` 代理访问后端。生产环境由
FastAPI 提供编译后的单页应用，因此前后端使用同源请求。

目录约定：

- 路由页面位于 `src/views`，文件名以 `View.vue` 结尾；
- 可复用界面组件位于 `src/components`；
- Pinia Store 位于 `src/stores`；
- HTTP 客户端位于 `src/api`。

许可证： [MIT License](../LICENSE)。
