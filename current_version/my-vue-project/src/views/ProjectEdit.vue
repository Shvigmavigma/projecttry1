<template>
  <div class="project-edit-page">
    <header class="edit-header">
      <h1>{{ isEdit ? 'Редактирование проекта' : 'Создание нового проекта' }}</h1>
      <div class="header-actions">
        <ThemeToggle />
        <button class="home-button" @click="goHome" title="На главную">🏠</button>
      </div>
    </header>

    <div class="edit-card">
      <form @submit.prevent="handleSubmit">
        <!-- Основная информация о проекте -->
        <div class="form-section">
          <h2>Основная информация</h2>
          <div class="form-group">
            <label for="title">Название проекта</label>
            <input id="title" v-model="form.title" type="text" required />
          </div>

          <div class="form-group">
            <label for="body">Описание</label>
            <textarea id="body" v-model="form.body" rows="4" required></textarea>
          </div>

          <div class="form-group">
            <label for="underbody">Дополнительная информация (необязательно)</label>
            <textarea id="underbody" v-model="form.underbody" rows="2"></textarea>
          </div>
        </div>

        <!-- Управление авторами -->
        <div class="form-section">
          <h2>Авторы проекта</h2>
          <div class="authors-section">
            <div class="current-authors" v-if="authors.length > 0">
              <span class="authors-label">Текущие авторы:</span>
              <div class="author-tags">
                <span
                  v-for="author in authors"
                  :key="author.id"
                  class="author-tag"
                >
                  {{ author.nickname }}
                  <button
                    type="button"
                    class="remove-author"
                    @click="removeAuthor(author.id)"
                    :disabled="authors.length === 1"
                    :title="authors.length === 1 ? 'Нельзя удалить единственного автора' : 'Удалить автора'"
                  >✕</button>
                </span>
              </div>
            </div>

            <div class="author-search">
              <label for="author-search">Добавить автора по нику</label>
              <input
                id="author-search"
                v-model="searchQuery"
                type="text"
                placeholder="Введите никнейм..."
                @input="searchAuthors"
              />
              <div v-if="searchResults.length > 0" class="search-results">
                <div
                  v-for="user in searchResults"
                  :key="user.id"
                  class="search-result-item"
                  @click.stop="addAuthor(user.id)"
                >
                  {{ user.nickname }} ({{ user.fullname }})
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Управление задачами -->
        <div class="form-section">
          <div class="tasks-header">
            <h2>Задачи проекта</h2>
            <button type="button" class="add-task-button" @click="addTask">+ Добавить задачу</button>
          </div>

          <div v-if="tasks.length === 0" class="no-tasks">
            Пока нет задач. Нажмите "Добавить задачу", чтобы создать первую.
          </div>

          <div v-else class="tasks-list">
            <div
              v-for="(task, index) in tasks"
              :key="index"
              class="task-item"
              :class="{ 'expanded': task.expanded }"
            >
              <!-- Компактное отображение задачи -->
              <div v-if="!task.expanded" class="task-compact" @click="toggleTaskExpand(index)">
                <span class="task-title">{{ task.title || 'Без названия' }}</span>
                <button
                  type="button"
                  class="delete-task-button"
                  @click.stop="removeTask(index)"
                  title="Удалить задачу"
                >✕</button>
              </div>

              <!-- Развёрнутая форма задачи -->
              <div v-else class="task-form">
                <div class="task-form-header">
                  <h3>{{ task.id ? 'Редактирование задачи' : 'Новая задача' }}</h3>
                  <button type="button" class="close-task-form" @click="toggleTaskExpand(index)">✕</button>
                </div>

                <div class="form-group">
                  <label :for="'task-title-'+index">Название задачи</label>
                  <input :id="'task-title-'+index" v-model="task.title" type="text" required />
                </div>

                <div class="form-group">
                  <label :for="'task-status-'+index">Статус</label>
                  <select :id="'task-status-'+index" v-model="task.status">
                    <option value="в работе">В работе</option>
                    <option value="ожидает">Ожидает</option>
                    <option value="выполнена">Выполнена</option>
                  </select>
                </div>

                <div class="form-group">
                  <label :for="'task-body-'+index">Описание задачи</label>
                  <textarea :id="'task-body-'+index" v-model="task.body" rows="2" required></textarea>
                </div>

                <div class="form-row">
                  <div class="form-group">
                    <label :for="'task-start-'+index">Дата начала (ДД.ММ.ГГГГ)</label>
                    <input
                      :id="'task-start-'+index"
                      :value="task.timeline"
                      @input="updateTaskDate(index, 'timeline', $event)"
                      type="text"
                      placeholder="01.01.2025"
                      :class="{ 'invalid': task.startError }"
                    />
                    <span v-if="task.startError" class="error-message">{{ task.startError }}</span>
                  </div>

                  <div class="form-group">
                    <label :for="'task-end-'+index">Дата окончания (ДД.ММ.ГГГГ)</label>
                    <input
                      :id="'task-end-'+index"
                      :value="task.timelinend"
                      @input="updateTaskDate(index, 'timelinend', $event)"
                      type="text"
                      placeholder="31.12.2025"
                      :class="{ 'invalid': task.endError }"
                    />
                    <span v-if="task.endError" class="error-message">{{ task.endError }}</span>
                  </div>
                </div>

                <div class="task-form-actions">
                  <button type="button" class="save-task-button" @click="saveTask(index)">✓ Готово</button>
                  <button type="button" class="cancel-task-button" @click="toggleTaskExpand(index)">Отмена</button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Кнопки сохранения/отмены -->
        <div class="form-actions">
          <button type="submit" class="save-button" :disabled="saving">
            {{ saving ? 'Сохранение...' : (isEdit ? 'Сохранить изменения' : 'Создать проект') }}
          </button>
          <button type="button" class="cancel-button" @click="goBack">Отмена</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useProjectsStore } from '@/stores/projects';
