<template>
  <button 
    class="theme-toggle" 
    @click="toggleTheme" 
    :title="`Переключить на ${isDark ? 'светлую' : 'тёмную'} тему`"
  >
    {{ isDark ? '☀️' : '🌙' }}
  </button>
</template>

<script setup lang="ts">
import { useThemeStore } from '@/stores/theme';
import { storeToRefs } from 'pinia';

const themeStore = useThemeStore();
const { isDark } = storeToRefs(themeStore);
const { toggleTheme } = themeStore;
</script>

<style scoped>
.theme-toggle {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 50%;
  width: 44px;
  height: 44px;
  font-size: 1.5rem;
  cursor: pointer;
  box-shadow: var(--shadow);
  transition: all 0.2s ease;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.theme-toggle:hover {
  transform: scale(1.1);
}
</style>