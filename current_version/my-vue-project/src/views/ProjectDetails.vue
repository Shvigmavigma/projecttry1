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

            <!-- Блок ссылок проекта (только для авторов) -->
            <div class="project-links">
              <h3>Ссылки проекта</h3>
              <div class="links-buttons">
                <!-- GitHub -->
                <template v-if="project.links?.github">
                  <div v-if="!showEditGithub" class="link-display">
                    <a
                      :href="project.links.github"
                      target="_blank"
                      rel="noopener noreferrer"
                      class="link-button github-link"
                    >
                      <img :src="githubIcon" alt="GitHub" class="icon" />
                      GitHub репозиторий
                    </a>
                    <div class="link-actions">
                      <button class="link-edit" @click="startEditGithub" title="Редактировать">✎</button>
                      <button class="link-delete" @click="deleteGithubLink" title="Удалить">✖</button>
                    </div>
                  </div>
                  <div v-else class="link-input-wrapper">
                    <input
                      v-model="githubEditValue"
                      type="url"
                      placeholder="https://github.com/..."
                      class="link-input"
                      @keyup.enter="saveEditGithub"
                    />
                    <button class="link-save" @click="saveEditGithub">✔</button>
                    <button class="link-cancel" @click="cancelEditGithub">✖</button>
                  </div>
                </template>
                <template v-else>
                  <div v-if="showGithubInput" class="link-input-wrapper">
                    <input
                      v-model="githubInput"
                      type="url"
                      placeholder="https://github.com/..."
                      class="link-input"
                      @keyup.enter="saveGithubLink"
                    />
                    <button class="link-save" @click="saveGithubLink">✔</button>
                    <button class="link-cancel" @click="cancelGithub">✖</button>
                  </div>
                  <button v-else class="link-button add-github" @click="showGithubInput = true">
                    <img :src="githubIcon" alt="GitHub" class="icon" />
                    + Добавить GitHub
                  </button>
                </template>

                <!-- Google Drive -->
                <template v-if="project.links?.google_drive">
                  <div v-if="!showEditDrive" class="link-display">
                    <a
                      :href="project.links.google_drive"
                      target="_blank"
                      rel="noopener noreferrer"
                      class="link-button drive-link"
                    >
                      <img :src="driveIcon" alt="Google Drive" class="icon" />
                      Google Диск
                    </a>
                    <div class="link-actions">
                      <button class="link-edit" @click="startEditDrive" title="Редактировать">✎</button>
                      <button class="link-delete" @click="deleteDriveLink" title="Удалить">✖</button>
                    </div>
                  </div>
                  <div v-else class="link-input-wrapper">
                    <input
                      v-model="driveEditValue"
                      type="url"
                      placeholder="https://drive.google.com/..."
                      class="link-input"
                      @keyup.enter="saveEditDrive"
                    />
                    <button class="link-save" @click="saveEditDrive">✔</button>
                    <button class="link-cancel" @click="cancelEditDrive">✖</button>
                  </div>
                </template>
                <template v-else>
                  <div v-if="showDriveInput" class="link-input-wrapper">
                    <input
                      v-model="driveInput"
                      type="url"
                      placeholder="https://drive.google.com/..."
                      class="link-input"
                      @keyup.enter="saveDriveLink"
                    />
                    <button class="link-save" @click="saveDriveLink">✔</button>
                    <button class="link-cancel" @click="cancelDrive">✖</button>
                  </div>
                  <button v-else class="link-button add-drive" @click="showDriveInput = true">
                    <img :src="driveIcon" alt="Google Drive" class="icon" />
                    + Добавить Google Диск
                  </button>
                </template>
              </div>
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
            <!-- Заголовок с кнопкой комментариев на одном уровне -->
            <div class="tasks-header">
              <h3>Активные задачи</h3>
              <button 
                v-if="isAuthor" 
                class="comments-header-btn"
                @click="showProjectComments = !showProjectComments"
              >
                <span class="btn-content">
                  <span class="comment-icon">💬</span>
                  {{ showProjectComments ? 'Скрыть комментарии' : 'Показать комментарии' }}
                  <span v-if="unreadProjectCommentsCount > 0" class="header-unread-badge">
                    {{ unreadProjectCommentsCount }}
                  </span>
                </span>
              </button>
            </div>

            <!-- Блок комментариев проекта (появляется под заголовком) -->
            <div v-if="showProjectComments && isAuthor" class="comments-container">
              <CommentsSection
                :comments="project.comments || []"
                :can-comment="isAuthor"
                :is-author="isAuthor"
                :on-add-comment="addProjectComment"
                :on-mark-as-read="markProjectCommentAsRead"
                :on-delete-comment="deleteProjectComment"
              />
            </div>

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
import CommentsSection from '@/components/CommentsSection.vue';
import type { Project, User, Task, Comment } from '@/types';
import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';

