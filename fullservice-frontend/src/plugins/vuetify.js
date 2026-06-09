// Vuetify yapılandırması — Türk Telekom kimliğine yakın dark/light tema.
// Magenta birincil renk, mavi ikincil; karanlık modda glass-card görünümü
// için arka plan transparant tutuluyor (LiquidBackground altta).
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { aliases, mdi } from 'vuetify/iconsets/mdi'

const TT_MAGENTA = '#E20074'
const TT_MAGENTA_LIGHT = '#FF4FAA'

export default createVuetify({
  components,
  directives,
  icons: { defaultSet: 'mdi', aliases, sets: { mdi } },
  theme: {
    defaultTheme: localStorage.getItem('fs_theme') === 'light' ? 'light' : 'dark',
    themes: {
      dark: {
        dark: true,
        colors: {
          primary: TT_MAGENTA,
          secondary: '#0A84FF',
          accent: TT_MAGENTA_LIGHT,
          success: '#30D158',
          warning: '#FF9F0A',
          error:   '#FF453A',
          info:    '#5E5CE6',
          background: '#0A0A12',
          surface:    '#16161E',
        },
      },
      light: {
        dark: false,
        colors: {
          primary: TT_MAGENTA,
          secondary: '#0A84FF',
          accent: TT_MAGENTA_LIGHT,
          success: '#2EA043',
          warning: '#D29922',
          error:   '#DA3633',
          info:    '#5E5CE6',
          background: '#F6F6F9',
          surface:    '#FFFFFF',
        },
      },
    },
  },
})