import { useAuthStore } from '@/stores/auth';
import { useUsersStore } from '@/stores/users';
import ThemeToggle from '@/components/ThemeToggle.vue';
import type { Project, Task, User } from '@/types';

const route = useRoute();
const router = useRouter();
const projectsStore = useProjectsStore();
const authStore = useAuthStore();
const usersStore = useUsersStore();

const isEdit = computed(() => route.params.id !== undefined);
const saving = ref(false);

// Форма проекта
const form = reactive({
  title: '',
  body: '',
  underbody: '',
});

// Авторы проекта (объекты User)
const authors = ref<User[]>([]);

// Поиск авторов
const searchQuery = ref('');
const searchResults = ref<User[]>([]);

// Загрузка пользователей при монтировании, если не загружены
onMounted(async () => {
  if (usersStore.users.length === 0) {
    await usersStore.fetchAllUsers();
  }

  if (isEdit.value) {
    const id = Number(route.params.id);
    if (isNaN(id)) {
      console.error('Неверный ID проекта');
      return;
    }
    const project = await projectsStore.fetchProjectById(id);
    if (project) {
      form.title = project.title;
      form.body = project.body;
      form.underbody = project.underbody || '';

      // Загружаем авторов из usersStore
      authors.value = usersStore.users.filter(u => project.authors_ids.includes(u.id));

      tasks.value = (project.tasks || []).map(task => ({
        ...task,
        expanded: false,
        startError: undefined,
        endError: undefined,
      }));
    }
  }
});

// Поиск пользователей
function searchAuthors() {
  if (!searchQuery.value.trim()) {
    searchResults.value = [];
    return;
  }
  const q = searchQuery.value.toLowerCase();
  searchResults.value = usersStore.users.filter(u =>
    u.nickname.toLowerCase().includes(q) &&
    !authors.value.some(a => a.id === u.id)
  ).slice(0, 10);
}

// Добавить автора
function addAuthor(userId: number) {
  const user = usersStore.users.find(u => u.id === userId);
  if (user && !authors.value.some(a => a.id === userId)) {
    authors.value.push(user);
  }
  searchQuery.value = '';
  searchResults.value = [];
}

// Удалить автора (с защитой от удаления последнего)
function removeAuthor(userId: number) {
  if (authors.value.length === 1) {
    alert('Проект должен иметь хотя бы одного автора');
    return;
  }
  authors.value = authors.value.filter(a => a.id !== userId);
}

// Тип для задачи с дополнительными UI-полями (id опциональный)
type EditableTask = Omit<Task, 'id'> & {
  id?: number;
  expanded: boolean;
  startError?: string;
  endError?: string;
};

const tasks = ref<EditableTask[]>([]);

// Форматирование даты (маска)
function formatDateInput(value: string): string {
  let digits = value.replace(/\D/g, '');
  if (digits.length > 8) digits = digits.slice(0, 8);
  let formatted = '';
  if (digits.length > 0) {
    formatted = digits.slice(0, 2);
    if (digits.length > 2) {
      formatted += '.' + digits.slice(2, 4);
    }
    if (digits.length > 4) {
      formatted += '.' + digits.slice(4, 8);
    }
  }
  return formatted;
}

