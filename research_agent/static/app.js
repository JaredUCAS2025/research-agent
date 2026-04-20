const state = {
    sessionId: '',
    currentTaskId: '',
    currentRunId: '',
    currentArtifacts: {},
    artifactOrder: [
        'diagram_index.md',
        'paper_digest.json',
        'summary.md',
        'claims.md',
        'paper_structure.md',
        'method_card.md',
        'compare_matrix.json',
        'comparison_report.md',
        'survey.md',
        'repo_profile.json',
        'ast_analysis.json',
        'env_resolution.json'
    ],
    pollingTimer: null,
};

const chatMessagesEl = document.getElementById('chat-messages');
const artifactContentEl = document.getElementById('artifact-content');
const taskStatusBadgeEl = document.getElementById('task-status-badge');
const taskProgressBarEl = document.getElementById('task-progress-bar');
const taskStageEl = document.getElementById('task-stage');
const taskMessageEl = document.getElementById('task-message');
const taskEtaEl = document.getElementById('task-eta');
const taskTraceEl = document.getElementById('task-trace');
const sessionIdEl = document.getElementById('session-id');
const historyListEl = document.getElementById('history-list');
const errorEl = document.getElementById('error-msg');

function showError(message) {
    errorEl.textContent = message;
    errorEl.classList.remove('hidden');
    setTimeout(() => errorEl.classList.add('hidden'), 5000);
}

