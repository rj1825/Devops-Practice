// API Backend Configuration
// Default to localhost:8000 for local dev if frontend is run from filesystem,
// otherwise use current origin (useful for K8s reverse-proxy/ingress setups)
const API_BASE = window.location.origin.includes('localhost:') && !window.location.origin.includes(':8000') 
    ? 'http://localhost:8000' 
    : (window.location.protocol === 'file:' ? 'http://localhost:8000' : window.location.origin);

console.log('Using API Base URL:', API_BASE);

// DOM Elements
const taskModal = document.getElementById('task-modal');
const taskForm = document.getElementById('task-form');
const modalTitle = document.getElementById('modal-title');
const btnAddTaskModal = document.getElementById('btn-add-task-modal');
const btnCloseModal = document.getElementById('btn-close-modal');
const btnCancelModal = document.getElementById('btn-cancel-modal');
const btnRefresh = document.getElementById('btn-refresh');
const healthIndicator = document.getElementById('health-indicator');

// Task Lists
const lists = {
    'todo': document.getElementById('list-todo'),
    'in-progress': document.getElementById('list-in-progress'),
    'done': document.getElementById('list-done')
};

// Task Counts
const counts = {
    'todo': document.getElementById('count-todo'),
    'in-progress': document.getElementById('count-in-progress'),
    'done': document.getElementById('count-done')
};

// Event Listeners
btnAddTaskModal.addEventListener('click', () => openModal());
btnCloseModal.addEventListener('click', closeModal);
btnCancelModal.addEventListener('click', closeModal);
btnRefresh.addEventListener('click', fetchTasks);
taskForm.addEventListener('submit', handleFormSubmit);

// Initial Load
document.addEventListener('DOMContentLoaded', () => {
    checkHealth();
    fetchTasks();
    // Poll health check every 10 seconds
    setInterval(checkHealth, 10000);
});

// Check API Health Status
async function checkHealth() {
    try {
        const res = await fetch(`${API_BASE}/health`);
        const data = await res.json();
        
        const dot = healthIndicator.querySelector('.status-dot');
        const text = healthIndicator.querySelector('.status-text');
        
        if (res.ok && data.status === 'healthy') {
            dot.className = 'status-dot active';
            text.textContent = data.database === 'connected' ? 'API Online' : 'API (Fallback)';
        } else {
            dot.className = 'status-dot warning';
            text.textContent = 'API Error';
        }
    } catch (err) {
        console.error('Health check failed:', err);
        const dot = healthIndicator.querySelector('.status-dot');
        const text = healthIndicator.querySelector('.status-text');
        dot.className = 'status-dot inactive';
        text.textContent = 'Offline';
    }
}

// Fetch Tasks from API
async function fetchTasks() {
    try {
        const res = await fetch(`${API_BASE}/api/tasks`);
        if (!res.ok) throw new Error('Failed to load tasks');
        const tasks = await res.json();
        renderTasks(tasks);
    } catch (err) {
        console.error('Error fetching tasks:', err);
    }
}

// Render Tasks into Columns
function renderTasks(tasks) {
    // Clear all lists
    Object.values(lists).forEach(list => list.innerHTML = '');
    
    // Track count per column
    const columnCounts = { 'todo': 0, 'in-progress': 0, 'done': 0 };

    tasks.forEach(task => {
        const column = task.status;
        if (lists[column]) {
            columnCounts[column]++;
            const taskCard = createTaskCard(task);
            lists[column].appendChild(taskCard);
        }
    });

    // Update count labels
    Object.keys(counts).forEach(status => {
        counts[status].textContent = columnCounts[status];
    });
}

