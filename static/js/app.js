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
async function showLogDetail(type, logId) {
    const log = logsData[type].find(l => l.id === logId);
    if (!log) return;
    
    const modal = document.getElementById('detail-modal');
    const modalTitle = document.getElementById('modal-title');
    const requestData = document.getElementById('request-data');
    const responseData = document.getElementById('response-data');
    const parsedContent = document.getElementById('parsed-content');
    
    modalTitle.textContent = `${type.toUpperCase()} 交互详情 - ${log.summary}`;
    
    // 设置原始数据视图
    if (type === 'llm') {
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
        requestData.textContent = JSON.stringify(log.details.request, null, 2);
        responseData.textContent = JSON.stringify(log.details.response || {error: "无响应数据"}, null, 2);
    }
    
    // 加载解析数据
    try {
        const response = await fetch(`/api/log/${type}/${logId}/parse`);
        const parsedData = await response.json();
        
        if (parsedData.error) {
            parsedContent.innerHTML = `<div class="error">解析失败: ${parsedData.error}</div>`;
        } else {
            parsedContent.innerHTML = renderParsedContent(type, parsedData);
        }
    } catch (error) {
        parsedContent.innerHTML = `<div class="error">解析失败: ${error.message}</div>`;
    }
    
    // 默认显示解析视图
    switchView('parsed');
    modal.style.display = 'block';
}

// 切换视图
function switchView(viewType) {
    // 更新按钮状态
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById(`${viewType}-view-btn`).classList.add('active');
    
    // 显示对应视图
    document.querySelectorAll('.view-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${viewType}-view`).classList.add('active');
}

// 渲染解析内容
function renderParsedContent(type, data) {
    if (type === 'llm') {
        return renderLLMParsedContent(data);
    } else if (type === 'mcp') {
        return renderMCPParsedContent(data);
    }
    return '<div class="error">未知的日志类型</div>';
}

// 渲染 LLM 解析内容
function renderLLMParsedContent(data) {
    let html = '';
    
    // 基本信息
    if (data.basic_info) {
        html += `
            <div class="parsed-section">
                <h3>基本信息</h3>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">请求 ID</div>
                        <div class="info-value">${data.basic_info.id || '未知'}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">时间戳</div>
                        <div class="info-value">${new Date(data.basic_info.timestamp).toLocaleString('zh-CN')}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">请求方法</div>
                        <div class="info-value">${data.basic_info.method}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">请求路径</div>
                        <div class="info-value">${data.basic_info.path}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">响应状态</div>
                        <div class="info-value ${getStatusClass(data.basic_info.status)}">${data.basic_info.status || '未知'}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">耗时</div>
                        <div class="info-value">${data.basic_info.duration_ms ? Math.round(data.basic_info.duration_ms) + 'ms' : '未知'}</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    // 模型信息
    if (data.model_info && data.model_info.model_name) {
        html += `
            <div class="parsed-section">
                <h3>模型信息</h3>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">模型名称</div>
                        <div class="info-value">${data.model_info.model_name}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">提供商</div>
                        <div class="info-value">${data.model_info.provider}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">模型类型</div>
                        <div class="info-value">${data.model_info.model_type}</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    // 请求配置
    if (data.request_info) {
        html += `
            <div class="parsed-section">
                <h3>请求配置</h3>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">温度</div>
                        <div class="info-value">${data.request_info.temperature ?? '默认'}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">最大令牌</div>
                        <div class="info-value">${data.request_info.max_tokens || '默认'}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">流式输出</div>
                        <div class="info-value">${data.request_info.stream ? '是' : '否'}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">工具数量</div>
                        <div class="info-value">${data.request_info.tools || 0}</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    // 对话内容
    if (data.conversation && data.conversation.length > 0) {
        html += `
            <div class="parsed-section">
                <h3>对话内容</h3>
        `;
        
        data.conversation.forEach(msg => {
            html += `
                <div class="conversation-item ${msg.role}">
                    <div class="conversation-role">${getRoleDisplayName(msg.role)}</div>
                    <div class="conversation-content">${msg.content}</div>
                    <div class="content-length">内容长度: ${msg.content_length} 字符</div>
                </div>
            `;
        });
        
        html += '</div>';
    }
    
    // 流式响应信息
    if (data.streaming_info && data.streaming_info.total_chunks > 0) {
        html += `
            <div class="parsed-section">
                <h3>流式响应信息</h3>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">数据块数量</div>
                        <div class="info-value">${data.streaming_info.total_chunks}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">生成内容长度</div>
                        <div class="info-value">${data.streaming_info.total_content_length} 字符</div>
                    </div>
                </div>
        `;
        
        if (data.streaming_info.generated_content) {
            html += `
                <div class="generated-content">
                    <div class="info-label">生成的内容:</div>
                    <pre>${data.streaming_info.generated_content}</pre>
                </div>
            `;
        }
        
        html += '</div>';
    }
    
    return html;
}

// 渲染 MCP 解析内容
function renderMCPParsedContent(data) {
    let html = '';
    
    // 基本信息
    if (data.basic_info) {
        html += `
            <div class="parsed-section">
                <h3>基本信息</h3>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">会话 ID</div>
                        <div class="info-value">${data.basic_info.session_id}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">时间戳</div>
                        <div class="info-value">${new Date(data.basic_info.timestamp).toLocaleString('zh-CN')}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">方向</div>
                        <div class="info-value">${data.basic_info.direction === 'request' ? '请求' : '响应'}</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    // 消息信息
    if (data.message_info) {
        html += `
            <div class="parsed-section">
                <h3>消息信息</h3>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">方法</div>
                        <div class="info-value">${data.message_info.method || '未知'}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">消息 ID</div>
                        <div class="info-value">${data.message_info.id || '未知'}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">JSON-RPC 版本</div>
                        <div class="info-value">${data.message_info.jsonrpc || '未知'}</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    // 工具信息
    if (data.tool_info) {
        html += `
            <div class="parsed-section">
                <h3>工具信息</h3>
        `;
        
        if (data.tool_info.tool_name) {
            html += `
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">工具名称</div>
                        <div class="info-value">${data.tool_info.tool_name}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">参数摘要</div>
                        <div class="info-value">${data.tool_info.arguments_summary}</div>
                    </div>
                </div>
            `;
            
            if (data.tool_info.arguments && Object.keys(data.tool_info.arguments).length > 0) {
                html += `
                    <div class="tool-args">
                        <div class="info-label">完整参数:</div>
                        <pre>${JSON.stringify(data.tool_info.arguments, null, 2)}</pre>
                    </div>
                `;
            }
        } else if (data.tool_info.available_tools) {
            html += `
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">可用工具数量</div>
                        <div class="info-value">${data.tool_info.tool_count}</div>
                    </div>
                </div>
                <div class="tool-args">
                    <div class="info-label">可用工具列表:</div>
                    <pre>${data.tool_info.available_tools.join(', ')}</pre>
                </div>
            `;
        }
        
        html += '</div>';
    }
    
    // 错误信息
    if (data.error_info && data.error_info.message) {
        html += `
            <div class="parsed-section">
                <h3>错误信息</h3>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">错误代码</div>
                        <div class="info-value error">${data.error_info.code}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">错误消息</div>
                        <div class="info-value error">${data.error_info.message}</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    return html;
}

// 辅助函数
function getStatusClass(status) {
    if (status >= 200 && status < 300) return 'success';
    if (status >= 400) return 'error';
    return 'warning';
}

function getRoleDisplayName(role) {
    const roleNames = {
        'system': '系统',
        'user': '用户',
        'assistant': '助手'
    };
    return roleNames[role] || role;
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