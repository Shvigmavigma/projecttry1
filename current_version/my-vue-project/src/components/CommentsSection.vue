<template>
  <div class="comments-section">
    <div class="comments-header">
      <h3>Комментарии</h3>
      <button 
        v-if="canComment" 
        class="add-comment-button"
        @click="showAddComment = true"
      >
        + Добавить комментарий
      </button>
    </div>

    <!-- Форма добавления комментария -->
    <div v-if="showAddComment" class="add-comment-form">
      <textarea
        v-model="newComment"
        placeholder="Введите комментарий..."
        rows="3"
      ></textarea>
      <div class="form-actions">
        <button @click="saveComment" :disabled="!newComment.trim()" class="save-btn">
          Отправить
        </button>
        <button @click="cancelAddComment" class="cancel-btn">Отмена</button>
      </div>
    </div>

    <!-- Список комментариев -->
    <div v-if="comments.length > 0" class="comments-list">
      <div
        v-for="comment in sortedComments"
        :key="comment.id"
        class="comment-item"
        :class="{ 'unread': !comment.isRead && isAuthor }"
      >
        <div class="comment-header">
          <div class="comment-author">
            <div class="author-avatar">
              <img
                v-if="getAuthorAvatar(comment.authorId)"
                :src="getAuthorAvatar(comment.authorId)"
                :alt="getAuthorNickname(comment.authorId)"
                @error="handleAuthorImageError(comment.authorId)"
              />
              <span v-else>{{ getAuthorInitials(comment.authorId) }}</span>
            </div>
            <span class="author-name">{{ getAuthorNickname(comment.authorId) }}</span>
          </div>
          <div class="comment-meta">
            <span class="comment-date">{{ formatDate(comment.createdAt) }}</span>
            <span v-if="!comment.isRead && isAuthor" class="unread-badge">Новый</span>
            
            <!-- Кнопка удаления комментария -->
            <button 
              v-if="canDeleteComment(comment)"
              class="delete-comment-btn"
              @click="confirmDeleteComment(comment)"
              title="Удалить комментарий"
            >
              <span class="delete-icon">🗑️</span>
            </button>
          </div>
        </div>
        <div class="comment-content">
          {{ comment.content }}
        </div>
        <div v-if="isAuthor && !comment.isRead" class="comment-actions">
          <button @click="markAsRead(comment.id)" class="mark-read-btn">
            Отметить как прочитанное
          </button>
        </div>
      </div>
    </div>
    <div v-else class="no-comments">
      Пока нет комментариев
    </div>

    <!-- Модальное окно подтверждения удаления (на весь экран) -->
    <div v-if="showDeleteModal" class="delete-modal-overlay" @click.self="closeDeleteModal">
      <div class="delete-modal-content">
        <div class="delete-modal-icon">🗑️</div>
        <h3>Удаление комментария</h3>
        <p>Вы уверены, что хотите удалить этот комментарий?</p>
        <p class="comment-preview">"{{ commentToDelete?.content.substring(0, 50) }}{{ commentToDelete?.content.length > 50 ? '...' : '' }}"</p>
        <div class="delete-modal-actions">
          <button class="delete-modal-confirm" @click="deleteComment">
            Да, удалить
          </button>
          <button class="delete-modal-cancel" @click="closeDeleteModal">
            Отмена
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import type { Comment } from '@/types';
import { useUsersStore } from '@/stores/users';
import { useAuthStore } from '@/stores/auth';

const props = defineProps<{
  comments: Comment[];
  canComment: boolean;
  isAuthor: boolean;
  onAddComment?: (content: string) => Promise<void>;
  onMarkAsRead?: (commentId: string) => Promise<void>;
  onDeleteComment?: (commentId: string) => Promise<void>;
}>();

const emit = defineEmits(['update:comments']);

const usersStore = useUsersStore();
const authStore = useAuthStore();

const showAddComment = ref(false);
const newComment = ref('');
const authorImageErrors = ref<Record<number, boolean>>({});
const showDeleteModal = ref(false);
const commentToDelete = ref<Comment | null>(null);

const baseUrl = 'http://localhost:8000';

// Сортировка комментариев по дате (новые сверху)
const sortedComments = computed(() => {
  return [...props.comments].sort((a, b) => 
    new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
  );
});

