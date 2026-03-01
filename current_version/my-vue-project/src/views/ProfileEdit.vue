<template>
  <div class="profile-edit-page">
    <header class="edit-header">
      <h1>Редактирование профиля</h1>
      <div class="header-actions">
        <ThemeToggle />
        <button class="home-button" @click="goHome" title="На главную">🏠</button>
      </div>
    </header>

    <div v-if="loading" class="loading">Загрузка...</div>
    <div v-else class="edit-card">
      <form @submit.prevent="handleSave">
        <div class="form-group">
          <label for="fullname">Полное имя</label>
          <input
            id="fullname"
            v-model="form.fullname"
            type="text"
            required
          />
        </div>

        <div class="form-group">
          <label for="email">Email</label>
          <input
            id="email"
            v-model="form.email"
            type="email"
            required
          />
        </div>

        <div class="form-group">
          <label for="class">Класс</label>
          <input
            id="class"
            v-model.number="form.class"
            type="number"
            step="0.1"
          />
        </div>

        <div class="form-group">
          <label for="speciality">Специальность</label>
          <input
            id="speciality"
            v-model="form.speciality"
            type="text"
          />
        </div>

        <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>

        <div class="button-group">
          <button type="submit" class="save-button" :disabled="saving">
            {{ saving ? 'Сохранение...' : 'Сохранить' }}
          </button>
          <button type="button" class="cancel-button" @click="goBack">
            Отмена
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router';
import ThemeToggle from '@/components/ThemeToggle.vue';
import axios from 'axios';

const authStore = useAuthStore();
const router = useRouter();

const form = ref({
  fullname: '',
  email: '',
  class: 0,
  speciality: '',
});

const loading = ref(true);
const saving = ref(false);
const errorMessage = ref('');

onMounted(() => {
  if (authStore.user) {
    form.value = {
      fullname: authStore.user.fullname,
      email: authStore.user.email,
      class: authStore.user.class,
      speciality: authStore.user.speciality || '',
    };
  }
  loading.value = false;
});

const handleSave = async () => {
  if (!authStore.user) return;

  saving.value = true;
  errorMessage.value = '';

  try {
    const { class: classValue, ...rest } = form.value;
    const updateData = {
      ...rest,
      class_: classValue,
    };

    const response = await axios.put(
      `http://localhost:8000/users/${authStore.user.id}`,
      updateData
    );

    authStore.user = response.data;
    localStorage.setItem('user', JSON.stringify(response.data));

    router.push('/profile');
  } catch (error: any) {
    console.error('Error updating profile:', error);
    errorMessage.value =
      error.response?.data?.detail || 'Ошибка при сохранении данных';
  } finally {
    saving.value = false;
  }
};

const goBack = () => {
  router.push('/profile');
};

const goHome = () => {
  router.push('/main');
};
</script>

<style scoped>
.profile-edit-page {
  min-height: 100vh;
  background: var(--bg-page);
  padding: 20px;
  box-sizing: border-box;
  transition: background 0.3s;
}

.edit-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 500px;
  margin: 0 auto 20px;
}

.edit-header h1 {
  color: var(--heading-color);
  font-size: 2rem;
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
  width: 44px;
  height: 44px;
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

.edit-card {
  background: var(--bg-card);
  border-radius: 32px;
  box-shadow: var(--shadow);
  padding: 40px;
  max-width: 500px;
  margin: 0 auto;
  transition: background 0.3s;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 6px;
  color: var(--text-secondary);
  font-weight: 500;
}

input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid var(--input-border);
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.2s, box-shadow 0.2s;
  outline: none;
  box-sizing: border-box;
  background: var(--input-bg);
  color: var(--text-primary);
}

input:focus {
  border-color: var(--accent-color);
  box-shadow: 0 0 0 3px rgba(1, 69, 172, 0.2);
}

.light-theme input:focus {
  box-shadow: 0 0 0 3px rgba(66, 185, 131, 0.2);
}

.error-message {
  background: var(--error-bg);
  color: var(--danger-color);
  padding: 10px;
  border-radius: 8px;
  margin-bottom: 20px;
  text-align: center;
  border: 1px solid var(--danger-color);
}

.button-group {
  display: flex;
  gap: 12px;
  margin-top: 32px;
}

.save-button, .cancel-button {
  flex: 1;
  padding: 14px;
  border: none;
  border-radius: 50px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.save-button {
  background-color: var(--accent-color);
  color: var(--button-text);
}

.save-button:hover:not(:disabled) {
  background-color: var(--accent-hover);
}

.save-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.cancel-button {
  background-color: var(--bg-page);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.cancel-button:hover {
  background-color: var(--bg-card);
}

.loading {
  text-align: center;
  color: var(--text-primary);
  font-size: 1.2rem;
  padding: 40px;
}
</style>