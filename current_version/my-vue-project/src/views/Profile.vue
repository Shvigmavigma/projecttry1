<template>
  <div>
    <h2>Личный кабинет</h2>
    <div v-if="user">
      <p><strong>Никнейм:</strong> {{ user.nickname }}</p>
      <p><strong>Полное имя:</strong> {{ user.fullname }}</p>
      <p><strong>Email:</strong> {{ user.email }}</p>
      <p><strong>Класс:</strong> {{ user.class }}</p>
      <p><strong>Специальность:</strong> {{ user.speciality || 'не указана' }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useAuthStore } from '../stores/auth';

const authStore = useAuthStore();
const user = computed(() => authStore.user);
</script>