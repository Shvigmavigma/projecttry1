export interface User {
  id: number;
  nickname: string;
  fullname: string;
  class: number;          // поле class_ сериализуется как class
  speciality: string | null;
  email: string;
}

export interface Task {
  title: string;
  status: string;
  body: string;
  timeline: string;
}

export interface Project {
  id: number;
  title: string;
  body: string;
  underbody: string;
  authors_ids: number[];
  tasks: Task[];
}

export type ProjectCreate = Omit<Project, 'id'>;

export interface ProjectUpdate {
  title?: string;
  body?: string;
  underbody?: string;
  tasks?: Task[];
  author_id?: number;
}