// src/api/axios.ts
import axios from 'axios'

// Настройка базового URL
axios.defaults.baseURL = 'http://localhost:8000'

// Добавляем перехватчик для автоматического обновления токена
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      
      try {
        const refreshToken = localStorage.getItem('refresh_token')
        const response = await axios.post('/auth/refresh', {
          refresh_token: refreshToken
        })
        
        const { access_token, refresh_token: newRefreshToken } = response.data
        
        localStorage.setItem('access_token', access_token)
        localStorage.setItem('refresh_token', newRefreshToken)
        
        axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
        originalRequest.headers['Authorization'] = `Bearer ${access_token}`
        
        return axios(originalRequest)
      } catch (refreshError) {
        // Если не удалось обновить токен, перенаправляем на страницу входа
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        delete axios.defaults.headers.common['Authorization']
        window.location.href = '/login'
      }
    }
    
    return Promise.reject(error)
  }
)

export default axios