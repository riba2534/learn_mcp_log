# MCP 学习工具

两个简单的服务器用于学习 AI 编程助手的工作原理。

## 配置

创建 `.env` 文件：

```
OPENAI_API_KEY=你的API密钥
OPENAI_BASE_URL=https://openrouter.ai/api
SERVER_HOST=127.0.0.1
SERVER_PORT=8000
```

## 启动

```bash
# 查看所有可用命令
make

# 启动代理服务器（前台）
make proxy

# 启动 MCP 服务器（前台，新终端）
make mcp

# 同时启动两个服务器（后台）
make both

# 查看服务状态
make status

# 停止所有服务
make stop
```

## 手动启动

```bash
# 启动代理服务器
uv run proxy.py

# 启动 MCP 服务器（新终端）
uv run mcp_server.py
```

## 使用

- 代理服务器：`http://127.0.0.1:8000`
- 日志文件：`proxy_logs.jsonl` 和 `mcp_logs.jsonl`

## 日志管理

```bash
# 查看最新日志
make logs

# 实时查看日志
make logs-live

# 清理所有日志
make clean
```

## AI 工具配置

在 Cline/Cursor 等工具中：
- API 端点：`http://127.0.0.1:8000`
- API Key：你的 OpenRouter API Key 