// Обновление даты с маской
function updateTaskDate(index: number, field: 'timeline' | 'timelinend', event: Event) {
  const task = tasks.value[index];
  if (!task) return;
  const input = event.target as HTMLInputElement;
  const formatted = formatDateInput(input.value);
  task[field] = formatted;
  if (field === 'timeline') task.startError = undefined;
  else task.endError = undefined;
}

// Парсинг даты (для проверки)
function parseDate(dateStr: string): Date | null {
  if (!dateStr) return null;
  const parts = dateStr.split('.');
  if (parts.length !== 3) return null;
  const [day, month, year] = parts.map(Number) as [number, number, number];
  if (isNaN(day) || isNaN(month) || isNaN(year)) return null;
  return new Date(year, month - 1, day);
}

// Валидация даты
function isValidDate(dateStr: string): boolean {
  if (!dateStr) return true;
  const parts = dateStr.split('.');
  if (parts.length !== 3) return false;
  const [day, month, year] = parts.map(Number) as [number, number, number];
  if (isNaN(day) || isNaN(month) || isNaN(year)) return false;
  if (day < 1 || day > 31 || month < 1 || month > 12 || year < 1000 || year > 9999) return false;
  const date = new Date(year, month - 1, day);
  return date.getDate() === day && date.getMonth() === month - 1 && date.getFullYear() === year;
}

// Добавить новую задачу
function addTask() {
  tasks.value.push({
    title: '',
    status: 'ожидает',
    body: '',
    timeline: '',
    timelinend: '',
    expanded: true,
    startError: undefined,
    endError: undefined,
  });
}

// Сохранить задачу (проверка и сворачивание)
function saveTask(index: number) {
  const task = tasks.value[index];
  if (!task) return;
  if (!task.title.trim()) {
    alert('Название задачи не может быть пустым');
    return;
  }
  if (!task.body.trim()) {
    alert('Описание задачи не может быть пустым');
    return;
  }

  task.startError = undefined;
  task.endError = undefined;
  let valid = true;

  if (!isValidDate(task.timeline || '')) {
    task.startError = 'Неверный формат даты начала';
    valid = false;
  }
  if (!isValidDate(task.timelinend || '')) {
    task.endError = 'Неверный формат даты окончания';
    valid = false;
  }

  if (!valid) return;

  if (task.timeline && task.timelinend) {
    const start = parseDate(task.timeline);
    const end = parseDate(task.timelinend);
    if (start && end && start > end) {
      alert('Дата начала не может быть позже даты окончания');
      return;
    }
  }

  task.expanded = false;
}

// Удалить задачу
function removeTask(index: number) {
  if (index >= 0 && index < tasks.value.length) {
    tasks.value.splice(index, 1);
  }
}

// Развернуть/свернуть задачу
function toggleTaskExpand(index: number) {
  const task = tasks.value[index];
  if (task) {
    task.expanded = !task.expanded;
  }
}

// Сохранение проекта
async function handleSubmit() {
  if (!form.title.trim() || !form.body.trim()) {
    alert('Заполните название и описание проекта');
    return;
  }

  for (let i = 0; i < tasks.value.length; i++) {
    if (tasks.value[i]?.expanded) {
      alert('Завершите редактирование всех задач (нажмите "Готово") перед сохранением проекта');
      return;
    }
  }

  const projectData = {
    title: form.title,
    body: form.body,
    underbody: form.underbody || '',
    authors_ids: authors.value.map(a => a.id),
    tasks: tasks.value.map(({ expanded, startError, endError, ...task }) => task),
  };

  saving.value = true;
  try {
    if (isEdit.value) {
      const id = Number(route.params.id);
      if (isNaN(id)) {
        throw new Error('Неверный ID проекта');
      }
      await projectsStore.updateProject(id, projectData);
      router.push(`/project/${id}`);
    } else {
      if (!authStore.userId) {
        throw new Error('Пользователь не авторизован');
      }
      // Добавляем текущего пользователя, если его ещё нет в списке
      const currentUserId = authStore.userId;
      if (!projectData.authors_ids.includes(currentUserId)) {
        projectData.authors_ids.push(currentUserId);
      }
      const payload = projectData;
      const created = await projectsStore.createProject(payload);
      router.push(`/project/${created.id}`);
    }
  } catch (err) {
    console.error('Ошибка сохранения проекта:', err);
    alert('Не удалось сохранить проект');
  } finally {
    saving.value = false;
  }
}

// Навигация
const goHome = () => router.push('/main');
const goBack = () => router.go(-1);
</script>

