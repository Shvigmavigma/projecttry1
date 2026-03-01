<template>
  <div class="register-page">
    <div class="theme-toggle-container">
      <ThemeToggle />
    </div>
    <div class="register-card">
      <h2>Регистрация</h2>
      <form @submit.prevent="handleRegister">
        <div class="form-group">
          <label for="nickname">Никнейм</label>
          <input id="nickname" v-model="form.nickname" type="text" placeholder="Введите никнейм" required />
        </div>

        <div class="form-group">
          <label for="fullname">Полное имя</label>
          <input id="fullname" v-model="form.fullname" type="text" placeholder="Введите полное имя" required />
        </div>

        <div class="form-group">
          <label for="email">Email</label>
          <input id="email" v-model="form.email" type="email" placeholder="Введите email" required />
        </div>

        <div class="form-group">
          <label for="class">Класс</label>
          <input id="class" v-model.number="form.class_" type="number" step="0.1" placeholder="11.0" />
        </div>

        <div class="form-group">
          <label for="speciality">Специальность</label>
          <input id="speciality" v-model="form.speciality" type="text" placeholder="Например, информатика" />
        </div>

        <div class="form-group">
          <label for="password">Пароль</label>
          <input id="password" v-model="form.password" type="password" placeholder="Введите пароль" required />
        </div>

        <button type="submit" class="register-button">Зарегистрироваться</button>
      </form>

      <p class="login-link">
        Уже есть аккаунт? <router-link to="/login">Войти</router-link>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import ThemeToggle from '@/components/ThemeToggle.vue';

interface RegisterForm {
  nickname: string;
  fullname: string;
  email: string;
  class_: number;
  speciality: string;
  password: string;
}

const authStore = useAuthStore();
const router = useRouter();
const form = reactive<RegisterForm>({
  nickname: '',
  fullname: '',
  email: '',
  class_: 0,
  speciality: '',
  password: '',
});

const handleRegister = async () => {
  const { class_, ...rest } = form;
  const userData = {
    ...rest,
    class: class_,
    password: form.password,
  };

  const success = await authStore.register(userData);
  if (success) {
    router.push('/main');
  } else {
    alert('Ошибка регистрации. Возможно, пользователь с таким никнеймом уже существует.');
  }
};
</script>

<style scoped>
.register-page {
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

.register-card {
  background: var(--bg-card);
  border-radius: 16px;
  box-shadow: var(--shadow-strong);
  padding: 40px 32px;
  width: 100%;
  max-width: 450px;
  transition: transform 0.2s ease, background 0.3s;
}

.register-card:hover {
  transform: translateY(-4px);
}

h2 {
  text-align: center;
  color: var(--heading-color);
  margin-bottom: 28px;
  font-weight: 500;
}

.form-group {
  margin-bottom: 16px;
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

.register-button {
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
  margin-top: 16px;
}

.register-button:hover {
  background-color: var(--accent-hover);
}

.register-button:active {
  transform: scale(0.98);
}

.login-link {
  text-align: center;
  margin-top: 20px;
  color: var(--text-secondary);
  font-size: 0.95rem;
}

.login-link a {
  color: var(--link-color);
  text-decoration: none;
  font-weight: 500;
}

.login-link a:hover {
  color: var(--link-hover);
  text-decoration: underline;
}
</style>