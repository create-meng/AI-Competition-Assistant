import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

import App from './App.vue'
import router from './router'
import pinia from './store'
import { useUserStore } from './store/user'

const app = createApp(App)

app.use(pinia)
app.use(router)
app.use(ElementPlus)

// 初始化用户状态
const userStore = useUserStore()
userStore.initFromStorage()

app.mount('#app')

