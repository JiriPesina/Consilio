<template>
  <div id="app">
    <!-- Upozornění při zobrazení na výšku -->
    <div v-if="showRotateWarning" class="rotate-warning">
      Prosím otočte zařízení vodorovně pro správné zobrazení aplikace.
    </div>

    <div v-else>
      <header v-if="isUserLoggedIn">
        <section id="Header-Content">
          <div id="Logo">
            <img src="../src/assets/Logo.png" alt="" width="70%" height="70%">
          </div>
          <div id="navigation">
            <nav>
              <ul>
                <li><router-link to="/dashboard" class="nav-link">Pracovní prostor</router-link></li>
                <li><router-link to="/settings" class="nav-link">Správa účtu</router-link></li>
              </ul>
            </nav>
          </div>
          <div id="SingUp">
            <a v-if="!isUserLoggedIn" href="/login">
              <img src="../src/assets/login.png" alt="Přihlásit se">
            </a>
            <div id="User" v-else>
              <p>{{ username }}</p>
              <img src="../src/assets/IconLogOut.png" alt="LogOut" @click="logout()">
            </div>
          </div>
        </section>
      </header>

      <main>
        <router-view />
      </main>
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex'
import axios from 'axios'

export default {
  data() {
    return {
      showRotateWarning: false
    }
  },
  computed: {
    ...mapState(['token', 'isAuthenticated', 'username', 'isUserLoggedIn'])
  },
  mounted() {
    this.checkOrientation()
    window.addEventListener('orientationchange', this.checkOrientation)
    window.addEventListener('resize', this.checkOrientation)
  },
  methods: {
    checkOrientation() {
      this.showRotateWarning = window.innerHeight > window.innerWidth && window.innerWidth < 800
    },
    logout() {
      axios.defaults.headers.common['Authorization'] = ''
      sessionStorage.removeItem('token')
      sessionStorage.removeItem('username')
      sessionStorage.removeItem('userid')
      this.$store.commit('removeToken')
      this.$router.push({ name: 'SingUpIn' })
    }
  }
}
</script>




