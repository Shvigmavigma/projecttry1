// src/router/index.ts
import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import VerifyEmail from '../views/VerifyEmail.vue'
import MainMenu from '../views/MainMenu.vue'
import AllUsers from '../views/AllUsers.vue'
import UserDetails from '../views/UserDetails.vue'
import AllProjects from '../views/AllProjects.vue'
import MyProjects from '../views/MyProjects.vue'  // Добавить импорт
import ProjectDetails from '../views/ProjectDetails.vue'
import ProjectEdit from '../views/ProjectEdit.vue'
import TaskDetails from '../views/TaskDetails.vue'
import TaskEdit from '../views/TaskEdit.vue'
import Profile from '../views/Profile.vue'
import ProfileEdit from '../views/ProfileEdit.vue'
import UserProjects from '../views/UserProjects.vue'
import InviteAccept from '@/views/InviteAccept.vue';

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/register',
    name: 'Register',
    component: Register
  },
  {
    path: '/verify-email',
    name: 'VerifyEmail',
    component: VerifyEmail
  },
  {
    path: '/main',
    name: 'MainMenu',
    component: MainMenu
  },
  {
    path: '/users',
    name: 'AllUsers',
    component: AllUsers
  },
  {
    path: '/user/:id',
    name: 'UserDetails',
    component: UserDetails
  },
  {
    path: '/projects',
    name: 'AllProjects',
    component: AllProjects
  },
  {
    path: '/my-projects',           // Добавить этот маршрут
    name: 'MyProjects',
    component: MyProjects
  },
  {
    path: '/project/:id',
    name: 'ProjectDetails',
    component: ProjectDetails
  },
  {
    path: '/project/edit/:id',
    name: 'ProjectEdit',
    component: ProjectEdit
  },
  {
    path: '/project/:projectId/task/:taskIndex',
    name: 'TaskDetails',
    component: TaskDetails
  },
  {
    path: '/project/:projectId/task/:taskIndex/edit',
    name: 'TaskEdit',
    component: TaskEdit
  },
  {
    path: '/profile',
    name: 'Profile',
    component: Profile
  },
  {
    path: '/profile/edit',
    name: 'ProfileEdit',
    component: ProfileEdit
  },
  {
    path: '/user/:id/projects',
    name: 'UserProjects',
    component: UserProjects
  },
  {
  path: '/invite/:token',
  name: 'InviteAccept',
  component: InviteAccept
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router