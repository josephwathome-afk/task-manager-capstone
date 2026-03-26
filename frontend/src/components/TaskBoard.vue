<template>
  <div class="board">
    <h1>Task Manager</h1>

    <!--  Add Task Form  -->
    <section class="add-form">
      <h2>Add a Task</h2>
      <div class="form-row">
        <input
          v-model="newTitle"
          placeholder="Title *"
          @keyup.enter="createTask"
        />
        <input
          v-model="newDescription"
          placeholder="Description (optional)"
          @keyup.enter="createTask"
        />
        <button :disabled="!newTitle.trim()" @click="createTask">
          + Add
        </button>
      </div>
      <p v-if="error" class="error">{{ error }}</p>
    </section>

    <!--  Filter Buttons  -->
    <section class="filters">
      <button
        v-for="f in filters"
        :key="f.value"
        :class="['filter-btn', { active: activeFilter === f.value }]"
        @click="activeFilter = f.value"
      >
        {{ f.label }}
        <span class="badge">{{ countFor(f.value) }}</span>
      </button>
    </section>

    <!--  Task List  -->
    <section class="task-list">
      <p v-if="loading">Loading…</p>
      <p v-else-if="filteredTasks.length === 0" class="empty">
        No tasks here yet.
      </p>

      <div
        v-for="task in filteredTasks"
        :key="task.id"
        class="task-card"
        :class="task.status"
      >
        <div class="task-info">
          <h3>{{ task.title }}</h3>
          <p v-if="task.description">{{ task.description }}</p>
          <span class="status-badge">{{ labelFor(task.status) }}</span>
        </div>

        <div class="task-actions">
          <!-- Status dropdown -->
          <select
            :value="task.status"
            @change="updateStatus(task.id, $event.target.value)"
          >
            <option value="pending">Pending</option>
            <option value="in_progress">In Progress</option>
            <option value="done">Done</option>
          </select>

          <!-- Delete -->
          <button class="remove-btn" @click="deleteTask(task.id)">
            Remove
          </button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

//  Config 
const API = 'http://localhost:5000'

//  State 
const tasks        = ref([])
const newTitle     = ref('')
const newDescription = ref('')
const activeFilter = ref('all')
const loading      = ref(false)
const error        = ref('')

//  Static data 
const filters = [
  { label: 'All',         value: 'all'         },
  { label: 'Todo',        value: 'pending'      },
  { label: 'In Progress', value: 'in_progress'  },
  { label: 'Done',        value: 'done'         },
]

const STATUS_LABELS = {
  pending:     'Pending',
  in_progress: 'In Progress',
  done:        'Done',
}

//  Computed 
const filteredTasks = computed(() =>
  activeFilter.value === 'all'
    ? tasks.value
    : tasks.value.filter(t => t.status === activeFilter.value)
)

function countFor(filterValue) {
  return filterValue === 'all'
    ? tasks.value.length
    : tasks.value.filter(t => t.status === filterValue).length
}

function labelFor(status) {
  return STATUS_LABELS[status] ?? status
}

// API helpers
async function fetchTasks() {
  loading.value = true
  try {
    const res = await fetch(`${API}/tasks/`)
    tasks.value = await res.json()
  } finally {
    loading.value = false
  }
}

async function createTask() {
  error.value = ''
  const title = newTitle.value.trim()
  if (!title) return

  const res = await fetch(`${API}/tasks/`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ title, description: newDescription.value }),
  })

  if (!res.ok) {
    const body = await res.json()
    error.value = body.error ?? 'Could not create task.'
    return
  }

  newTitle.value       = ''
  newDescription.value = ''
  await fetchTasks()
}

async function updateStatus(id, status) {
  await fetch(`${API}/tasks/${id}`, {
    method:  'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ status }),
  })
  await fetchTasks()
}

async function deleteTask(id) {
  await fetch(`${API}/tasks/${id}`, { method: 'DELETE' })
  await fetchTasks()
}

// ── Lifecycle ────────────────────────────────────────────────
onMounted(fetchTasks)
</script>

<style scoped>
.board        { max-width: 720px; margin: 2rem auto; font-family: sans-serif; padding: 0 1rem; }
h1            { font-size: 1.8rem; margin-bottom: 1.5rem; }
h2            { font-size: 1.1rem; margin-bottom: .75rem; }

/* Form */
.add-form     { background: #f9f9f9; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem; }
.form-row     { display: flex; gap: .5rem; flex-wrap: wrap; }
.form-row input { flex: 1; min-width: 140px; padding: .5rem; border: 1px solid #ccc; border-radius: 6px; }
.form-row button { padding: .5rem 1rem; background: #2563eb; color: #fff; border: none; border-radius: 6px; cursor: pointer; }
.form-row button:disabled { opacity: .5; cursor: not-allowed; }
.error        { color: #dc2626; font-size: .85rem; margin-top: .5rem; }

/* Filters */
.filters      { display: flex; gap: .5rem; margin-bottom: 1.25rem; flex-wrap: wrap; }
.filter-btn   { padding: .4rem .9rem; border: 1px solid #d1d5db; background: #fff; border-radius: 20px; cursor: pointer; font-size: .85rem; }
.filter-btn.active { background: #2563eb; color: #fff; border-color: #2563eb; }
.badge        { display: inline-block; background: rgba(0,0,0,.12); border-radius: 10px; font-size: .75rem; padding: 0 .4rem; margin-left: .3rem; }

/* Cards */
.task-card    { display: flex; justify-content: space-between; align-items: center;
                background: #fff; border: 1px solid #e5e7eb; border-radius: 8px;
                padding: 1rem; margin-bottom: .75rem; gap: 1rem; }
.task-card.done { opacity: .65; }
.task-info h3 { margin: 0 0 .25rem; font-size: 1rem; }
.task-info p  { margin: 0 0 .4rem; font-size: .85rem; color: #6b7280; }
.status-badge { font-size: .75rem; padding: .15rem .5rem; border-radius: 10px; background: #e5e7eb; }
.task-card.pending     .status-badge { background: #fef3c7; color: #92400e; }
.task-card.in_progress .status-badge { background: #dbeafe; color: #1e40af; }
.task-card.done        .status-badge { background: #dcfce7; color: #166534; }

.task-actions { display: flex; gap: .5rem; flex-shrink: 0; }
.task-actions select { padding: .35rem; border: 1px solid #d1d5db; border-radius: 6px; font-size: .85rem; cursor: pointer; }
.remove-btn   { padding: .35rem .75rem; background: #fee2e2; color: #dc2626; border: none; border-radius: 6px; cursor: pointer; font-size: .85rem; }
.remove-btn:hover { background: #fecaca; }

.empty        { color: #9ca3af; text-align: center; padding: 2rem 0; }
</style>