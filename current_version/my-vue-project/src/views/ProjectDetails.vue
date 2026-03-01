<template>
  <div class="project-details-page">
    <!-- Шапка: для не-авторов заголовок слева, для авторов только кнопки -->
    <header class="details-header" :class="{ 'author-header': isAuthor }">
      <h1 v-if="!isAuthor" class="page-title">{{ project?.title || 'Проект' }}</h1>
      <div class="header-buttons">
        <ThemeToggle />
        <button class="home-button" @click="goHome" title="На главную">🏠</button>
      </div>
    </header>

    <!-- Состояния загрузки/ошибки -->
    <div v-if="loading" class="loading">Загрузка...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="project">
      <!-- Макет для НЕ-авторов (обычный просмотр) -->
      <div v-if="!isAuthor" class="non-author-layout">
        <div class="project-card">
          <div class="project-section">
            <h3>Описание</h3>
            <p>{{ project.body }}</p>
          </div>
          <div v-if="project.underbody" class="project-section">
            <h3>Дополнительно</h3>
            <p>{{ project.underbody }}</p>
          </div>
          <div class="project-section">
            <h3>Авторы</h3>
            <div v-if="authors.length" class="authors-list">
              <span
                v-for="author in authors"
                :key="author.id"
                class="author-link"
                @click="goToUser(author.id)"
              >
                {{ author.nickname }}
              </span>
            </div>
            <p v-else>Нет авторов</p>
          </div>
        </div>
      </div>

      <!-- Макет для АВТОРОВ с диаграммой Ганта -->
      <div v-else class="author-layout">
        <h1 class="project-title-center">{{ project.title }}</h1>

        <div class="two-columns">
          <!-- Левая колонка: информация о проекте и выполненные задачи -->
          <div class="info-column">
            <div class="project-section">
              <h3>Описание</h3>
              <p>{{ project.body }}</p>
            </div>
            <div v-if="project.underbody" class="project-section">
              <h3>Дополнительно</h3>
              <p>{{ project.underbody }}</p>
            </div>
            <div class="project-section">
              <h3>Авторы</h3>
              <div v-if="authors.length" class="authors-list">
                <span
                  v-for="author in authors"
                  :key="author.id"
                  class="author-link"
                  @click="goToUser(author.id)"
                >
                  {{ author.nickname }}
                </span>
              </div>
              <p v-else>Нет авторов</p>
            </div>

            <!-- Блок выполненных задач (кликабельно) -->
            <div v-if="completedTasks.length" class="project-section">
              <h3>Выполненные задачи</h3>
              <div class="completed-tasks">
                <div
                  v-for="task in completedTasks"
                  :key="task.title"
                  class="completed-task"
                  @click="goToTask(task)"
                >
                  <span class="completed-task-title">{{ task.title }}</span>
                  <span class="completed-task-date">{{ formatTaskDates(task) }}</span>
                </div>
              </div>
            </div>

            <!-- Кнопки управления проектом (только для авторов) -->
            <div class="project-actions">
              <button class="edit-project-button" @click="goToEdit">✎ Редактировать проект</button>
              <button class="delete-project-button" @click="deleteProject">🗑 Удалить проект</button>
            </div>
          </div>

          <!-- Правая колонка: активные задачи и диаграмма Ганта -->
          <div class="tasks-column">
            <h3>Активные задачи</h3>
            <div v-if="activeTasks.length" class="task-tree">
              <div
                v-for="task in activeTasks"
                :key="task.title"
                class="task-node"
                :class="taskStatusClass(task)"
                @click="goToTask(task)"
              >
                <span class="task-icon">📄</span>
                <div class="task-content">
                  <strong>{{ task.title }}</strong>
                  <span class="task-status">{{ task.status }}</span>
                  <p>{{ task.body }}</p>
                  <span v-if="task.status === 'в работе'" class="task-progress">
                    Прогресс: {{ task.progress ?? 0 }}%
                  </span>
                  <small>Срок: {{ formatTaskDates(task) }}</small>
                  <span v-if="isTaskOverdue(task)" class="overdue-badge">Просрочено</span>
                  <span v-if="isTaskInvalid(task)" class="invalid-badge">Некорректные даты</span>
                  <span v-if="isTaskNotStarted(task)" class="not-started-badge">Не начато</span>
                </div>
              </div>
            </div>
            <div v-else class="no-tasks">Нет активных задач</div>

            <!-- Диаграмма Ганта (только для активных задач) -->
            <div v-if="activeTasks.length" class="gantt-section">
              <h3>Таймлайн задач (прошедшее время)</h3>
              <div class="gantt-chart">
                <div v-for="(task, index) in activeTasksProgress" :key="index" class="gantt-row">
                  <div class="gantt-label">{{ task.title }}</div>
                  <div class="gantt-bar-container">
                    <div
                      class="gantt-bar"
                      :style="{ backgroundColor: task.barColor }"
                    ></div>
                    <span class="gantt-text">
                      {{ task.startStr || '???' }} – {{ task.endStr || '???' }} ({{ task.progress.toFixed(1) }}%)
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useProjectsStore } from '@/stores/projects';
import { useAuthStore } from '@/stores/auth';
import { useUsersStore } from '@/stores/users';
import ThemeToggle from '@/components/ThemeToggle.vue';
import type { Project, User, Task } from '@/types';

