import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useThemeStore = defineStore('theme', () => {
  // Проверяем сохранённую тему или предпочтения системы
  const savedTheme = localStorage.getItem('theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const initialDark = savedTheme === 'dark' || (savedTheme === null && prefersDark);

  const isDark = ref(initialDark);

  function setTheme(dark: boolean) {
    isDark.value = dark;
    localStorage.setItem('theme', dark ? 'dark' : 'light');
    applyTheme(dark);
  }

  function toggleTheme() {
    setTheme(!isDark.value);
  }

  function applyTheme(dark: boolean) {
    if (dark) {
      document.documentElement.classList.add('dark-theme');
      document.documentElement.classList.remove('light-theme');
    } else {
      document.documentElement.classList.add('light-theme');
      document.documentElement.classList.remove('dark-theme');
    }
  }

  // Инициализация
  applyTheme(isDark.value);

  return { isDark, toggleTheme, setTheme };
});