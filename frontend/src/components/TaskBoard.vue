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
      <p v-if="loading" class="loading">Loading…</p>
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
          <select
            :value="task.status"
            @change="updateStatus(task.id, $event.target.value)"
          >
            <option value="pending">Pending</option>
            <option value="in_progress">In Progress</option>
            <option value="done">Done</option>
          </select>

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

<style>
/* Global background gradient */
body {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  margin: 0;
  min-height: 100vh;
  padding: 2rem 1rem;
}
</style>

<style scoped>
.board {
  max-width: 800px;
  margin: 0 auto;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(2px);
  border-radius: 32px;
  box-shadow: 0 25px 45px -12px rgba(0, 0, 0, 0.3);
  padding: 2rem;
  transition: all 0.2s ease;
}

h1 {
  font-size: 2rem;
  font-weight: 600;
  margin: 0 0 1.5rem 0;
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  letter-spacing: -0.02em;
}

h2 {
  font-size: 1.25rem;
  font-weight: 500;
  margin-bottom: 0.75rem;
  color: #1e293b;
}

/* Add Task Form */
.add-form {
  background: #f8fafc;
  padding: 1.25rem;
  border-radius: 20px;
  margin-bottom: 2rem;
  border: 1px solid rgba(0, 0, 0, 0.05);
  transition: box-shadow 0.2s;
}

.form-row {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.form-row input {
  flex: 1;
  min-width: 160px;
  padding: 0.75rem 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  font-size: 0.95rem;
  transition: all 0.2s;
  background: white;
}

.form-row input:focus {
  outline: none;
  border-color: #818cf8;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
}

.form-row button {
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  color: white;
  border: none;
  border-radius: 40px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.form-row button:not(:disabled):hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 20px -6px rgba(79, 70, 229, 0.4);
}

.form-row button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.error {
  color: #ef4444;
  font-size: 0.875rem;
  margin-top: 0.75rem;
  background: #fef2f2;
  padding: 0.5rem 1rem;
  border-radius: 12px;
  display: inline-block;
}

/* Filter Buttons */
.filters {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.75rem;
  flex-wrap: wrap;
}

.filter-btn {
  padding: 0.5rem 1.25rem;
  border: none;
  background: #f1f5f9;
  border-radius: 40px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  color: #334155;
}

.filter-btn.active {
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  color: white;
  box-shadow: 0 4px 10px -2px rgba(79, 70, 229, 0.3);
}

.filter-btn:not(.active):hover {
  background: #e2e8f0;
  transform: translateY(-1px);
}

.badge {
  display: inline-block;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 30px;
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.1rem 0.5rem;
  margin-left: 0.4rem;
  vertical-align: middle;
}

.filter-btn.active .badge {
  background: rgba(255, 255, 255, 0.25);
  color: white;
}

/* Task Cards */
.task-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.task-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  border-radius: 20px;
  padding: 1.25rem;
  gap: 1rem;
  transition: all 0.2s ease;
  border: 1px solid #f1f5f9;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.02);
}

.task-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 25px -12px rgba(0, 0, 0, 0.15);
  border-color: #e2e8f0;
}

.task-card.done {
  opacity: 0.75;
  background: #fefefe;
}

.task-info {
  flex: 1;
}

.task-info h3 {
  margin: 0 0 0.25rem 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #0f172a;
}

.task-info p {
  margin: 0 0 0.5rem 0;
  font-size: 0.85rem;
  color: #475569;
  line-height: 1.4;
}

.status-badge {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.2rem 0.75rem;
  border-radius: 30px;
  display: inline-block;
  letter-spacing: 0.3px;
  text-transform: uppercase;
}

.task-card.pending .status-badge {
  background: #fef3c7;
  color: #b45309;
}

.task-card.in_progress .status-badge {
  background: #e0f2fe;
  color: #0369a1;
}

.task-card.done .status-badge {
  background: #dcfce7;
  color: #15803d;
}

.task-actions {
  display: flex;
  gap: 0.75rem;
  flex-shrink: 0;
}

.task-actions select {
  padding: 0.5rem 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 40px;
  background: #f8fafc;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  color: #1e293b;
}

.task-actions select:focus {
  outline: none;
  border-color: #818cf8;
}

.remove-btn {
  padding: 0.5rem 1rem;
  background: #fee2e2;
  color: #dc2626;
  border: none;
  border-radius: 40px;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.remove-btn:hover {
  background: #fecaca;
  transform: scale(0.96);
}

.loading,
.empty {
  text-align: center;
  padding: 2.5rem;
  color: #64748b;
  background: #f8fafc;
  border-radius: 24px;
  font-weight: 500;
}

.empty {
  font-style: italic;
}

/* Responsive */
@media (max-width: 640px) {
  .board {
    padding: 1.25rem;
  }

  .task-card {
    flex-direction: column;
    align-items: flex-start;
  }

  .task-actions {
    width: 100%;
    justify-content: flex-end;
    margin-top: 0.5rem;
  }

  .form-row button {
    width: 100%;
  }
}
</style>