const route = useRoute();
const router = useRouter();
const projectsStore = useProjectsStore();
const authStore = useAuthStore();
const usersStore = useUsersStore();

const project = ref<Project | null>(null);
const loading = ref(true);
const error = ref('');
const authors = ref<User[]>([]);

const isAuthor = computed(() => {
  if (!authStore.userId || !project.value) return false;
  return project.value.authors_ids.includes(authStore.userId);
});

// Загрузка данных авторов по их ID
async function loadAuthors(ids: number[]) {
  if (ids.length === 0) {
    authors.value = [];
    return;
  }
  if (usersStore.users.length === 0) {
    await usersStore.fetchAllUsers();
  }
  authors.value = usersStore.users.filter(u => ids.includes(u.id));
}

// Загрузка проекта
async function loadProject() {
  const id = Number(route.params.id);
  if (isNaN(id)) {
    error.value = 'Неверный ID проекта';
    loading.value = false;
    return;
  }

  try {
    project.value = await projectsStore.fetchProjectById(id);
    if (project.value) {
      await loadAuthors(project.value.authors_ids);
    }
  } catch (err) {
    error.value = 'Ошибка загрузки проекта';
    console.error(err);
  } finally {
    loading.value = false;
  }
}

onMounted(loadProject);

watch(() => project.value, (newProject) => {
  if (newProject) {
    loadAuthors(newProject.authors_ids);
  }
});

// Парсинг даты из строки "DD.MM.YYYY"
function parseDate(dateStr: string): Date | null {
  if (!dateStr) return null;
  const parts = dateStr.split('.');
  if (parts.length !== 3) return null;
  const [day, month, year] = parts.map(Number) as [number, number, number];
  if (isNaN(day) || isNaN(month) || isNaN(year)) return null;
  return new Date(year, month - 1, day);
}

// Форматирование дат для отображения (с поддержкой старого формата)
function formatTaskDates(task: Task): string {
  if (task.timelinend) {
    return `${task.timeline || '?'} – ${task.timelinend}`;
  } else if (task.timeline && task.timeline.includes('-')) {
    const parts = task.timeline.split('-');
    if (parts.length === 2) return `${parts[0]} – ${parts[1]}`;
  }
  return task.timeline || '?';
}

