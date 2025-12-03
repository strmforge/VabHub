/**
 * VabHub 前端应用入口
 * 现代化、美观的WebUI
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import vuetify from './plugins/vuetify'
import { createI18n } from 'vue-i18n'
import Toast from 'vue-toastification'
import 'vue-toastification/dist/index.css'
import './styles/main.scss'
import './styles/novel-reader.scss'

// 国际化（暂时简化，后续完善）
const i18n = createI18n({
  locale: 'zh-CN',
  fallbackLocale: 'en',
  messages: {
    'zh-CN': {},
    'en': {}
  },
  legacy: false
})

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(vuetify)
app.use(i18n)
app.use(Toast, {
  transition: 'Vue-Toastification__bounce',
  maxToasts: 5,
  newestOnTop: true
})

app.mount('#app')

