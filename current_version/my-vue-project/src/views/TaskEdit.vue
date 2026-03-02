<template>
  <div class="task-edit-page">
    <header class="edit-header">
      <h1>Редактирование задачи</h1>
      <div class="header-actions">
        <ThemeToggle />
        <button class="home-button" @click="goHome" title="На главную">🏠</button>
      </div>
    </header>

    <div v-if="loading" class="loading">Загрузка...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="editedTask" class="edit-card">
      <form @submit.prevent="handleSave">
        <!-- Основные поля задачи -->
        <div class="form-group">
          <label for="title">Название</label>
          <input id="title" v-model="editedTask.title" type="text" required />
        </div>

        <div class="form-group">
          <label for="status">Статус</label>
          <select id="status" v-model="editedTask.status">
            <option value="в работе">В работе</option>
            <option value="ожидает">Ожидает</option>
            <option value="выполнена">Выполнена</option>
          </select>
        </div>

        <div class="form-group">
          <label for="body">Описание</label>
          <textarea id="body" v-model="editedTask.body" rows="4" required></textarea>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="timeline">Дата начала</label>
            <input
              id="timeline"
              :value="editedTask.timeline"
              @input="onTimelineInput"
              type="text"
              placeholder="01.01.2025"
              :class="{ 'invalid': timelineError }"
            />
            <span v-if="timelineError" class="error-message">{{ timelineError }}</span>
          </div>
          <div class="form-group">
            <label for="timelinend">Дата окончания</label>
            <input
              id="timelinend"
              :value="editedTask.timelinend"
              @input="onTimelinendInput"
              type="text"
              placeholder="31.12.2025"
              :class="{ 'invalid': timelinendError }"
            />
            <span v-if="timelinendError" class="error-message">{{ timelinendError }}</span>
          </div>
        </div>

        <!-- Блок подзадач -->
        <div class="form-section">
          <div class="subtasks-header">
            <h3>Подзадачи</h3>
            <button type="button" class="add-subtask-button" @click="addSubtask">+ Добавить подзадачу</button>
          </div>

          <div v-if="subtasks.length === 0" class="no-subtasks">
            Нет подзадач. Добавьте подзадачи, чтобы распределить прогресс.
          </div>

          <div v-else class="subtasks-list">
            <div
              v-for="(subtask, index) in subtasks"
              :key="subtask.id"
              class="subtask-item"
            >
              <div class="subtask-header">
                <input
                  v-model="subtask.title"
                  placeholder="Название подзадачи"
                  class="subtask-title-input"
                />
                <button
                  type="button"
                  class="remove-subtask"
                  @click="removeSubtask(index)"
                  title="Удалить подзадачу"
                >✕</button>
              </div>
              <textarea
                v-model="subtask.description"
                placeholder="Описание (необязательно)"
                rows="2"
                class="subtask-description"
              ></textarea>
              <div class="subtask-percent">
                <label>Процент от задачи:</label>
                <input
                  type="number"
                  v-model.number="subtask.progressPercent"
                  min="0"
                  max="100"
                  step="1"
                />%
                <span class="percent-hint">(сумма: {{ totalSubtasksPercent }}%)</span>
              </div>
            </div>
          </div>
          <div v-if="totalSubtasksPercent > 100" class="error-message">
            Сумма процентов подзадач не может превышать 100%! Текущая сумма: {{ totalSubtasksPercent }}%
          </div>
        </div>

        <div class="button-group">
          <button type="submit" class="save-button" :disabled="saving || totalSubtasksPercent > 100">
            {{ saving ? 'Сохранение...' : 'Сохранить' }}
          </button>
          <button type="button" class="cancel-button" @click="goBack">Отмена</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useProjectsStore } from '@/stores/projects';
import ThemeToggle from '@/components/ThemeToggle.vue';
import type { Task, SubTask } from '@/types';

const route = useRoute();
const router = useRouter();
const projectsStore = useProjectsStore();

const projectId = Number(route.params.projectId);
const taskIndex = Number(route.params.taskIndex);

const project = ref<any>(null);
const task = ref<Task | null>(null);
const editedTask = ref<Task | null>(null);
const loading = ref(true);
const error = ref('');
const saving = ref(false);
const timelineError = ref('');
const timelinendError = ref('');

// Подзадачи (локальное состояние формы)
const subtasks = ref<SubTask[]>([]);

// Вычисляем общую сумму процентов подзадач
const totalSubtasksPercent = computed(() => {
  return subtasks.value.reduce((sum, st) => sum + (st.progressPercent || 0), 0);
});

// Функции для работы с датами (без изменений)
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

const onTimelineInput = (e: Event) => {
  const input = e.target as HTMLInputElement;
  const formatted = formatDateInput(input.value);
  if (editedTask.value) {
    editedTask.value.timeline = formatted;
  }
  timelineError.value = '';
};

const onTimelinendInput = (e: Event) => {
  const input = e.target as HTMLInputElement;
  const formatted = formatDateInput(input.value);
  if (editedTask.value) {
    editedTask.value.timelinend = formatted;
  }
  timelinendError.value = '';
};

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

