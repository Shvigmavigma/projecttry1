<template>
  <div class="register-page">
    <div class="theme-toggle-container">
      <ThemeToggle />
    </div>
    <div class="register-card">
      <h2>Регистрация</h2>
      <form @submit.prevent="handleRegister">
        <!-- Поле для выбора аватарки -->
        <div class="form-group avatar-group">
          <label>Аватар (необязательно)</label>
          <div class="avatar-preview">
            <img
              v-if="avatarPreview"
              :src="avatarPreview"
              alt="Avatar preview"
            />
            <span v-else class="avatar-placeholder">
              {{ form.nickname?.charAt(0)?.toUpperCase() || '?' }}
            </span>
          </div>
          <input
            type="file"
            accept="image/*"
            @change="onFileChange"
            ref="fileInput"
            :disabled="loading"
          />
          <button
            type="button"
            class="clear-avatar"
            v-if="avatarFile"
            @click="clearAvatar"
            :disabled="loading"
          >
            ✕
          </button>
        </div>

        <div class="form-group">
          <label for="nickname">Никнейм</label>
          <input
            id="nickname"
            v-model="form.nickname"
            type="text"
            placeholder="Введите никнейм"
            required
          />
        </div>

        <div class="form-group">
          <label for="fullname">Полное имя</label>
          <input
            id="fullname"
            v-model="form.fullname"
            type="text"
            placeholder="Введите полное имя"
            required
          />
        </div>

        <div class="form-group">
          <label for="email">Email</label>
          <input
            id="email"
            v-model="form.email"
            type="email"
            placeholder="Введите email"
            required
          />
        </div>

        <div class="form-group">
          <label for="class">Класс</label>
          <input
            id="class"
            v-model.number="form.class_"
            type="number"
            step="0.1"
            placeholder="11.0"
          />
        </div>

        <div class="form-group">
          <label for="speciality">Специальность</label>
          <input
            id="speciality"
            v-model="form.speciality"
            type="text"
            placeholder="Например, информатика"
          />
        </div>

        <div class="form-group">
          <label for="password">Пароль</label>
          <input
            id="password"
            v-model="form.password"
            type="password"
            placeholder="Введите пароль"
            required
          />
        </div>

        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>

        <button type="submit" class="register-button" :disabled="loading">
          {{ loading ? 'Регистрация...' : 'Зарегистрироваться' }}
        </button>
      </form>

      <p class="login-link">
        Уже есть аккаунт? <router-link to="/login">Войти</router-link>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import ThemeToggle from '@/components/ThemeToggle.vue';
import axios from 'axios';

interface RegisterForm {
  nickname: string;
  fullname: string;
  email: string;
  class_: number;
  speciality: string;
  password: string;
}

const authStore = useAuthStore();
const router = useRouter();

const form = reactive<RegisterForm>({
  nickname: '',
  fullname: '',
  email: '',
  class_: 0,
  speciality: '',
  password: '',
});

const loading = ref(false);
const errorMessage = ref('');

// Данные аватарки
const avatarFile = ref<File | null>(null);
const avatarPreview = ref<string | null>(null);
const fileInput = ref<HTMLInputElement | null>(null);

const onFileChange = (event: Event) => {
  const input = event.target as HTMLInputElement;
  if (!input.files || input.files.length === 0) {
    clearAvatar();
    return;
  }

  const file = input.files[0];
  // Ограничение размера 5 МБ
  if (file.size > 5 * 1024 * 1024) {
    errorMessage.value = 'Файл слишком большой (макс. 5 МБ)';
    clearAvatar();
    return;
  }

  avatarFile.value = file;
  const reader = new FileReader();
  reader.onload = (e) => {
    avatarPreview.value = e.target?.result as string;
  };
  reader.readAsDataURL(file);
};

const clearAvatar = () => {
  avatarFile.value = null;
  avatarPreview.value = null;
  if (fileInput.value) {
    fileInput.value.value = '';
  }
};

