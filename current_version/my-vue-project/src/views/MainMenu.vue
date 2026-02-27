<template>
  <div class="main-menu">
    <h1>Добро пожаловать, {{ authStore.user?.nickname }}</h1>
    <div class="menu-grid">
      <button @click="goTo('my-projects')">📁 Ваши проекты</button>
      <button @click="goTo('users')">👥 Список пользователей</button>
      <button @click="goTo('projects')">📋 Все проекты</button>
      <button @click="goTo('profile')">👤 Личный кабинет</button>
    </div>
    <button class="logout" @click="logout">Выйти</button>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '../stores/auth';
import { useRouter } from 'vue-router';

const authStore = useAuthStore();
const router = useRouter();

const goTo = (route: string) => {
  router.push(`/${route}`);
};

const logout = () => {
  authStore.logout();
  router.push('/login');
};
</script>

<style scoped>
.main-menu { text-align: center; padding: 2rem; }
.menu-grid { display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; margin: 2rem 0; }
.menu-grid button { padding: 1rem 2rem; font-size: 1.2rem; cursor: pointer; }
.logout { background: #ff4444; color: white; border: none; padding: 0.5rem 1rem; border-radius: 4px; }
</style>