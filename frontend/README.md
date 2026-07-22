# DocNexus Web

Vue 3, Pinia, Vue Router, Axios, ECharts, and Vite frontend for DocNexus.

```powershell
npm install
npm run dev
npm run lint
npm run build
```

Development requests use the `/api` Vite proxy configured in `vite.config.js`.
Production requests are same-origin because FastAPI serves the compiled SPA.

Conventions:

- routed screens live in `src/views` and end with `View.vue`;
- reusable UI lives in `src/components`;
- Pinia stores live in `src/stores`;
- HTTP clients live in `src/api`.
