import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import pinia from './stores'
import { useUserStore } from './stores/user'

const app = createApp(App)

app.use(pinia)
app.use(router)
app.mount('#app')

const userStore = useUserStore(pinia)
if (userStore.isLogin) userStore.startHeartbeat()
