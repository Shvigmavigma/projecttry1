<template>
  <div>
    <h2>{{ isEdit ? 'Редактировать проект' : 'Новый проект' }}</h2>
    <ProjectForm
      :initial-data="projectData"
      :is-edit="isEdit"
      @submit="handleSubmit"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useProjectsStore } from '../stores/projects';
import ProjectForm from '../components/ProjectForm.vue';
import type { Project } from '@/types';

const route = useRoute();
const router = useRouter();
const projectsStore = useProjectsStore();
const isEdit = computed(() => route.params.id !== undefined);
const projectData = ref<Project | null>(null);

onMounted(async () => {
  if (isEdit.value) {
    const id = Number(route.params.id);
    projectData.value = await projectsStore.fetchProjectById(id);
  }
});

const handleSubmit = async (formData: any) => {
  if (isEdit.value) {
    const id = Number(route.params.id);
    await projectsStore.updateProject(id, formData);
  } else {
    await projectsStore.createProject(formData);
  }
  router.push('/my-projects');
};
</script>