// Backend HTTP istemcisi. Sunucu dashboard'ı statik servis ettiği için
// göreceli yol kullanıyoruz (`/api/...`). Dev modda Vite proxy aynı yolu
// `http://localhost:8770`'e iletir.
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 8000,
})

// Kullanıcı girişi — grk_users'tan doğrulanır; DB kapalıysa cpeteam/cpeteam her zaman geçerli.
export const login = (username, password) =>
  api.post('/login', { username, password }).then((r) => r.data)

export const fetchState = () => api.get('/state').then((r) => r.data)

export const startSession = (overrides) => api.post('/session/start', overrides).then((r) => r.data)

export const stopSession = () => api.post('/session/stop').then((r) => r.data)

// Her şeyi başa al (testleri durdur + oturum/ilerleme sıfırla)
export const resetSession = () => api.post('/session/reset').then((r) => r.data)

// Aktif bağlantı kontrolü — her düğümün anlık erişilebilirliği (kırmızı/yeşil)
export const healthCheck = () => api.get('/health-check').then((r) => r.data)

// ── Firmware DB (Marka / Model / Firmware) ────────────────────────────────
// DB erişilemezse istek 503 fırlatır; çağıran taraf serbest-metin'e düşer.
export const getBrandsRaw = () => api.get('/firmware/brands').then((r) => r.data)
export const getModels    = (brand) => api.get(`/firmware/models/${encodeURIComponent(brand)}`).then((r) => r.data)
export const getVersions  = (brand, model) =>
  api.get(`/firmware/versions/${encodeURIComponent(brand)}/${encodeURIComponent(model)}`).then((r) => r.data)

// Tüm markaları her birinin model listesiyle birleştirir (GRK getBrands deseni).
export const getBrands = async () => {
  const brands = await getBrandsRaw()
  const result = []
  for (const brand of brands) {
    const models = await getModels(brand)
    result.push({ title: brand, value: brand, models })
  }
  return result
}

export default api
