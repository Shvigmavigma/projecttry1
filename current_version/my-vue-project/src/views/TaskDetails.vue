<template>
  <div class="task-details-page">
    <header class="details-header">
      <h1>Детали задачи</h1>
      <div class="header-actions">
        <ThemeToggle />
        <router-link :to="`/project/${projectId}/task/${taskIndex}/edit`">
          <button class="icon-button edit-task-button" title="Редактировать задачу">✎</button>
        </router-link>
        <button class="icon-button home-button" @click="goHome" title="На главную">🏠</button>
        <button class="icon-button back-button" @click="goBack" title="Вернуться к проекту">◀</button>
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

      <!-- Ползунок прогресса (только для задач в работе) -->
      <div v-if="task.status === 'в работе'" class="progress-section">
        <h3>Ручной прогресс</h3>
        <div class="progress-slider">
          <span class="progress-value">{{ tempProgress }}%</span>
          <input
            type="range"
            v-model.number="tempProgress"
            min="0"
            max="100"
            step="1"
          />
        </div>
        <!-- Кнопка применения прогресса -->
        <button class="apply-progress-button" @click="openConfirmDialog">Применить прогресс</button>
      </div>

      <!-- Кнопки действий -->
      <div class="action-buttons">
        <div v-if="task.status !== 'выполнена'">
          <button class="complete-button" @click="completeTask" :disabled="actionInProgress">
            {{ actionInProgress ? 'Завершение...' : '✓ Завершить задачу' }}
          </button>
        </div>
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

    <!-- Модальное окно подтверждения -->
    <div v-if="showConfirmDialog" class="modal-overlay" @click.self="closeConfirmDialog">
      <div class="modal-content">
        <h3>Подтверждение</h3>
        <p>Изменить прогресс с {{ progressValue }}% на {{ tempProgress }}%?</p>
        <div class="modal-actions">
          <button class="modal-confirm" @click="confirmProgressChange">Да</button>
          <button class="modal-cancel" @click="closeConfirmDialog">Нет</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useProjectsStore } from '@/stores/projects';
import ThemeToggle from '@/components/ThemeToggle.vue';
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

const progressValue = ref(0);
const tempProgress = ref(0);
const showConfirmDialog = ref(false);

function parseDate(dateStr?: string): Date | null {
  if (!dateStr) return null;
  const parts = dateStr.split('.');
  if (parts.length !== 3) return null;
  const [day, month, year] = parts.map(Number) as [number, number, number];
  if (isNaN(day) || isNaN(month) || isNaN(year)) return null;
  return new Date(year, month - 1, day);
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

function isValidDateFormat(dateStr?: string): boolean {
  if (!dateStr) return true;
  const parts = dateStr.split('.');
  if (parts.length !== 3) return false;
  const [day, month, year] = parts.map(Number) as [number, number, number];
  if (isNaN(day) || isNaN(month) || isNaN(year)) return false;
  if (day < 1 || day > 31 || month < 1 || month > 12 || year < 1000 || year > 9999) return false;
  const date = new Date(year, month - 1, day);
  return date.getDate() === day && date.getMonth() === month - 1 && date.getFullYear() === year;
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
      const loadedTask = project.value.tasks[taskIndex];
      task.value = loadedTask;
      progressValue.value = loadedTask.progress ?? 0;
      tempProgress.value = loadedTask.progress ?? 0;
    }
  } catch (err) {
    error.value = 'Ошибка загрузки';
    console.error(err);
  } finally {
    loading.value = false;
  }
});

watch(task, (newTask) => {
  if (newTask) {
    progressValue.value = newTask.progress ?? 0;
    tempProgress.value = newTask.progress ?? 0;
  }
});

// Вычисляемые свойства
const isInvalid = computed(() => {
  const t = task.value;
  if (!t) return false;
  let startStr = t.timeline;
  let endStr = t.timelinend;
  if (!endStr && startStr && startStr.includes('-')) {
    const parts = startStr.split('-');
    startStr = parts[0] || '';
    endStr = parts[1] || '';
  }
  const start = parseDate(startStr || '');
  const end = parseDate(endStr || '');
  const startValid = isValidDateFormat(startStr);
  const endValid = isValidDateFormat(endStr);
  if ((startStr && !startValid) || (endStr && !endValid)) return true;
  return !start || !end || start > end;
});

const isOverdue = computed(() => {
  const t = task.value;
  if (!t || isInvalid.value) return false;
  let endStr = t.timelinend;
  if (!endStr && t.timeline && t.timeline.includes('-')) {
    const parts = t.timeline.split('-');
    endStr = parts[1] || '';
  }
  const end = parseDate(endStr || '');
  if (!end) return false;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return today > end && t.status !== 'выполнена';
});