// Импорт иконок
import githubIcon from '@/assets/icons/icons8-github-30.png';
import driveIcon from '@/assets/icons/icons8-google-drive-48.png';

const baseUrl = 'http://localhost:8000';

const route = useRoute();
const router = useRouter();
const projectsStore = useProjectsStore();
const authStore = useAuthStore();
const usersStore = useUsersStore();

const project = ref<Project | null>(null);
const loading = ref(true);
const error = ref('');
const authors = ref<User[]>([]);
const showProjectComments = ref(false);

// Состояния для ввода ссылок
const showGithubInput = ref(false);
const githubInput = ref('');
const showDriveInput = ref(false);
const driveInput = ref('');

// Состояния для редактирования ссылок
const showEditGithub = ref(false);
const githubEditValue = ref('');
const showEditDrive = ref(false);
const driveEditValue = ref('');

const isAuthor = computed(() => {
  if (!authStore.userId || !project.value) return false;
  return project.value.authors_ids.includes(authStore.userId);
});

// Количество непрочитанных комментариев
const unreadProjectCommentsCount = computed(() => {
  return (project.value?.comments || []).filter(c => !c.isRead).length;
});

// Загрузка данных авторов
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

// Парсинг даты
function parseDate(dateStr: string): Date | null {
  if (!dateStr) return null;
  const parts = dateStr.split('.');
  if (parts.length !== 3) return null;
  const [day, month, year] = parts.map(Number) as [number, number, number];
  if (isNaN(day) || isNaN(month) || isNaN(year)) return null;
  return new Date(year, month - 1, day);
}

// Форматирование дат для отображения
function formatTaskDates(task: Task): string {
  if (task.timelinend) {
    return `${task.timeline || '?'} – ${task.timelinend}`;
  } else if (task.timeline && task.timeline.includes('-')) {
    const parts = task.timeline.split('-');
    if (parts.length === 2) return `${parts[0]} – ${parts[1]}`;
  }
  return task.timeline || '?';
}

// Функции для статуса задачи
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

// Разделение задач
const activeTasks = computed<Task[]>(() => {
  if (!project.value || !project.value.tasks) return [];
  return project.value.tasks.filter(task => task.status !== 'выполнена');
});

const completedTasks = computed<Task[]>(() => {
  if (!project.value || !project.value.tasks) return [];
  return project.value.tasks.filter(task => task.status === 'выполнена');
});

// Прогресс для активных задач
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

// Переход к задаче
const goToTask = (task: Task) => {
  if (!project.value || !project.value.tasks) return;
  const index = project.value.tasks.findIndex(t => t === task);
  if (index !== -1) {
    router.push(`/project/${route.params.id}/task/${index}`);
  }
};

// --- Функции для работы со ссылками ---
async function updateProjectLinks(updates: Partial<NonNullable<Project['links']>>) {
  if (!project.value) return;
  try {
    const newLinks = { ...(project.value.links || {}), ...updates };
    await axios.put(`${baseUrl}/projects/${project.value.id}`, { links: newLinks });
    project.value.links = newLinks;
  } catch (err) {
    console.error('Failed to update links', err);
    alert('Ошибка при сохранении ссылки');
  }
}

// GitHub: добавление
function saveGithubLink() {
  if (githubInput.value.trim()) {
    updateProjectLinks({ github: githubInput.value.trim() });
  }
  showGithubInput.value = false;
  githubInput.value = '';
}

function cancelGithub() {
  showGithubInput.value = false;
  githubInput.value = '';
}

// GitHub: редактирование
function startEditGithub() {
  githubEditValue.value = project.value?.links?.github || '';
  showEditGithub.value = true;
}

