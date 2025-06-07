import { createRouter, createWebHistory } from 'vue-router';

// Import view components
import DashboardView from '../views/DashboardView.vue';
import TasksView from '../views/TasksView.vue';
import BatchesView from '../views/BatchesView.vue';
import ProvidersView from '../views/ProvidersView.vue';
import KnowledgeView from '../views/KnowledgeView.vue';
import SystemView from '../views/SystemView.vue';
import SettingsView from '../views/SettingsView.vue';

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: DashboardView
  },
  {
    path: '/tasks',
    name: 'Tasks',
    component: TasksView
  },
  {
    path: '/batches',
    name: 'Batches',
    component: BatchesView
  },
  {
    path: '/providers',
    name: 'Providers',
    component: ProvidersView
  },
  {
    path: '/knowledge',
    name: 'Knowledge',
    component: KnowledgeView
  },
  {
    path: '/system',
    name: 'System',
    component: SystemView
  },
  {
    path: '/settings',
    name: 'Settings',
    component: SettingsView
  },
  // Add a catch-all route for 404 errors
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../views/NotFoundView.vue') // Lazy load 404 page
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  linkActiveClass: 'router-link-active', // Use the class defined in App.vue
  linkExactActiveClass: 'router-link-exact-active'
});

export default router;