function escapeHtml(text) {
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function renderMarkdown(text) {
    if (!text) return '<p>暂无内容</p>';
    try {
        return marked.parse(text);
    } catch {
        // Fallback if marked.js not loaded
        const safe = escapeHtml(text);
        return safe
            .replace(/^### (.*?)$/gm, '<h3>$1</h3>')
            .replace(/^## (.*?)$/gm, '<h2>$1</h2>')
            .replace(/^# (.*?)$/gm, '<h1>$1</h1>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }
}

function renderMaybeJson(text) {
    try {
        const parsed = JSON.parse(text);
        return `<pre>${escapeHtml(JSON.stringify(parsed, null, 2))}</pre>`;
    } catch {
        return renderMarkdown(text);
    }
}

function renderMessages(messages) {
    chatMessagesEl.innerHTML = '';
    if (!messages.length) {
        chatMessagesEl.innerHTML = '<div class="empty-state">先上传论文、生成综述或分析仓库，再开始提问。</div>';
        return;
    }

    for (const message of messages) {
        const item = document.createElement('div');
        item.className = `chat-message ${message.role}`;
        const scope = Array.isArray(message.scope) && message.scope.length
            ? `<div class="chat-scope">scope: ${escapeHtml(message.scope.join(', '))}</div>`
            : '';
        item.innerHTML = `
            <div class="chat-role">${message.role === 'user' ? '你' : message.role === 'assistant' ? 'Agent' : 'System'}</div>
            ${scope}
            <div class="chat-bubble">${renderMarkdown(message.content)}</div>
        `;
        chatMessagesEl.appendChild(item);
    }
    chatMessagesEl.scrollTop = chatMessagesEl.scrollHeight;
}

function renderArtifacts(artifacts) {
    state.currentArtifacts = artifacts || {};
    const activeTab = document.querySelector('.artifact-tab.active');
    const artifactName = activeTab?.dataset.artifact || state.artifactOrder[0];
    renderArtifactContent(artifactName);
}

function renderArtifactContent(name) {
    const content = state.currentArtifacts[name] || '';

    // 特殊处理：阅读卡片
    if (name === 'paper_digest.json' && content) {
        try {
            const data = JSON.parse(content);
            let html = '<div class="paper-digest">';

            if (data.metadata) {
                html += '<div class="section">';
                html += '<h2>📄 论文信息</h2>';
                html += `<p><strong>标题：</strong>${escapeHtml(data.metadata.title || '')}</p>`;
                if (data.metadata.authors) {
                    const authors = Array.isArray(data.metadata.authors)
                        ? data.metadata.authors.join(', ')
                        : data.metadata.authors;
                    html += `<p><strong>作者：</strong>${escapeHtml(authors)}</p>`;
                }
                if (data.metadata.venue) {
                    html += `<p><strong>发表于：</strong>${escapeHtml(data.metadata.venue)}</p>`;
                }
                if (data.metadata.year) {
                    html += `<p><strong>年份：</strong>${escapeHtml(data.metadata.year)}</p>`;
                }
                if (data.metadata.keywords) {
                    const keywords = Array.isArray(data.metadata.keywords)
                        ? data.metadata.keywords.join(', ')
                        : data.metadata.keywords;
                    html += `<p><strong>关键词：</strong>${escapeHtml(keywords)}</p>`;
                }
                html += '</div>';
            }

            if (data.problem) {
                html += '<div class="section">';
                html += '<h2>❓ 研究问题</h2>';
                html += `<p>${escapeHtml(data.problem)}</p>`;
                html += '</div>';
            }

            if (data.method) {
                html += '<div class="section">';
                html += '<h2>🔬 方法</h2>';
                html += `<p>${escapeHtml(data.method)}</p>`;
                html += '</div>';
            }

            if (data.results) {
                html += '<div class="section">';
                html += '<h2>📊 结果</h2>';
                html += `<p>${escapeHtml(data.results)}</p>`;
                html += '</div>';
            }

            if (data.contributions && Array.isArray(data.contributions) && data.contributions.length > 0) {
                html += '<div class="section">';
                html += '<h2>✨ 贡献</h2>';
                html += '<ul>';
                data.contributions.forEach(c => {
                    html += `<li>${escapeHtml(c)}</li>`;
                });
                html += '</ul>';
                html += '</div>';
            }

            html += '</div>';
            artifactContentEl.innerHTML = html;
            return;
        } catch (e) {
            console.error('Failed to parse paper_digest.json:', e);
            console.log('Content:', content);
            // 解析失败，继续使用默认 JSON 显示
        }
    }

    // 特殊处理：对比矩阵
    if (name === 'compare_matrix.json' && content) {
        try {
            const data = JSON.parse(content);
            let html = '<div class="compare-matrix">';

            if (data.common_task) {
                html += '<h2>共同任务</h2>';
                html += `<p>${escapeHtml(data.common_task)}</p>`;
            }

            if (data.dimensions && Array.isArray(data.dimensions)) {
                html += '<h2>对比维度</h2>';
                data.dimensions.forEach(dim => {
                    html += `<h3>${escapeHtml(dim.name || '')}</h3>`;
                    html += `<p>${escapeHtml(dim.summary || '')}</p>`;
                });
            }

            if (data.papers && Array.isArray(data.papers)) {
                html += '<h2>论文列表</h2>';
                html += '<ul>';
                data.papers.forEach(paper => {
                    html += `<li><strong>${escapeHtml(paper.title || '')}</strong>`;
                    if (paper.year) html += ` (${escapeHtml(paper.year)})`;
                    html += '</li>';
                });
                html += '</ul>';
            }

            html += '</div>';
            artifactContentEl.innerHTML = html;
            return;
        } catch (e) {
            // 解析失败，继续使用默认 JSON 显示
        }
    }

    // 特殊处理：图表索引
    if (name === 'diagram_index.md' && content) {
        // 解析 Markdown 中的图表链接并渲染图片
        let html = '<div class="diagram-gallery">';
        html += '<h2>生成的图表</h2>';

        // 提取所有图片链接
        const imageRegex = /!\[([^\]]*)\]\(([^)]+)\)/g;
        let match;
        let hasImages = false;

        while ((match = imageRegex.exec(content)) !== null) {
            hasImages = true;
            const altText = match[1];
            const imagePath = match[2];
            // 构建完整的图片 URL
            const imageUrl = `/api/diagrams/${state.currentRunId}/${imagePath.split('/').pop()}`;
            html += `<div class="diagram-item">`;
            html += `<h3>${escapeHtml(altText)}</h3>`;
            html += `<img src="${imageUrl}" alt="${escapeHtml(altText)}" style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 4px; padding: 8px; background: white;">`;
            html += `</div>`;
        }

        if (!hasImages) {
            html += '<p>暂无生成的图表</p>';
        }

        html += '</div>';
        artifactContentEl.innerHTML = html;
        return;
    }

    // 根据文件扩展名决定渲染方式
    if (name.endsWith('.json')) {
        // JSON 文件：格式化显示
        try {
            const parsed = JSON.parse(content);
            artifactContentEl.innerHTML = `<pre>${escapeHtml(JSON.stringify(parsed, null, 2))}</pre>`;
        } catch {
            artifactContentEl.innerHTML = `<pre>${escapeHtml(content || '暂无该产物')}</pre>`;
        }
    } else if (name.endsWith('.md')) {
        // Markdown 文件：渲染为 HTML
        artifactContentEl.innerHTML = renderMarkdown(content || '暂无该产物');
    } else {
        // 其他文件：纯文本显示
        artifactContentEl.innerHTML = `<pre>${escapeHtml(content || '暂无该产物')}</pre>`;
    }
}

function setTaskState(task) {
    taskStatusBadgeEl.textContent = task.status;
    taskStatusBadgeEl.dataset.status = task.status;
    taskProgressBarEl.style.width = `${Math.max(2, Math.round((task.progress || 0) * 100))}%`;
    taskStageEl.textContent = task.stage || 'unknown';
    taskMessageEl.textContent = task.message || '任务执行中';
    taskEtaEl.textContent = typeof task.eta_seconds === 'number' ? `预计剩余：${task.eta_seconds}s` : '预计剩余：--';

    // Per-stage ETA breakdown
    const breakdownEl = document.getElementById('task-eta-breakdown');
    if (breakdownEl && Array.isArray(task.eta_breakdown) && task.eta_breakdown.length) {
        breakdownEl.innerHTML = task.eta_breakdown.map(item => {
            const isCurrent = task.stage === item.stage;
            const cls = isCurrent ? 'eta-stage current' : 'eta-stage';
            return `<span class="${cls}">${escapeHtml(item.label)} ~${item.seconds}s</span>`;
        }).join(' → ');
    } else if (breakdownEl) {
        breakdownEl.innerHTML = '';
    }

    // Show/hide cancel button
    const cancelBtn = document.getElementById('cancel-task-btn');
    if (cancelBtn) {
        cancelBtn.style.display = (task.status === 'running' || task.status === 'queued') ? 'inline-block' : 'none';
    }

    // Show/hide confirm panel
    const confirmPanel = document.getElementById('confirm-panel');
    const confirmMsg = document.getElementById('confirm-message');
    if (confirmPanel) {
        if (task.status === 'awaiting_confirmation') {
            confirmPanel.style.display = 'block';
            if (confirmMsg) confirmMsg.textContent = task.message || '是否继续？';
        } else {
            confirmPanel.style.display = 'none';
        }
    }

    taskTraceEl.textContent = task.trace?.length ? JSON.stringify(task.trace, null, 2) : '暂无运行轨迹';
    if (task.artifacts) {
        renderArtifacts(task.artifacts);
    }
}

function renderHistory(runs) {
    historyListEl.innerHTML = '';
    if (!runs.length) {
        historyListEl.innerHTML = '<div class="empty-state">暂无历史运行</div>';
        return;
    }
    for (const run of runs) {
        const item = document.createElement('div');
        item.className = 'history-item';
        item.innerHTML = `
            <strong>${escapeHtml(run.project_name)}</strong>
            <span>${escapeHtml(run.mode)}</span>
            <small>${escapeHtml(run.timestamp)}</small>
        `;
        historyListEl.appendChild(item);
    }
}

async function createSession() {
    const response = await fetch('/api/session', { method: 'POST' });
    const data = await response.json();
    state.sessionId = data.session_id;
    sessionIdEl.textContent = state.sessionId;
    renderMessages(data.messages || []);
    renderArtifacts(data.artifacts || {});
}

async function refreshSession() {
    if (!state.sessionId) return;
    const response = await fetch(`/api/session/${state.sessionId}`);
    const data = await response.json();
    renderMessages(data.messages || []);
    renderArtifacts(data.artifacts || {});
}

async function loadHistory() {
    const response = await fetch('/api/history');
    const data = await response.json();
    renderHistory(data.runs || []);
}

async function submitTask(mode) {
    let response;
    if (mode === 'repo') {
        const payload = {
            session_id: state.sessionId,
            project_name: document.getElementById('repo-project').value || 'repo-analysis',
            repo_path: document.getElementById('repo-path').value.trim(),
        };
        response = await fetch('/api/repo', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
    } else if (mode === 'research_full') {
        const query = document.getElementById('research-query').value.trim();
        if (!query) {
            showError('请输入 GitHub 搜索关键词');
            return;
        }
        const payload = {
            session_id: state.sessionId,
            project_name: document.getElementById('research-project').value || 'my-research',
            github_query: query,
            language: document.getElementById('research-language').value.trim() || undefined,
            min_stars: parseInt(document.getElementById('research-min-stars').value) || undefined,
        };
        response = await fetch('/api/research_full', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
    } else {
        const formData = new FormData();
        formData.append('session_id', state.sessionId);

        if (mode === 'single') {
            const projectName = document.getElementById('single-project').value || 'untitled';
            const fileInput = document.getElementById('single-file');
            if (!fileInput.files.length) {
                showError('请选择一个论文文件');
                return;
            }
            formData.append('project_name', projectName);
            formData.append('file', fileInput.files[0]);
        } else {
            const projectName = document.getElementById('survey-project').value || 'untitled';
            const fileInput = document.getElementById('survey-files');
            if (!fileInput.files.length || fileInput.files.length < 2) {
                showError('请选择至少 2 个论文文件');
                return;
            }
            formData.append('project_name', projectName);
            for (const file of fileInput.files) {
                formData.append('files', file);
            }
        }

        response = await fetch(`/api/${mode}`, {
            method: 'POST',
            body: formData,
        });
    }

    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.error || '任务提交失败');
    }
    state.currentTaskId = data.task_id;
    state.currentRunId = data.run_id || data.task_id;
    state.sessionId = data.session_id;
    sessionIdEl.textContent = state.sessionId;
    await refreshSession();
    await loadHistory();
    startPollingTask();
}

async function pollTask() {
    if (!state.currentTaskId) return;
    const response = await fetch(`/api/task/${state.currentTaskId}`);
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.error || '获取任务状态失败');
    }
    setTaskState(data);
    if (data.status === 'completed' || data.status === 'failed' || data.status === 'cancelled') {
        stopPollingTask();
        await refreshSession();
        await loadHistory();
    }
}

function startPollingTask() {
    stopPollingTask();
    pollTask().catch(error => showError(error.message));
    state.pollingTimer = setInterval(() => {
        pollTask().catch(error => {
            stopPollingTask();
            showError(error.message);
        });
    }, 2000);
}

function stopPollingTask() {
    if (state.pollingTimer) {
        clearInterval(state.pollingTimer);
        state.pollingTimer = null;
    }
}

async function sendChatMessage(event) {
    event.preventDefault();
    const input = document.getElementById('chat-input');
    const scopeInput = document.getElementById('chat-scope');
    const message = input.value.trim();
    if (!message) return;
    const scope = scopeInput.value
        .split(',')
        .map(item => item.trim())
        .filter(Boolean);

    input.value = '';

    // Always use non-streaming endpoint for reliability
    const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            session_id: state.sessionId,
            message,
            scope,
        }),
    });
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.error || '发送消息失败');
    }
    renderMessages(data.messages || []);
}

