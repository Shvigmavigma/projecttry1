// types/index.ts
export interface User {
  id: number;
  nickname: string;
  fullname: string;
  class: number;
  speciality?: string;
  email: string;
  avatar?: string;
  is_active?: boolean;
  is_verified?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface SubTask {
  id: string;         
  title: string;
  description?: string;
  progressPercent: number; 
  completed: boolean;
}

export interface Task {
  title: string;
  status: string;
  body: string;
  timeline?: string;
  timelinend?: string;
  progress?: number;   
  subtasks?: SubTask[];
}

export interface Project {
  id: number;
  title: string;
  body: string;
  underbody: string;
  authors_ids: number[];
  tasks: Task[];
  links?: ProjectLinks;
}

export type ProjectCreate = Omit<Project, 'id'>;

export interface ProjectUpdate {
  title?: string;
  body?: string;
  underbody?: string;
  tasks?: Task[];
  author_id?: number;
}

export interface ProjectLinks {
  github?: string;
  google_drive?: string;
}