const isUrgent = computed(() => {
  const t = task.value;
  if (!t || isInvalid.value || isOverdue.value) return false;
  let startStr = t.timeline;
  let endStr = t.timelinend;
  if (!endStr && startStr && startStr.includes('-')) {
    const parts = startStr.split('-');
    startStr = parts[0] || '';
    endStr = parts[1] || '';
  }
  const start = parseDate(startStr || '');
  const end = parseDate(endStr || '');
  if (!start || !end) return false;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const totalDuration = (end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24);
  if (totalDuration <= 0) return false;
  const elapsed = (today.getTime() - start.getTime()) / (1000 * 60 * 60 * 24);
  if (elapsed < 0) return false;
  const prog = elapsed / totalDuration;
  return prog > 2 / 3 && t.status !== 'выполнена';
});

const progress = computed(() => {
  const t = task.value;
  if (!t || isInvalid.value) return 0;
  let startStr = t.timeline;
  let endStr = t.timelinend;
  if (!endStr && startStr && startStr.includes('-')) {
    const parts = startStr.split('-');
    startStr = parts[0] || '';
    endStr = parts[1] || '';
  }
  const start = parseDate(startStr || '');
  const end = parseDate(endStr || '');
  if (!start || !end) return 0;
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

// Методы
const completeTask = async () => {
  const currentProject = project.value;
  const currentTask = task.value;
  if (!currentProject || !currentTask || actionInProgress.value) return;
  actionInProgress.value = true;
  try {
    const updatedTasks = [...currentProject.tasks];
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

const updateTaskStatus = async (newStatus: string) => {
  const currentProject = project.value;
  const currentTask = task.value;
  if (!currentProject || !currentTask || actionInProgress.value) return;
  actionInProgress.value = true;
  try {
    const updatedTasks = [...currentProject.tasks];
    updatedTasks[taskIndex] = { ...updatedTasks[taskIndex], status: newStatus } as Task;
    await projectsStore.updateProject(projectId, { tasks: updatedTasks });
    project.value = { ...currentProject, tasks: updatedTasks };
    task.value = updatedTasks[taskIndex];
    showRenewOptions.value = false;
  } catch (err) {
    console.error('Ошибка при обновлении статуса задачи:', err);
    alert('Не удалось изменить статус задачи');
  } finally {
    actionInProgress.value = false;
  }
};

const openConfirmDialog = () => {
  if (tempProgress.value === progressValue.value) return;
  showConfirmDialog.value = true;
};

const closeConfirmDialog = () => {
  tempProgress.value = progressValue.value;
  showConfirmDialog.value = false;
};

const confirmProgressChange = async () => {
  const currentProject = project.value;
  const currentTask = task.value;
  if (!currentProject || !currentTask) {
    closeConfirmDialog();
    return;
  }
  try {
    const updatedTasks = [...currentProject.tasks];
    updatedTasks[taskIndex] = {
      ...updatedTasks[taskIndex],
      progress: tempProgress.value
    } as Task;
    await projectsStore.updateProject(projectId, { tasks: updatedTasks });
    project.value = { ...currentProject, tasks: updatedTasks };
    task.value = updatedTasks[taskIndex];
    progressValue.value = tempProgress.value;
  } catch (err) {
    console.error('Ошибка при обновлении прогресса:', err);
    alert('Не удалось изменить прогресс');
    tempProgress.value = progressValue.value;
  } finally {
    showConfirmDialog.value = false;
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
  background: var(--bg-page);
  padding: 20px;
  box-sizing: border-box;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  transition: background 0.3s;
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
  color: var(--heading-color);
  font-size: 2rem;
  margin: 0;
  text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
}

.light-theme .details-header h1 {
  text-shadow: 1px 1px 2px rgba(255,255,255,0.5);
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.icon-button {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 50%;
  width: 44px;
  height: 44px;
  font-size: 1.4rem;
  cursor: pointer;
  box-shadow: var(--shadow);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  color: var(--text-primary);
}

.icon-button:hover {
  background: var(--bg-card);
  transform: scale(1.1);
  box-shadow: var(--shadow-strong);
}

.task-card {
  background: var(--bg-card);
  border-radius: 32px;
  box-shadow: var(--shadow-strong);
  padding: 30px;
  max-width: 800px;
  margin: 0 auto;
  transition: border 0.2s, transform 0.2s, background 0.3s;
}

.task-card:hover {
  transform: translateY(-2px);
}

.task-card.task-overdue {
  border: 2px solid #f44336;
}

.task-card.task-urgent {
  border: 2px solid #ff9800;
}

.task-card.task-invalid {
  border: 2px solid #9e9e9e;
  opacity: 0.9;
}

.task-title {
  color: var(--heading-color);
  margin-bottom: 24px;
  font-size: 2rem;
  border-bottom: 2px solid var(--border-color);
  padding-bottom: 10px;
}

.task-section {
  margin-bottom: 28px;
}

.task-section h3 {
  color: var(--heading-color);
  margin-bottom: 10px;
  font-weight: 500;
  font-size: 1.2rem;
}

.task-section p {
  color: var(--text-primary);
  line-height: 1.6;
}

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
  border-top: 2px dashed var(--border-color);
}

.gantt-section h3 {
  color: var(--heading-color);
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
  background: var(--input-bg);
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
  transition: width 0.3s ease;
}

.gantt-dates {
  position: absolute;
  right: 10px;
  font-size: 0.85rem;
  color: var(--text-primary);
  background: rgba(0,0,0,0.5);
  padding: 2px 8px;
  border-radius: 12px;
  font-weight: 500;
}

.light-theme .gantt-dates {
  background: rgba(255,255,255,0.8);
  color: #1a3a1a;
}

.gantt-labels {
  display: flex;
  justify-content: space-between;
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin-top: 5px;
}

.progress-section {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 2px dashed var(--border-color);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
}

.progress-section h3 {
  color: var(--heading-color);
  margin-bottom: 5px;
  font-weight: 500;
}

.progress-slider {
  display: flex;
  align-items: center;
  gap: 20px;
  width: 100%;
}

.progress-value {
  font-weight: 600;
  color: var(--heading-color);
  min-width: 45px;
  font-size: 1.2rem;
}

.progress-slider input[type=range] {
  flex: 1;
  height: 8px;
  -webkit-appearance: none;
  -moz-appearance: none;
  appearance: none;
  background: var(--input-bg);
  border-radius: 4px;
  outline: none;
}

.progress-slider input[type=range]::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 24px;
  height: 24px;
  background: var(--accent-color);
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 2px 6px var(--shadow);
  transition: transform 0.1s;
}

.progress-slider input[type=range]::-webkit-slider-thumb:hover {
  transform: scale(1.15);
  background: var(--accent-hover);
}

.progress-slider input[type=range]::-moz-range-thumb {
  width: 24px;
  height: 24px;
  background: var(--accent-color);
  border-radius: 50%;
  cursor: pointer;
  border: none;
}

.apply-progress-button {
  background: var(--accent-color);
  color: var(--button-text);
  border: none;
  border-radius: 30px;
  padding: 10px 30px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s, transform 0.1s;
  box-shadow: var(--shadow);
}

.apply-progress-button:hover {
  background: var(--accent-hover);
  transform: scale(1.02);
}

.action-buttons {
  margin-top: 30px;
  text-align: center;
}

.complete-button, .renew-button {
  background: var(--accent-color);
  color: var(--button-text);
  border: none;
  border-radius: 30px;
  padding: 12px 30px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s, transform 0.1s;
  box-shadow: var(--shadow);
}

.complete-button:hover:not(:disabled), .renew-button:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: scale(1.02);
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
  transition: all 0.2s;
  box-shadow: var(--shadow);
}

.status-option.work {
  background: var(--accent-color);
  color: var(--button-text);
}

.status-option.work:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: scale(1.02);
}

.status-option.waiting {
  background: #ff9800;
  color: white;
}

.status-option.waiting:hover:not(:disabled) {
  background: #f57c00;
}

.status-option.cancel {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.status-option.cancel:hover:not(:disabled) {
  background: var(--bg-page);
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
  box-shadow: var(--shadow);
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
  color: var(--text-primary);
  font-size: 1.2rem;
  padding: 40px;
}

/* Модальное окно */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: var(--overlay-bg);
  backdrop-filter: blur(3px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s;
}

.modal-content {
  background: var(--modal-bg);
  border-radius: 32px;
  padding: 30px;
  max-width: 400px;
  width: 90%;
  box-shadow: var(--shadow-strong);
  animation: slideUp 0.3s;
  color: var(--modal-text);
}

.modal-content h3 {
  color: var(--heading-color);
  margin-bottom: 15px;
  font-weight: 500;
  font-size: 1.5rem;
}

.modal-content p {
  color: var(--text-primary);
  margin-bottom: 25px;
  font-size: 1.1rem;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.modal-confirm, .modal-cancel {
  padding: 10px 25px;
  border: none;
  border-radius: 30px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.modal-confirm {
  background: var(--accent-color);
  color: var(--button-text);
}

.modal-confirm:hover {
  background: var(--accent-hover);
  transform: scale(1.02);
}

.modal-cancel {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.modal-cancel:hover {
  background: var(--bg-page);
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
</style>