// Вспомогательные функции для статуса задачи
function isTaskOverdue(task: Task): boolean {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  let endStr = task.timelinend;
  if (!endStr && task.timeline && task.timeline.includes('-')) {
    const parts = task.timeline.split('-');
    endStr = parts[1] || '';
  }
  const endDate = parseDate(endStr || '');
  if (!endDate) return false;
  return today > endDate && task.status !== 'выполнена';
}

function isTaskInvalid(task: Task): boolean {
  let startStr = task.timeline;
  let endStr = task.timelinend;
  if (!endStr && startStr && startStr.includes('-')) {
    const parts = startStr.split('-');
    startStr = parts[0] || '';
    endStr = parts[1] || '';
  }
  const start = parseDate(startStr || '');
  const end = parseDate(endStr || '');
  if (!start || !end) return true;
  return start > end;
}

function isTaskNotStarted(task: Task): boolean {
  if (isTaskInvalid(task) || isTaskOverdue(task)) return false;
  let startStr = task.timeline;
  if (!task.timelinend && startStr && startStr.includes('-')) {
    const parts = startStr.split('-');
    startStr = parts[0] || '';
  }
  const start = parseDate(startStr || '');
  if (!start) return false;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return today < start;
}

function isTaskUrgent(task: Task): boolean {
  if (isTaskInvalid(task) || isTaskOverdue(task) || isTaskNotStarted(task)) return false;
  let startStr = task.timeline;
  let endStr = task.timelinend;
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
  const progress = elapsed / totalDuration;
  return progress > 2 / 3 && task.status !== 'выполнена';
}

function taskStatusClass(task: Task): string {
  if (isTaskInvalid(task)) return 'task-invalid';
  if (isTaskOverdue(task)) return 'task-overdue';
  if (isTaskNotStarted(task)) return 'task-not-started';
  if (isTaskUrgent(task)) return 'task-urgent';
  return '';
}

// --- РАЗДЕЛЕНИЕ ЗАДАЧ ---
const activeTasks = computed<Task[]>(() => {
  if (!project.value || !project.value.tasks) return [];
  return project.value.tasks.filter(task => task.status !== 'выполнена');
});

const completedTasks = computed<Task[]>(() => {
  if (!project.value || !project.value.tasks) return [];
  return project.value.tasks.filter(task => task.status === 'выполнена');
});

// Прогресс для активных задач (для диаграммы Ганта)
const activeTasksProgress = computed(() => {
  if (!project.value || !activeTasks.value) return [];
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  return activeTasks.value.map(task => {
    let startStr = task.timeline || '';
    let endStr = task.timelinend || '';

    if (!endStr && startStr.includes('-')) {
      const parts = startStr.split('-');
      startStr = parts[0] || '';
      endStr = parts[1] || '';
    }

    const startDate = parseDate(startStr);
    const endDate = parseDate(endStr);
    let progress = 0;
    let invalid = false;
    let overdue = false;
    let urgent = false;
    let notStarted = false;

    if (!startDate || !endDate) {
      invalid = true;
    } else if (startDate > endDate) {
      invalid = true;
    } else {
      if (today < startDate) {
        notStarted = true;
        progress = 0;
      } else if (today > endDate) {
        overdue = true;
        progress = 100;
      } else {
        const totalDuration = (endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24);
        if (totalDuration > 0) {
          const elapsed = (today.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24);
          progress = (elapsed / totalDuration) * 100;
        } else {
          progress = today >= startDate ? 100 : 0;
        }
        if (progress > 66.6) {
          urgent = true;
        }
      }
    }

    if (isNaN(progress)) progress = 0;

    let barColor = '#42b983';
    if (invalid) barColor = '#9e9e9e';
    else if (overdue) barColor = '#f44336';
    else if (notStarted) barColor = '#bdbdbd';
    else if (urgent) barColor = '#ff9800';
    else {
      const hue = 120 * (1 - progress / 100);
      barColor = `hsl(${Math.max(0, Math.min(120, hue))}, 80%, 50%)`;
    }

    return {
      title: task.title,
      startStr,
      endStr,
      progress: Math.min(100, Math.max(0, progress)),
      barColor,
    };
  });
});

