<template>
  <div class="container" ref="container">
    <!-- Registrace -->
    <div class="form-container sign-up">
      <form @submit.prevent="submitFormSingUp">
        <h1>Registrace</h1>
        <input type="text" placeholder="Uživatelské jméno" v-model="usernameSingUp" />
        <input type="password" placeholder="Heslo" v-model="passwordSingUp" />
        <input type="password" placeholder="Potvrďte heslo" v-model="password2SingUp" />
        <input type="email" placeholder="Email" v-model="emailSingUp" />
        <input type="text" placeholder="Klíč API" v-model="API_Key" />
        <button>Registrovat se</button>
        <div class="ErrorNotification" v-if="errors.length">
          <p v-for="error in errors" :key="error">{{ error }}</p>
        </div>
      </form>
    </div>

    <!-- Přihlášení -->
    <div class="form-container sign-in">
      <form @submit.prevent="submitForm">
        <h1>Přihlášení</h1>
        <input type="text" placeholder="Uživatelské jméno" v-model="username" />
        <input type="password" placeholder="Heslo" v-model="password" />
        <button>Přihlásit se</button>
        <div class="ErrorNotification" v-if="errors.length">
          <p v-for="error in errors" :key="error">{{ error }}</p>
        </div>
      </form>
    </div>

    <!-- Přepínač panelů -->
    <div class="toggle-container">
      <div class="toggle">
        <div class="toggle-panel toggle-left">
          <h1>Vítejte zpátky!</h1>
          <p>Pro poskytnutí všech funkcí vložte údaje</p>
          <button class="hidden" @click="activateSignIn">Přihlásit se</button>
        </div>

        <div class="toggle-panel toggle-right">
          <h1>Vítejte!</h1>
          <p>Pro poskytnutí všech funkcí vložte údaje</p>
          <button class="hidden" @click="activateSignUp">Registrovat se</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { toast } from 'vue3-toastify'
import 'vue3-toastify/dist/index.css'

export default {
  name: 'SignUpIn',
  data() {
    return {
      username: '',
      password: '',
      usernameSingUp: '',
      passwordSingUp: '',
      password2SingUp: '',
      emailSingUp: '',
      API_Key: '',
      errors: []
    }
  },
  methods: {
    activateSignUp() {
      this.$refs.container.classList.add('active')
    },
    activateSignIn() {
      this.$refs.container.classList.remove('active')
    },

    async submitFormSingUp() {
      this.errors = []
      if (!this.usernameSingUp)   this.errors.push('Chybí uživatelské jméno')
      if (!this.passwordSingUp)   this.errors.push('Chybí heslo')
      if (this.passwordSingUp !== this.password2SingUp) this.errors.push('Hesla se neshodují')
      if (!this.emailSingUp)      this.errors.push('Chybí email')
      if (!this.API_Key)          this.errors.push('Chybí klíč API')
      if (this.errors.length) return

      try {
        const formData = {
          username: this.usernameSingUp,
          password: this.passwordSingUp,
          email:    this.emailSingUp,
          API_Key:  this.API_Key
        }

        const signupResponse = await axios.post('/api/v1/users/create/', formData)

        if (signupResponse.status === 201 || signupResponse.data.id) {
          toast.success('Účet byl úspěšně vytvořen! Můžete se přihlásit.', {
            autoClose: 3000
          })
          this.usernameSingUp = ''
          this.passwordSingUp = ''
          this.password2SingUp = ''
          this.emailSingUp = ''
          this.API_Key = ''
          this.activateSignIn()
        } else {
          this.errors.push('Registrace proběhla, ale server nevrátil potvrzení. Zkuste to znovu.')
        }
      } catch (error) {
        if (error.response && error.response.data) {
          const data = error.response.data
          if (data.non_field_errors) {
            data.non_field_errors.forEach(msg => this.errors.push(msg))
          }
          for (const prop in data) {
            if (prop === 'non_field_errors') continue
            if (Array.isArray(data[prop])) {
              data[prop].forEach(msg => this.errors.push(`${prop}: ${msg}`))
            } else {
              this.errors.push(`${prop}: ${data[prop]}`)
            }
          }
        } else {
          this.errors.push('Nepodařilo se spojit se serverem.')
          console.error(error)
        }
      }
    },

    async submitForm() {
      this.errors = []
      if (!this.username) this.errors.push('Chybí uživatelské jméno')
      if (!this.password) this.errors.push('Chybí heslo')
      if (this.errors.length) return

      try {
        // 1) Přihlášení a získání tokenu
        const response = await axios.post('/api/v1/auth/token/login/', {
          username: this.username,
          password: this.password
        })
        const token = response.data.auth_token

        // 2) Uložení do store a sessionStorage
        this.$store.commit('setToken', token)
        this.$store.commit('setUsername', this.username)
        axios.defaults.headers.common['Authorization'] = 'Token ' + token

        // 3) Načtení detailů přihlášeného uživatele
        const meRes = await axios.get('/api/v1/users/me/')
        this.$store.commit('setIsSuperuser', meRes.data.is_superuser)
        this.$store.commit('setRedmineId', meRes.data.redmine_id)

        // 4) Přesměrování na Dashboard
        this.$router.push({ name: 'Dashboard' })
      } catch (error) {
        if (error.response && error.response.data) {
          const data = error.response.data
          if (data.non_field_errors) {
            this.errors.push('Zadané údaje nejsou platné')
          } else {
            for (const prop in data) {
              if (Array.isArray(data[prop])) {
                data[prop].forEach(msg => this.errors.push(`${prop}: ${msg}`))
              } else {
                this.errors.push(`${prop}: ${data[prop]}`)
              }
            }
          }
        } else {
          this.errors.push('Přihlášení se nezdařilo. Zkuste to znovu.')
          console.error(error)
        }
      }
    }
  }
}

</script>

<style lang="css" scoped src="../assets/LoginStyle.css"></style>