async function cancelTask() {
    if (!state.currentTaskId) return;
    const response = await fetch(`/api/task/${state.currentTaskId}/cancel`, { method: 'POST' });
    const data = await response.json();
    if (!response.ok) {
        showError(data.error || '取消任务失败');
    }
}

async function confirmTask(choice) {
    if (!state.currentTaskId) return;
    const response = await fetch(`/api/task/${state.currentTaskId}/confirm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ choice }),
    });
    const data = await response.json();
    if (!response.ok) {
        showError(data.error || '确认失败');
    }
}

async function resetSession() {
    if (!state.sessionId) return;
    await fetch(`/api/reset/${state.sessionId}`, { method: 'POST' });
    stopPollingTask();
    state.currentTaskId = '';
    state.currentArtifacts = {};
    await createSession();
    await loadHistory();
    setTaskState({
        status: 'idle',
        progress: 0,
        stage: 'idle',
        message: '会话已重置',
        eta_seconds: 0,
        trace: [],
        artifacts: {},
    });
}

function bindEvents() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(node => node.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(node => node.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(btn.dataset.tab).classList.add('active');
        });
    });

    document.querySelectorAll('.artifact-tab').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.artifact-tab').forEach(node => node.classList.remove('active'));
            btn.classList.add('active');
            renderArtifactContent(btn.dataset.artifact);
        });
    });

    document.getElementById('run-single-btn').addEventListener('click', () => {
        submitTask('single').catch(error => showError(error.message));
    });
    document.getElementById('run-survey-btn').addEventListener('click', () => {
        submitTask('survey').catch(error => showError(error.message));
    });
    document.getElementById('run-repo-btn').addEventListener('click', () => {
        submitTask('repo').catch(error => showError(error.message));
    });
    document.getElementById('run-research-full-btn').addEventListener('click', () => {
        submitTask('research_full').catch(error => showError(error.message));
    });
    document.getElementById('chat-form').addEventListener('submit', event => {
        sendChatMessage(event).catch(error => showError(error.message));
    });
    const cancelBtn = document.getElementById('cancel-task-btn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
            cancelTask().catch(error => showError(error.message));
        });
    }
    const confirmContinueBtn = document.getElementById('confirm-continue-btn');
    if (confirmContinueBtn) {
        confirmContinueBtn.addEventListener('click', () => {
            confirmTask('continue').catch(error => showError(error.message));
        });
    }
    const confirmCancelBtn = document.getElementById('confirm-cancel-btn');
    if (confirmCancelBtn) {
        confirmCancelBtn.addEventListener('click', () => {
            confirmTask('cancel').catch(error => showError(error.message));
        });
    }
    document.getElementById('reset-session-btn').addEventListener('click', () => {
        resetSession().catch(error => showError(error.message));
    });
}

bindEvents();
createSession().then(loadHistory).catch(error => showError(error.message));
setTaskState({ status: 'idle', progress: 0, stage: 'idle', message: '等待任务', eta_seconds: 0, trace: [], artifacts: {} });
