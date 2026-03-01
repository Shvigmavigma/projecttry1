import { defineStore } from 'pinia';
import { ref, watch } from 'vue';

export const useThemeStore = defineStore('theme', () => {
  // По умолчанию светлая тема (false)
  const savedTheme = localStorage.getItem('theme');
  const isDark = ref(savedTheme === 'dark');

  // Функция переключения темы
  function toggleTheme() {
    isDark.value = !isDark.value;
  }

  // Установка темы
  function setTheme(dark: boolean) {
    isDark.value = dark;
  }

  // Следим за изменением и сохраняем в localStorage
  watch(isDark, (newValue) => {
    localStorage.setItem('theme', newValue ? 'dark' : 'light');
    applyTheme(newValue);
  }, { immediate: true });

  // Применяем тему к документу
  function applyTheme(dark: boolean) {
    if (dark) {
      document.documentElement.classList.add('dark-theme');
      document.documentElement.classList.remove('light-theme');
    } else {
      document.documentElement.classList.add('light-theme');
      document.documentElement.classList.remove('dark-theme');
    }
  }

  return { isDark, toggleTheme, setTheme };
});