import { installServices } from './bootstrap.js'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './presentation/style.css'
import './presentation/styles/workspace.css'
import './presentation/styles/inventory-store.css'
import App from './presentation/App.vue'
import router from './presentation/router'
import { initializeTheme } from './presentation/composables/useTheme'


const app = createApp(App)

const pinia = createPinia()
installServices(pinia)
app.use(pinia)
initializeTheme()
app.use(router)

// El guard del router valida la sesión; cada vista solicita sus datos al montar.

app.mount('#app')
