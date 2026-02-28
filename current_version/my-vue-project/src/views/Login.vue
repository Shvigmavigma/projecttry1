<template>
  <div class="login-page">
    <div class="login-card">
      <h2>Вход в систему</h2>
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="nickname">Никнейм</label>
          <input
            id="nickname"
            v-model="nickname"
            type="text"
            placeholder="Введите никнейм"
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

        <button type="submit" class="login-button">Войти</button>
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

const authStore = useAuthStore();
const router = useRouter();
const nickname = ref('');
const password = ref('');

const handleLogin = async () => {
  try {
    const success = await authStore.login(nickname.value, password.value);
    if (success) {
      router.push('/main');
    } else {
      alert('Неверный никнейм или пароль');
    }
  } catch (error: any) {
    alert('Ошибка: ' + (error.response?.data?.detail || error.message));
  }
};
</script>

<style scoped>
.login-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #e8f5e9; /* светло-зелёный фон */
  margin: -20px; /* компенсируем отступы body из App.vue */
  padding: 20px;
}

.login-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
  padding: 40px 32px;
  width: 100%;
  max-width: 400px;
  transition: transform 0.2s ease;
}

.login-card:hover {
  transform: translateY(-4px);
}

h2 {
  text-align: center;
  color: #2c3e50;
  margin-bottom: 28px;
  font-weight: 500;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 6px;
  color: #4a5568;
  font-size: 0.9rem;
  font-weight: 500;
}

input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #cbd5e0;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.2s, box-shadow 0.2s;
  outline: none;
  box-sizing: border-box;
}

input:focus {
  border-color: #42b983;
  box-shadow: 0 0 0 3px rgba(66, 185, 131, 0.2);
}

.login-button {
  width: 100%;
  padding: 14px;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s, transform 0.1s;
  margin-top: 8px;
}

.login-button:hover {
  background-color: #3aa876;
}

.login-button:active {
  transform: scale(0.98);
}

.register-link {
  text-align: center;
  margin-top: 24px;
  color: #4a5568;
  font-size: 0.95rem;
}

.register-link a {
  color: #42b983;
  text-decoration: none;
  font-weight: 500;
}

.register-link a:hover {
  text-decoration: underline;
}
</style>