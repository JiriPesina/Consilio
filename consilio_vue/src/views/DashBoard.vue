<template>
  <div v-if="initialized" class="dashboard-container">
    <div class="cards-container">
      <!-- Project Cards -->
      <div
        v-for="proj in selectedProjects"
        :key="`proj-${proj.id}`"
        class="card issue-card project-card"
      >
        <h3>
          {{ proj.name }}
          <img
            v-if="proj.parent_id"
            :src="ParentIcon"
            alt="Má rodičovský projekt"
            class="icon-parent"
          />
        </h3>
        <draggable
          class="issue-list"
          :list="projectIssues[proj.id]"
          :group="{ name: 'issues', pull: 'clone', put: true }"
          :clone="cloneIssue"
          :sort="false"
          item-key="id"
          @add="onProjectDropBack(proj, $event)"
        >
          <template #item="{ element }">
            <div class="issue-item" :class="{ assigned: isNewAssignment(element) }">
              <span
                class="issue-pill"
                :style="{ width: (element.completion_percentage || 0) + '%' }"
              />
              <div class="issue-text">
                <div class="title">{{ element.name }}</div>
                <div class="detail">
                  <span class="deadline">{{ formatDate(element.deadline) }}</span>
                  <span v-if="element.assigned_username" class="assigned-user">
                    {{ element.assigned_username }}
                  </span>
                  <span v-else class="unassigned-dot" />
                </div>
              </div>
            </div>
          </template>
        </draggable>
      </div>

      <!-- User Cards -->
      <div
        v-for="user in selectedUsers"
        :key="`user-${user.redmine_id}`"
        class="card issue-card user-card"
      >
        <h3>{{ user.username }}</h3>
        <!-- přidána třída drop-area, aby prázdné karty měly plochu pro drop -->
        <draggable
          class="issue-list drop-area"
          :list="assignments[user.redmine_id]"
          :group="{ name: 'issues', pull: true, put: true }"
          item-key="id"
          @add="onAssign(user, $event)"
          @remove="onUnassign(user, $event)"
        >
          <template #item="{ element }">
            <div class="issue-item dragging-visible">
              <span
                class="issue-pill"
                :style="{ width: (element.completion_percentage || 0) + '%' }"
              />
              <div class="issue-text">
                <div class="title">
                  {{ element.name }}
                  <img
                    v-if="element.project_parent_id"
                    :src="ParentIcon"
                    alt="Project má rodiče"
                    class="icon-parent"
                  />
                </div>
                <div class="detail">
                  <span class="deadline">{{ formatDate(element.deadline) }}</span>
                </div>
              </div>
              <img
                :src="iconInfo"
                alt="info"
                class="info-icon"
                @click="openIssue(element.id)"
              />
            </div>
          </template>
        </draggable>
      </div>
    </div>

    <!-- Slide-up config panel, pouze pro superusera -->
    <div
      v-if="isSuperuser"
      ref="panel"
      class="slide-panel"
      :style="{ top: panelTop + 'px' }"
      @mousedown.prevent="onDragStart"
      @touchstart.prevent="onDragStart"
    >
      <div class="panel-header">
        <button
          v-if="hasNewAssignments"
          class="btn-save"
          @click="saveAssignments"
          :disabled="saving"
        >
          {{ saving ? 'Ukládám...' : 'Uložit změny' }}
        </button>
      </div>
      <div ref="handle" class="handle"></div>
      <div class="panel-content">
        <div class="config-section">
          <h4>Projekty</h4>
          <div class="config-list">
            <div
              v-for="p in projects"
              :key="p.id"
              class="config-item"
              :class="{ selected: selectedProjectsMap[p.id] }"
              @click="toggleProject(p)"
            >
              {{ p.name }}
            </div>
          </div>
        </div>
        <div class="config-section">
          <h4>Zaměstnanci</h4>
          <div class="config-list">
            <div
              v-for="u in users"
              :key="u.redmine_id"
              class="config-item"
              :class="{ selected: selectedUsersMap[u.redmine_id] }"
              @click="toggleUser(u)"
            >
              {{ u.username }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { toast } from 'vue3-toastify'
import draggable from 'vuedraggable'
import iconInfo from '@/assets/IconInfo.png'
import ParentIcon from '@/assets/IconParent.png'

export default {
  name: 'Dashboard',
  components: { draggable },
  data() {
    return {
      projects: [],
      users: [],
      issues: [],

      selectedProjects: [],
      selectedUsers: [],
      projectIssues: {},
      assignments: {},

      panelTop: 0,
      startY: 0,
      startTop: 0,
      closedTop: 0,
      openTop: 0,
      handleHeight: 0,
      headerHeight: 0,
      viewportHeight: window.innerHeight,
      defaultPeek: 100,

      initialized: false,
      saving: false,
      iconInfo,
      ParentIcon
    }
  },
  computed: {
    isSuperuser() {
      return this.$store.state.is_superuser
    },
    currentRedmineId() {
      return this.$store.state.redmine_id
    },
    selectedProjectsMap() {
      return Object.fromEntries(this.selectedProjects.map(p => [p.id, true]))
    },
    selectedUsersMap() {
      return Object.fromEntries(this.selectedUsers.map(u => [u.redmine_id, true]))
    },
    hasNewAssignments() {
      return Object.values(this.assignments)
        .flat()
        .some(issue => !issue.initialAssigned)
    }
  },
  methods: {
    async fetchAll() {
      toast.info('Synchronizace dat zahájena.', { autoClose: 2000 })
      this.$store.commit('setIsLoading', true)
      try {
        await axios.post('/api/v1/workspace/load/')
        const [pRes, uRes, iRes] = await Promise.all([
          axios.get('/api/v1/projects/'),
          axios.get('/api/v1/users/'),
          axios.get('/api/v1/issues/')
        ])
        this.projects = pRes.data
        this.users = uRes.data
        this.issues = iRes.data

        // při každém načtení vždy prázdné (slide-panel si uživatel sám vyplní)
        this.selectedProjects = []
        this.selectedUsers = []

        // non-superuser vidí od začátku jen svou kartu
        if (!this.isSuperuser) {
          const me = this.users.find(u => u.redmine_id === this.currentRedmineId)
          if (me) this.selectedUsers = [me]
        }

        // projektové sloupce
        this.projectIssues = {}
        this.issues.forEach(issue => {
          issue.initialAssigned = Boolean(issue.assigned)
          ;(this.projectIssues[issue.project_id] ||= []).push(issue)
        })

        // uživatelské karty
        this.assignments = {}
        this.users.forEach(u => {
          this.assignments[u.redmine_id] = []
        })
        this.issues.forEach(issue => {
          if (issue.assigned) {
            const rid = issue.assigned
            const user = this.users.find(u => u.redmine_id === rid)
            if (user) {
              issue.assigned_username = user.username
              this.assignments[rid].push(issue)
            }
          }
        })

        this.initialized = true
        toast.success('Data synchronizována.', { autoClose: 2000 })
      } catch (e) {
        console.error(e)
        toast.error('Chyba synchronizace: ' + e.message, { autoClose: 2000 })
      } finally {
        this.$store.commit('setIsLoading', false)
      }
    },
    formatDate(d) {
      return d ? new Date(d).toLocaleDateString() : '-'
    },
    toggleProject(p) {
      const pid = p.id
      this.selectedProjects = this.selectedProjectsMap[pid]
        ? this.selectedProjects.filter(x => x.id !== pid)
        : [...this.selectedProjects, p]
    },
    toggleUser(u) {
      const rid = u.redmine_id
      this.selectedUsers = this.selectedUsersMap[rid]
        ? this.selectedUsers.filter(x => x.redmine_id !== rid)
        : [...this.selectedUsers, u]
    },
    cloneIssue(issue) {
      return { ...issue }
    },
    openIssue(id) {
      window.open(`https://projects.olc.cz/issues/${id}`, '_blank')
    },
    onAssign(user, evt) {
      const moved = evt.item.__vue__?.element || evt.clone
      moved.assigned_username = user.username
    },
    onUnassign(user, evt) {
      // tu můžeš řešit odřazení úkolu zpět na projekt, pokud potřebuješ
    },
    onProjectDropBack(proj, evt) {
      const dropped = evt.clone
      Object.keys(this.assignments).forEach(rid => {
        this.assignments[rid] = this.assignments[rid].filter(i => i.id !== dropped.id)
      })
      this.projectIssues[proj.id].splice(evt.newIndex, 1)
    },
    isNewAssignment(element) {
      return this.isAssigned(element.id) && !element.initialAssigned
    },
    isAssigned(id) {
      return !!Object.values(this.assignments).flat().find(i => i.id === id)
    },
    async saveAssignments() {
      this.saving = true
      toast.info('Ukládám změny...', { autoClose: 2000 })
      const payload = {
        assignments: this.selectedUsers.map(u => ({
          user_redmine_id: u.redmine_id,
          issue_ids: this.assignments[u.redmine_id].map(i => i.id)
        }))
      }
      try {
        const res = await axios.post('/api/v1/assign-tasks/', payload)
        const { success = [], failed = [] } = res.data
        if (!failed.length)
          toast.success(`Přiřazení proběhlo úspěšně.`, {
            autoClose: 3000
          })
        else
          toast.error(
            `Chyba u ${failed.length} úkolů: ` +
              failed.map(f => `#${f.issue_id}`).join(', '),
            { autoClose: 5000 }
          )
        await this.fetchAll()
      } catch (e) {
        toast.error('Nepodařilo se uložit změny: ' + e.message, { autoClose: 5000 })
      } finally {
        this.saving = false
      }
    },
    updatePanelBounds() {
      this.viewportHeight = window.innerHeight
      this.headerHeight = document.querySelector('.app-header')?.clientHeight || 0
      const handleEl = this.$refs.handle
      this.handleHeight = handleEl ? handleEl.offsetHeight : 0
      this.closedTop = this.viewportHeight - this.handleHeight
      this.openTop = this.headerHeight
      if (this.panelTop === 0) {
        this.panelTop = this.closedTop - this.defaultPeek
      }
    },
    onDragStart(e) {
      this.startY = (e.touches ? e.touches[0] : e).clientY
      this.startTop = this.panelTop
      window.addEventListener('mousemove', this.onDragMove)
      window.addEventListener('mouseup', this.onDragEnd)
    },
    onDragMove(e) {
      const y = (e.touches ? e.touches[0] : e).clientY
      this.panelTop = Math.min(
        Math.max(this.openTop, this.startTop + (y - this.startY)),
        this.closedTop
      )
    },
    onDragEnd() {
      window.removeEventListener('mousemove', this.onDragMove)
      window.removeEventListener('mouseup', this.onDragEnd)
    }
  },
  mounted() {
    document.title = 'Dashboard | Consilio'
    this.$nextTick(() => {
      this.updatePanelBounds()
      window.addEventListener('resize', this.updatePanelBounds)
    })
    this.fetchAll()
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.updatePanelBounds)
  }
}
</script>