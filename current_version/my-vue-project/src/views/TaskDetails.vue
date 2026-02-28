<template>
  <div class="task-details-page">
    <header class="details-header">
      <h1>Детали задачи</h1>
      <div class="header-buttons">
        <router-link :to="`/project/${projectId}/task/${taskIndex}/edit`">
          <button class="edit-task-button" title="Редактировать задачу">✎</button>
        </router-link>
        <button class="home-button" @click="goHome" title="На главную">🏠</button>
        <button class="back-button" @click="goBack" title="Вернуться к проекту">◀ Назад</button>
      </div>
    </header>

    <div v-if="loading" class="loading">Загрузка...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="task" class="task-card" :class="taskStatusClass">
      <h2 class="task-title">{{ task.title }}</h2>

      <div class="task-section">
        <h3>Статус</h3>
        <p>{{ task.status }}</p>
      </div>

      <div class="task-section">
        <h3>Описание</h3>
        <p>{{ task.body }}</p>
      </div>

      <div class="task-section">
        <h3>Период выполнения</h3>
        <p>
          <span :class="{ 'invalid-date': !isValidDateFormat(task.timeline) }">
            {{ task.timeline || '?' }}
          </span>
          –
          <span :class="{ 'invalid-date': !isValidDateFormat(task.timelinend) }">
            {{ task.timelinend || '?' }}
          </span>
        </p>
        <span v-if="!isValidDateFormat(task.timeline) && task.timeline" class="date-warning">
          ⚠️ Неверный формат даты начала
        </span>
        <span v-if="!isValidDateFormat(task.timelinend) && task.timelinend" class="date-warning">
          ⚠️ Неверный формат даты окончания
        </span>
      </div>

      <!-- Диаграмма Ганта с прогрессом -->
      <div class="gantt-section">
        <h3>Прогресс выполнения</h3>
        <div class="gantt-container">
          <div class="gantt-bar-container">
            <div
              class="gantt-bar"
              :style="{ width: progress + '%', backgroundColor: barColor }"
              :title="`Прогресс: ${progress.toFixed(1)}%`"
            ></div>
            <span class="gantt-dates">{{ task.timeline || '?' }} – {{ task.timelinend || '?' }}</span>
          </div>
          <div class="gantt-labels">
            <span>{{ task.timeline || '?' }}</span>
            <span>Сегодня</span>
            <span>{{ task.timelinend || '?' }}</span>
          </div>
        </div>
      </div>

      <!-- Кнопки действий -->
      <div class="action-buttons">
        <!-- Для активных задач: кнопка завершения -->
        <div v-if="task.status !== 'выполнена'">
          <button class="complete-button" @click="completeTask" :disabled="actionInProgress">
            {{ actionInProgress ? 'Завершение...' : '✓ Завершить задачу' }}
          </button>
        </div>

        <!-- Для выполненных задач: кнопка возобновления и выбор статуса -->
        <div v-else>
          <button
            v-if="!showRenewOptions"
            class="renew-button"
            @click="showRenewOptions = true"
            :disabled="actionInProgress"
          >
            🔄 Возобновить
          </button>
          <div v-else class="renew-options">
            <button
              class="status-option work"
              @click="updateTaskStatus('в работе')"
              :disabled="actionInProgress"
            >
              В работе
            </button>
            <button
              class="status-option waiting"
              @click="updateTaskStatus('ожидает')"
              :disabled="actionInProgress"
            >
              Ожидает
            </button>
            <button class="status-option cancel" @click="showRenewOptions = false">Отмена</button>
          </div>
        </div>
      </div>

      <!-- Бейджики состояния -->
      <div class="status-badges">
        <span v-if="isInvalid" class="badge invalid">Невозможный дедлайн</span>
        <span v-if="isOverdue" class="badge overdue">Просрочено</span>
        <span v-if="isUrgent && !isOverdue && !isInvalid" class="badge urgent">Срочно</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
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
const loading = ref(true);
const error = ref('');
const actionInProgress = ref(false);
const showRenewOptions = ref(false);

// Функция проверки формата даты ДД.ММ.ГГГГ
// Парсинг даты из строки "DD.MM.YYYY"
function parseDate(dateStr?: string): Date | null {
  if (!dateStr) return null;
  const parts = dateStr.split('.');
  if (parts.length !== 3) return null;
  // Явно указываем, что после map получится кортеж из трёх чисел
  const [day, month, year] = parts.map(Number) as [number, number, number];
  // Дополнительная проверка на NaN (хотя map уже дал числа)
  if (isNaN(day) || isNaN(month) || isNaN(year)) return null;
  return new Date(year, month - 1, day);
}

// Функция проверки формата даты ДД.ММ.ГГГГ
function isValidDateFormat(dateStr?: string): boolean {
  if (!dateStr) return true; // пустая строка допустима
  const parts = dateStr.split('.');
  if (parts.length !== 3) return false;
  const [day, month, year] = parts.map(Number) as [number, number, number];
  if (isNaN(day) || isNaN(month) || isNaN(year)) return false;
  if (day < 1 || day > 31 || month < 1 || month > 12 || year < 1000 || year > 9999) return false;
  const date = new Date(year, month - 1, day);
  return date.getDate() === day && date.getMonth() === month - 1 && date.getFullYear() === year;
}

