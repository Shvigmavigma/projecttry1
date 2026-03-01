<template>
  <div class="all-projects-page">
    <header class="projects-header">
      <h1>Все проекты</h1>
      <div class="header-actions">
        <ThemeToggle />
        <button class="home-button" @click="goHome" title="На главную">🏠</button>
      </div>
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
import ThemeToggle from '@/components/ThemeToggle.vue';
import axios from 'axios';
import type { Project } from '@/types';

const router = useRouter();
const usersStore = useUsersStore();
const projects = ref<Project[]>([]);
const search = ref('');
const loading = ref(true);

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
  background: var(--bg-page);
  padding: 20px;
  box-sizing: border-box;
  transition: background 0.3s;
}

.projects-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto 20px;
}

.projects-header h1 {
  color: var(--heading-color);
  font-size: 2.5rem;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 10px;
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
  color: var(--text-primary);
}

.home-button:hover {
  background: rgba(255, 255, 255, 0.1);
}

.dark-theme .home-button:hover {
  background: rgba(255, 255, 255, 0.1);
}

.light-theme .home-button:hover {
  background: rgba(0, 0, 0, 0.05);
}

.search-container {
  max-width: 600px;
  margin: 0 auto 30px;
}

.search-container input {
  width: 100%;
  padding: 12px 20px;
  border: 1px solid var(--input-border);
  border-radius: 50px;
  font-size: 1rem;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
  background: var(--input-bg);
  color: var(--text-primary);
}

.search-container input::placeholder {
  color: var(--text-secondary);
}

.search-container input:focus {
  border-color: var(--accent-color);
  box-shadow: 0 0 0 3px rgba(66, 185, 131, 0.2);
}

.dark-theme .search-container input:focus {
  box-shadow: 0 0 0 3px rgba(1, 69, 172, 0.2);
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.project-card {
  background: var(--bg-card);
  border-radius: 16px;
  padding: 20px;
  box-shadow: var(--shadow);
  transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border-color);
}

.project-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-strong);
  border-color: var(--accent-color);
}

.card-title {
  color: var(--heading-color);
  margin-bottom: 12px;
  font-size: 1.3rem;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 8px;
  overflow-wrap: break-word;
  word-wrap: break-word;
  hyphens: auto;
}

.card-description {
  color: var(--text-primary);
  line-height: 1.5;
  flex: 1;
  margin-bottom: 16px;
  overflow-wrap: break-word;
  word-wrap: break-word;
  hyphens: auto;
}

.card-footer {
  border-top: 1px solid var(--border-color);
  padding-top: 12px;
  color: var(--text-secondary);
  font-size: 0.9rem;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  overflow-wrap: break-word;
  word-wrap: break-word;
}

.authors-label {
  font-weight: 500;
  color: var(--text-secondary);
}

.authors-list {
  display: inline;
}

.author-link {
  cursor: pointer;
  color: var(--link-color);
  text-decoration: underline;
  overflow-wrap: break-word;
  word-wrap: break-word;
  hyphens: auto;
  display: inline-block;
  max-width: 100%;
}

.author-link:hover {
  color: var(--link-hover);
}

.loading, .no-projects {
  text-align: center;
  color: var(--text-primary);
  font-size: 1.2rem;
  padding: 40px;
}
</style>