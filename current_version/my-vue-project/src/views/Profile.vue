<template>
  <div class="profile-page">
    <!-- Кнопка домик в правом верхнем углу -->
    <button class="home-button" @click="goToMain" title="Главное меню">🏠</button>

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
  background: linear-gradient(135deg, #f0f9f0 0%, #d4eed7 100%);
  margin: -20px;
  padding: 20px;
  position: relative;
}

/* Кнопка домик в правом верхнем углу */
.home-button {
  position: absolute;
  top: 30px;
  right: 30px;
  background: white;
  border: none;
  border-radius: 50%;
  width: 56px;
  height: 56px;
  font-size: 28px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0,40,0,0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  z-index: 10;
  color: #2c5e2e;
}

.home-button:hover {
  background: #e8ffe8;
  transform: scale(1.1) translateY(-2px);
  box-shadow: 0 8px 20px rgba(66, 185, 131, 0.3);
}

.profile-card {
  background: white;
  border-radius: 32px;
  box-shadow: 0 20px 40px rgba(0, 40, 0, 0.1);
  padding: 40px;
  width: 100%;
  max-width: 500px;
  transition: transform 0.2s;
  overflow: hidden; /* гарантирует, что ничего не вылезет за скруглённые углы */
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
  background: #e8f5e9;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #2c5e2e;
}

.profile-header h2 {
  font-size: 2rem;
  color: #1f4f22;
  margin: 0;
  font-weight: 500;
  overflow-wrap: break-word;
  word-wrap: break-word;
  hyphens: auto;
  max-width: calc(100% - 96px); /* чтобы не наезжать на аватар */
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
  border-bottom: 1px solid #e0f0e0;
  overflow-wrap: break-word;
  word-wrap: break-word;
  gap: 10px; /* добавляем зазор между label и value */
}

.info-label {
  font-weight: 600;
  color: #3b5e3b;
  font-size: 1rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  min-width: 120px;
  flex-shrink: 0; /* не даём label сжиматься */
}

.info-value {
  color: #1a3a1a;
  font-size: 1.1rem;
  text-align: right;
  overflow-wrap: break-word;
  word-wrap: break-word;
  hyphens: auto;
  flex: 1; /* занимает оставшееся место, но переносит текст */
  min-width: 0; /* разрешает переносить */
}

.loading {
  text-align: center;
  color: #3b5e3b;
  padding: 20px;
  font-style: italic;
}

.edit-button {
  width: 100%;
  padding: 14px;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 50px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s, transform 0.1s;
  margin-top: 8px;
}

.edit-button:hover {
  background-color: #3aa876;
}

.edit-button:active {
  transform: scale(0.98);
}

.logout-button {
  width: 100%;
  padding: 14px;
  background-color: #fee;
  color: #c44;
  border: none;
  border-radius: 50px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s, transform 0.1s;
  margin-top: 12px;
}

.logout-button:hover {
  background-color: #fdd;
}

.logout-button:active {
  transform: scale(0.98);
}
</style>