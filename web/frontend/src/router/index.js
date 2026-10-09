import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import SimulationView from '@/views/SimulationView.vue'
import SensorsView from '@/views/SensorsView.vue'
import TrackingView from '@/views/TrackingView.vue'
import EventsView from '@/views/EventsView.vue'
import ReportsView from '@/views/ReportsView.vue'
import TestsView from '@/views/TestsView.vue'
import SettingsView from '@/views/SettingsView.vue'
import ScenarioEditorView from '@/views/ScenarioEditorView.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
    meta: { title: 'الرئيسية' }
  },
  {
    path: '/simulation',
    name: 'simulation',
    component: SimulationView,
    meta: { title: 'المشهد ثنائي الأبعاد' }
  },
  {
    path: '/sensors',
    name: 'sensors',
    component: SensorsView,
    meta: { title: 'المستشعرات الافتراضية' }
  },
  {
    path: '/tracking',
    name: 'tracking',
    component: TrackingView,
    meta: { title: 'تتبع الأجسام' }
  },
  {
    path: '/events',
    name: 'events',
    component: EventsView,
    meta: { title: 'سجل الأحداث' }
  },
  {
    path: '/reports',
    name: 'reports',
    component: ReportsView,
    meta: { title: 'التقارير' }
  },
  {
    path: '/tests',
    name: 'tests',
    component: TestsView,
    meta: { title: 'الاختبارات' }
  },
  {
    path: '/scenario-editor',
    name: 'scenario-editor',
    component: ScenarioEditorView,
    meta: { title: 'محرر السيناريوهات' }
  },
  {
    path: '/settings',
    name: 'settings',
    component: SettingsView,
    meta: { title: 'الإعدادات' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} - نادوس Dv1.0` : 'نادوس Dv1.0'
  next()
})

export default router