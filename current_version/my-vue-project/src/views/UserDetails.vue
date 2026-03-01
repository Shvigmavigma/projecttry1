<template>
  <div class="user-details-page">
    <header class="details-header">
      <h1>Профиль пользователя</h1>
      <div class="header-actions">
        <ThemeToggle />
        <button class="home-button" @click="goHome" title="На главную">🏠</button>
      </div>
    </header>

    <div v-if="loadingUser" class="loading">Загрузка данных пользователя...</div>
    <div v-else-if="errorUser" class="error">{{ errorUser }}</div>
    <div v-else-if="user" class="user-info-card">
      <div class="user-avatar">{{ user.nickname.charAt(0).toUpperCase() }}</div>
      <h2 class="user-nickname">{{ user.nickname }}</h2>
      <p class="user-fullname">{{ user.fullname }}</p>
      <p class="user-email">{{ user.email }}</p>
      <p class="user-class">Класс: {{ user.class }}</p>
      <p v-if="user.speciality" class="user-speciality">Специальность: {{ user.speciality }}</p>
    </div>

    <div class="projects-section">
      <h2>Проекты пользователя</h2>
      <div v-if="loadingProjects" class="loading">Загрузка проектов...</div>
      <div v-else-if="projects.length === 0" class="no-projects">Нет проектов</div>
      <div v-else class="projects-grid">
        <div
          v-for="project in projects"
          :key="project.id"
          class="project-card"
          @click="goToProject(project.id)"
        >
          <h3 class="card-title">{{ project.title }}</h3>
          <p class="card-description">{{ project.body.slice(0, 100) }}...</p>
          <div class="card-footer">
            <span class="authors-label">Авторы:</span>
            <span class="authors-list">
              <span
                v-for="(authorId, index) in project.authors_ids"
                :key="authorId"
                class="author-item"
              >
                <span class="author-link" @click.stop="goToUser(authorId)">
                  {{ getAuthorNickname(authorId) }}
                </span>
                <span v-if="index < project.authors_ids.length - 1">, </span>
              </span>
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useUsersStore } from '@/stores/users';
import ThemeToggle from '@/components/ThemeToggle.vue';
import type { User, Project } from '@/types';

const route = useRoute();
const router = useRouter();
const usersStore = useUsersStore();

const user = ref<User | null>(null);
const projects = ref<Project[]>([]);
const loadingUser = ref(true);
const loadingProjects = ref(true);
const errorUser = ref('');

// Функция загрузки данных пользователя и его проектов
const loadUserData = async (id: number) => {
  loadingUser.value = true;
  loadingProjects.value = true;
  errorUser.value = '';

  // Загружаем всех пользователей один раз для получения никнеймов
  if (usersStore.users.length === 0) {
    await usersStore.fetchAllUsers();
  }

  // Загружаем данные пользователя через поиск по ID
  try {
    await usersStore.searchUsers(id.toString());
    const found = usersStore.users.find(u => u.id === id);
    if (found) {
      user.value = found;
    } else {
      errorUser.value = 'Пользователь не найден';
    }
  } catch (err) {
    errorUser.value = 'Ошибка загрузки пользователя';
    console.error(err);
  } finally {
    loadingUser.value = false;
  }

  // Загружаем проекты пользователя
  try {
    const response = await fetch(`http://localhost:8000/projects/?author_id=${id}`);
    if (response.ok) {
      projects.value = await response.json();
    } else {
      console.error('Ошибка загрузки проектов');
    }
  } catch (err) {
    console.error('Ошибка загрузки проектов:', err);
  } finally {
    loadingProjects.value = false;
  }
};

// Первоначальная загрузка при монтировании
onMounted(async () => {
  const id = Number(route.params.id);
  if (!isNaN(id)) {
    await loadUserData(id);
  } else {
    errorUser.value = 'Неверный ID пользователя';
    loadingUser.value = false;
  }
});

