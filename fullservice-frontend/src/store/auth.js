// Kimlik doğrulama durumu — giriş ekranı bunu kullanır.
//  • token + kullanıcı bilgisi localStorage'da saklanır (sayfa yenilense de oturum sürer).
//  • login(): backend /api/login'e gider (grk_users; DB kapalıysa cpeteam/cpeteam).
//  • logout(): oturumu temizler.
import { defineStore } from 'pinia'
import { login as apiLogin } from '@/services/api'

// Kullanıcıya gösterilecek hata mesajları — kısa, Türkçe, çok detay vermeden,
// gerektiğinde sistem yöneticisine yönlendiren. Teknik detay konsolda kalır.
const ADMIN = 'Lütfen sistem yöneticinize başvurun.'
function mapLoginError(e) {
  const status = e?.response?.status
  if (status === 401) return 'Kullanıcı adı veya şifre hatalı.'
  if (status === 503) return `Veritabanına ulaşılamıyor. ${ADMIN}`
  if (status === 405 || status === 404) return `Sunucu güncel değil. ${ADMIN}`
  if (!e?.response) return `Sunucuya ulaşılamıyor. ${ADMIN}`
  return `Giriş yapılamadı. ${ADMIN}`
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('fs_token') || null,
    user: JSON.parse(localStorage.getItem('fs_user') || 'null'),
    error: null,
    loading: false,
  }),

  getters: {
    isAuthenticated: (s) => !!s.token,
    displayName: (s) =>
      s.user ? `${s.user.name || ''} ${s.user.surname || ''}`.trim() || s.user.username : '',
  },

  actions: {
    async login(username, password) {
      this.loading = true
      this.error = null
      try {
        const data = await apiLogin(username, password)
        this.token = data.token
        this.user = data.user
        localStorage.setItem('fs_token', data.token)
        localStorage.setItem('fs_user', JSON.stringify(data.user))
        return true
      } catch (e) {
        this.error = mapLoginError(e)
        return false
      } finally {
        this.loading = false
      }
    },

    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('fs_token')
      localStorage.removeItem('fs_user')
    },
  },
})