function splitOldFormat(task: Task): Task {
  const timeline = task.timeline || '';
  const timelinend = task.timelinend || '';
  const newTask: Task = {
    title: task.title,
    status: task.status,
    body: task.body,
    timeline,
    timelinend,
  };
  if (!timelinend && timeline.includes('-')) {
    const parts = timeline.split('-') as [string, string];
    newTask.timeline = parts[0];
    newTask.timelinend = parts[1];
  }
  return newTask;
}

// Загрузка существующей задачи
onMounted(async () => {
  if (isNaN(projectId) || isNaN(taskIndex) || taskIndex < 0) {
    error.value = 'Некорректные параметры';
    loading.value = false;
    return;
  }

  try {
    project.value = await projectsStore.fetchProjectById(projectId);
    if (!project.value || !project.value.tasks || !project.value.tasks[taskIndex]) {
      error.value = 'Задача не найдена';
    } else {
      task.value = project.value.tasks[taskIndex];
      editedTask.value = splitOldFormat(task.value!);
      // Инициализируем подзадачи
      subtasks.value = task.value.subtasks ? task.value.subtasks.map(st => ({ ...st })) : [];
    }
  } catch (err) {
    error.value = 'Ошибка загрузки';
    console.error(err);
  } finally {
    loading.value = false;
  }
});

// Управление подзадачами
function addSubtask() {
  subtasks.value.push({
    id: Date.now() + Math.random().toString(36).substr(2, 9),
    title: '',
    description: '',
    progressPercent: 0,
    completed: false,
  });
}

function removeSubtask(index: number) {
  subtasks.value.splice(index, 1);
}

// Сохранение
async function handleSave() {
  if (!project.value || !editedTask.value || saving.value) return;

  // Валидация дат
  timelineError.value = '';
  timelinendError.value = '';

  const startValid = isValidDate(editedTask.value.timeline || '');
  const endValid = isValidDate(editedTask.value.timelinend || '');

  if (!startValid) timelineError.value = 'Неверный формат даты начала';
  if (!endValid) timelinendError.value = 'Неверный формат даты окончания';
  if (!startValid || !endValid) return;

  // Проверка суммы процентов подзадач
  if (totalSubtasksPercent.value > 100) {
    alert(`Сумма процентов подзадач (${totalSubtasksPercent.value}%) не может превышать 100%`);
    return;
  }

  saving.value = true;
  try {
    const updatedTasks = [...project.value.tasks];
    updatedTasks[taskIndex] = {
      ...editedTask.value,
      subtasks: subtasks.value, // сохраняем подзадачи
    } as Task;
    await projectsStore.updateProject(projectId, { tasks: updatedTasks });
    router.push(`/project/${projectId}/task/${taskIndex}`);
  } catch (err) {
    console.error('Ошибка при сохранении задачи:', err);
    alert('Не удалось сохранить изменения');
  } finally {
    saving.value = false;
  }
}

// Навигация
const goBack = () => router.push(`/project/${projectId}/task/${taskIndex}`);
const goHome = () => router.push('/main');
</script>

<style scoped>
.task-edit-page {
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
  max-width: 600px;
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
  box-shadow: var(--shadow-strong);
  padding: 40px;
  max-width: 600px;
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
  box-shadow: 0 0 0 3px rgba(1, 69, 172, 0.2);
}

.light-theme input:focus,
.light-theme select:focus,
.light-theme textarea:focus {
  box-shadow: 0 0 0 3px rgba(66, 185, 131, 0.2);
}

input.invalid {
  border-color: var(--danger-color);
}

input.invalid:focus {
  border-color: var(--danger-color);
  box-shadow: 0 0 0 3px rgba(244, 67, 54, 0.2);
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

/* Стили для подзадач */
.form-section {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 2px dashed var(--border-color);
}

.subtasks-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.add-subtask-button {
  background: var(--accent-color);
  color: var(--button-text);
  border: none;
  border-radius: 30px;
  padding: 6px 12px;
  font-size: 0.9rem;
  cursor: pointer;
}

.no-subtasks {
  text-align: center;
  color: var(--text-secondary);
  font-style: italic;
  padding: 1rem;
  border: 1px dashed var(--border-color);
  border-radius: 8px;
}

.subtasks-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.subtask-item {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 1rem;
  background: var(--bg-card);
}

.subtask-header {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.subtask-title-input {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid var(--input-border);
  border-radius: 4px;
  background: var(--input-bg);
  color: var(--text-primary);
}

.remove-subtask {
  background: none;
  border: none;
  color: var(--danger-color);
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0 0.5rem;
}

.subtask-description {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid var(--input-border);
  border-radius: 4px;
  background: var(--input-bg);
  color: var(--text-primary);
  margin-bottom: 0.5rem;
  resize: vertical;
}

.subtask-percent {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.subtask-percent input {
  width: 70px;
  padding: 0.3rem;
  border: 1px solid var(--input-border);
  border-radius: 4px;
  background: var(--input-bg);
  color: var(--text-primary);
}

.percent-hint {
  font-size: 0.85rem;
  color: var(--text-secondary);
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

.loading, .error {
  text-align: center;
  color: var(--text-primary);
  font-size: 1.2rem;
  padding: 40px;
}
</style>