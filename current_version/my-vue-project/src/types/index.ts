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

export interface Comment {
  id: string;
  authorId: number;
  content: string;
  createdAt: string;
  isRead: boolean;
}

export interface SubTask {
  id: string;         
  title: string;
  description?: string;
  progressPercent: number; 
  completed: boolean;
  comments?: Comment[];
}

export interface Task {
  title: string;
  status: string;
  body: string;
  timeline?: string;
  timelinend?: string;
  progress?: number;   
  subtasks?: SubTask[];
  comments?: Comment[];
}

export interface Project {
  id: number;
  title: string;
  body: string;
  underbody: string;
  authors_ids: number[];
  tasks: Task[];
  links?: ProjectLinks;
  comments?: Comment[];
}

export type ProjectCreate = Omit<Project, 'id'>;

export interface ProjectUpdate {
  title?: string;
  body?: string;
  underbody?: string;
  tasks?: Task[];
  author_id?: number;
  links?: ProjectLinks;
  comments?: Comment[];
}

export interface ProjectLinks {
  github?: string;
  google_drive?: string;
}