<style scoped>
.project-edit-page {
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
  max-width: 800px;
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
  align-items: center;
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
  box-shadow: var(--shadow-strong);
  padding: 40px;
  max-width: 800px;
  margin: 0 auto;
  transition: background 0.3s;
}

.form-section {
  margin-bottom: 40px;
  padding-bottom: 20px;
  border-bottom: 2px dashed var(--border-color);
}

.form-section h2 {
  color: var(--heading-color);
  margin-bottom: 20px;
  font-weight: 500;
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

input, select, textarea {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid var(--input-border);
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.2s, box-shadow 0.2s;
  outline: none;
  box-sizing: border-box;
  font-family: inherit;
  background: var(--input-bg);
  color: var(--text-primary);
}

input:focus, select:focus, textarea:focus {
  border-color: var(--accent-color);
  box-shadow: 0 0 0 3px rgba(66, 185, 131, 0.2);
}

.dark-theme input:focus,
.dark-theme select:focus,
.dark-theme textarea:focus {
  box-shadow: 0 0 0 3px rgba(1, 69, 172, 0.2);
}

input.invalid {
  border-color: var(--danger-color);
}

.error-message {
  display: block;
  margin-top: 4px;
  color: var(--danger-color);
  font-size: 0.85rem;
}

textarea {
  resize: vertical;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

/* Стили для авторов */
.authors-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.current-authors {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.authors-label {
  font-weight: 500;
  color: var(--text-secondary);
}

.author-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.author-tag {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  padding: 6px 12px;
  border-radius: 30px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.9rem;
  color: var(--text-primary);
}

.remove-author {
  background: none;
  border: none;
  color: var(--danger-color);
  font-size: 1.1rem;
  cursor: pointer;
  padding: 0 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  transition: background 0.2s;
}

.remove-author:hover:not(:disabled) {
  background: var(--danger-bg);
}

.remove-author:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.author-search {
  position: relative;
}

.search-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  margin-top: 4px;
  max-height: 200px;
  overflow-y: auto;
  z-index: 10;
  box-shadow: var(--shadow);
}

.search-result-item {
  padding: 10px 16px;
  cursor: pointer;
  border-bottom: 1px solid var(--border-color);
  transition: background 0.2s;
  color: var(--text-primary);
}

.search-result-item:hover {
  background: var(--bg-page);
}

.search-result-item:last-child {
  border-bottom: none;
}

/* Стили для задач */
.tasks-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.add-task-button {
  background: var(--accent-color);
  color: var(--button-text);
  border: none;
  border-radius: 30px;
  padding: 8px 16px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.add-task-button:hover {
  background: var(--accent-hover);
}

.no-tasks {
  text-align: center;
  color: var(--text-secondary);
  font-style: italic;
  padding: 20px;
  background: var(--bg-page);
  border-radius: 12px;
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-item {
  border: 1px solid var(--border-color);
  border-radius: 12px;
  background: var(--bg-card);
  transition: all 0.2s;
}

.task-item.expanded {
  border-color: var(--accent-color);
  box-shadow: var(--shadow);
}

.task-compact {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  border-radius: 12px;
}

.task-compact:hover {
  background: var(--bg-page);
}

.task-title {
  font-weight: 500;
  color: var(--text-primary);
  overflow-wrap: break-word;
  word-wrap: break-word;
  hyphens: auto;
}

.delete-task-button {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  color: var(--danger-color);
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.delete-task-button:hover {
  background: var(--danger-bg);
}

.task-form {
  padding: 20px;
  border-top: 1px solid var(--border-color);
}

.task-form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.task-form-header h3 {
  color: var(--heading-color);
  margin: 0;
  font-weight: 500;
}

.close-task-form {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: var(--text-secondary);
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.close-task-form:hover {
  background: var(--bg-page);
}

.task-form-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}

.save-task-button, .cancel-task-button {
  flex: 1;
  padding: 10px;
  border: none;
  border-radius: 30px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.save-task-button {
  background: var(--accent-color);
  color: var(--button-text);
}

.save-task-button:hover {
  background: var(--accent-hover);
}

.cancel-task-button {
  background: var(--bg-page);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.cancel-task-button:hover {
  background: var(--bg-card);
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 40px;
}

.save-button, .cancel-button {
  flex: 1;
  padding: 14px;
  border: none;
  border-radius: 50px;
  font-size: 1.1rem;
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

.loading, .error {
  text-align: center;
  color: var(--text-primary);
  font-size: 1.2rem;
  padding: 40px;
}
</style>