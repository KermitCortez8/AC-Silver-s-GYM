import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './style.css'
import App from './App.vue'
import router from './router'
import { initializeTheme } from './composables/useTheme'

initializeTheme()

const app = createApp(App)

const pinia = createPinia()
app.use(pinia)
app.use(router)

// El guard del router valida la sesión; cada vista solicita sus datos al montar.

app.mount('#app')
