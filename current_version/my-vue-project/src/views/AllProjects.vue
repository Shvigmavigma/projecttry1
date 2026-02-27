<template>
  <div>
    <h2>Все проекты</h2>
    <input v-model="search" placeholder="Поиск по названию..." @input="searchProjects" />
    <div v-for="project in projects" :key="project.id" class="project-card">
      <h3>{{ project.title }}</h3>
      <p>{{ project.body }}</p>
      <p>Авторы: {{ project.authors_ids.join(', ') }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';
import type { Project } from '@/types';

const projects = ref<Project[]>([]);
const search = ref('');

onMounted(fetchAll);

async function fetchAll() {
  const res = await axios.get<Project[]>('http://localhost:8000/projects/');
  projects.value = res.data;
}

async function searchProjects() {
  if (!search.value) return fetchAll();
  const res = await axios.get<Project[]>('http://localhost:8000/search', {
    params: { q: search.value }
  });
  projects.value = res.data;
}
</script>