function saveEditGithub() {
  if (githubEditValue.value.trim()) {
    updateProjectLinks({ github: githubEditValue.value.trim() });
  }
  showEditGithub.value = false;
  githubEditValue.value = '';
}

function cancelEditGithub() {
  showEditGithub.value = false;
  githubEditValue.value = '';
}

// GitHub: удаление
async function deleteGithubLink() {
  if (!project.value?.links?.github) return;
  if (confirm('Удалить ссылку на GitHub?')) {
    const newLinks = { ...project.value.links };
    delete newLinks.github;
    await updateProjectLinks(newLinks as Partial<NonNullable<Project['links']>>);
  }
}

// Google Drive: добавление
function saveDriveLink() {
  if (driveInput.value.trim()) {
    updateProjectLinks({ google_drive: driveInput.value.trim() });
  }
  showDriveInput.value = false;
  driveInput.value = '';
}

function cancelDrive() {
  showDriveInput.value = false;
  driveInput.value = '';
}

// Google Drive: редактирование
function startEditDrive() {
  driveEditValue.value = project.value?.links?.google_drive || '';
  showEditDrive.value = true;
}

function saveEditDrive() {
  if (driveEditValue.value.trim()) {
    updateProjectLinks({ google_drive: driveEditValue.value.trim() });
  }
  showEditDrive.value = false;
  driveEditValue.value = '';
}

function cancelEditDrive() {
  showEditDrive.value = false;
  driveEditValue.value = '';
}

// Google Drive: удаление
async function deleteDriveLink() {
  if (!project.value?.links?.google_drive) return;
  if (confirm('Удалить ссылку на Google Диск?')) {
    const newLinks = { ...project.value.links };
    delete newLinks.google_drive;
    await updateProjectLinks(newLinks as Partial<NonNullable<Project['links']>>);
  }
}

// --- Функции для работы с комментариями ---
const addProjectComment = async (content: string) => {
  if (!project.value || !authStore.user) return;
  
  const newComment: Comment = {
    id: uuidv4(),
    authorId: authStore.user.id,
    content,
    createdAt: new Date().toISOString(),
    isRead: false
  };
  
  const updatedComments = [...(project.value.comments || []), newComment];
  
  try {
    await axios.put(`${baseUrl}/projects/${project.value.id}`, {
      comments: updatedComments
    });
    
    project.value.comments = updatedComments;
  } catch (error) {
    console.error('Failed to add comment:', error);
    alert('Ошибка при добавлении комментария');
  }
};

const markProjectCommentAsRead = async (commentId: string) => {
  if (!project.value || !isAuthor.value) return;
  
  const updatedComments = (project.value.comments || []).map(c => 
    c.id === commentId ? { ...c, isRead: true } : c
  );
  
  try {
    await axios.put(`${baseUrl}/projects/${project.value.id}`, {
      comments: updatedComments
    });
    
    project.value.comments = updatedComments;
  } catch (error) {
    console.error('Failed to mark comment as read:', error);
  }
};

const deleteProjectComment = async (commentId: string) => {
  if (!project.value) return;
  
  const updatedComments = (project.value.comments || []).filter(c => c.id !== commentId);
  
  try {
    await axios.put(`${baseUrl}/projects/${project.value.id}`, {
      comments: updatedComments
    });
    
    project.value.comments = updatedComments;
  } catch (error) {
    console.error('Failed to delete comment:', error);
    alert('Ошибка при удалении комментария');
  }
};

// --- Удаление проекта ---
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

// --- Навигация ---
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

/* Общие стили */
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

/* Макеты */
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

/* Заголовок задач с кнопкой комментариев */
.tasks-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.tasks-header h3 {
  color: var(--heading-color);
  font-weight: 500;
  font-size: 1.5rem;
  margin: 0;
}

.comments-header-btn {
  background: var(--accent-color);
  color: var(--button-text);
  border: none;
  border-radius: 30px;
  padding: 8px 16px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  box-shadow: var(--shadow);
}

.comments-header-btn:hover {
  background: var(--accent-hover);
  transform: translateY(-2px);
  box-shadow: var(--shadow-strong);
}

.btn-content {
  display: flex;
  align-items: center;
  gap: 6px;
}

.comment-icon {
  font-size: 1.1rem;
}

