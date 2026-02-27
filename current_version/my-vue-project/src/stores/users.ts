import { defineStore } from 'pinia';
import axios from 'axios';
import type { User } from '@/types';

interface UsersState {
  users: User[];
}

export const useUsersStore = defineStore('users', {
  state: (): UsersState => ({
    users: [],
  }),
  actions: {
    async fetchAllUsers(): Promise<void> {
      const response = await axios.get<User[]>('http://localhost:8000/userslist/');
      this.users = response.data;
    },
    async searchUsers(query: string): Promise<void> {
      const response = await axios.get<User[]>('http://localhost:8000/users/', {
        params: { q: query },
      });
      this.users = response.data;
    },
  },
});