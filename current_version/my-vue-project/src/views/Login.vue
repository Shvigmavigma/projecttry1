<template>
  <div class="auth-form">
    <h2>Вход</h2>
    <form @submit.prevent="handleLogin">
      <input v-model="nickname" placeholder="Никнейм" required />
      <input v-model="password" type="password" placeholder="Пароль" required />
      <button type="submit">Войти</button>
    </form>
    <p>Нет аккаунта? <router-link to="/register">Зарегистрироваться</router-link></p>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useAuthStore } from '../stores/auth';
import { useRouter } from 'vue-router';

const authStore = useAuthStore();
const router = useRouter();
const nickname = ref('');
const password = ref('');

const handleLogin = async () => {
  const success = await authStore.login(nickname.value, password.value);
  if (success) {
    router.push('/main');
  } else {
    alert('Неверный никнейм или пароль');
  }
};
</script>