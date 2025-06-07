// src/store/index.js
import { createStore } from 'vuex'

const store = createStore({
  state: {
    token: '',
    isAuthenticated: false,
    isUserLoggedIn: false,
    username: '',
    isLoading: false
  },
  mutations: {
    initializeStore(state) {
      const token = sessionStorage.getItem('token')
      if (token) {
        state.token = token
        state.isAuthenticated = true
        state.username = sessionStorage.getItem('username') || ''
        state.isUserLoggedIn = !!state.username
      } else {
        state.token = ''
        state.isAuthenticated = false
        state.username = ''
        state.isUserLoggedIn = false
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
    removeToken(state) {
      state.token = ''
      state.isAuthenticated = false
      state.username = ''
      state.isUserLoggedIn = false
      sessionStorage.removeItem('token')
      sessionStorage.removeItem('username')
    },
    setIsLoading(state, status) {
      state.isLoading = status
    }
  }
})

store.commit('initializeStore')
window.addEventListener('beforeunload', () => store.commit('removeToken'))

export default store


