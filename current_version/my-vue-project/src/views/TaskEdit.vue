<template>
  <div class="task-details-page">
    <header class="details-header">
      <h1>Детали задачи</h1>
      <div class="header-actions">
        <ThemeToggle />
        <!-- Кнопка редактирования только для заказчика -->
        <router-link
          v-if="canEditTask"
          :to="`/project/${projectId}/task/${taskIndex}/edit`"
        >
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

      <section class="task-section">
        <h3>Статус</h3>
        <p>{{ task.status }}</p>
      </section>

      <section class="task-section">
        <h3>Описание</h3>
        <p>{{ task.body }}</p>
      </section>

      <section class="task-section">
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
        <span v-if="!isValidDateFormat(task.timeline) && task.timeline" class="date-warning">⚠️ Неверный формат даты начала</span>
        <span v-if="!isValidDateFormat(task.timelinend) && task.timelinend" class="date-warning">⚠️ Неверный формат даты окончания</span>
      </section>

      <!-- Комментарии к задаче -->
      <section class="task-section comments-main-section">
        <div class="section-header">
          <h3>Комментарии к задаче</h3>
          <button
            v-if="isProjectParticipant"
            class="comment-toggle-btn"
            @click="showTaskComments = !showTaskComments"
          >
            <span class="btn-content">
              <span class="comment-icon">💬</span>
              {{ showTaskComments ? 'Скрыть' : 'Показать' }}
              <span v-if="unreadTaskCommentsCount > 0" class="header-unread-badge">
                {{ unreadTaskCommentsCount }}
              </span>
            </span>
          </button>
        </div>

        <CommentsSection
          v-if="showTaskComments"
          :comments="taskComments"
          :can-comment="isProjectParticipant"
          :is-author="canEditTask"
          :can-hide-comments="canHideComments"
          :on-add-comment="addTaskComment"
          :on-mark-as-read="markTaskCommentAsRead"
          :on-hide-comment="hideTaskComment"
        />
      </section>

      <!-- Диаграмма Ганта (общий прогресс) -->
      <section class="gantt-section">
        <h3>Общий прогресс</h3>
        <div class="gantt-container">
          <div class="gantt-bar-container">
            <div
              class="gantt-bar"
              :style="{ width: totalProgress + '%', backgroundColor: barColor }"
              :title="`Прогресс: ${totalProgress.toFixed(1)}%`"
            ></div>
            <span class="gantt-percent">{{ totalProgress.toFixed(1) }}%</span>
            <span class="gantt-dates">{{ task.timeline || '?' }} – {{ task.timelinend || '?' }}</span>
          </div>
          <div class="gantt-labels">
            <span>{{ task.timeline || '?' }}</span>
            <span>Сегодня</span>
            <span>{{ task.timelinend || '?' }}</span>
          </div>
        </div>
        <div class="progress-breakdown" v-if="subtasks.length > 0">
          <div class="breakdown-item">
            <span class="breakdown-label">Подзадачи:</span>
            <span class="breakdown-value">{{ completedSubtasksPercent.toFixed(1) }}%</span>
          </div>
          <div class="breakdown-item">
            <span class="breakdown-label">Дополнительно:</span>
            <span class="breakdown-value">{{ extraProgress }}%</span>
          </div>
        </div>
      </section>

      <!-- Подзадачи -->
      <section v-if="subtasks.length > 0" class="subtasks-section">
        <h3>Подзадачи</h3>
        <div class="subtasks-list">
          <div
            v-for="subtask in subtasks"
            :key="subtask.id"
            class="subtask-item"
            :class="{ completed: subtask.completed }"
          >
            <div class="subtask-info">
              <input
                type="checkbox"
                :checked="subtask.completed"
                @change="toggleSubtask(subtask)"
                :disabled="actionInProgress || !isProjectParticipant"
              />
              <span class="subtask-title">{{ subtask.title }}</span>
              <span class="subtask-percent">{{ subtask.progressPercent }}%</span>
            </div>
            <p v-if="subtask.description" class="subtask-description">{{ subtask.description }}</p>
          </div>
        </div>
        <div class="subtasks-summary">
          Выполнено подзадач: {{ completedSubtasksPercent.toFixed(1) }}% / {{ totalSubtasksPercent.toFixed(1) }}%
        </div>
      </section>

      <!-- Ползунок дополнительного прогресса (только для участников, если задача в работе) -->
      <section v-if="showManualProgress && isProjectParticipant" class="progress-section">
        <h3>Дополнительный прогресс (вне подзадач)</h3>
        <div class="progress-slider-container">
          <span class="progress-value">{{ sliderValue }}%</span>
          <span class="progress-max"> / {{ maxExtra.toFixed(1) }}%</span>
          <input
            type="range"
            v-model.number="sliderValue"
            class="progress-slider"
            :min="0"
            :max="maxExtra"
            step="1"
          />
        </div>
        <button class="apply-progress-button" @click="openConfirmDialog">Применить дополнительный прогресс</button>
      </section>

      <!-- Кнопки действий (только для участников) -->
      <section class="action-buttons" v-if="isProjectParticipant">
        <div v-if="task.status !== 'выполнена'">
          <button
            class="complete-button"
            @click="completeTask"
            :disabled="actionInProgress || totalProgress < 100"
            :title="totalProgress < 100 ? 'Завершить задачу можно только при 100% прогрессе' : ''"
          >
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
            <button class="status-option work" @click="updateTaskStatus('в работе')" :disabled="actionInProgress">В работе</button>
            <button class="status-option waiting" @click="updateTaskStatus('ожидает')" :disabled="actionInProgress">Ожидает</button>
            <button class="status-option cancel" @click="showRenewOptions = false">Отмена</button>
          </div>
        </div>
      </section>

      <!-- Бейджики состояния -->
      <section class="status-badges">
        <span v-if="isInvalid" class="badge invalid">Невозможный дедлайн</span>
        <span v-if="isOverdue" class="badge overdue">Просрочено</span>
        <span v-if="isUrgent && !isOverdue && !isInvalid" class="badge urgent">Срочно</span>
      </section>
    </div>

    <!-- Модальное окно подтверждения -->
    <div v-if="showConfirmDialog" class="modal-overlay" @click.self="closeConfirmDialog">
      <div class="modal-content">
        <h3>Подтверждение</h3>
        <p>
          Изменить дополнительный прогресс с {{ oldSliderValue }}% на {{ sliderValue }}%?
        </p>
        <div class="modal-actions">
          <button class="modal-confirm" @click="confirmExtraChange">Да</button>
          <button class="modal-cancel" @click="closeConfirmDialog">Нет</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useProjectsStore } from '@/stores/projects';
