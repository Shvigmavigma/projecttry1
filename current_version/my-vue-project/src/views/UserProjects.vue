<template>
  <div>
    <h2>Ваши проекты</h2>
    <button @click="$router.push('/project/new')">+ Создать проект</button>
    <div v-if="loading">Загрузка...</div>
    <div v-else-if="projects.length === 0">
      <p>У вас пока нет проектов.</p>
    </div>
    <div v-else>
      <div v-for="project in projects" :key="project.id" class="project-card">
        <h3>{{ project.title }}</h3>
        <p>{{ project.body.slice(0, 100) }}...</p>
        <p><strong>Авторы:</strong> {{ project.authors_ids.join(', ') }}</p>
        <button @click="editProject(project.id)">Редактировать</button>
        <button @click="deleteProject(project.id)">Удалить</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useProjectsStore } from '../stores/projects';
import { useRouter } from 'vue-router';
import type { Project } from '@/types';

const projectsStore = useProjectsStore();
const router = useRouter();
const projects = ref<Project[]>([]);
const loading = ref(true);

onMounted(async () => {
  projects.value = await projectsStore.fetchUserProjects();
  loading.value = false;
});

const editProject = (id: number) => {
  router.push(`/project/edit/${id}`);
};

const deleteProject = async (id: number) => {
  if (confirm('Удалить проект?')) {
    await projectsStore.deleteProject(id);
    projects.value = await projectsStore.fetchUserProjects();
  }
};
</script>