.header-unread-badge {
  background: #f44336;
  color: white;
  border-radius: 50%;
  min-width: 20px;
  height: 20px;
  font-size: 11px;
  font-weight: bold;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
  margin-left: 4px;
}

/* Контейнер для комментариев - исправлен для попадания в рамку */
.comments-container {
  margin-bottom: 25px;
  border: 1px solid var(--border-color);
  border-radius: 16px;
  overflow: hidden;
  width: 100%;
  box-sizing: border-box;
  background: var(--bg-card);
}

/* Стили для внутреннего компонента CommentsSection */
.comments-container :deep(.comments-section) {
  margin-top: 0;
  border: none;
  border-radius: 0;
  box-shadow: none;
  background: transparent;
  padding: 0 15px;
}

/* Заголовок комментариев */
.comments-container :deep(.comments-section .comments-header) {
  margin-top: 0;
  padding-top: 15px;
  padding-bottom: 10px;
  margin-bottom: 10px;
}

/* Список комментариев */
.comments-container :deep(.comments-section .comments-list) {
  max-height: 350px;
  overflow-y: auto;
  padding-right: 5px;
  margin-bottom: 0;
}

/* Последний комментарий */
.comments-container :deep(.comments-section .comments-list .comment-item:last-child) {
  margin-bottom: 5px;
}

/* Сообщение об отсутствии комментариев */
.comments-container :deep(.comments-section .no-comments) {
  padding: 20px 15px;
  margin-bottom: 0;
}

/* Форма добавления комментария */
.comments-container :deep(.comments-section .add-comment-form) {
  margin: 10px 0 15px 0;
  padding: 15px;
  background: var(--bg-page);
  border-radius: 12px;
}

/* Кнопка добавления комментария */
.comments-container :deep(.comments-section .add-comment-button) {
  margin-right: 0;
}

.task-tree {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-top: 20px;
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
  color: black;
  font-size: 0.85rem;
  font-weight: 500;
  background-color: transparent;
}

/* Выполненные задачи */
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

/* Кнопки управления */
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

/* Ссылки проекта */
.project-links {
  margin-bottom: 28px;
}

.project-links h3 {
  color: var(--heading-color);
  margin-bottom: 10px;
  font-weight: 500;
}

.links-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.link-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 16px;
  border-radius: 50px;
  font-size: 0.95rem;
  font-weight: 500;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.link-button .icon {
  width: 20px;
  height: 20px;
  margin-right: 6px;
  object-fit: contain;
}

.add-github,
.add-drive {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.add-github:hover,
.add-drive:hover {
  background: var(--bg-page);
  transform: translateY(-2px);
  box-shadow: var(--shadow);
}

.link-input-wrapper {
  display: flex;
  gap: 4px;
  align-items: center;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 50px;
  padding: 4px 4px 4px 12px;
}

.link-input {
  flex: 1;
  min-width: 200px;
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: 0.95rem;
  outline: none;
}

.link-save,
.link-cancel,
.link-edit,
.link-delete {
  background: transparent;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 50%;
  transition: background 0.2s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.link-save {
  color: #4caf50;
}

.link-save:hover {
  background: rgba(76, 175, 80, 0.2);
}

.link-cancel {
  color: #f44336;
}

.link-cancel:hover {
  background: rgba(244, 67, 54, 0.2);
}

.link-edit {
  color: #ff9800;
}

.link-edit:hover {
  background: rgba(255, 152, 0, 0.2);
}

.link-delete {
  color: #f44336;
}

.link-delete:hover {
  background: rgba(244, 67, 54, 0.2);
}

.link-display {
  display: flex;
  align-items: center;
  gap: 8px;
}

.link-actions {
  display: flex;
  gap: 4px;
}

.github-link {
  background: #24292e;
  color: white;
}

.github-link:hover {
  background: #2c3e50;
  transform: translateY(-2px);
  box-shadow: var(--shadow-strong);
}

.drive-link {
  background: #4285f4;
  color: white;
}

.drive-link:hover {
  background: #3367d6;
  transform: translateY(-2px);
  box-shadow: var(--shadow-strong);
}

.loading,
.error {
  text-align: center;
  color: var(--text-primary);
  font-size: 1.2rem;
  padding: 40px;
}
</style>