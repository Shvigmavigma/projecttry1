import { defineStore } from 'pinia';
import axios from 'axios';
import type { Project, ProjectCreate, ProjectUpdate } from '@/types';
import { useAuthStore } from './auth';

interface ProjectsState {
  projects: Project[];
  currentProject: Project | null;
}

export const useProjectsStore = defineStore('projects', {
  state: (): ProjectsState => ({
    projects: [],
    currentProject: null,
  }),
  actions: {
    async fetchAllProjects(): Promise<void> {
      const response = await axios.get<Project[]>('http://localhost:8000/projects/');
      this.projects = response.data;
    },
    async fetchUserProjects(): Promise<Project[]> {
      const auth = useAuthStore();
      if (!auth.userId) return [];
      const response = await axios.get<Project[]>('http://localhost:8000/projects/', {
        params: { author_id: auth.userId },
      });
      this.projects = response.data;
      return response.data;
    },
    async fetchProjectById(id: number): Promise<Project> {
      const response = await axios.get<Project>(`http://localhost:8000/projects/${id}`);
      this.currentProject = response.data;
      return response.data;
    },
    async createProject(projectData: Omit<ProjectCreate, 'authors_ids'>): Promise<Project> {
      const auth = useAuthStore();
      const payload: ProjectCreate = {
        ...projectData,
        authors_ids: [auth.userId!],
      };
      const response = await axios.post<Project>('http://localhost:8000/projects/', payload);
      return response.data;
    },
    async updateProject(id: number, updateData: ProjectUpdate): Promise<Project> {
      const response = await axios.put<Project>(`http://localhost:8000/projects/${id}`, updateData);
      return response.data;
    },
    async deleteProject(id: number): Promise<void> {
      await axios.delete(`http://localhost:8000/projects/?project_id=${id}`);
    },
  },
});