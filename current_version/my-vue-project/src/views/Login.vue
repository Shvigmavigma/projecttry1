<template>
  <div class="login-page">
    <div class="theme-toggle-container">
      <ThemeToggle />
    </div>
    <div class="login-card">
      <h2>Вход в систему</h2>
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="nickname">Никнейм или Email</label>
          <input
            id="nickname"
            v-model="nickname"
            type="text"
            placeholder="Введите никнейм или почту"
            required
          />
        </div>

        <div class="form-group">
          <label for="password">Пароль</label>
          <input
            id="password"
            v-model="password"
            type="password"
            placeholder="Введите пароль"
            required
          />
        </div>

        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>

        <button type="submit" class="login-button" :disabled="loading">
          {{ loading ? 'Вход...' : 'Войти' }}
        </button>
      </form>

      <p class="register-link">
        Нет аккаунта? <router-link to="/register">Зарегистрироваться</router-link>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router';
import ThemeToggle from '@/components/ThemeToggle.vue';
import axios from 'axios';

const authStore = useAuthStore();
const router = useRouter();
const nickname = ref('');
const password = ref('');
const loading = ref(false);
const errorMessage = ref('');

const handleLogin = async () => {
  if (!nickname.value || !password.value) {
    errorMessage.value = 'Заполните все поля';
    return;
  }

  loading.value = true;
  errorMessage.value = '';

  try {
    // Отправляем запрос на новый эндпоинт /auth/login
    const response = await axios.post('http://localhost:8000/auth/login', {
      nickname: nickname.value,
      password: password.value
    });

    // Сохраняем токены
    const { access_token, refresh_token } = response.data;
    
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    
    // Настраиваем axios для автоматической отправки токена
    axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
    
    // Получаем данные пользователя
    const userResponse = await axios.get('http://localhost:8000/users/me');
    authStore.user = userResponse.data;
    
    // Перенаправляем на главную
    router.push('/main');
    
  } catch (error: any) {
    console.error('Login error:', error);
    
    if (error.code === 'ERR_NETWORK') {
      errorMessage.value = 'Ошибка сети. Проверьте подключение к серверу.';
    } else if (error.response) {
      // Обработка разных статусов ошибок
      switch (error.response.status) {
        case 401:
          errorMessage.value = 'Неверный логин или пароль';
          break;
        case 403:
          errorMessage.value = 'Email не подтвержден. Проверьте почту.';
          break;
        default:
          errorMessage.value = error.response.data?.detail || 'Ошибка при входе';
      }
    } else {
      errorMessage.value = error.message || 'Произошла ошибка';
    }
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-page {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: var(--bg-page);
  margin: -20px;
  padding: 20px;
  position: relative;
  transition: background 0.3s;
}

.theme-toggle-container {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 10;
}

.login-card {
  background: var(--bg-card);
  border-radius: 16px;
  box-shadow: var(--shadow-strong);
  padding: 40px 32px;
  width: 100%;
  max-width: 400px;
  transition: transform 0.2s ease, background 0.3s;
}

.login-card:hover {
  transform: translateY(-4px);
}

h2 {
  text-align: center;
  color: var(--heading-color);
  margin-bottom: 28px;
  font-weight: 500;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 6px;
  color: var(--text-secondary);
  font-size: 0.9rem;
  font-weight: 500;
}

input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid var(--input-border);
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.2s, box-shadow 0.2s;
  outline: none;
  box-sizing: border-box;
  background: var(--input-bg);
  color: var(--text-primary);
}

input:focus {
  border-color: var(--accent-color);
  box-shadow: 0 0 0 3px rgba(66, 185, 131, 0.2);
}

.dark-theme input:focus {
  box-shadow: 0 0 0 3px rgba(1, 69, 172, 0.2);
}

.error-message {
  background: var(--error-bg);
  color: var(--danger-color);
  padding: 10px;
  border-radius: 8px;
  margin-bottom: 20px;
  text-align: center;
  border: 1px solid var(--danger-color);
  font-size: 0.9rem;
}

.login-button {
  width: 100%;
  padding: 14px;
  background-color: var(--accent-color);
  color: var(--button-text);
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s, transform 0.1s;
  margin-top: 8px;
}

.login-button:hover:not(:disabled) {
  background-color: var(--accent-hover);
}

.login-button:active:not(:disabled) {
  transform: scale(0.98);
}

.login-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.register-link {
  text-align: center;
  margin-top: 24px;
  color: var(--text-secondary);
  font-size: 0.95rem;
}

.register-link a {
  color: var(--link-color);
  text-decoration: none;
  font-weight: 500;
}

.register-link a:hover {
  color: var(--link-hover);
  text-decoration: underline;
}
</style>