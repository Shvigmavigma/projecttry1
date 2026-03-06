<template>
  <div class="verify-page">
    <div class="theme-toggle-container">
      <ThemeToggle />
    </div>
    <div class="verify-card">
      <h2>Подтверждение email</h2>
      
      <div v-if="verifying" class="loading">
        Подтверждение...
      </div>
      
      <div v-else-if="success" class="success">
        ✅ Регистрация успешно завершена!
        <p>Сейчас вы будете перенаправлены на страницу входа...</p>
      </div>
      
      <div v-else-if="error" class="error">
        ❌ {{ error }}
        <p v-if="errorDetails" class="error-details">{{ errorDetails }}</p>
        <button @click="goBack" class="back-button">Вернуться к регистрации</button>
      </div>
      
      <div v-else>
        <p>Введите код подтверждения, отправленный на</p>
        <p class="email-highlight">{{ email }}</p>
        
        <div class="form-group">
          <input
            v-model="code"
            type="text"
            placeholder="6-значный код"
            maxlength="6"
            @keyup.enter="verifyCode"
          />
        </div>
        
        <button @click="verifyCode" :disabled="verifying">
          {{ verifying ? 'Проверка...' : 'Подтвердить и завершить регистрацию' }}
        </button>
        
        <p class="resend">
          <a href="#" @click.prevent="resendCode">Отправить код повторно</a>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import ThemeToggle from '@/components/ThemeToggle.vue'

const route = useRoute()
const router = useRouter()
const email = ref(route.query.email || '')
const code = ref('')
const verifying = ref(false)
const success = ref(false)
const error = ref('')
const errorDetails = ref('')

onMounted(() => {
  const pendingData = sessionStorage.getItem('pending_registration')
  console.log('Проверка sessionStorage на VerifyEmail:', pendingData ? 'Данные найдены' : 'Данные не найдены')
  
  if (!pendingData) {
    error.value = 'Данные регистрации не найдены'
    errorDetails.value = 'Пожалуйста, начните регистрацию заново'
  }
})

async function verifyCode() {
  if (!code.value || code.value.length !== 6) {
    error.value = 'Введите 6-значный код'
    return
  }
  
  const pendingData = sessionStorage.getItem('pending_registration')
  if (!pendingData) {
    error.value = 'Данные регистрации не найдены'
    errorDetails.value = 'Пожалуйста, вернитесь на страницу регистрации'
    return
  }
  
  verifying.value = true
  error.value = ''
  errorDetails.value = ''
  
  try {
    const userData = JSON.parse(pendingData)
    console.log('Данные пользователя из sessionStorage:', userData)
    
    const response = await axios.post(
      'http://localhost:8000/auth/register-with-verification',
      {
        email: email.value,
        code: code.value,
        user_data: userData
      }
    )
    
    console.log('Пользователь успешно создан:', response.data)
    
    // Если была аватарка - загружаем её
    const pendingAvatar = sessionStorage.getItem('pending_avatar')
    if (pendingAvatar && response.data.id) {
      try {
        const blob = await fetch(pendingAvatar).then(res => res.blob())
        const file = new File([blob], 'avatar.webp', { type: 'image/webp' })
        
        const formData = new FormData()
        formData.append('file', file)
        
        await axios.post(
          `http://localhost:8000/users/${response.data.id}/avatar`,
          formData,
          { headers: { 'Content-Type': 'multipart/form-data' } }
        )
        console.log('Аватарка загружена')
      } catch (avatarError) {
        console.error('Ошибка загрузки аватарки:', avatarError)
      }
    }
    
    sessionStorage.removeItem('pending_registration')
    sessionStorage.removeItem('pending_avatar')
    
    success.value = true
    setTimeout(() => router.push('/login'), 3000)
    
  } catch (err: any) {
    console.error('Ошибка верификации:', err)
    
    if (err.code === 'ERR_NETWORK') {
      error.value = 'Ошибка сети. Проверьте подключение к серверу.'
    } else if (err.response) {
      error.value = err.response.data?.detail || 'Ошибка сервера'
      errorDetails.value = JSON.stringify(err.response.data)
    } else {
      error.value = err.message || 'Неизвестная ошибка'
    }
  } finally {
    verifying.value = false
  }
}

async function resendCode() {
  verifying.value = true
  error.value = ''
  try {
    await axios.post('http://localhost:8000/auth/request-verification-code', {
      email: email.value
    })
    alert('Код отправлен повторно')
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Ошибка при отправке кода'
  } finally {
    verifying.value = false
  }
}

function goBack() {
  router.push('/register')
}
</script>

<style scoped>
.verify-page {
  min-height: 100vh;
  background: var(--bg-page);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  position: relative;
}

.theme-toggle-container {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 10;
}

.verify-card {
  background: var(--bg-card);
  border-radius: 16px;
  padding: 40px;
  max-width: 400px;
  width: 90%;
  box-shadow: var(--shadow-strong);
}

h2 {
  color: var(--heading-color);
  margin-bottom: 20px;
  text-align: center;
}

.email-highlight {
  font-weight: bold;
  color: var(--accent-color);
  text-align: center;
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 20px;
}

input {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--input-border);
  border-radius: 8px;
  font-size: 18px;
  text-align: center;
  background: var(--input-bg);
  color: var(--text-primary);
  outline: none;
}

input:focus {
  border-color: var(--accent-color);
  box-shadow: 0 0 0 3px rgba(66, 185, 131, 0.2);
}

button {
  width: 100%;
  padding: 14px;
  background: var(--accent-color);
  color: var(--button-text);
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

button:hover:not(:disabled) {
  background: var(--accent-hover);
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.back-button {
  margin-top: 15px;
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.success {
  color: #4caf50;
  text-align: center;
  padding: 20px;
}

.error {
  color: #f44336;
  text-align: center;
  padding: 20px;
}

.error-details {
  font-size: 0.85rem;
  background: rgba(244, 67, 54, 0.1);
  padding: 10px;
  border-radius: 8px;
  margin-top: 10px;
  word-break: break-word;
}

.resend {
  text-align: center;
  margin-top: 20px;
}

.resend a {
  color: var(--link-color);
  text-decoration: none;
}

.resend a:hover {
  text-decoration: underline;
}

.loading {
  text-align: center;
  color: var(--text-secondary);
  padding: 20px;
}
</style>