// Create Task HTML Element
function createTaskCard(task) {
    const card = document.createElement('div');
    card.className = 'task-card';
    card.setAttribute('data-id', task.id);
    
    // Status navigation
    let moveButtonsHtml = '';
    if (task.status === 'todo') {
        moveButtonsHtml = `<button class="btn-icon" onclick="moveTask('${task.id}', 'in-progress')" title="Start Task"><i class="fa-solid fa-arrow-right"></i></button>`;
    } else if (task.status === 'in-progress') {
        moveButtonsHtml = `
            <button class="btn-icon" onclick="moveTask('${task.id}', 'todo')" title="Move to Todo"><i class="fa-solid fa-arrow-left"></i></button>
            <button class="btn-icon" onclick="moveTask('${task.id}', 'done')" title="Complete Task"><i class="fa-solid fa-check"></i></button>
        `;
    } else if (task.status === 'done') {
        moveButtonsHtml = `<button class="btn-icon" onclick="moveTask('${task.id}', 'in-progress')" title="Reopen Task"><i class="fa-solid fa-arrow-left"></i></button>`;
    }

    card.innerHTML = `
        <div class="task-card-header">
            <h4>${escapeHTML(task.title)}</h4>
            <span class="priority-badge ${task.priority}">${task.priority}</span>
        </div>
        <p>${escapeHTML(task.description || 'No description provided.')}</p>
        <div class="task-card-footer">
            <div class="action-buttons">
                <button class="btn-icon" onclick="editTask('${task.id}', '${escapeQuote(task.title)}', '${escapeQuote(task.description)}', '${task.status}', '${task.priority}')" title="Edit"><i class="fa-solid fa-pen"></i></button>
                <button class="btn-icon btn-delete" onclick="deleteTask('${task.id}')" title="Delete"><i class="fa-solid fa-trash-can"></i></button>
            </div>
            <div class="move-buttons">
                ${moveButtonsHtml}
            </div>
        </div>
    `;
    
    return card;
}

// Open Modal for Create or Edit
function openModal(id = '', title = '', desc = '', status = 'todo', priority = 'medium') {
    document.getElementById('task-id').value = id;
    document.getElementById('task-title').value = title;
    document.getElementById('task-desc').value = desc;
    document.getElementById('task-status').value = status;
    document.getElementById('task-priority').value = priority;
    
    modalTitle.textContent = id ? 'Edit Task' : 'Create New Task';
    taskModal.classList.add('active');
}

// Close Modal
function closeModal() {
    taskModal.classList.remove('active');
    taskForm.reset();
}

// Handle Form Submission
async function handleFormSubmit(e) {
    e.preventDefault();
    
    const id = document.getElementById('task-id').value;
    const taskData = {
        title: document.getElementById('task-title').value,
        description: document.getElementById('task-desc').value,
        status: document.getElementById('task-status').value,
        priority: document.getElementById('task-priority').value
    };

    try {
        let res;
        if (id) {
            // Update existing
            res = await fetch(`${API_BASE}/api/tasks/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(taskData)
            });
        } else {
            // Create new
            res = await fetch(`${API_BASE}/api/tasks`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(taskData)
            });
        }

        if (res.ok) {
            closeModal();
            fetchTasks();
        } else {
            const err = await res.json();
            alert(`Error: ${err.detail || 'Failed to save task'}`);
        }
    } catch (err) {
        console.error('Error submitting form:', err);
        alert('Server connection error. Task not saved.');
    }
}

// Delete Task
async function deleteTask(id) {
    if (!confirm('Are you sure you want to delete this task?')) return;
    
    try {
        const res = await fetch(`${API_BASE}/api/tasks/${id}`, {
            method: 'DELETE'
        });
        if (res.ok) {
            fetchTasks();
        } else {
            alert('Failed to delete task.');
        }
    } catch (err) {
        console.error('Error deleting task:', err);
    }
}

// Move Task Status
async function moveTask(id, newStatus) {
    try {
        // Fetch current details first, then update status
        const fetchRes = await fetch(`${API_BASE}/api/tasks`);
        const tasks = await fetchRes.json();
        const task = tasks.find(t => t.id === id);
        
        if (!task) return;
        
        task.status = newStatus;
        
        const res = await fetch(`${API_BASE}/api/tasks/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(task)
        });
        
        if (res.ok) {
            fetchTasks();
        }
    } catch (err) {
        console.error('Error moving task:', err);
    }
}

// Edit Task Event Handler (bound globally)
window.editTask = (id, title, desc, status, priority) => {
    openModal(id, title, desc, status, priority);
};

// Global delete/move mappings for HTML onclick handlers
window.deleteTask = deleteTask;
window.moveTask = moveTask;

// Helper Functions
function escapeHTML(str) {
    if (!str) return '';
    return str.replace(/[&<>'"]/g, 
        tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
    );
}

function escapeQuote(str) {
    if (!str) return '';
    return str.replace(/'/g, "\\'").replace(/"/g, '&quot;');
}
