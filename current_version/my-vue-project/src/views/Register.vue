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
          <ClassInput
            id="class"
            v-model="form.class_"
            placeholder="3.1 – 11.6"
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

        <!-- Поле подтверждение пароля -->
        <div class="form-group">
          <label for="confirmPassword">Подтверждение пароля</label>
          <input
            id="confirmPassword"
            v-model="confirmPassword"
            type="password"
            placeholder="Повторите пароль"
            required
            @input="passwordMatchError = false"
          />
        </div>

        <!-- Чекбокс для выбора типа регистрации -->
        <div class="form-group checkbox-group">
          <label class="checkbox-label">
            <input
              type="checkbox"
              v-model="requireEmailVerification"
              class="checkbox-input"
            />
            <span class="checkbox-text">
              Подтвердить email (на указанный адрес будет отправлен код)
            </span>
          </label>
          <div v-if="requireEmailVerification" class="verification-info">
            <small>✉️ Код подтверждения будет отправлен на {{ form.email || 'указанный email' }}</small>
          </div>
        </div>

        <!-- Отображение ошибки, если пароли не совпадают -->
        <div v-if="passwordMatchError" class="error-message">
          Пароли не совпадают
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
import ClassInput from '@/components/ClassInput.vue';
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

// Поле подтверждения пароля
const confirmPassword = ref('');
const passwordMatchError = ref(false);

// Чекбокс для выбора типа регистрации
const requireEmailVerification = ref(false);

const onFileChange = (event: Event) => {
  const input = event.target as HTMLInputElement;
  if (!input.files || input.files.length === 0) {
    clearAvatar();
    return;
  }

  const file = input.files[0];
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
  // Проверка совпадения паролей
  if (form.password !== confirmPassword.value) {
    passwordMatchError.value = true;
    return;
  }
  passwordMatchError.value = false;

  // Проверка email, если выбрана верификация
  if (requireEmailVerification.value && !form.email) {
    errorMessage.value = 'Email обязателен для подтверждения';
    return;
  }

  loading.value = true;
  errorMessage.value = '';

  const { class_, ...rest } = form;
  const userData = {
    ...rest,
    class: class_,
    password: form.password,
  };

  try {
    if (requireEmailVerification.value) {
      // Регистрация с подтверждением по email
      await handleEmailVerification(userData);
    } else {
      // Обычная регистрация (без подтверждения)
      await handleSimpleRegistration(userData);
    }
  } catch (error: any) {
    console.error('Registration error:', error);
    errorMessage.value =
      error.response?.data?.detail || 'Произошла ошибка при регистрации';
  } finally {
    loading.value = false;
  }
};

// Обычная регистрация (без подтверждения email)
const handleSimpleRegistration = async (userData: any) => {
  try {
    // Создаем пользователя через отдельный эндпоинт
    const response = await axios.post('http://localhost:8000/users/', userData);
    const newUser = response.data;
    
    console.log('User created:', newUser);
    console.log('is_active:', newUser.is_active);    // true
    console.log('is_verified:', newUser.is_verified); // false
    
    // Автоматически логиним пользователя
    const loginSuccess = await authStore.login(userData.nickname, userData.password);
    
    if (!loginSuccess) {
      throw new Error('Не удалось выполнить автоматический вход');
    }

    // Загружаем аватарку, если есть
    if (avatarFile.value && authStore.user?.id) {
      await uploadAvatar(authStore.user.id);
    }
    
    router.push('/main');
  } catch (error: any) {
    console.error('Simple registration error:', error);
    if (error.response?.status === 400) {
      const detail = error.response.data?.detail;
      if (typeof detail === 'string') {
        errorMessage.value = detail;
      } else if (Array.isArray(detail)) {
        errorMessage.value = detail.map((d: any) => d.msg).join(', ');
      } else {
        errorMessage.value = 'Ошибка регистрации. Возможно, пользователь с таким никнеймом или email уже существует.';
      }
    } else {
      throw error;
    }
  }
};

// Регистрация с подтверждением по email
const handleEmailVerification = async (userData: any) => {
  // 1. Запрос кода подтверждения
  await axios.post('http://localhost:8000/auth/request-verification-code', {
    email: form.email
  });

  // 2. Сохраняем данные пользователя в sessionStorage
  sessionStorage.setItem('pending_registration', JSON.stringify(userData));

  // 3. Сохраняем аватарку, если есть
  if (avatarFile.value) {
    const reader = new FileReader();
    reader.onload = () => {
      sessionStorage.setItem('pending_avatar', reader.result as string);
    };
    reader.readAsDataURL(avatarFile.value);
    
    // Даем время на чтение файла
    setTimeout(() => {
      router.push(`/verify-email?email=${encodeURIComponent(form.email)}`);
    }, 500);
  } else {
    router.push(`/verify-email?email=${encodeURIComponent(form.email)}`);
  }
};

// Загрузка аватарки
const uploadAvatar = async (userId: number) => {
  if (!avatarFile.value) return;
  
  const formData = new FormData();
  formData.append('file', avatarFile.value);

  const response = await axios.post(
    `http://localhost:8000/users/${userId}/avatar`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  );

  // Обновляем данные пользователя в store
  if (authStore.user) {
    authStore.user.avatar = response.data.avatar;
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

input[type="text"],
input[type="email"],
input[type="password"],
input[type="number"] {
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

.checkbox-group {
  margin-top: 20px;
  padding-top: 10px;
  border-top: 1px solid var(--border-color);
}

.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  cursor: pointer;
  font-weight: normal;
  color: var(--text-primary);
}

.checkbox-input {
  width: 18px;
  height: 18px;
  margin-top: 2px;
  cursor: pointer;
  accent-color: var(--accent-color);
}

.checkbox-text {
  flex: 1;
  font-size: 0.95rem;
  line-height: 1.4;
}

.verification-info {
  margin-top: 8px;
  padding: 8px 12px;
  background: rgba(66, 185, 131, 0.1);
  border-radius: 6px;
  color: var(--accent-color);
  font-size: 0.9rem;
  border-left: 3px solid var(--accent-color);
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
  width: 100%;
  box-sizing: border-box;
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