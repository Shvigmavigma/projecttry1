<template>
  <div class="my-projects-page">
    <header class="page-header">
      <h1>Ваши проекты</h1>
      <button class="home-button" @click="goHome" title="На главную">🏠</button>
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
import type { Project } from '@/types';

const projectsStore = useProjectsStore();
const usersStore = useUsersStore();
const router = useRouter();
const projects = ref<Project[]>([]);
const loading = ref(true);

onMounted(async () => {
  // Загружаем пользователей, если ещё не загружены
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
  background: linear-gradient(135deg, #f0f9f0 0%, #d4eed7 100%);
  padding: 20px;
  box-sizing: border-box;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto 20px;
}

.page-header h1 {
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

.action-bar {
  max-width: 1200px;
  margin: 0 auto 30px;
  display: flex;
  justify-content: flex-start;
}

.create-button {
  background: #42b983;
  color: white;
  border: none;
  border-radius: 50px;
  padding: 12px 24px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s, transform 0.1s;
  box-shadow: 0 4px 10px rgba(0,0,0,0.05);
}

.create-button:hover {
  background: #3aa876;
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

.project-title {
  color: #2c5e2e;
  margin-bottom: 12px;
  font-size: 1.3rem;
  border-bottom: 1px solid #e0f0e0;
  padding-bottom: 8px;
  overflow-wrap: break-word;
  word-wrap: break-word;
  hyphens: auto;
}

.project-description {
  color: #1a3a1a;
  line-height: 1.5;
  flex: 1;
  margin-bottom: 16px;
  font-size: 0.95rem;
  overflow-wrap: break-word;
  word-wrap: break-word;
  hyphens: auto;
}

.project-authors {
  color: #3b5e3b;
  font-size: 0.9rem;
  margin-bottom: 16px;
  border-top: 1px solid #e0f0e0;
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