const apiStatus = document.getElementById('apiStatus');
const dbStatus = document.getElementById('dbStatus');
const completedCount = document.getElementById('completedCount');
const totalCount = document.getElementById('totalCount');
const taskList = document.getElementById('taskList');
const taskForm = document.getElementById('taskForm');
const taskInput = document.getElementById('taskInput');
const refreshBtn = document.getElementById('refreshBtn');

async function requestJson(url, options = {}) {
    const response = await fetch(url, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(data.error || data.msg || 'Request failed');
    }

    return data;
}

function formatDate(value) {
    return new Intl.DateTimeFormat('en', {
        year: 'numeric',
        month: 'short',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
    }).format(new Date(value));
}

function renderTasks(tasks) {
    totalCount.textContent = tasks.length;
    completedCount.textContent = tasks.filter(task => task.is_done).length;

    if (!tasks.length) {
        taskList.innerHTML = '<div class="empty-state">No tasks yet. Add your first Docker task above.</div>';
        return;
    }

    taskList.innerHTML = tasks.map(task => `
        <article class="task-item ${task.is_done ? 'done' : ''}">
            <button class="task-check" data-action="toggle" data-id="${task.id}" aria-label="Toggle task">
                ${task.is_done ? '✓' : ''}
            </button>
            <div>
                <p class="task-title">${escapeHtml(task.title)}</p>
                <p class="task-date">Created ${formatDate(task.created_at)}</p>
            </div>
            <button class="delete-btn" data-action="delete" data-id="${task.id}">Delete</button>
        </article>
    `).join('');
}

function escapeHtml(value) {
    return value
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
}

async function loadHealth() {
    try {
        await requestJson('/health');
        apiStatus.textContent = 'Online';
    } catch (error) {
        apiStatus.textContent = 'Offline';
    }
}

async function loadDbStatus() {
    try {
        const data = await requestJson('/db-check');
        dbStatus.textContent = data.connection === 'successful' ? 'Connected' : 'Failed';
    } catch (error) {
        dbStatus.textContent = 'Failed';
    }
}

async function loadTasks() {
    try {
        const tasks = await requestJson('/tasks');
        renderTasks(tasks);
    } catch (error) {
        taskList.innerHTML = `<div class="error-state">Cannot load tasks: ${escapeHtml(error.message)}</div>`;
    }
}

async function addTask(title) {
    await requestJson('/tasks', {
        method: 'POST',
        body: JSON.stringify({ title }),
    });
    taskInput.value = '';
    await loadTasks();
}

async function toggleTask(id) {
    await requestJson(`/tasks/${id}/toggle`, { method: 'PATCH' });
    await loadTasks();
}

async function deleteTask(id) {
    await requestJson(`/tasks/${id}`, { method: 'DELETE' });
    await loadTasks();
}

taskForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const title = taskInput.value.trim();
    if (!title) return;

    taskForm.querySelector('button').disabled = true;
    try {
        await addTask(title);
    } finally {
        taskForm.querySelector('button').disabled = false;
        taskInput.focus();
    }
});

taskList.addEventListener('click', async (event) => {
    const button = event.target.closest('button[data-action]');
    if (!button) return;

    const { action, id } = button.dataset;
    button.disabled = true;

    try {
        if (action === 'toggle') await toggleTask(id);
        if (action === 'delete') await deleteTask(id);
    } finally {
        button.disabled = false;
    }
});

refreshBtn.addEventListener('click', async () => {
    await Promise.all([loadHealth(), loadDbStatus(), loadTasks()]);
});

Promise.all([loadHealth(), loadDbStatus(), loadTasks()]);