// Проверка, может ли пользователь удалить комментарий
const canDeleteComment = (comment: Comment) => {
  // Автор проекта может удалять любые комментарии
  if (props.isAuthor) return true;
  
  // Автор комментария может удалить свой комментарий
  if (authStore.user?.id === comment.authorId) return true;
  
  return false;
};

// Форматирование даты
const formatDate = (dateStr: string) => {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'только что';
  if (diffMins < 60) return `${diffMins} мин назад`;
  if (diffHours < 24) return `${diffHours} ч назад`;
  if (diffDays === 1) return 'вчера';
  if (diffDays < 7) return `${diffDays} дн назад`;
  
  return date.toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// Получение данных автора
const getAuthorNickname = (id: number): string => {
  const user = usersStore.users.find(u => u.id === id);
  return user ? user.nickname : `ID: ${id}`;
};

const getAuthorAvatar = (id: number): string | undefined => {
  if (authorImageErrors.value[id]) return undefined;
  const user = usersStore.users.find(u => u.id === id);
  return user?.avatar ? `${baseUrl}/avatars/${user.avatar}` : undefined;
};

const getAuthorInitials = (id: number): string => {
  const user = usersStore.users.find(u => u.id === id);
  return user?.nickname?.charAt(0).toUpperCase() || '?';
};

const handleAuthorImageError = (id: number) => {
  authorImageErrors.value[id] = true;
};

// Добавление комментария
const saveComment = async () => {
  if (!newComment.value.trim() || !props.onAddComment) return;
  
  await props.onAddComment(newComment.value);
  newComment.value = '';
  showAddComment.value = false;
};

const cancelAddComment = () => {
  newComment.value = '';
  showAddComment.value = false;
};

// Отметка как прочитанное
const markAsRead = async (commentId: string) => {
  if (props.onMarkAsRead) {
    await props.onMarkAsRead(commentId);
  }
};

// Удаление комментария
const confirmDeleteComment = (comment: Comment) => {
  commentToDelete.value = comment;
  showDeleteModal.value = true;
};

const closeDeleteModal = () => {
  showDeleteModal.value = false;
  commentToDelete.value = null;
};

const deleteComment = async () => {
  if (!commentToDelete.value || !props.onDeleteComment) return;
  
  await props.onDeleteComment(commentToDelete.value.id);
  closeDeleteModal();
};

// Прокрутка вниз
const scrollToBottom = () => {
  const container = document.querySelector('.comments-list');
  if (container) {
    container.scrollTop = container.scrollHeight;
  }
};

// Следим за новыми комментариями для автопрокрутки
watch(() => props.comments.length, () => {
  scrollToBottom();
});
</script>

<style scoped>
.comments-section {
  margin-top: 30px;
  padding: 20px;
  background: var(--bg-card);
  border-radius: 16px;
  box-shadow: var(--shadow);
  position: relative;
  max-width: 100%;
  overflow-x: hidden;
}

.comments-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 2px solid var(--border-color);
}

.comments-header h3 {
  color: var(--heading-color);
  font-size: 1.2rem;
  font-weight: 500;
  margin: 0;
}

.add-comment-button {
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

.add-comment-button:hover {
  background: var(--accent-hover);
}

.add-comment-form {
  margin-bottom: 20px;
  padding: 15px;
  background: var(--bg-page);
  border-radius: 12px;
}

.add-comment-form textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--input-border);
  border-radius: 8px;
  background: var(--input-bg);
  color: var(--text-primary);
  font-size: 0.95rem;
  resize: vertical;
  margin-bottom: 10px;
  box-sizing: border-box;
}

.add-comment-form textarea:focus {
  outline: none;
  border-color: var(--accent-color);
}

