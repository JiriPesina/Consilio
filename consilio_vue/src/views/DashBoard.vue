<template>
  <div v-if="initialized" class="dashboard-container">
    <div class="cards-container">
      <!-- Project Cards -->
      <div
        v-for="proj in selectedProjects"
        :key="`proj-${proj.id}`"
        class="card issue-card project-card"
      >
        <h3>{{ proj.name }} <img v-if="proj.parent_id" :src="ParentIcon" alt="Má rodičovský projekt" class="icon-parent"/></h3>
        <draggable
          :list="projectIssues[proj.id]"
          :group="{ name: 'issues', pull: 'clone', put: true }"
          :clone="cloneIssue"
          :sort="false"
          item-key="id"
          @add="onProjectDropBack(proj, $event)"
        >
          <template #item="{ element }">
            <div
              class="issue-item"
              :class="{ assigned: isNewAssignment(element) }"
            >
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
        <draggable
          :list="assignments[user.redmine_id]"
          :group="'issues'"
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
                <div class="title">{{ element.name }} <img v-if="element.project_parent_id" :src="ParentIcon" alt="Project má rodiče" class="icon-parent"/></div>
                <div class="detail">
                  <span class="deadline">{{ formatDate(element.deadline) }}</span>
                </div>
              </div>
              <!-- Info ikonka -->
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

    <!-- Slide-up config panel -->
    <div
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
// import ikony z assets
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
      projectIssues: {},        // { projectId: Issue[] }
      assignments: {},          // { userRedmineId: Issue[] }

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
      iconInfo ,
      ParentIcon 
    }
  },
  computed: {
    selectedProjectsMap() {
      return Object.fromEntries(this.selectedProjects.map(p => [p.id, true]))
    },
    selectedUsersMap() {
      return Object.fromEntries(this.selectedUsers.map(u => [u.redmine_id, true]))
    },
    // kontrola, jestli je někde nově přiřazené issue
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
        this.users    = uRes.data
        this.issues   = iRes.data

        // naplnění projectIssues + původní stav přiřazení
        this.projectIssues = {}
        this.issues.forEach(issue => {
          issue.initialAssigned = Boolean(issue.assigned)
          ;(this.projectIssues[issue.project_id] ||= []).push(issue)
        })

        // inicializace assignments
        this.assignments = {}
        this.users.forEach(u => {
          this.assignments[u.redmine_id] = []
        })
        // naplnění původně přiřazených
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
      if (this.selectedProjectsMap[pid]) {
        this.selectedProjects = this.selectedProjects.filter(x => x.id !== pid)
      } else {
        this.selectedProjects.push(p)
      }
    },
    toggleUser(u) {
      const rid = u.redmine_id
      if (this.selectedUsersMap[rid]) {
        this.selectedUsers = this.selectedUsers.filter(x => x.redmine_id !== rid)
      } else {
        this.selectedUsers.push(u)
      }
    },
    cloneIssue(issue) {
      return { ...issue }
    },
    // klik na info ikonku
    openIssue(id) {
      window.open(`https://projects.olc.cz/issues/${id}`, '_blank')
    },
    onAssign(user, evt) {
      const moved = evt.item.__vue__?.element || evt.clone
      moved.assigned_username = user.username
    },
    onUnassign(user, evt) {
      // vuedraggable odstraní model automaticky
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
      return !!Object.values(this.assignments)
        .flat()
        .find(i => i.id === id)
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
        if (!failed.length) toast.success(`Přiřazení proběhlo úspěšně (${success.length} úkolů).`, { autoClose: 3000 })
        else toast.error(`Chyba u ${failed.length} úkolů: ` + failed.map(f => `#${f.issue_id}`).join(', '), { autoClose: 5000 })
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

<style scoped>
.icon-parent {
  width: 20px;
  height: 20px;
  margin-left: 6px;
  vertical-align: middle;
}
.dashboard-container {
  display: flex;
  flex-direction: column;
  padding: 1rem;
}
.cards-container {
  display: flex;
  flex-wrap: nowrap;
  gap: 1rem;
  overflow-x: auto;
}
.card.issue-card {
  background: #3e3f45;
  border-radius: 20px;
  padding: 0.8rem;
  min-width: 250px;
  user-select: none;
}
.card.issue-card h3 {
  color: #fff;
  margin: 0 0 0.5rem 0;
  border-bottom: 1px solid rgba(255,255,255,0.2);
  padding-bottom: 0.3rem;
}
.issue-item {
  position: relative;
  background: #eaeaea;
  border-radius: 2rem;
  padding: 0.4rem;
  margin-bottom: 0.8rem;
  cursor: grab;
  overflow: hidden;
  user-select: none;
  transition: opacity 0.2s;
}
.issue-item.assigned {
  opacity: 0.5;
}
.issue-item.dragging-visible {
  opacity: 1 !important;
}
.issue-pill {
  position: absolute;
  top: 0;
  left: 0;
  height: 5px;
  background: #4caf50;
}
.unassigned-dot {
  position: absolute;
  bottom: 8px;
  right: 8px;
  width: 12px;
  height: 12px;
  background: #f44336;
  border-radius: 50%;
}
.assigned-user {
  margin-left: 5.5rem;
  font-size: 0.85rem;
  color: #8d8d8d;
  font-weight: 500;
}
/* Info ikonka */
.info-icon {
  position: absolute;
  bottom: 8px;
  right: 8px;
  width: 18px;
  height: 18px;
  cursor: pointer;
}

/* Slide Panel Styling */
.slide-panel {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #3e3f45;
  border-top-left-radius: 12px;
  border-top-right-radius: 12px;
  z-index: 1000;
}
.handle {
  width: 50px;
  height: 5px;
  background: #bbb;
  border-radius: 3px;
  margin: 10px auto;
  cursor: grab;
}
.panel-content {
  flex: 1 1 auto;
  overflow-y: auto;
  display: flex;
  gap: 2rem;
  padding: 0 20rem;
}
.config-section {
  flex: 1;
}
.config-list {
  max-height: 200px;
  overflow-y: auto;
}
.config-item {
  padding: 0.6rem;
  background: #fff;
  color: #000;
  border-radius: 6px;
  cursor: pointer;
  margin-bottom: 0.5rem;
}
.config-item.selected {
  background: #ffa500;
  color: #fff;
}

.title {
  font-weight: 600;
  margin-left: 0.3rem;
}
.detail .deadline {
  margin-left: 0.3rem;
  color: #8d8d8d;
  font-weight: 500;
  font-size: 0.85rem;
}

.panel-header {
  display: flex;
  justify-content: flex-end;
  padding: 0.5rem 1rem;
  background: #2e3037;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}
.btn-save {
  background: #4caf50;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
}
.btn-save:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>


