<template>
  <div class="profile-edit-page">
    <div class="edit-card">
      <h2>Редактирование профиля</h2>
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
import axios from 'axios';

const authStore = useAuthStore();
const router = useRouter();

const form = ref({
  fullname: '',
  email: '',
  class: 0,
  speciality: '',
});

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
});

const handleSave = async () => {
  if (!authStore.user) return;

  saving.value = true;
  errorMessage.value = '';

  try {
    // Преобразуем поле class (в форме) в class_ для отправки
    const { class: classValue, ...rest } = form.value;
    const updateData = {
      ...rest,
      class_: classValue, // бэкенд ожидает class_
    };

    const response = await axios.put(
      `http://localhost:8000/users/${authStore.user.id}`,
      updateData
    );

    // Обновляем данные пользователя в хранилище и localStorage
    authStore.user = response.data;
    localStorage.setItem('user', JSON.stringify(response.data));

    // Переходим обратно в профиль
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
</script>

<style scoped>
.profile-edit-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #f0f9f0 0%, #d4eed7 100%);
  margin: -20px;
  padding: 20px;
}

.edit-card {
  background: white;
  border-radius: 32px;
  box-shadow: 0 20px 40px rgba(0, 40, 0, 0.1);
  padding: 40px;
  width: 100%;
  max-width: 500px;
}

h2 {
  color: #1f4f22;
  margin-bottom: 28px;
  text-align: center;
  font-weight: 500;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 6px;
  color: #3b5e3b;
  font-weight: 500;
}

input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #cbd5e0;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.2s;
  outline: none;
  box-sizing: border-box;
}

input:focus {
  border-color: #42b983;
  box-shadow: 0 0 0 3px rgba(66, 185, 131, 0.2);
}

.error-message {
  background: #fee;
  color: #c44;
  padding: 10px;
  border-radius: 8px;
  margin-bottom: 20px;
  text-align: center;
}

.button-group {
  display: flex;
  gap: 12px;
  margin-top: 32px;
}

.save-button,
.cancel-button {
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
  background-color: #42b983;
  color: white;
}

.save-button:hover:not(:disabled) {
  background-color: #3aa876;
}

.save-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.cancel-button {
  background-color: #e8f5e9;
  color: #2c5e2e;
}

.cancel-button:hover {
  background-color: #d4eed7;
}
</style>