.form-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.save-btn, .cancel-btn {
  padding: 8px 20px;
  border: none;
  border-radius: 30px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.save-btn {
  background: var(--accent-color);
  color: var(--button-text);
}

.save-btn:hover:not(:disabled) {
  background: var(--accent-hover);
}

.save-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.cancel-btn {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.cancel-btn:hover {
  background: var(--bg-page);
}

.comments-list {
  max-height: 400px;
  overflow-y: auto;
  padding-right: 5px;
}

.comment-item {
  padding: 15px;
  margin-bottom: 10px;
  background: var(--bg-page);
  border-radius: 12px;
  transition: all 0.2s;
  border-left: 4px solid transparent;
  position: relative;
}

.comment-item.unread {
  border-left-color: var(--accent-color);
  background: rgba(66, 185, 131, 0.05);
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.comment-author {
  display: flex;
  align-items: center;
  gap: 8px;
}

.author-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--accent-color);
  color: var(--button-text);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
  overflow: hidden;
}

.author-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.author-avatar span {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.author-name {
  color: var(--heading-color);
  font-weight: 600;
  font-size: 0.95rem;
}

.comment-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.comment-date {
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.unread-badge {
  background: var(--accent-color);
  color: var(--button-text);
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
}

.delete-comment-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 6px;
  border-radius: 50%;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.6;
}

.delete-icon {
  font-size: 1.1rem;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.1));
}

/* Стили для светлой темы */
.light-theme .delete-icon {
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.2));
}

.delete-comment-btn:hover {
  opacity: 1;
  background: rgba(244, 67, 54, 0.1);
  transform: scale(1.1);
}

.light-theme .delete-comment-btn:hover {
  background: rgba(244, 67, 54, 0.15);
}

.comment-content {
  color: var(--text-primary);
  font-size: 0.95rem;
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
  padding-right: 30px;
}

.comment-actions {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
}

.mark-read-btn {
  background: transparent;
  color: var(--accent-color);
  border: 1px solid var(--accent-color);
  border-radius: 20px;
  padding: 4px 12px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s;
}

.mark-read-btn:hover {
  background: var(--accent-color);
  color: var(--button-text);
}

.no-comments {
  text-align: center;
  color: var(--text-secondary);
  padding: 30px;
  font-style: italic;
}

/* Модальное окно на весь экран */
.delete-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(5px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  animation: fadeIn 0.2s ease;
}

.delete-modal-content {
  background: var(--modal-bg);
  border-radius: 32px;
  padding: 40px;
  max-width: 450px;
  width: 90%;
  box-shadow: var(--shadow-strong);
  animation: slideUp 0.3s ease;
  color: var(--modal-text);
  text-align: center;
  position: relative;
  top: -5vh;
}

.delete-modal-icon {
  font-size: 4rem;
  margin-bottom: 20px;
  animation: shake 0.5s ease;
}

.delete-modal-content h3 {
  color: var(--heading-color);
  margin-bottom: 15px;
  font-weight: 600;
  font-size: 1.8rem;
}

.delete-modal-content p {
  color: var(--text-primary);
  margin-bottom: 10px;
  font-size: 1.1rem;
}

.comment-preview {
  background: var(--bg-page);
  padding: 15px;
  border-radius: 12px;
  margin: 20px 0;
  font-style: italic;
  color: var(--text-secondary);
  border-left: 4px solid var(--accent-color);
  text-align: left;
  max-height: 100px;
  overflow-y: auto;
}

.delete-modal-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-top: 30px;
}

.delete-modal-confirm, .delete-modal-cancel {
  padding: 12px 30px;
  border: none;
  border-radius: 50px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 140px;
}

.delete-modal-confirm {
  background: #d32f2f;
  color: white;
  box-shadow: 0 4px 10px rgba(211, 47, 47, 0.3);
}

.delete-modal-confirm:hover {
  background: #b71c1c;
  transform: translateY(-2px);
  box-shadow: 0 6px 15px rgba(211, 47, 47, 0.4);
}

.light-theme .delete-modal-confirm {
  box-shadow: 0 4px 10px rgba(211, 47, 47, 0.2);
}

.delete-modal-cancel {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.delete-modal-cancel:hover {
  background: var(--bg-page);
  transform: translateY(-2px);
  box-shadow: var(--shadow-strong);
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { transform: translateY(30px); opacity: 0; }
  to { transform: translateY(-5vh); opacity: 1; }
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-2px); }
  20%, 40%, 60%, 80% { transform: translateX(2px); }
}

/* Убедимся, что комментарии не выходят за пределы */
.comments-section,
.comments-container {
  max-width: 100%;
  overflow-x: hidden;
}
</style>