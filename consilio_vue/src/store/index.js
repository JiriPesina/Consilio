import { createStore } from 'vuex'

const store = createStore({
  state: {
    token: '',
    isAuthenticated: false,
    isUserLoggedIn: false,
    username: '',
    isLoading: false,
    is_superuser: false,
    redmine_id: null
  },
  mutations: {
    initializeStore(state) {
      const token = sessionStorage.getItem('token')
      if (token) {
        state.token = token
        state.isAuthenticated = true
        state.username = sessionStorage.getItem('username') || ''
        state.isUserLoggedIn = !!state.username
        state.is_superuser = JSON.parse(sessionStorage.getItem('is_superuser') || 'false')
        const rid = sessionStorage.getItem('redmine_id')
        state.redmine_id = rid !== null ? Number(rid) : null
      } else {
        state.token = ''
        state.isAuthenticated = false
        state.username = ''
        state.isUserLoggedIn = false
        state.is_superuser = false
        state.redmine_id = null
      }
    },
    setToken(state, token) {
      state.token = token
      state.isAuthenticated = true
      sessionStorage.setItem('token', token)
    },
    setUsername(state, username) {
      state.username = username
      state.isUserLoggedIn = true
      sessionStorage.setItem('username', username)
    },
    setIsSuperuser(state, flag) {
      state.is_superuser = flag
      sessionStorage.setItem('is_superuser', JSON.stringify(flag))
    },
    setRedmineId(state, id) {
      state.redmine_id = id
      if (id !== null && id !== undefined) {
        sessionStorage.setItem('redmine_id', String(id))
      } else {
        sessionStorage.removeItem('redmine_id')
      }
    },
    removeToken(state) {
      state.token = ''
      state.isAuthenticated = false
      state.username = ''
      state.isUserLoggedIn = false
      state.is_superuser = false
      state.redmine_id = null
      sessionStorage.removeItem('token')
      sessionStorage.removeItem('username')
      sessionStorage.removeItem('is_superuser')
      sessionStorage.removeItem('redmine_id')
    },
    setIsLoading(state, status) {
      state.isLoading = status
    }
  }
})

store.commit('initializeStore')
window.addEventListener('beforeunload', () => store.commit('removeToken'))

export default store


