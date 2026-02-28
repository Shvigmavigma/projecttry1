<template>
  <div class="all-projects-page">
    <header class="projects-header">
      <h1>Все проекты</h1>
      <button class="home-button" @click="goHome" title="На главную">🏠</button>
    </header>

    <div class="search-container">
      <input
        v-model="search"
        placeholder="Поиск по названию..."
        @input="searchProjects"
      />
    </div>

    <div v-if="loading" class="loading">Загрузка...</div>
    <div v-else-if="projects.length === 0" class="no-projects">Проекты не найдены</div>
    <div v-else class="projects-grid">
      <div
        v-for="project in projects"
        :key="project.id"
        class="project-card"
        @click="goToProject(project.id)"
      >
        <h3 class="card-title">{{ project.title }}</h3>
        <p class="card-description">{{ project.body.slice(0, 150) }}...</p>
        <div class="card-footer">
          <span class="authors-label">Авторы:</span>
          <span class="authors-list">
            <span
              v-for="(authorId, index) in project.authors_ids"
              :key="authorId"
              class="author-link"
              @click.stop="goToUser(authorId)"
            >
              {{ getAuthorNickname(authorId) }}
              <span v-if="index < project.authors_ids.length - 1">, </span>
            </span>
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useUsersStore } from '@/stores/users';
import axios from 'axios';
import type { Project } from '@/types';

const router = useRouter();
const usersStore = useUsersStore();
const projects = ref<Project[]>([]);
const search = ref('');
const loading = ref(true);

// Загружаем пользователей при монтировании, если ещё не загружены
onMounted(async () => {
  if (usersStore.users.length === 0) {
    await usersStore.fetchAllUsers();
  }
  await fetchAll();
});

async function fetchAll() {
  loading.value = true;
  try {
    const res = await axios.get<Project[]>('http://localhost:8000/projects/');
    projects.value = res.data;
  } catch (error) {
    console.error('Error fetching projects:', error);
  } finally {
    loading.value = false;
  }
}

async function searchProjects() {
  if (!search.value) {
    await fetchAll();
    return;
  }
  loading.value = true;
  try {
    const res = await axios.get<Project[]>('http://localhost:8000/search', {
      params: { q: search.value }
    });
    projects.value = res.data;
  } catch (error) {
    console.error('Error searching projects:', error);
  } finally {
    loading.value = false;
  }
}

function getAuthorNickname(id: number): string {
  const user = usersStore.users.find(u => u.id === id);
  return user ? user.nickname : `ID: ${id}`;
}

function goToProject(id: number) {
  router.push(`/project/${id}`);
}

function goToUser(id: number) {
  router.push(`/user/${id}`);
}

function goHome() {
  router.push('/main');
}
</script>

<style scoped>
.all-projects-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #f0f9f0 0%, #d4eed7 100%);
  padding: 20px;
  box-sizing: border-box;
}

.projects-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto 20px;
}

.projects-header h1 {
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

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.project-card {
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  border: 1px solid #e0f0e0;
}

.project-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 28px rgba(66, 185, 131, 0.2);
  border-color: #b8e0b8;
}

.card-title {
  color: #2c5e2e;
  margin-bottom: 12px;
  font-size: 1.3rem;
  border-bottom: 1px solid #e0f0e0;
  padding-bottom: 8px;
}

.card-description {
  color: #1a3a1a;
  line-height: 1.5;
  flex: 1;
  margin-bottom: 16px;
}

.card-footer {
  border-top: 1px solid #e0f0e0;
  padding-top: 12px;
  color: #3b5e3b;
  font-size: 0.9rem;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.authors-label {
  font-weight: 500;
}

.authors-list {
  display: inline;
}

.author-link {
  cursor: pointer;
  color: #42b983;
  text-decoration: underline;
}

.author-link:hover {
  color: #2c5e2e;
}

.loading, .no-projects {
  text-align: center;
  color: #1f4f22;
  font-size: 1.2rem;
  padding: 40px;
}
</style>