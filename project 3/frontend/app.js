// API Backend Configuration
// Defaults to localhost:8000 for local file runs, or same-origin for containers
const API_BASE = window.location.origin.includes('localhost:') && !window.location.origin.includes(':8000') 
    ? 'http://localhost:8000' 
    : (window.location.protocol === 'file:' ? 'http://localhost:8000' : window.location.origin);

console.log('SQLAgent Frontend API URL:', API_BASE);

// DOM Elements
const chatHistory = document.getElementById('chat-history');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const sqlCode = document.getElementById('sql-code');
const resultsTable = document.getElementById('results-table');
const rowCountBadge = document.getElementById('row-count-badge');
const healthIndicator = document.getElementById('health-indicator');

// Event Listeners
chatForm.addEventListener('submit', handleFormSubmit);

// Initializations
document.addEventListener('DOMContentLoaded', () => {
    checkHealth();
    // Poll health check every 10 seconds
    setInterval(checkHealth, 10000);
});

// Check Backend Health Status
async function checkHealth() {
    try {
        const res = await fetch(`${API_BASE}/health`);
        const data = await res.json();
        
        const dot = healthIndicator.querySelector('.status-dot');
        const text = healthIndicator.querySelector('.status-text');
        
        if (res.ok && data.status === 'healthy') {
            dot.className = 'status-dot active';
            text.textContent = data.agent_mode === 'LLM' ? 'AI Agent Online' : 'AI Offline Fallback';
        } else {
            dot.className = 'status-dot warning';
            text.textContent = 'API Error';
        }
    } catch (err) {
        console.error('Health check failed:', err);
        const dot = healthIndicator.querySelector('.status-dot');
        const text = healthIndicator.querySelector('.status-text');
        dot.className = 'status-dot inactive';
        text.textContent = 'Backend Offline';
    }
}

// Global hook to trigger suggested prompts
function usePrompt(promptText) {
    userInput.value = promptText;
    chatForm.dispatchEvent(new Event('submit'));
}
window.usePrompt = usePrompt;

// Form Submit Handler
async function handleFormSubmit(e) {
    e.preventDefault();
    
    const question = userInput.value.trim();
    if (!question) return;

    // Clear input
    userInput.value = '';

    // 1. Render User Bubble
    appendBubble(question, 'user');
    
    // 2. Render Loading Indicator
    const loadingId = appendLoadingBubble();

    try {
        const res = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });
        
        // Remove loading bubble
        removeBubble(loadingId);

        if (res.ok) {
            const data = await res.json();
            // 3. Render Assistant Bubble
            appendBubble(data.answer, 'assistant');
            
            // 4. Update SQL Inspector and Table
            updateSQLInspector(data.sql_query);
            updateResultsTable(data.columns, data.results);
        } else {
            const err = await res.json();
            appendBubble(`Error: ${err.detail || 'Failed to process question.'}`, 'assistant');
        }
    } catch (err) {
        console.error('API execution error:', err);
        removeBubble(loadingId);
        appendBubble('Connection error. Please check if backend server is running.', 'assistant');
    }
}

// Append Chat Bubble
function appendBubble(text, sender) {
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${sender}`;
    bubble.textContent = text;
    chatHistory.appendChild(bubble);
    autoScroll();
}

// Append Loading Bubble
function appendLoadingBubble() {
    const id = 'loading-' + Date.now();
    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble loading';
    bubble.id = id;
    bubble.innerHTML = `
        <div class="loading-dot"></div>
        <div class="loading-dot"></div>
        <div class="loading-dot"></div>
    `;
    chatHistory.appendChild(bubble);
    autoScroll();
    return id;
}

// Remove Bubble by ID
function removeBubble(id) {
    const bubble = document.getElementById(id);
    if (bubble) bubble.remove();
}

// Scroll to bottom of chat history
function autoScroll() {
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

// Update SQL Inspector Code Box
function updateSQLInspector(sql) {
    sqlCode.textContent = sql;
}

// Render DB query results table dynamically
function updateResultsTable(columns, rows) {
    // 1. Update Row Count
    rowCountBadge.textContent = `${rows.length} row${rows.length === 1 ? '' : 's'}`;

    // 2. Clear Table Header & Body
    resultsTable.innerHTML = '';

    if (rows.length === 0) {
        resultsTable.innerHTML = `
            <thead>
                <tr><th>Query Column Result</th></tr>
            </thead>
            <tbody>
                <tr><td class="empty-cell">Empty dataset. No rows matched in database.</td></tr>
            </tbody>
        `;
        return;
    }

    // 3. Render Headers
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    columns.forEach(col => {
        const th = document.createElement('th');
        th.textContent = col;
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    resultsTable.appendChild(thead);

    // 4. Render Rows
    const tbody = document.createElement('tbody');
    rows.forEach(row => {
        const tr = document.createElement('tr');
        columns.forEach(col => {
            const td = document.createElement('td');
            td.textContent = row[col] !== null ? row[col] : 'NULL';
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
    resultsTable.appendChild(tbody);
}

// Copy SQL to Clipboard
function copySQL() {
    const text = sqlCode.textContent;
    if (text.startsWith('--')) return; // ignore initial comment
    navigator.clipboard.writeText(text).then(() => {
        const btn = document.getElementById('btn-copy-sql');
        btn.innerHTML = '<i class="fa-solid fa-check"></i> Copied!';
        setTimeout(() => {
            btn.innerHTML = '<i class="fa-regular fa-copy"></i> Copy';
        }, 2000);
    });
}
window.copySQL = copySQL;
