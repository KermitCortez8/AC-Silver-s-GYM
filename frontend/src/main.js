import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './style.css'
import App from './App.vue'
import router from './router'
import { APP_CONFIG } from './config/appConfig'
import { initializeTheme } from './composables/useTheme'
import { useAuthStore } from './stores/authStore'
import { useGymStore } from './stores/gymStore'

initializeTheme()

const app = createApp(App)

const pinia = createPinia()
app.use(pinia)
app.use(router)

// Los visitantes usan únicamente los endpoints públicos de cada vista.
// La sincronización completa requiere una sesión autenticada.
const auth = useAuthStore()
auth.initializeAuth().then(() => {
	if (APP_CONFIG.authApiBaseUrl && auth.isAuthenticated) {
		try {
			const gym = useGymStore()
			gym.fetchFromBackend().catch((err) => console.warn('Error sync datos remotos:', err))
		} catch (e) {
			console.warn('No se pudo inicializar sincronización con backend', e)
		}
	}
})

app.mount('#app')