// --- МЕТОД ДЛЯ ПЕРЕХОДА К ЗАДАЧЕ ---
const goToTask = (task: Task) => {
  if (!project.value || !project.value.tasks) return;
  const index = project.value.tasks.findIndex(t => t === task);
  if (index !== -1) {
    router.push(`/project/${route.params.id}/task/${index}`);
  }
};

// --- УДАЛЕНИЕ ПРОЕКТА ---
const deleteProject = async () => {
  if (!project.value) return;
  if (confirm('Вы уверены, что хотите удалить проект?')) {
    try {
      await projectsStore.deleteProject(project.value.id);
      router.push('/main');
    } catch (err) {
      console.error('Ошибка при удалении проекта:', err);
      alert('Не удалось удалить проект');
    }
  }
};

// --- МЕТОДЫ НАВИГАЦИИ ---
const goToEdit = () => {
  router.push(`/project/edit/${route.params.id}`);
};

const goHome = () => {
  router.push('/main');
};

const goToUser = (userId: number) => {
  router.push(`/user/${userId}`);
};
</script>

<style scoped>
.project-details-page {
  min-height: 100vh;
  background: var(--bg-page);
  padding: 20px;
  box-sizing: border-box;
  transition: background 0.3s;
}

/* Шапка */
.details-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto 20px;
  flex-wrap: wrap;
  gap: 10px;
}

/* Для авторов в шапке только кнопки */
.author-header {
  justify-content: flex-end;
}

.page-title {
  color: var(--heading-color);
  font-size: 2rem;
  margin: 0;
}

.header-buttons {
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

/* Общие стили для секций */
.project-section {
  margin-bottom: 28px;
}

.project-section h3 {
  color: var(--heading-color);
  margin-bottom: 10px;
  font-weight: 500;
}

.project-section p {
  color: var(--text-primary);
  line-height: 1.6;
}

/* Список авторов */
.authors-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.author-link {
  cursor: pointer;
  color: var(--link-color);
  text-decoration: underline;
  margin-right: 8px;
  display: inline-block;
}

.author-link:hover {
  color: var(--link-hover);
}

/* ----- Макет для НЕ-авторов ----- */
.non-author-layout {
  max-width: 800px;
  margin: 0 auto;
}

.project-card {
  background: var(--bg-card);
  border-radius: 24px;
  box-shadow: var(--shadow-strong);
  padding: 30px;
  transition: background 0.3s;
}

/* ----- Макет для АВТОРОВ ----- */
.author-layout {
  max-width: 1200px;
  margin: 0 auto;
}

.project-title-center {
  text-align: center;
  color: var(--heading-color);
  font-size: 2.5rem;
  margin-bottom: 30px;
}

.two-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 40px;
}

.info-column {
  background: var(--bg-column);
  backdrop-filter: blur(4px);
  border-radius: 24px;
  padding: 30px;
  box-shadow: var(--shadow);
  transition: background 0.3s;
}

.tasks-column {
  background: var(--bg-column);
  backdrop-filter: blur(4px);
  border-radius: 24px;
  padding: 30px;
  box-shadow: var(--shadow);
  transition: background 0.3s;
}

.tasks-column h3 {
  color: var(--heading-color);
  margin-bottom: 20px;
  font-weight: 500;
  font-size: 1.5rem;
  text-align: center;
}

