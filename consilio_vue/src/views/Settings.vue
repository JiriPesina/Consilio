<template>
  <div id="Settings">
    <article id="LoginContent">
      <section id="LoginBox">
        <h4>O vás</h4>

        <h5>
          Uživatelské jméno:
          <input
            type="text"
            v-model="username"
            placeholder="Zadejte nové uživatelské jméno"
          />
        </h5>
        <h5>
          E-mail:
          <input
            type="email"
            v-model="email"
            placeholder="Zadejte nový e-mail"
          />
        </h5>
        <h5>
          Klíč API:
          <input
            type="text"
            v-model="API_Key"
            placeholder="Zadejte svůj Redmine API klíč"
          />
        </h5>

        <div class="button">
          <button @click="submitFormSettings">Uložit změny</button>
        </div>

        <div id="ErrorNotification" v-if="infoErrors.length">
          <p v-for="(err, idx) in infoErrors" :key="idx">{{ err }}</p>
        </div>
      </section>

      <section id="PasswordBox">
        <h4>Změna hesla</h4>

        <h5>
          Aktuální heslo:
          <input
            type="password"
            v-model="currentPassword"
            placeholder="Zadejte aktuální heslo"
          />
        </h5>
        <h5>
          Nové heslo:
          <input
            type="password"
            v-model="newPassword"
            placeholder="Zadejte nové heslo"
          />
        </h5>
        <h5>
          Potvrzení nového hesla:
          <input
            type="password"
            v-model="confirmNewPassword"
            placeholder="Potvrďte nové heslo"
          />
        </h5>

        <div class="button">
          <button @click="submitPasswordChange">Aktualizovat heslo</button>
        </div>

        <div id="PasswordErrorNotification" v-if="passwordErrors.length">
          <p v-for="(err, idx) in passwordErrors" :key="idx">{{ err }}</p>
        </div>
      </section>
    </article>
  </div>
</template>

<script>
import axios from 'axios'
import { toast } from 'vue3-toastify'
import 'vue3-toastify/dist/index.css'

export default {
  name: 'Settings',
  data() {
    return {
      username: '',
      email: '',
      API_Key: '',
      infoErrors: [],
      currentPassword: '',
      newPassword: '',
      confirmNewPassword: '',
      passwordErrors: []
    }
  },
  async mounted() {
    document.title = 'Settings | Consilio'
    await this.fetchCurrentUser()
  },
  methods: {
    async fetchCurrentUser() {
      try {
        const response = await axios.get('/api/v1/users/me/')
        this.username = response.data.username
        this.email = response.data.email
        this.API_Key = response.data.API_Key || ''
      } catch (err) {
        console.error('Chyba při načítání uživatele:', err)
        toast.error('Nepodařilo se načíst data uživatele.')
      }
    },

    async submitFormSettings() {
      this.infoErrors = []

      if (!this.username) {
        this.infoErrors.push('Uživatelské jméno je povinné')
      }
      if (!this.email) {
        this.infoErrors.push('E-mail je povinný')
      }
      if (!this.API_Key) {
        this.infoErrors.push('API klíč je povinný (pro ověření v Redmine)')
      }
      if (this.infoErrors.length) {
        return
      }

      try {
        const payload = {
          username: this.username,
          email: this.email,
          API_Key: this.API_Key,
        }
        const response = await axios.put('/api/v1/users/update/', payload)

        if (response.status === 200 && response.data.success) {
          toast.success('Údaje byly úspěšně aktualizované')
          await this.fetchCurrentUser()
        } else {
          toast.error('Nové údaje nesouhlasí s údaji v Redmine')
        }
      } catch (error) {
        if (error.response && error.response.status === 400) {
          const data = error.response.data
          if (data.non_field_errors) {
            data.non_field_errors.forEach((msg) => this.infoErrors.push(msg))
            toast.error('Nové údaje nesouhlasí s údaji v Redmine')
          }
          for (const prop in data) {
            if (prop === 'non_field_errors') continue
            if (Array.isArray(data[prop])) {
              data[prop].forEach((msg) => this.infoErrors.push(`${prop}: ${msg}`))
            } else {
              this.infoErrors.push(`${prop}: ${data[prop]}`)
            }
          }
        } else {
          console.error(error)
          toast.error('Nepodařilo se spojit se serverem')
        }
      }
    },

    async submitPasswordChange() {
      this.passwordErrors = []

      if (!this.currentPassword) {
        this.passwordErrors.push('Aktuální heslo je povinné')
      }
      if (!this.newPassword) {
        this.passwordErrors.push('Nové heslo je povinné')
      }
      if (!this.confirmNewPassword) {
        this.passwordErrors.push('Potvrzení nového hesla je povinné')
      }
      if (this.newPassword && this.confirmNewPassword && this.newPassword !== this.confirmNewPassword) {
        this.passwordErrors.push('Nové heslo a potvrzení se musí shodovat')
      }
      if (this.passwordErrors.length) {
        return
      }

      try {
        const payload = {
          current_password: this.currentPassword,
          new_password: this.newPassword
        }
        const response = await axios.put('/api/v1/users/change_password/', payload)

        if (response.status === 200 && response.data.success) {
          toast.success('Heslo bylo úspěšně změněno')
          this.currentPassword = ''
          this.newPassword = ''
          this.confirmNewPassword = ''
        } else {
          toast.error('Aktuální heslo nesouhlasí')
          this.passwordErrors.push('Aktuální heslo nesouhlasí')
        }
      } catch (error) {
        if (error.response && error.response.status === 400) {
          const data = error.response.data
          if (data.non_field_errors) {
            data.non_field_errors.forEach((msg) => this.passwordErrors.push(msg))
            toast.error('Aktuální heslo nesouhlasí')
          }
          for (const prop in data) {
            if (prop === 'non_field_errors') continue
            if (Array.isArray(data[prop])) {
              data[prop].forEach((msg) => this.passwordErrors.push(`${prop}: ${msg}`))
            } else {
              this.passwordErrors.push(`${prop}: ${data[prop]}`)
            }
          }
        } else {
          console.error(error)
          toast.error('Nepodařilo se spojit se serverem')
        }
      }
    }
  }
}
</script>

<style lang="css" scoped src="../assets/Settings.css"></style>