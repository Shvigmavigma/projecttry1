<template>
  <div class="my-projects-page">
    <header class="page-header">
      <h1>Ваши проекты</h1>
      <div class="header-actions">
        <ThemeToggle />
        <button class="home-button" @click="goHome" title="На главную">🏠</button>
      </div>
    </header>

    <div class="action-bar">
      <button class="create-button" @click="createProject">+ Создать проект</button>
    </div>

    <div v-if="loading" class="loading">Загрузка...</div>
    <div v-else-if="projects.length === 0" class="no-projects">
      У вас пока нет проектов.
    </div>
    <div v-else class="projects-grid">
      <div
        v-for="project in projects"
        :key="project.id"
        class="project-card"
        @click="goToDetails(project.id)"
      >
        <h3 class="project-title">{{ project.title }}</h3>
        <p class="project-description">{{ project.body.slice(0, 120) }}...</p>
        <p class="project-authors">
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
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useProjectsStore } from '@/stores/projects';
import { useUsersStore } from '@/stores/users';
import { useRouter } from 'vue-router';
import ThemeToggle from '@/components/ThemeToggle.vue';
import type { Project } from '@/types';

const projectsStore = useProjectsStore();
const usersStore = useUsersStore();
const router = useRouter();
const projects = ref<Project[]>([]);
const loading = ref(true);

onMounted(async () => {
  if (usersStore.users.length === 0) {
    await usersStore.fetchAllUsers();
  }
  projects.value = await projectsStore.fetchUserProjects();
  loading.value = false;
});

const createProject = () => {
  router.push('/project/new');
};

const goToDetails = (id: number) => {
  router.push(`/project/${id}`);
};

const goHome = () => {
  router.push('/main');
};

const goToUser = (userId: number) => {
  router.push(`/user/${userId}`);
};

const getAuthorNickname = (id: number): string => {
  const user = usersStore.users.find(u => u.id === id);
  return user ? user.nickname : `ID: ${id}`;
};
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

.action-bar {
  max-width: 1200px;
  margin: 0 auto 30px;
  display: flex;
  justify-content: flex-start;
}

.create-button {
  background: var(--accent-color);
  color: var(--button-text);
  border: none;
  border-radius: 50px;
  padding: 12px 24px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s, transform 0.1s;
  box-shadow: var(--shadow);
}

.create-button:hover {
  background: var(--accent-hover);
}

.create-button:active {
  transform: scale(0.98);
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

.project-title {
  color: var(--heading-color);
  margin-bottom: 12px;
  font-size: 1.3rem;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 8px;
  overflow-wrap: break-word;
  word-wrap: break-word;
  hyphens: auto;
}

.project-description {
  color: var(--text-primary);
  line-height: 1.5;
  flex: 1;
  margin-bottom: 16px;
  font-size: 0.95rem;
  overflow-wrap: break-word;
  word-wrap: break-word;
  hyphens: auto;
}

.project-authors {
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin-bottom: 16px;
  border-top: 1px solid var(--border-color);
  padding-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  overflow-wrap: break-word;
  word-wrap: break-word;
}

.authors-label {
  font-weight: 500;
  margin-right: 4px;
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