.task-tree {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.task-node {
  display: flex;
  align-items: flex-start;
  gap: 15px;
  padding: 15px;
  background: var(--bg-card);
  border-radius: 12px;
  box-shadow: var(--shadow);
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  border-left: 4px solid var(--accent-color);
}

.task-node:hover {
  transform: translateX(5px);
  box-shadow: var(--shadow-strong);
}

/* Классы состояния задач */
.task-node.task-overdue {
  background-color: var(--overdue-bg);
  border-left-color: #f44336;
}

.task-node.task-urgent {
  background-color: var(--urgent-bg);
  border-left-color: #ff9800;
}

.task-node.task-invalid {
  background-color: var(--invalid-bg);
  border-left-color: #9e9e9e;
  opacity: 0.7;
}

.task-node.task-not-started {
  background-color: var(--not-started-bg);
  border-left-color: #bdbdbd;
  opacity: 0.8;
}

.task-icon {
  font-size: 1.5rem;
  color: var(--accent-color);
}

.task-content {
  flex: 1;
}

.task-content strong {
  color: var(--heading-color);
  display: block;
  margin-bottom: 4px;
}

.task-status {
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin-left: 8px;
}

.task-content p {
  color: var(--text-primary);
  margin: 8px 0 4px;
}

.task-progress {
  display: inline-block;
  margin-top: 4px;
  margin-right: 8px;
  font-size: 0.9rem;
  color: var(--heading-color);
  background: var(--completed-bg);
  padding: 2px 8px;
  border-radius: 12px;
}

.task-content small {
  color: var(--text-secondary);
}

.overdue-badge,
.invalid-badge,
.not-started-badge {
  display: inline-block;
  margin-left: 8px;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: bold;
  color: white;
}

.overdue-badge {
  background-color: #f44336;
}

.invalid-badge {
  background-color: #9e9e9e;
}

.not-started-badge {
  background-color: #757575;
}

.no-tasks {
  text-align: center;
  color: var(--text-secondary);
  font-style: italic;
  padding: 20px;
}

/* Диаграмма Ганта */
.gantt-section {
  margin-top: 30px;
  border-top: 2px dashed var(--border-color);
  padding-top: 20px;
}

.gantt-section h3 {
  color: var(--heading-color);
  margin-bottom: 15px;
  font-weight: 500;
  text-align: center;
}

.gantt-chart {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.gantt-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.gantt-label {
  width: 120px;
  font-weight: 500;
  color: var(--heading-color);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.gantt-bar-container {
  position: relative;
  flex: 1;
  height: 24px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.gantt-bar {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border-radius: 12px;
  transition: background-color 0.2s ease;
}

.gantt-text {
  position: relative;
  z-index: 1;
  color: var(--text-primary);
  font-size: 0.85rem;
  font-weight: 500;
  background-color: transparent;
  text-shadow: 0 0 2px rgba(0, 0, 0, 0.5);
}

.light-theme .gantt-text {
  text-shadow: 0 0 2px rgba(255, 255, 255, 0.7);
}

.loading,
.error {
  text-align: center;
  color: var(--text-primary);
  font-size: 1.2rem;
  padding: 40px;
}

/* Стили для выполненных задач */
.completed-tasks {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 10px;
}

.completed-task {
  cursor: pointer;
  background: var(--completed-bg);
  padding: 10px;
  border-radius: 8px;
  border-left: 4px solid var(--accent-color);
  transition: transform 0.1s, box-shadow 0.1s;
}

.completed-task:hover {
  transform: translateX(4px);
  box-shadow: var(--shadow);
}

.completed-task-title {
  font-weight: 600;
  color: var(--heading-color);
}

.completed-task-date {
  display: block;
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-top: 4px;
}

/* Кнопки управления проектом */
.project-actions {
  margin-top: 30px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.edit-project-button,
.delete-project-button {
  flex: 1;
  padding: 12px 20px;
  border: none;
  border-radius: 50px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.edit-project-button {
  background: var(--accent-color);
  color: var(--button-text);
}

.edit-project-button:hover {
  background: var(--accent-hover);
  transform: translateY(-2px);
  box-shadow: var(--shadow-strong);
}

.delete-project-button {
  background: var(--danger-bg);
  color: var(--danger-color);
}

.delete-project-button:hover {
  background: var(--danger-hover);
  transform: translateY(-2px);
  box-shadow: var(--shadow-strong);
}
</style>