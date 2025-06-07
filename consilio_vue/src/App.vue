<template>
  <div id="app">
    <!-- Header se zobrazí pouze pokud je uživatel přihlášený -->
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

    <!-- Hlavní obsah -->
    <main>
      <router-view />
    </main>

    <!-- Footer, schovaný pokud má routa meta.hideFooter -->
    <footer v-if="!$route.meta.hideFooter">
      <h2>Skupina OLC group</h2>
      <article id="Footer-Content">
        <section class="Footer-box">
          <h3>OLC Systems s.r.o</h3>
          <p>Výrobní a řídící systémy</p>
          <a href="https://www.olc.cz">www.olc.cz</a>
        </section>
        <section class="Footer-box">
          <h3>IZON s.r.o.</h3>
          <p>Web, online marketing</p>
          <a href="https://www.izon.cz">www.izon.cz</a>
        </section>
        <section class="Footer-box">
          <h3>NET University s.r.o.</h3>
          <p>Online vzdělávání</p>
          <a href="https://www.net-university.cz">www.net-university.cz</a>
        </section>
        <section class="Footer-box">
          <h3>Orbinet s.r.o.</h3>
          <p>Web, Eshop</p>
          <a href="https://www.orbinet.cz">www.orbinet.cz</a>
        </section>
        <section class="Footer-box">
          <h3>INOL Grow Up s.r.o.</h3>
          <p>Inovativní produkty na klíč</p>
        </section>
      </article>
    </footer>
  </div>
</template>

<script>
import { mapState } from 'vuex'
import axios from 'axios'

export default {
  computed: {
    ...mapState(['token', 'isAuthenticated', 'username', 'isUserLoggedIn'])
  },
  methods: {
    logout() {
      axios.defaults.headers.common['Authorization'] = ''
      // odstraňujeme z sessionStorage, pokud jste přepnuli na sessionStorage
      sessionStorage.removeItem('token')
      sessionStorage.removeItem('username')
      sessionStorage.removeItem('userid')
      this.$store.commit('removeToken')
      this.$router.push({ name: 'SingUpIn' })
    }
  }
}
</script>

<style lang="css" src="../src/assets/MainStyle.css"></style>