import { useAuthStore } from '@/stores/auth';
import { useUsersStore } from '@/stores/users';
import ThemeToggle from '@/components/ThemeToggle.vue';
import CommentsSection from '@/components/CommentsSection.vue';
import type { Task, SubTask, Comment, ProjectRole } from '@/types';
import axios from 'axios';

const baseUrl = 'http://localhost:8000';
const generateId = () => Date.now().toString(36) + Math.random().toString(36).substr(2);

const route = useRoute();
const router = useRouter();
const projectsStore = useProjectsStore();
const authStore = useAuthStore();
const usersStore = useUsersStore();

const projectId = Number(route.params.projectId);
const taskIndex = Number(route.params.taskIndex);

const project = ref<any>(null);
const task = ref<Task | null>(null);
const loading = ref(true);
const error = ref('');
const actionInProgress = ref(false);
const showRenewOptions = ref(false);
const showTaskComments = ref(false);

const savedProgress = ref(0);
const sliderValue = ref(0);
const oldSliderValue = ref(0);
const showConfirmDialog = ref(false);

const extraProgress = computed(() => sliderValue.value);

// Роль текущего пользователя в проекте
const userRole = computed<ProjectRole | null>(() => {
  if (!authStore.userId || !project.value) return null;
  const participant = project.value.participants?.find((p: any) => p.user_id === authStore.userId);
  return participant?.role || null;
});

// Является ли пользователь участником проекта
const isProjectParticipant = computed(() => !!userRole.value);

