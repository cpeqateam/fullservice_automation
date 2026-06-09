// Backend HTTP istemcisi. Sunucu dashboard'ı statik servis ettiği için
// göreceli yol kullanıyoruz (`/api/...`). Dev modda Vite proxy aynı yolu
// `http://localhost:8770`'e iletir.
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 8000,
})

export const fetchState = () => api.get('/state').then((r) => r.data)

export const startSession = (overrides) => api.post('/session/start', overrides).then((r) => r.data)

export const stopSession = () => api.post('/session/stop').then((r) => r.data)

export default api
