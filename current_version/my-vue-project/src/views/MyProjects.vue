<template>
  <div class="my-projects-page">
    <header class="page-header">
      <h1>Мои проекты</h1>
      <div class="header-actions">
        <ThemeToggle />
        <button class="home-button" @click="goHome" title="На главную">🏠</button>
      </div>
    </header>

    <div v-if="loading" class="loading">Загрузка проектов...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="projects.length === 0" class="no-projects">
      <p>У вас пока нет проектов</p>
      <button class="create-button" @click="createProject">Создать проект</button>
    </div>
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
          <div class="authors-list">
            <div
              v-for="(authorId, index) in project.authors_ids"
              :key="authorId"
              class="author-item"
              @click.stop="goToUser(authorId)"
            >
              <div class="author-avatar">
                <img
                  v-if="getAuthorAvatar(authorId)"
                  :src="getAuthorAvatar(authorId)"
                  :alt="getAuthorNickname(authorId)"
                  @error="handleImageError(authorId)"
                />
                <span v-else>{{ getAuthorInitials(authorId) }}</span>
              </div>
              <span class="author-name">{{ getAuthorNickname(authorId) }}</span>
              <span v-if="index < project.authors_ids.length - 1">,</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useUsersStore } from '@/stores/users';
import ThemeToggle from '@/components/ThemeToggle.vue';
import axios from 'axios';
import type { Project } from '@/types';

const router = useRouter();
const authStore = useAuthStore();
const usersStore = useUsersStore();

const projects = ref<Project[]>([]);
const loading = ref(true);
const error = ref('');
const authorImageErrors = ref<Record<number, boolean>>({});
const authChecked = ref(false);

const currentUserId = computed(() => authStore.user?.id);
const isAuthenticated = computed(() => authStore.isAuthenticated);

// Проверяем авторизацию при монтировании
onMounted(async () => {
  console.log('MyProjects mounted - checking auth...');
  console.log('Token exists:', !!localStorage.getItem('access_token'));
  
  // Проверяем авторизацию
  if (!authStore.isAuthenticated) {
    const isValid = await authStore.checkAuth();
    console.log('Auth check result:', isValid);
    
    if (!isValid) {
      console.log('Not authenticated, redirecting to login');
      router.push('/login');
      return;
    }
  }
  
  authChecked.value = true;
  await loadUserProjects();
});

// Следим за изменением isAuthenticated
watch(isAuthenticated, (newVal) => {
  console.log('isAuthenticated changed:', newVal);
  if (!newVal) {
    router.push('/login');
  }
});

async function loadUserProjects() {
  if (!authChecked.value) return;
  
  console.log('Loading projects for user:', currentUserId.value);
  
  if (!currentUserId.value) {
    error.value = 'Пользователь не авторизован';
    loading.value = false;
    return;
  }

  loading.value = true;
  error.value = '';

  try {
    // Загружаем всех пользователей для получения авторов
    if (usersStore.users.length === 0) {
      await usersStore.fetchAllUsers();
    }

    // Загружаем проекты текущего пользователя
    console.log('Fetching projects for author_id:', currentUserId.value);
    const response = await axios.get(`/projects/?author_id=${currentUserId.value}`);
    projects.value = response.data;
    console.log('Projects loaded:', projects.value.length);
  } catch (err: any) {
    console.error('Error loading projects:', err);
    
    if (err.response?.status === 401) {
      // Если токен истек, пробуем обновить авторизацию
      const isValid = await authStore.checkAuth();
      if (isValid) {
        // Повторяем запрос
        try {
          const response = await axios.get(`/projects/?author_id=${currentUserId.value}`);
          projects.value = response.data;
        } catch (retryErr) {
          error.value = 'Ошибка загрузки проектов';
        }
      } else {
        router.push('/login');
      }
    } else {
      error.value = err.response?.data?.detail || 'Ошибка загрузки проектов';
    }
  } finally {
    loading.value = false;
  }
}

function getAuthorNickname(id: number): string {
  const user = usersStore.users.find(u => u.id === id);
  return user ? user.nickname : `ID: ${id}`;
}

function getAuthorAvatar(id: number): string | undefined {
  if (authorImageErrors.value[id]) return undefined;
  const user = usersStore.users.find(u => u.id === id);
  return user?.avatar ? `http://localhost:8000/avatars/${user.avatar}` : undefined;
}

function getAuthorInitials(id: number): string {
  const user = usersStore.users.find(u => u.id === id);
  return user?.nickname?.charAt(0).toUpperCase() || '?';
}

function handleImageError(id: number) {
  authorImageErrors.value[id] = true;
}

function goToProject(id: number) {
  router.push(`/project/${id}`);
}

function goToUser(id: number) {
  router.push(`/user/${id}`);
}

function createProject() {
  router.push('/project/edit/new');
}

function goHome() {
  router.push('/main');
}
</script>

<style scoped>
.my-projects-page {
  min-height: 100vh;
  background: var(--bg-page);
  padding: 20px;
  box-sizing: border-box;
  transition: background 0.3s;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto 20px;
}

.page-header h1 {
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
  margin-right: 4px;
  flex-shrink: 0;
}

.authors-list {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 2px;
}

.author-item {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.author-item:hover {
  background: rgba(128, 128, 128, 0.1);
}

.author-avatar {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--accent-color);
  color: var(--button-text);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
  overflow: hidden;
  flex-shrink: 0;
}

.author-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.author-avatar span {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.author-name {
  color: var(--link-color);
  text-decoration: underline;
  font-size: 0.9rem;
  overflow-wrap: break-word;
  word-wrap: break-word;
  hyphens: auto;
  max-width: 100px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.author-item:hover .author-name {
  color: var(--link-hover);
}

.create-button {
  margin-top: 20px;
  padding: 12px 24px;
  background-color: var(--accent-color);
  color: var(--button-text);
  border: none;
  border-radius: 50px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
}

.create-button:hover {
  background-color: var(--accent-hover);
}

.loading, .error, .no-projects {
  text-align: center;
  color: var(--text-primary);
  font-size: 1.2rem;
  padding: 40px;
}
</style>