// Может ли редактировать задачу (только заказчик)
const canEditTask = computed(() => userRole.value === 'customer');

// Может ли скрывать комментарии (научный руководитель)
const canHideComments = computed(() => userRole.value === 'supervisor');

const taskComments = computed(() => task.value?.comments || []);

const unreadTaskCommentsCount = computed(() => {
  return taskComments.value.filter(c => !c.isRead).length;
});

// Вспомогательные функции
function parseDate(dateStr?: string): Date | null {
  if (!dateStr) return null;
  const parts = dateStr.split('.');
  if (parts.length !== 3) return null;
  const [day, month, year] = parts.map(Number);
  if (isNaN(day) || isNaN(month) || isNaN(year)) return null;
  return new Date(year, month - 1, day);
}

function isValidDateFormat(dateStr?: string): boolean {
  if (!dateStr) return true;
  const parts = dateStr.split('.');
  if (parts.length !== 3) return false;
  const [day, month, year] = parts.map(Number);
  if (isNaN(day) || isNaN(month) || isNaN(year)) return false;
  if (day < 1 || day > 31 || month < 1 || month > 12 || year < 1000 || year > 9999) return false;
  const date = new Date(year, month - 1, day);
  return date.getDate() === day && date.getMonth() === month - 1 && date.getFullYear() === year;
}

// Подзадачи
const subtasks = computed(() => task.value?.subtasks || []);
const totalSubtasksPercent = computed(() =>
  subtasks.value.reduce((sum, st) => sum + (st.progressPercent || 0), 0)
);
const completedSubtasksPercent = computed(() =>
  subtasks.value.filter(st => st.completed).reduce((sum, st) => sum + (st.progressPercent || 0), 0)
);

const maxExtra = computed(() => 100 - completedSubtasksPercent.value);
const totalProgress = computed(() => completedSubtasksPercent.value + sliderValue.value);

const showManualProgress = computed(() => {
  return task.value?.status === 'в работе' && maxExtra.value > 0;
});

// Загрузка
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
      savedProgress.value = loadedTask.progress ?? 0;

      if (loadedTask.subtasks && loadedTask.subtasks.length > 0) {
        const completedSum = loadedTask.subtasks
          .filter((st: SubTask) => st.completed)
          .reduce((sum: number, st: SubTask) => sum + (st.progressPercent || 0), 0);
        sliderValue.value = Math.max(0, savedProgress.value - completedSum);
      } else {
        sliderValue.value = savedProgress.value;
      }
    }
  } catch (err) {
    error.value = 'Ошибка загрузки';
    console.error(err);
  } finally {
    loading.value = false;
  }
});

// Статусы задачи
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
  const today = new Date(); today.setHours(0, 0, 0, 0);
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
  const today = new Date(); today.setHours(0, 0, 0, 0);
  const totalDuration = (end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24);
  if (totalDuration <= 0) return false;
  const elapsed = (today.getTime() - start.getTime()) / (1000 * 60 * 60 * 24);
  if (elapsed < 0) return false;
  const prog = elapsed / totalDuration;
  return prog > 2 / 3 && t.status !== 'выполнена';
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

// --- Методы для задач ---
const toggleSubtask = async (subtask: SubTask) => {
  if (!isProjectParticipant.value) {
    alert('Только участники могут изменять подзадачи');
    return;
  }
  const currentProject = project.value;
  const currentTask = task.value;
  if (!currentProject || !currentTask) return;
  actionInProgress.value = true;

  try {
    const updatedSubtasks = currentTask.subtasks?.map(st => {
      if (st.id === subtask.id) return { ...st, completed: !st.completed };
      return st;
    }) || [];

    const newCompletedSum = updatedSubtasks
      .filter(st => st.completed)
      .reduce((sum, st) => sum + (st.progressPercent || 0), 0);

    if (sliderValue.value > (100 - newCompletedSum)) {
      sliderValue.value = 100 - newCompletedSum;
    }

    const newTotal = newCompletedSum + sliderValue.value;

    const updatedTask = {
      ...currentTask,
      subtasks: updatedSubtasks,
      progress: newTotal,
    };

    const updatedTasks = [...currentProject.tasks];
    updatedTasks[taskIndex] = updatedTask;
    await projectsStore.updateProject(projectId, { tasks: updatedTasks });

    project.value.tasks = updatedTasks;
    task.value = updatedTask;
    savedProgress.value = newTotal;
  } catch (err) {
    console.error('Ошибка при переключении подзадачи:', err);
    alert('Не удалось обновить подзадачу');
  } finally {
    actionInProgress.value = false;
  }
};

