<template>
  <div class="auth-form">
    <h2>Регистрация</h2>
    <form @submit.prevent="handleRegister">
      <input v-model="form.nickname" placeholder="Никнейм" required />
      <input v-model="form.fullname" placeholder="Полное имя" required />
      <input v-model="form.email" type="email" placeholder="Email" required />
      <input v-model="form.class_" step="0.1" placeholder="Класс (например, 11.0)" />
      <input v-model="form.speciality" placeholder="Специальность" />
      <input v-model="form.password" type="password" placeholder="Пароль" required />
      <button type="submit">Зарегистрироваться</button>
    </form>
    <p>Уже есть аккаунт? <router-link to="/login">Войти</router-link></p>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

interface RegisterForm {
  nickname: string;
  fullname: string;
  email: string;
  class_: number;      // в форме используем class_, но API ожидает class
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
  // Преобразуем поле class_ в class для отправки на бэкенд
  const { class_, ...rest } = form;
  const userData = {
    ...rest,
    class: class_,     // теперь поле называется class
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
.auth-form {
  max-width: 400px;
  margin: 2rem auto;
  padding: 2rem;
  border: 1px solid #ccc;
  border-radius: 8px;
  background: #fff;
}
.auth-form h2 {
  text-align: center;
  margin-bottom: 1.5rem;
}
.auth-form input {
  display: block;
  width: 100%;
  padding: 0.5rem;
  margin-bottom: 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}
.auth-form button {
  width: 100%;
  padding: 0.75rem;
  background: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
.auth-form button:hover {
  background: #3aa876;
}
.auth-form p {
  text-align: center;
  margin-top: 1rem;
}
</style>