function formatTaskDates(task: Task): string {
  if (task.timelinend) {
    return `${task.timeline || '?'} – ${task.timelinend}`;
  } else if (task.timeline && task.timeline.includes('-')) {
    const parts = task.timeline.split('-');
    if (parts.length === 2) return `${parts[0]} – ${parts[1]}`;
  }
  return task.timeline || '?';
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
    }
  } catch (err) {
    error.value = 'Ошибка загрузки';
    console.error(err);
  } finally {
    loading.value = false;
  }
});

// Вычисляемые статусы
const isInvalid = computed(() => {
  if (!task.value) return false;
  let startStr = task.value.timeline;
  let endStr = task.value.timelinend;
  if (!endStr && startStr && startStr.includes('-')) {
    const parts = startStr.split('-');
    startStr = parts[0] || '';
    endStr = parts[1] || '';
  }
  const start = parseDate(startStr);
  const end = parseDate(endStr);
  const startValid = isValidDateFormat(startStr);
  const endValid = isValidDateFormat(endStr);
  // Если даты заданы, но формат неверный, считаем задачу некорректной
  if ((startStr && !startValid) || (endStr && !endValid)) return true;
  return !start || !end || start > end;
});

const isOverdue = computed(() => {
  if (!task.value || isInvalid.value) return false;
  let endStr = task.value.timelinend;
  if (!endStr && task.value.timeline && task.value.timeline.includes('-')) {
    const parts = task.value.timeline.split('-');
    endStr = parts[1] || '';
  }
  const end = parseDate(endStr);
  if (!end) return false;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return today > end && task.value.status !== 'выполнена';
});

const isUrgent = computed(() => {
  if (!task.value || isInvalid.value || isOverdue.value) return false;
  let startStr = task.value.timeline;
  let endStr = task.value.timelinend;
  if (!endStr && startStr && startStr.includes('-')) {
    const parts = startStr.split('-');
    startStr = parts[0] || '';
    endStr = parts[1] || '';
  }
  const start = parseDate(startStr);
  const end = parseDate(endStr);
  if (!start || !end) return false; // добавили проверку на null
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const totalDuration = (end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24);
  if (totalDuration <= 0) return false;
  const elapsed = (today.getTime() - start.getTime()) / (1000 * 60 * 60 * 24);
  if (elapsed < 0) return false;
  const prog = elapsed / totalDuration;
  return prog > 2 / 3 && task.value.status !== 'выполнена';
});

const progress = computed(() => {
  if (!task.value || isInvalid.value) return 0;
  let startStr = task.value.timeline;
  let endStr = task.value.timelinend;
  if (!endStr && startStr && startStr.includes('-')) {
    const parts = startStr.split('-');
    startStr = parts[0] || '';
    endStr = parts[1] || '';
  }
  const start = parseDate(startStr);
  const end = parseDate(endStr);
  if (!start || !end) return 0; // если даты не определены, прогресс 0
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const totalDuration = (end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24);
  if (totalDuration <= 0) return today >= start ? 100 : 0;
  let elapsed = (today.getTime() - start.getTime()) / (1000 * 60 * 60 * 24);
  if (elapsed < 0) elapsed = 0;
  if (elapsed > totalDuration) elapsed = totalDuration;
  return (elapsed / totalDuration) * 100;
});

const barColor = computed(() => {
  if (isInvalid.value) return '#9e9e9e';
  if (isOverdue.value) return '#f44336';
  if (isUrgent.value) return '#ff9800';
  return '#42b983';
});

const taskStatusClass = computed(() => {
  if (isInvalid.value) return 'task-invalid';
  if (isOverdue.value) return 'task-overdue';
  if (isUrgent.value) return 'task-urgent';
  return '';
});

// Метод завершения задачи
const completeTask = async () => {
  if (!project.value || !task.value || actionInProgress.value) return;
  actionInProgress.value = true;
  try {
    const updatedTasks = [...project.value.tasks];
    updatedTasks[taskIndex] = { ...updatedTasks[taskIndex], status: 'выполнена' } as Task;
    await projectsStore.updateProject(projectId, { tasks: updatedTasks });
    router.push(`/project/${projectId}`);
  } catch (err) {
    console.error('Ошибка при завершении задачи:', err);
    alert('Не удалось завершить задачу');
  } finally {
    actionInProgress.value = false;
  }
};

// Метод обновления статуса (для возобновления)
const updateTaskStatus = async (newStatus: string) => {
  if (!project.value || !task.value || actionInProgress.value) return;
  actionInProgress.value = true;
  try {
    const updatedTasks = [...project.value.tasks];
    updatedTasks[taskIndex] = { ...updatedTasks[taskIndex], status: newStatus } as Task;
    await projectsStore.updateProject(projectId, { tasks: updatedTasks });
    project.value.tasks = updatedTasks;
    task.value = updatedTasks[taskIndex];
    showRenewOptions.value = false;
  } catch (err) {
    console.error('Ошибка при обновлении статуса задачи:', err);
    alert('Не удалось изменить статус задачи');
  } finally {
    actionInProgress.value = false;
  }
};