const completeTask = async () => {
  if (!isProjectParticipant.value) {
    alert('Только участники могут завершать задачи');
    return;
  }
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
  if (!isProjectParticipant.value) {
    alert('Только участники могут изменять статус');
    return;
  }
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

// --- Функции для работы с комментариями ---
const addTaskComment = async (content: string) => {
  if (!isProjectParticipant.value) {
    alert('Только участники могут комментировать');
    return;
  }
  if (!project.value || !task.value || !authStore.user) return;

  const newComment: Comment = {
    id: generateId(),
    authorId: authStore.user.id,
    content,
    createdAt: new Date().toISOString(),
    isRead: false,
    hidden: false,
  };

  try {
    const response = await axios.post(
      `${baseUrl}/projects/${projectId}/tasks/${taskIndex}/comments`,
      newComment
    );
    project.value = response.data;
    task.value = project.value.tasks[taskIndex];
    showTaskComments.value = true; // открываем блок комментариев
  } catch (error) {
    console.error('Failed to add comment:', error);
    alert('Ошибка при добавлении комментария');
  }
};

const markTaskCommentAsRead = async (commentId: string) => {
  if (!task.value || !isProjectParticipant.value) return;
  const updatedComments = (task.value.comments || []).map(c =>
    c.id === commentId ? { ...c, isRead: true } : c
  );
  const updatedTask = { ...task.value, comments: updatedComments };
  const updatedTasks = [...project.value.tasks];
  updatedTasks[taskIndex] = updatedTask;

  try {
    await projectsStore.updateProject(projectId, { tasks: updatedTasks });
    task.value = updatedTask;
    project.value.tasks = updatedTasks;
  } catch (error) {
    console.error('Failed to mark comment as read:', error);
  }
};

const hideTaskComment = async (commentId: string) => {
  if (!project.value) return;
  try {
    const response = await axios.delete(
      `${baseUrl}/projects/${projectId}/tasks/${taskIndex}/comments/${commentId}`
    );
    project.value = response.data;
    task.value = project.value.tasks[taskIndex];
  } catch (error) {
    console.error('Failed to hide comment:', error);
    alert('Ошибка при скрытии комментария');
  }
};

// Диалог подтверждения изменения дополнительного прогресса
const openConfirmDialog = () => {
  oldSliderValue.value = sliderValue.value;
  showConfirmDialog.value = true;
};

const closeConfirmDialog = () => {
  showConfirmDialog.value = false;
};

const confirmExtraChange = async () => {
  if (!isProjectParticipant.value) {
    alert('Только участники могут изменять прогресс');
    closeConfirmDialog();
    return;
  }
  const currentProject = project.value;
  const currentTask = task.value;
  if (!currentProject || !currentTask) {
    closeConfirmDialog();
    return;
  }

  const newTotal = completedSubtasksPercent.value + sliderValue.value;

  actionInProgress.value = true;
  try {
    const updatedTasks = [...currentProject.tasks];
    updatedTasks[taskIndex] = {
      ...updatedTasks[taskIndex],
      progress: newTotal,
    } as Task;
    await projectsStore.updateProject(projectId, { tasks: updatedTasks });

    project.value.tasks = updatedTasks;
    task.value = updatedTasks[taskIndex];
    savedProgress.value = newTotal;
  } catch (err) {
    console.error('Ошибка при обновлении прогресса:', err);
    alert('Не удалось изменить прогресс');
    sliderValue.value = savedProgress.value - completedSubtasksPercent.value;
  } finally {
    actionInProgress.value = false;
    showConfirmDialog.value = false;
  }
};

// Навигация
const goBack = () => router.push(`/project/${projectId}`);
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