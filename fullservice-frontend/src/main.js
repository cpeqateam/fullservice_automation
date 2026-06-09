// Uygulama girişi — Vue + Pinia + Vuetify + global SCSS.
import { createApp } from 'vue'
import App from './App.vue'
import pinia from './store'
import vuetify from './plugins/vuetify'

import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'
import './assets/styles/main.scss'

createApp(App).use(pinia).use(vuetify).mount('#app')
