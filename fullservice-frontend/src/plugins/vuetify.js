// Vuetify yapılandırması — Türk Telekom kimliğine yakın dark/light tema.
// Birincil renk Türk Telekom mavisi; karanlık modda glass-card görünümü
// için arka plan transparant tutuluyor (LiquidBackground altta).
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { aliases, mdi } from 'vuetify/iconsets/mdi'

// Türk Telekom mavisi paleti
const TT_BLUE       = '#0A84FF'   // birincil — canlı kurumsal mavi
const TT_BLUE_DEEP  = '#0050C8'   // ikincil — daha koyu mavi
const TT_BLUE_LIGHT = '#5AC8FA'   // vurgu — açık mavi / camgöbeği

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
          primary: TT_BLUE,
          secondary: TT_BLUE_DEEP,
          accent: TT_BLUE_LIGHT,
          success: '#30D158',
          warning: '#FF9F0A',
          error:   '#FF453A',
          info:    '#5AC8FA',
          background: '#0A0E16',
          surface:    '#141A24',
        },
      },
      light: {
        dark: false,
        colors: {
          primary: TT_BLUE,
          secondary: TT_BLUE_DEEP,
          accent: TT_BLUE_LIGHT,
          success: '#2EA043',
          warning: '#D29922',
          error:   '#DA3633',
          info:    '#0050C8',
          background: '#F4F7FB',
          surface:    '#FFFFFF',
        },
      },
    },
  },
})
