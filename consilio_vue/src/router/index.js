import { createRouter, createWebHistory } from 'vue-router'
import store from '@/store'

import Dashboard from '../views/DashBoard.vue'
import SignUpIn from '../views/SingUpIn.vue'
import Settings from '../views/Settings.vue'

const routes = [
  {
    path: '/',
    redirect: () => store.state.isAuthenticated ? '/dashboard' : '/singup-in'
  },
  {
    path: '/dashboard',
    name: 'Dashboard', 
    component: Dashboard,
    meta: { requiresAuth: true, hideFooter: true }
  },
  {
    path: '/singup-in',
    name: 'SingUpIn',
    component: SignUpIn,
    meta: { guestOnly: true, hideFooter: true }
  },

  {
    path: '/settings',
    name: 'settings',
    component: Settings,
    meta: { hideFooter: true }
  },
  {
    path: '/:catchAll(.*)',
    redirect: () => store.state.isAuthenticated ? '/dashboard' : '/singup-in'
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

router.beforeEach((to, from, next) => {
  const isAuth = store.state.isAuthenticated

  if (to.meta.requiresAuth && !isAuth) {
    return next({ name: 'SingUpIn' })
  }
  if (to.meta.guestOnly && isAuth) {
    return next({ name: 'Dashboard' })
  }
  next()
})

export default router



