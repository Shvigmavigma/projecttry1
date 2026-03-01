<template>
  <div class="profile-page">
    <!-- Кнопки в правом верхнем углу -->
    <div class="header-actions">
      <ThemeToggle />
      <button class="home-button" @click="goToMain" title="Главное меню">🏠</button>
    </div>

    <div class="profile-card">
      <!-- Заголовок с иконкой -->
      <div class="profile-header">
        <span class="avatar">👤</span>
        <h2>Личный кабинет</h2>
      </div>

      <!-- Информация о пользователе -->
      <div v-if="user" class="profile-info">
        <div class="info-row">
          <span class="info-label">Никнейм</span>
          <span class="info-value">{{ user.nickname }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Полное имя</span>
          <span class="info-value">{{ user.fullname }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Email</span>
          <span class="info-value">{{ user.email }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Класс</span>
          <span class="info-value">{{ user.class }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Специальность</span>
          <span class="info-value">{{ user.speciality || 'не указана' }}</span>
        </div>
      </div>

      <!-- Заглушка, если пользователь не загружен -->
      <div v-else class="loading">
        Загрузка данных...
      </div>

      <!-- Кнопка редактирования -->
      <button class="edit-button" @click="editProfile">Редактировать профиль</button>

      <!-- Кнопка выхода -->
      <button class="logout-button" @click="logout">Выйти</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router';
import ThemeToggle from '@/components/ThemeToggle.vue';

const authStore = useAuthStore();
const router = useRouter();
const user = computed(() => authStore.user);

const editProfile = () => {
  router.push('/profile/edit');
};

const goToMain = () => {
  router.push('/main');
};

const logout = () => {
  if (confirm('Вы уверены, что хотите выйти?')) {
    authStore.logout();
    router.push('/login');
  }
};
</script>

<style scoped>
.profile-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: var(--bg-page);
  margin: -20px;
  padding: 20px;
  position: relative;
  transition: background 0.3s;
}

/* Контейнер для кнопок в правом верхнем углу */
.header-actions {
  position: absolute;
  top: 30px;
  right: 30px;
  display: flex;
  gap: 10px;
  z-index: 10;
}

.home-button {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 50%;
  width: 50px;
  height: 50px;
  font-size: 28px;
  cursor: pointer;
  box-shadow: var(--shadow);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  color: var(--text-primary);
}

.home-button:hover {
  background: var(--bg-card);
  transform: scale(1.1) translateY(-2px);
  box-shadow: var(--shadow-strong);
}

.profile-card {
  background: var(--bg-card);
  border-radius: 32px;
  box-shadow: var(--shadow-strong);
  padding: 40px;
  width: 100%;
  max-width: 500px;
  transition: transform 0.2s, background 0.3s;
  overflow: hidden;
}

.profile-card:hover {
  transform: translateY(-5px);
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 32px;
}

.avatar {
  font-size: 48px;
  background: var(--bg-page);
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--heading-color);
}

.profile-header h2 {
  font-size: 2rem;
  color: var(--heading-color);
  margin: 0;
  font-weight: 500;
  overflow-wrap: break-word;
  word-wrap: break-word;
  hyphens: auto;
  max-width: calc(100% - 96px);
}

.profile-info {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 32px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border-color);
  overflow-wrap: break-word;
  word-wrap: break-word;
  gap: 10px;
}

.info-label {
  font-weight: 600;
  color: var(--text-secondary);
  font-size: 1rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  min-width: 120px;
  flex-shrink: 0;
}

.info-value {
  color: var(--text-primary);
  font-size: 1.1rem;
  text-align: right;
  overflow-wrap: break-word;
  word-wrap: break-word;
  hyphens: auto;
  flex: 1;
  min-width: 0;
}

.loading {
  text-align: center;
  color: var(--text-secondary);
  padding: 20px;
  font-style: italic;
}

.edit-button {
  width: 100%;
  padding: 14px;
  background-color: var(--accent-color);
  color: var(--button-text);
  border: none;
  border-radius: 50px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s, transform 0.1s;
  margin-top: 8px;
}

.edit-button:hover {
  background-color: var(--accent-hover);
}

.edit-button:active {
  transform: scale(0.98);
}

.logout-button {
  width: 100%;
  padding: 14px;
  background-color: var(--danger-bg);
  color: var(--danger-color);
  border: none;
  border-radius: 50px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s, transform 0.1s;
  margin-top: 12px;
}

.logout-button:hover {
  background-color: var(--danger-hover);
}

.logout-button:active {
  transform: scale(0.98);
}
</style>