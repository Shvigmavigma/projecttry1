<template>
  <div class="all-users-page">
    <header class="users-header">
      <h1>Пользователи</h1>
      <button class="home-button" @click="goHome" title="На главную">🏠</button>
    </header>

    <div class="search-container">
      <input
        v-model="search"
        placeholder="Поиск по никнейму, имени или email"
        @input="searchUsers"
      />
    </div>

    <div v-if="loading" class="loading">Загрузка...</div>
    <div v-else-if="users.length === 0" class="no-users">Пользователи не найдены</div>
    <div v-else class="users-grid">
      <div
        v-for="user in users"
        :key="user.id"
        class="user-card"
        @click="goToUser(user.id)"
      >
        <div class="user-avatar">{{ user.nickname.charAt(0).toUpperCase() }}</div>
        <h3 class="user-nickname">{{ user.nickname }}</h3>
        <p class="user-fullname">{{ user.fullname }}</p>
        <p class="user-email">{{ user.email }}</p>
        <div class="user-class">Класс: {{ user.class }}</div>
        <div v-if="user.speciality" class="user-speciality">{{ user.speciality }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useUsersStore } from '@/stores/users';
import type { User } from '@/types';

const router = useRouter();
const usersStore = useUsersStore();
const users = ref<User[]>([]);
const search = ref('');
const loading = ref(true);

onMounted(async () => {
  await loadUsers();
});

async function loadUsers() {
  loading.value = true;
  await usersStore.fetchAllUsers();
  users.value = usersStore.users;
  loading.value = false;
}

async function searchUsers() {
  loading.value = true;
  if (search.value) {
    await usersStore.searchUsers(search.value);
  } else {
    await usersStore.fetchAllUsers();
  }
  users.value = usersStore.users;
  loading.value = false;
}

function goToUser(id: number) {
  router.push(`/user/${id}`);
}

function goHome() {
  router.push('/main');
}
</script>

<style scoped>
.all-users-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #f0f9f0 0%, #d4eed7 100%);
  padding: 20px;
  box-sizing: border-box;
}

.users-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto 20px;
}

.users-header h1 {
  color: #1f4f22;
  font-size: 2.5rem;
  margin: 0;
}

.home-button {
  background: none;
  border: none;
  font-size: 2rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 50%;
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.home-button:hover {
  background: rgba(255,255,255,0.5);
}

.search-container {
  max-width: 600px;
  margin: 0 auto 30px;
}

.search-container input {
  width: 100%;
  padding: 12px 20px;
  border: 1px solid #cbd5e0;
  border-radius: 50px;
  font-size: 1rem;
  outline: none;
  transition: border-color 0.2s;
  background: white;
}

.search-container input:focus {
  border-color: #42b983;
  box-shadow: 0 0 0 3px rgba(66, 185, 131, 0.2);
}

.users-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.user-card {
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  border: 1px solid #e0f0e0;
}

.user-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 28px rgba(66, 185, 131, 0.2);
  border-color: #b8e0b8;
}

.user-avatar {
  width: 60px;
  height: 60px;
  background: #42b983;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 12px;
}

.user-nickname {
  color: #2c5e2e;
  margin-bottom: 4px;
  font-size: 1.2rem;
  font-weight: 600;
}

.user-fullname {
  color: #1a3a1a;
  font-size: 0.95rem;
  margin-bottom: 6px;
}

.user-email {
  color: #5f7f5f;
  font-size: 0.85rem;
  margin-bottom: 8px;
}

.user-class, .user-speciality {
  color: #3b5e3b;
  font-size: 0.9rem;
  margin-top: 4px;
}

.loading, .no-users {
  text-align: center;
  color: #1f4f22;
  font-size: 1.2rem;
  padding: 40px;
}
</style>