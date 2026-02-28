<template>
  <div class="main-menu">
    <!-- Шапка с центрированным приветствием и кнопкой профиля справа -->
    <header class="menu-header">
      <div class="header-left"></div> <!-- пустой левый блок для центрирования -->
      <h1 class="welcome-message">
        Добро пожаловать, <span class="username">{{ authStore.user?.nickname }}</span>!
      </h1>
      <button class="profile-button" @click="goTo('profile')">
        Личный кабинет
      </button>
    </header>

    <!-- Основные кнопки меню в виде списка слева -->
    <div class="menu-container">
      <nav class="menu-list">
        <button class="menu-item" @click="goTo('my-projects')">
          Ваши проекты
        </button>
        <button class="menu-item" @click="goTo('users')">
          Список пользователей
        </button>
        <button class="menu-item" @click="goTo('projects')">
          Все проекты
        </button>
      </nav>
    </div>

    <!-- Кнопка выхода -->
    <button class="logout-button" @click="logout">Выйти</button>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '@/stores/auth';
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
.main-menu {
  min-height: 100vh;
  background: linear-gradient(135deg, #f0f9f0 0%, #d4eed7 100%);
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  padding: 2rem;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

/* Шапка: сетка для центрирования приветствия */
.menu-header {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  margin-bottom: 3rem;
  gap: 1rem;
}


.welcome-message {
  font-size: 2rem;
  font-weight: 400;
  color: #2c5e2e;
  margin: 0;
  text-shadow: 1px 1px 2px rgba(255,255,255,0.8);
  text-align: center;
}

.username {
  font-weight: 500;
  color: #1f4f22;
  /* убран фон и паддинг */
}

/* Кнопка личного кабинета справа сверху */
.profile-button {
  background: white;
  border: none;
  border-radius: 40px;
  padding: 0.8rem 1.8rem;
  font-size: 1.1rem;
  font-weight: 500;
  color: #2c5e2e;
  cursor: pointer;
  box-shadow: 0 4px 10px rgba(0,0,0,0.05);
  transition: all 0.2s ease;
  border: 1px solid #b8e0b8;
  justify-self: end; /* прижимаем к правому краю */
}

.profile-button:hover {
  background: #e8ffe8;
  box-shadow: 0 6px 15px rgba(66, 185, 131, 0.2);
  transform: translateY(-2px);
}

/* Контейнер для списка кнопок */
.menu-container {
  flex: 1;
  display: flex;
  justify-content: flex-start;
  align-items: center;
  padding-left: 2rem;
}

.menu-list {
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
  max-width: 400px;
  width: 100%;
}

/* Кнопки меню без иконок */
.menu-item {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(4px);
  border: none;
  border-radius: 16px;
  padding: 1.2rem 2rem;
  font-size: 1.4rem;
  font-weight: 500;
  color: #1e3b1e;
  cursor: pointer;
  box-shadow: 0 8px 20px rgba(0,0,0,0.05);
  transition: all 0.2s ease;
  text-align: left;
  border: 1px solid rgba(255,255,255,0.8);
}

.menu-item:hover {
  background: white;
  box-shadow: 0 12px 28px rgba(66, 185, 131, 0.25);
  transform: translateX(10px) scale(1.02);
  border-color: #b8e0b8;
}

/* Кнопка выхода */
.logout-button {
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid #c8e6c9;
  border-radius: 40px;
  padding: 0.8rem 2rem;
  font-size: 1rem;
  color: #3b5e3b;
  cursor: pointer;
  align-self: flex-end;
  margin-top: 2rem;
  transition: all 0.2s;
  width: fit-content;
}

.logout-button:hover {
  background: #fff;
  color: #c44;
  border-color: #faa;
}
</style>