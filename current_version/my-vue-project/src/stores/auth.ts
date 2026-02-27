import { defineStore } from 'pinia';
import axios from 'axios';
import type { User } from '@/types';

interface AuthState {
  user: User | null;
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: null,
  }),
  getters: {
    isAuthenticated: (state) => !!state.user,
    userId: (state) => state.user?.id,
  },
  actions: {
    async login(nickname: string, password: string): Promise<boolean> {
      try {
        const response = await axios.post<User>('http://localhost:8000/login', {
          nickname,
          password,
        });
        this.user = response.data;
        localStorage.setItem('user', JSON.stringify(this.user));
        return true;
      } catch (error) {
        console.error('Login error:', error);
        return false;
      }
    },
    async register(userData: Omit<User, 'id'> & { password: string }): Promise<boolean> {
      try {
        const response = await axios.post<User>('http://localhost:8000/users/', userData);
        this.user = response.data;
        localStorage.setItem('user', JSON.stringify(this.user));
        return true;
      } catch (error) {
        console.error('Registration error:', error);
        return false;
      }
    },
    logout() {
      this.user = null;
      localStorage.removeItem('user');
    },
    loadUserFromStorage() {
      const stored = localStorage.getItem('user');
      if (stored) {
        this.user = JSON.parse(stored);
      }
    },
  },
});