const handleRegister = async () => {
  loading.value = true;
  errorMessage.value = '';

  // Подготовка данных пользователя
  const { class_, ...rest } = form;
  const userData = {
    ...rest,
    class: class_,
    password: form.password,
  };

  try {
    // 1. Создание пользователя (JSON)
    const success = await authStore.register(userData);
    if (!success) {
      errorMessage.value =
        'Ошибка регистрации. Возможно, пользователь с таким никнеймом уже существует.';
      loading.value = false;
      return;
    }

    const userId = authStore.user?.id;
    if (!userId) {
      throw new Error('Не удалось получить ID пользователя');
    }

    // 2. Загрузка аватарки, если файл выбран
    if (avatarFile.value) {
      const formData = new FormData();
      formData.append('file', avatarFile.value);

      const response = await axios.post(
        `http://localhost:8000/users/${userId}/avatar`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );

      // Обновляем данные пользователя в store (сервер возвращает обновлённого пользователя)
      authStore.user = response.data;
      localStorage.setItem('user', JSON.stringify(response.data));
    }

    // Всё успешно — переход на главную
    router.push('/main');
  } catch (error: any) {
    console.error('Registration error:', error);
    errorMessage.value =
      error.response?.data?.detail || 'Произошла ошибка при регистрации';
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.register-page {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: var(--bg-page);
  margin: -20px;
  padding: 20px;
  position: relative;
  transition: background 0.3s;
}

.theme-toggle-container {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 10;
}

.register-card {
  background: var(--bg-card);
  border-radius: 16px;
  box-shadow: var(--shadow-strong);
  padding: 40px 32px;
  width: 100%;
  max-width: 450px;
  transition: transform 0.2s ease, background 0.3s;
}

.register-card:hover {
  transform: translateY(-4px);
}

h2 {
  text-align: center;
  color: var(--heading-color);
  margin-bottom: 28px;
  font-weight: 500;
}

.form-group {
  margin-bottom: 16px;
}

label {
  display: block;
  margin-bottom: 6px;
  color: var(--text-secondary);
  font-size: 0.9rem;
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
  box-shadow: 0 0 0 3px rgba(66, 185, 131, 0.2);
}

.dark-theme input:focus {
  box-shadow: 0 0 0 3px rgba(1, 69, 172, 0.2);
}

.error-message {
  background: var(--error-bg);
  color: var(--danger-color);
  padding: 10px;
  border-radius: 8px;
  margin-bottom: 20px;
  text-align: center;
  border: 1px solid var(--danger-color);
  font-size: 0.9rem;
}

.register-button {
  width: 100%;
  padding: 14px;
  background-color: var(--accent-color);
  color: var(--button-text);
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s, transform 0.1s;
  margin-top: 16px;
}

.register-button:hover:not(:disabled) {
  background-color: var(--accent-hover);
}

.register-button:active:not(:disabled) {
  transform: scale(0.98);
}

.register-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.login-link {
  text-align: center;
  margin-top: 20px;
  color: var(--text-secondary);
  font-size: 0.95rem;
}

.login-link a {
  color: var(--link-color);
  text-decoration: none;
  font-weight: 500;
}

.login-link a:hover {
  color: var(--link-hover);
  text-decoration: underline;
}

/* Стили для блока аватарки */
.avatar-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 24px;
}

.avatar-preview {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: var(--accent-color);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 10px;
  overflow: hidden;
  color: var(--button-text);
  font-size: 36px;
  font-weight: bold;
}

.avatar-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

input[type="file"] {
  padding: 8px;
  background: var(--input-bg);
  border: 1px solid var(--input-border);
  border-radius: 8px;
  color: var(--text-primary);
  cursor: pointer;
  margin-bottom: 8px;
}

input[type="file"]::-webkit-file-upload-button {
  background: var(--accent-color);
  color: var(--button-text);
  border: none;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  margin-right: 10px;
}

.clear-avatar {
  background: none;
  border: none;
  color: var(--danger-color);
  font-size: 1.2rem;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background 0.2s;
}

.clear-avatar:hover:not(:disabled) {
  background: rgba(255, 0, 0, 0.1);
}

.clear-avatar:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>