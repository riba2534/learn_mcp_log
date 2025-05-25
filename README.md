# MCP Proxy Logger

一个用于学习和理解大模型 API 与 MCP (Model Context Protocol) 协议交互的中间人代理工具。通过拦截和记录客户端与服务端之间的通信，帮助开发者深入理解协议细节。

## 🎯 项目目标

本项目旨在帮助开发者和学习者：
- 理解客户端与大模型 API 之间的 HTTP 通信协议和数据格式
- 学习 MCP 协议中 Host 与 Server 之间的 JSON-RPC 交互过程
- 通过可视化界面实时查看请求/响应的原始数据包
- 调试和分析 API 调用问题

## 🛠️ 核心功能

### 1. LLM API 代理
- 作为透明代理拦截所有 HTTP 请求和响应
- 支持任何兼容 OpenAI API 格式的服务（OpenAI、OpenRouter、Azure OpenAI 等）
- 完整支持流式输出 (Server-Sent Events)
- 自动记录所有交互数据为 JSON 格式

### 2. MCP 协议服务
- 实现标准 MCP 协议的天气查询服务
- 提供 `get_weather` 和 `get_forecast` 两个示例工具
- 通过 stdio 通信，记录所有 JSON-RPC 消息
- 可集成到支持 MCP 的客户端（如 Claude Desktop）

### 3. Web 可视化界面
- 实时展示所有交互日志
- 分类查看 LLM API 和 MCP 协议的通信数据
- 点击查看完整的请求/响应详情
- 美观现代的响应式设计

## 📦 安装

### 前置要求
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) 包管理工具

### 安装步骤

1. 克隆项目
```bash
git clone <repository-url>
cd mcp-proxy-logger
```

2. 安装 uv（如果尚未安装）
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. 安装项目依赖
```bash
uv sync
```

## 🚀 快速开始

### 使用 Makefile 管理服务

```bash
# 查看所有可用命令
make help

# 启动所有服务（默认代理到 OpenRouter）
make run

# 启动所有服务（代理到 OpenAI）
make run-openai

# 指定自定义目标 URL
make run TARGET_URL=https://your-api.com/v1

# 停止所有服务
make stop

# 查看服务状态
make test

# 清理日志文件
make clean
```

### 单独启动各个组件

```bash
# 仅启动代理服务
make run-proxy

# 仅启动 Web 界面
make run-web

# 开发模式（前台运行，显示日志）
make dev
```

### 自定义配置

```bash
# 使用自定义端口
make run PROXY_PORT=8001 WEB_PORT=8081

# 使用环境变量
export TARGET_URL=https://api.openai.com
make run
```

### MCP 服务

```bash
# 直接运行（用于测试）
uv run python src/mcp/weather_server.py
```

在 Claude Desktop 或其他支持 MCP 的客户端中配置：

```json
{
  "mcpServers": {
    "weather": {
      "command": "uv",
      "args": ["run", "python", "/path/to/mcp-proxy-logger/src/mcp/weather_server.py"],
      "env": {}
    }
  }
}
```

## 📖 使用指南

### 配置客户端使用代理

#### Python (OpenAI SDK)
```python
from openai import OpenAI

# OpenAI
client = OpenAI(
    api_key="your-api-key",
    base_url="http://localhost:8000/v1"
)

# OpenRouter
client = OpenAI(
    api_key="your-openrouter-api-key",
    base_url="http://localhost:8000/v1",
    default_headers={
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "Your App Name"
    }
)

# 使用示例
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)
```

#### curl
```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```



### 查看交互日志

1. **通过 Web 界面**
   - 访问 http://localhost:8080
   - 点击 "LLM API 交互" 查看代理日志
   - 点击 "MCP 服务交互" 查看 MCP 日志
   - 点击任意日志条目查看详细信息

2. **查看日志文件**
   - LLM 代理日志：`logs/llm_proxy/*.json`
   - MCP 服务日志：`logs/mcp_weather/*.jsonl`

## 🧪 测试

### 测试服务连接
```bash
# 检查服务状态
make test
```

### 测试 API 调用
使用 curl 或任何 HTTP 客户端测试代理功能：

```bash
# 测试代理服务
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## 📁 项目结构

```
mcp-proxy-logger/
├── src/
│   ├── proxy/
│   │   └── llm_proxy.py      # LLM API 代理实现
│   ├── mcp/
│   │   └── weather_server.py  # MCP 天气服务实现
│   └── web/
│       └── app.py            # Web 界面后端
├── templates/
│   └── index.html            # Web 界面模板
├── static/
│   ├── css/
│   │   └── style.css         # 样式文件
│   └── js/
│       └── app.js            # 前端交互逻辑
├── logs/                     # 日志存储目录（自动创建）
│   ├── llm_proxy/           # LLM 交互日志
│   └── mcp_weather/         # MCP 交互日志
├── run_proxy.py             # 代理服务启动脚本
├── run_web.py               # Web 界面启动脚本
├── Makefile                 # 项目管理脚本
├── LICENSE                  # MIT 许可证
├── README.md                # 项目文档
└── pyproject.toml           # 项目配置文件
```

## 🔍 日志格式

### LLM 代理日志 (JSON)
```json
{
  "id": "uuid",
  "timestamp": "2024-01-01 12:00:00",
  "method": "POST",
  "path": "/v1/chat/completions",
  "headers": {...},
  "body": {
    "model": "gpt-3.5-turbo",
    "messages": [...]
  },
  "response_status": 200,
  "response_headers": {...},
  "response_body": {...},
  "response_chunks": [...],  // 流式响应时
  "duration_ms": 1234.5
}
```

### MCP 服务日志 (JSONL)
```json
{"session_id": "uuid", "timestamp": "2024-01-01 12:00:00", "direction": "request", "message": {...}}
{"session_id": "uuid", "timestamp": "2024-01-01 12:00:01", "direction": "response", "message": {...}}
```

## ⚙️ 配置选项

### 环境变量
- `TARGET_BASE_URL`: 目标 API 的基础 URL
- `OPENAI_API_KEY`: OpenAI API 密钥
- `OPENROUTER_API_KEY`: OpenRouter API 密钥

### 命令行参数
- `--target-url`: 指定目标 API URL
- `--port`: 指定代理服务端口

## 🛡️ 安全注意事项

1. **仅用于开发和学习**：本工具不应在生产环境中使用
2. **API 密钥安全**：日志中会包含 API 密钥，请妥善保管日志文件
3. **敏感数据**：日志可能包含敏感对话内容，注意数据隐私
4. **网络安全**：代理服务默认监听所有网络接口，建议仅在本地使用

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 高性能 Web 框架
- [httpx](https://www.python-httpx.org/) - 现代 HTTP 客户端
- [MCP](https://modelcontextprotocol.io/) - Model Context Protocol
- [uv](https://github.com/astral-sh/uv) - 快速的 Python 包管理器
