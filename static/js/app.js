// 全局变量
let currentTab = 'llm';
let logsData = {
    llm: [],
    mcp: []
};

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    loadLogs('llm');
    loadLogs('mcp');
    
    // 自动刷新日志
    setInterval(() => {
        loadLogs(currentTab);
    }, 5000);
});

// 切换标签页
function switchTab(tab) {
    currentTab = tab;
    
    // 更新标签按钮状态
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // 显示对应内容
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tab}-content`).classList.add('active');
}

// 加载日志
async function loadLogs(type) {
    try {
        const response = await fetch(`/api/logs/${type}`);
        const logs = await response.json();
        logsData[type] = logs;
        displayLogs(type, logs);
    } catch (error) {
        console.error(`Error loading ${type} logs:`, error);
    }
}

// 显示日志列表
function displayLogs(type, logs) {
    const container = document.getElementById(`${type}-logs`);
    
    if (logs.length === 0) {
        container.innerHTML = '<div class="no-data">暂无数据</div>';
        return;
    }
    
    let html = '';
    logs.forEach(log => {
        const timestamp = new Date(log.timestamp).toLocaleString('zh-CN');
        html += `
            <div class="log-item" onclick="showLogDetail('${type}', '${log.id}')">
                <div class="log-header">
                    <div>
                        <span class="log-type ${type}">${type.toUpperCase()}</span>
                        <span class="log-summary">${log.summary}</span>
                    </div>
                    <span class="log-timestamp">${timestamp}</span>
                </div>
                ${getLogPreview(log)}
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// 获取日志预览
function getLogPreview(log) {
    let preview = '<div class="log-details">';
    
    if (log.type === 'llm') {
        if (log.details.body) {
            if (log.details.body.messages) {
                const lastMessage = log.details.body.messages[log.details.body.messages.length - 1];
                if (lastMessage && lastMessage.content) {
                    const content = typeof lastMessage.content === 'string' 
                        ? lastMessage.content 
                        : JSON.stringify(lastMessage.content);
                    preview += `消息: ${content.substring(0, 100)}${content.length > 100 ? '...' : ''}`;
                }
            }
        }
        if (log.details.response_status) {
            preview += ` | 状态: ${log.details.response_status}`;
        }
        if (log.details.duration_ms) {
            preview += ` | 耗时: ${log.details.duration_ms.toFixed(0)}ms`;
        }
    } else if (log.type === 'mcp') {
        const request = log.details.request;
        if (request.method) {
            preview += `方法: ${request.method}`;
        }
        if (request.params) {
            preview += ` | 参数: ${JSON.stringify(request.params).substring(0, 50)}...`;
        }
    }
    
    preview += '</div>';
    return preview;
}

// 显示日志详情
function showLogDetail(type, logId) {
    const log = logsData[type].find(l => l.id === logId);
    if (!log) return;
    
    const modal = document.getElementById('detail-modal');
    const modalTitle = document.getElementById('modal-title');
    const requestData = document.getElementById('request-data');
    const responseData = document.getElementById('response-data');
    
    modalTitle.textContent = `${type.toUpperCase()} 交互详情 - ${log.summary}`;
    
    if (type === 'llm') {
        // LLM 日志详情
        const requestInfo = {
            method: log.details.method,
            path: log.details.path,
            headers: log.details.headers,
            body: log.details.body
        };
        requestData.textContent = JSON.stringify(requestInfo, null, 2);
        
        const responseInfo = {
            status: log.details.response_status,
            headers: log.details.response_headers,
            body: log.details.response_body,
            chunks: log.details.response_chunks,
            duration_ms: log.details.duration_ms
        };
        responseData.textContent = JSON.stringify(responseInfo, null, 2);
    } else if (type === 'mcp') {
        // MCP 日志详情
        requestData.textContent = JSON.stringify(log.details.request, null, 2);
        responseData.textContent = JSON.stringify(log.details.response || {error: "无响应数据"}, null, 2);
    }
    
    modal.style.display = 'block';
}

// 关闭模态框
function closeModal() {
    document.getElementById('detail-modal').style.display = 'none';
}

// 点击模态框外部关闭
window.onclick = function(event) {
    const modal = document.getElementById('detail-modal');
    if (event.target === modal) {
        modal.style.display = 'none';
    }
} 