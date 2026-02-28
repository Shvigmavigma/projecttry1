<template>
  <div class="task-edit-page">
    <header class="edit-header">
      <h1>Редактирование задачи</h1>
      <button class="home-button" @click="goHome" title="На главную">🏠</button>
    </header>

    <div v-if="loading" class="loading">Загрузка...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="editedTask" class="edit-card">
      <form @submit.prevent="handleSave">
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

        <div class="form-group">
          <label for="timeline">Дата начала (ДД.ММ.ГГГГ)</label>
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
          <label for="timelinend">Дата окончания (ДД.ММ.ГГГГ)</label>
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

        <div class="button-group">
          <button type="submit" class="save-button" :disabled="saving">
            {{ saving ? 'Сохранение...' : 'Сохранить' }}
          </button>
          <button type="button" class="cancel-button" @click="goBack">Отмена</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useProjectsStore } from '@/stores/projects';
import type { Task } from '@/types';

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

// Функция форматирования ввода даты (маска)
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

// Обработчики ввода с маской
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

// Функция проверки корректности даты
function isValidDate(dateStr: string): boolean {
  if (!dateStr) return true; // пустое поле допустимо
  const parts = dateStr.split('.');
  if (parts.length !== 3) return false;
  const [day, month, year] = parts.map(Number) as [number, number, number];
  if (isNaN(day) || isNaN(month) || isNaN(year)) return false;
  if (day < 1 || day > 31 || month < 1 || month > 12 || year < 1000 || year > 9999) return false;
  const date = new Date(year, month - 1, day);
  return date.getDate() === day && date.getMonth() === month - 1 && date.getFullYear() === year;
}

// Разделение старого формата "дата-дата" при загрузке
function splitOldFormat(task: Task): Task {
  // Гарантируем, что поля timeline и timelinend всегда строки (пустые, если отсутствуют)
  const newTask: Task = {
    title: task.title,
    status: task.status,
    body: task.body,
    timeline: task.timeline || '',
    timelinend: task.timelinend || '',
  };
  if (!newTask.timelinend && newTask.timeline.includes('-')) {
    const parts = newTask.timeline.split('-') as [string, string];
    newTask.timeline = parts[0];
    newTask.timelinend = parts[1];
  }
  return newTask;
}

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
      // task.value не null, используем ! для TypeScript
      editedTask.value = splitOldFormat(task.value!);
    }
  } catch (err) {
    error.value = 'Ошибка загрузки';
    console.error(err);
  } finally {
    loading.value = false;
  }
});

const handleSave = async () => {
  if (!project.value || !editedTask.value || saving.value) return;

  // Валидация дат
  timelineError.value = '';
  timelinendError.value = '';

  const startValid = isValidDate(editedTask.value.timeline || '');
  const endValid = isValidDate(editedTask.value.timelinend || '');

  if (!startValid) {
    timelineError.value = 'Неверный формат даты начала';
  }
  if (!endValid) {
    timelinendError.value = 'Неверный формат даты окончания';
  }

  if (!startValid || !endValid) {
    return;
  }

  saving.value = true;
  try {
    const updatedTasks = [...project.value.tasks];
    updatedTasks[taskIndex] = { ...editedTask.value } as Task;
    await projectsStore.updateProject(projectId, { tasks: updatedTasks });
    router.push(`/project/${projectId}/task/${taskIndex}`);
  } catch (err) {
    console.error('Ошибка при сохранении задачи:', err);
    alert('Не удалось сохранить изменения');
  } finally {
    saving.value = false;
  }
};

const goBack = () => {
  router.push(`/project/${projectId}/task/${taskIndex}`);
};

const goHome = () => {
  router.push('/main');
};
</script>

<style scoped>
.task-edit-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #f0f9f0 0%, #d4eed7 100%);
  padding: 20px;
  box-sizing: border-box;
}

.edit-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 600px;
  margin: 0 auto 20px;
}

.edit-header h1 {
  color: #1f4f22;
  font-size: 2rem;
  margin: 0;
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
}

.home-button:hover {
  background: rgba(255,255,255,0.5);
}

.edit-card {
  background: white;
  border-radius: 24px;
  box-shadow: 0 10px 30px rgba(0, 40, 0, 0.1);
  padding: 30px;
  max-width: 600px;
  margin: 0 auto;
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

input, select, textarea {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #cbd5e0;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.2s;
  outline: none;
  box-sizing: border-box;
  font-family: inherit;
}

input:focus, select:focus, textarea:focus {
  border-color: #42b983;
  box-shadow: 0 0 0 3px rgba(66, 185, 131, 0.2);
}

input.invalid {
  border-color: #f44336;
}

input.invalid:focus {
  border-color: #f44336;
  box-shadow: 0 0 0 3px rgba(244, 67, 54, 0.2);
}

.error-message {
  display: block;
  margin-top: 4px;
  color: #f44336;
  font-size: 0.85rem;
}

textarea {
  resize: vertical;
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

.loading, .error {
  text-align: center;
  color: #1f4f22;
  font-size: 1.2rem;
  padding: 40px;
}
</style>