// Следим за изменением параметра маршрута (переход на другого пользователя)
watch(() => route.params.id, async (newId) => {
  const id = Number(newId);
  if (!isNaN(id)) {
    await loadUserData(id);
  } else {
    errorUser.value = 'Неверный ID пользователя';
    loadingUser.value = false;
  }
});

const getAuthorNickname = (id: number): string => {
  const u = usersStore.users.find(u => u.id === id);
  return u ? u.nickname : `ID: ${id}`;
};

const goToProject = (projectId: number) => {
  router.push(`/project/${projectId}`);
};

const goToUser = (userId: number) => {
  router.push(`/user/${userId}`);
};

const goHome = () => {
  router.push('/main');
};
</script>

<style scoped>
.user-details-page {
  min-height: 100vh;
  background: var(--bg-page);
  padding: 20px;
  box-sizing: border-box;
  transition: background 0.3s;
}

.details-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto 20px;
}

.details-header h1 {
  color: var(--heading-color);
  font-size: 2rem;
  margin: 0;
  overflow-wrap: break-word;
  word-wrap: break-word;
  hyphens: auto;
}

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
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

.light-theme .home-button:hover {
  background: rgba(0, 0, 0, 0.05);
}

.user-info-card {
  background: var(--bg-card);
  border-radius: 24px;
  box-shadow: var(--shadow-strong);
  padding: 30px;
  max-width: 600px;
  margin: 0 auto 40px;
  text-align: center;
  overflow: hidden;
  transition: background 0.3s;
}

.user-avatar {
  width: 80px;
  height: 80px;
  background: var(--accent-color);
  color: var(--button-text);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
  font-weight: bold;
  margin: 0 auto 16px;
}

.user-nickname {
  color: var(--heading-color);
  margin-bottom: 8px;
  font-size: 1.8rem;
  overflow-wrap: break-word;
  word-wrap: break-word;
  hyphens: auto;
  max-width: 100%;
}

.user-fullname {
  color: var(--text-primary);
  font-size: 1.2rem;
  margin-bottom: 8px;
  overflow-wrap: break-word;
  word-wrap: break-word;
  hyphens: auto;
}

.user-email {
  color: var(--text-secondary);
  font-size: 1rem;
  margin-bottom: 8px;
  overflow-wrap: break-word;
  word-wrap: break-word;
  hyphens: auto;
}

.user-class, .user-speciality {
  color: var(--text-secondary);
  font-size: 1rem;
  margin-top: 4px;
  overflow-wrap: break-word;
  word-wrap: break-word;
  hyphens: auto;
}

.projects-section {
  max-width: 1000px;
  margin: 0 auto;
}

.projects-section h2 {
  color: var(--heading-color);
  font-size: 1.8rem;
  margin-bottom: 24px;
  text-align: center;
  overflow-wrap: break-word;
  word-wrap: break-word;
  hyphens: auto;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.project-card {
  background: var(--bg-card);
  border-radius: 16px;
  padding: 20px;
  box-shadow: var(--shadow);
  transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
  cursor: pointer;
  border: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
}

.project-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-strong);
  border-color: var(--accent-color);
}

.card-title {
  color: var(--heading-color);
  margin-bottom: 10px;
  font-size: 1.2rem;
  overflow-wrap: break-word;
  word-wrap: break-word;
  hyphens: auto;
}

.card-description {
  color: var(--text-primary);
  line-height: 1.5;
  margin-bottom: 12px;
  font-size: 0.95rem;
  overflow-wrap: break-word;
  word-wrap: break-word;
  hyphens: auto;
  flex: 1;
}

.card-footer {
  border-top: 1px solid var(--border-color);
  padding-top: 8px;
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
  margin-right: 4px;
  flex-shrink: 0;
  color: var(--text-secondary);
}

.authors-list {
  display: inline;
  overflow-wrap: break-word;
  word-wrap: break-word;
}

.author-item {
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

.loading, .error, .no-projects {
  text-align: center;
  color: var(--text-primary);
  font-size: 1.2rem;
  padding: 40px;
}
</style>