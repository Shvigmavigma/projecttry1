<template>
  <div>
    <h2>Все пользователи</h2>
    <input v-model="search" placeholder="Поиск по никнейму, имени или email" @input="searchUsers" />
    <div v-for="user in users" :key="user.id" class="user-item">
      {{ user.nickname }} ({{ user.fullname }}) – {{ user.email }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useUsersStore } from '../stores/users';
import type { User } from '@/types';

const usersStore = useUsersStore();
const users = ref<User[]>([]);
const search = ref('');

onMounted(async () => {
  await usersStore.fetchAllUsers();
  users.value = usersStore.users;
});

const searchUsers = async () => {
  if (search.value) {
    await usersStore.searchUsers(search.value);
    users.value = usersStore.users;
  } else {
    await usersStore.fetchAllUsers();
    users.value = usersStore.users;
  }
};
</script>