const goBack = () => {
  router.push(`/project/${projectId}`);
};

const goHome = () => {
  router.push('/main');
};

</script>

<style scoped>
.task-details-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #f0f9f0 0%, #d4eed7 100%);
  padding: 20px;
  box-sizing: border-box;
}

.details-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 800px;
  margin: 0 auto 20px;
  flex-wrap: wrap;
  gap: 10px;
}

.details-header h1 {
  color: #1f4f22;
  font-size: 2rem;
  margin: 0;
}

.header-buttons {
  display: flex;
  gap: 10px;
}

.back-button, .home-button {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0.5rem 1rem;
  border-radius: 30px;
  transition: background 0.2s;
  display: flex;
  align-items: center;
  gap: 5px;
  background: rgba(255,255,255,0.5);
}

.back-button:hover, .home-button:hover {
  background: rgba(255,255,255,0.8);
}

.home-button {
  font-size: 1.8rem;
  padding: 0.5rem;
  border-radius: 50%;
  width: 50px;
  height: 50px;
  justify-content: center;
}

.task-card {
  background: white;
  border-radius: 24px;
  box-shadow: 0 10px 30px rgba(0, 40, 0, 0.1);
  padding: 30px;
  max-width: 800px;
  margin: 0 auto;
  transition: border 0.2s;
}

.task-card.task-overdue {
  border: 2px solid #f44336;
}

.task-card.task-urgent {
  border: 2px solid #ff9800;
}

.task-card.task-invalid {
  border: 2px solid #9e9e9e;
  opacity: 0.8;
}

.task-title {
  color: #2c5e2e;
  margin-bottom: 24px;
  font-size: 2rem;
  border-bottom: 2px solid #c8e6c9;
  padding-bottom: 10px;
}

.task-section {
  margin-bottom: 28px;
}

.task-section h3 {
  color: #1f4f22;
  margin-bottom: 10px;
  font-weight: 500;
}

.task-section p {
  color: #1a3a1a;
  line-height: 1.6;
}

/* Стили для невалидных дат */
.invalid-date {
  color: #f44336;
  font-weight: 600;
  text-decoration: underline wavy #f44336;
}

.date-warning {
  display: block;
  color: #f44336;
  font-size: 0.85rem;
  margin-top: 4px;
}

.gantt-section {
  margin-top: 40px;
  padding-top: 20px;
  border-top: 2px dashed #c8e6c9;
}

.gantt-section h3 {
  color: #1f4f22;
  margin-bottom: 15px;
  font-weight: 500;
  text-align: center;
}

.gantt-container {
  width: 100%;
}

.gantt-bar-container {
  position: relative;
  height: 30px;
  background: #e0f0e0;
  border-radius: 15px;
  margin-bottom: 5px;
  display: flex;
  align-items: center;
  overflow: hidden;
}

.gantt-bar {
  height: 100%;
  background: #42b983;
  border-radius: 15px 0 0 15px;
  width: 0%;
}

.gantt-dates {
  position: absolute;
  right: 10px;
  font-size: 0.85rem;
  color: #3b5e3b;
  background: rgba(255,255,255,0.7);
  padding: 2px 6px;
  border-radius: 10px;
}

.gantt-labels {
  display: flex;
  justify-content: space-between;
  color: #3b5e3b;
  font-size: 0.9rem;
  margin-top: 5px;
}

.action-buttons {
  margin-top: 30px;
  text-align: center;
}

.complete-button, .renew-button {
  background: #42b983;
  color: white;
  border: none;
  border-radius: 30px;
  padding: 12px 30px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s, transform 0.1s;
}

.complete-button:hover:not(:disabled), .renew-button:hover:not(:disabled) {
  background: #3aa876;
}

.complete-button:disabled, .renew-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.renew-options {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}

.status-option {
  padding: 10px 20px;
  border: none;
  border-radius: 30px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.status-option.work {
  background: #42b983;
  color: white;
}

.status-option.work:hover:not(:disabled) {
  background: #3aa876;
}

.status-option.waiting {
  background: #ff9800;
  color: white;
}

.status-option.waiting:hover:not(:disabled) {
  background: #f57c00;
}

.status-option.cancel {
  background: #e0e0e0;
  color: #333;
}

.status-option.cancel:hover:not(:disabled) {
  background: #bdbdbd;
}

.status-option:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.status-badges {
  margin-top: 20px;
  display: flex;
  gap: 10px;
  justify-content: center;
}

.badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: bold;
  color: white;
}

.badge.overdue {
  background-color: #f44336;
}

.badge.urgent {
  background-color: #ff9800;
}

.badge.invalid {
  background-color: #9e9e9e;
}

.loading, .error {
  text-align: center;
  color: #1f4f22;
  font-size: 1.2rem;
  padding: 40px;
}

.edit-task-button {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 30px;
  transition: background 0.2s;
  background: rgba(255,255,255,0.5);
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.edit-task-button:hover {
  background: rgba(255,255,255,0.8);
}
</style>