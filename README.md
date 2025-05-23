# Cline 和大模型交互学习工具

这个项目包含两个程序，用于学习和分析 Cline 与大模型以及 MCP 服务器的交互过程。

## 📋 项目简介

### 1. OpenAI API 代理服务器 (`openai_proxy.py`)
- 作为大模型 API 的中间人代理
- 拦截 Cline 发送给大模型的请求
- 转发请求到真实的 API
- 记录完整的交互过程到日志文件

### 2. MCP 学习服务器 (`mcp_server.py`)
- 实现 Model Context Protocol (MCP) 服务器
- 接受 Cline 作为 MCP 客户端的请求
- 提供多种工具和资源
- 记录 MCP 协议的交互过程

## 🔐 配置管理

本项目支持安全的配置管理，敏感信息（如 API Key）不会提交到 Git 仓库。

### 配置方式

项目支持三种配置方式（优先级从高到低）：

1. **环境变量** - 最高优先级
2. **配置文件** (`config.json`) - 中等优先级  
3. **默认值** - 最低优先级

### 快速配置

```bash
# 使用配置向导（推荐）
uv run setup_config.py

# 或者手动复制配置文件
cp config.example.json config.json
# 然后编辑 config.json 填入真实的 API Key
```

### 环境变量配置

```bash
# 复制环境变量模板
cp env.example .env
# 编辑 .env 文件填入真实配置

# 或者直接设置环境变量
export OPENAI_API_KEY="your-real-api-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"
```

### 配置文件说明

- `config.example.json` - 配置模板（会提交到 Git）
- `config.json` - 实际配置文件（不会提交到 Git）
- `env.example` - 环境变量模板（会提交到 Git）
- `.env` - 实际环境变量文件（不会提交到 Git）

## 🚀 快速开始

### 安装 uv（如果尚未安装）

```bash
# macOS 和 Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或者使用 brew (macOS)
brew install uv

# 或者使用 pip
pip install uv
```

### 初始化项目

```bash
# 克隆或进入项目目录
cd learn_mcp_log

# 使用 uv 安装依赖
uv sync

# 配置项目（设置 API Key 等）
uv run setup_config.py
```

### 使用方法

#### 启动单个服务

```bash
# 启动 OpenAI API 代理服务器
uv run openai_proxy.py --host 127.0.0.1 --port 8000

# 启动 MCP 学习服务器
uv run mcp_server.py
```

#### 使用启动脚本同时启动两个服务

```bash
# 同时启动两个服务器
uv run start_servers.py

# 只启动 API 代理
uv run start_servers.py --mode proxy

# 只启动 MCP 服务器
uv run start_servers.py --mode mcp
```

#### 查看日志

```bash
# 查看最近的交互日志
uv run log_viewer.py

# 查看详细信息
uv run log_viewer.py --detailed

# 查看统计信息
uv run log_viewer.py --stats

# 只查看 API 日志
uv run log_viewer.py --type openai

# 只查看 MCP 日志
uv run log_viewer.py --type mcp
```

## 🔧 配置 Cline

### 配置 API 代理

在 Cline 中将 API 端点配置为：
```
http://127.0.0.1:8000
```

### 配置 MCP 服务器

在 Cline 的 MCP 配置中添加：
```json
{
  "learning-mcp-server": {
    "command": "uv",
    "args": ["run", "mcp_server.py"],
    "cwd": "/path/to/mcp_test"
  }
}
```

或者使用绝对路径：
```json
{
  "learning-mcp-server": {
    "command": "uv",
    "args": ["--directory", "/path/to/mcp_test", "run", "mcp_server.py"]
  }
}
```

## 📊 日志文件说明

### OpenAI API 代理日志 (`openai_interactions.jsonl`)

每行包含一个完整的请求-响应交互：

```json
{
  "request": {
    "timestamp": "2023-12-10T10:30:00.123456",
    "type": "request",
    "method": "POST",
    "url": "https://api.openai.com/v1/chat/completions",
    "headers": {"Authorization": "Bearer sk-...", ...},
    "body": {"model": "gpt-4", "messages": [...], ...},
    "client_ip": "127.0.0.1"
  },
  "response": {
    "timestamp": "2023-12-10T10:30:02.456789",
    "type": "response", 
    "status_code": 200,
    "headers": {"content-type": "application/json", ...},
    "body": {"choices": [...], "usage": {...}, ...},
    "response_time_seconds": 2.333
  }
}
```

### MCP 交互日志 (`mcp_interactions.jsonl`)

记录所有 MCP 协议交互：

```json
{
  "timestamp": "2023-12-10T10:30:00.123456",
  "type": "list_tools",
  "data": {"action": "获取工具列表"}
}
{
  "timestamp": "2023-12-10T10:30:05.789012", 
  "type": "call_tool",
  "data": {"tool_name": "read_file", "arguments": {"file_path": "test.txt"}}
}
```

## 🛠️ MCP 服务器功能

### 可用工具

1. **read_file** - 读取本地文件内容
2. **write_file** - 将内容写入本地文件
3. **list_directory** - 列出目录中的文件和子目录
4. **get_system_info** - 获取系统信息
5. **calculate** - 执行简单的数学计算

### 可用资源

1. **file://README.md** - 项目说明文档
2. **config://server-info** - 服务器配置和状态信息
3. **log://interactions** - 交互历史记录

### 提示模板

1. **analyze_code** - 代码分析提示模板
2. **file_summary** - 文件内容摘要提示模板
3. **debug_help** - 调试帮助提示模板

## 📚 学习建议

1. **启动两个服务器**：同时运行 API 代理和 MCP 服务器
2. **配置 Cline**：将 Cline 连接到这两个服务器
3. **进行交互**：在 Cline 中尝试各种操作
4. **查看日志**：分析生成的日志文件，理解协议格式
5. **对比学习**：比较 OpenAI API 和 MCP 协议的不同之处

## 🔍 调试技巧

### 查看实时日志

```bash
# 查看 API 代理日志
tail -f openai_interactions.jsonl

# 查看 MCP 交互日志  
tail -f mcp_interactions.jsonl

# 查看 MCP 服务器运行日志
tail -f mcp_server.log
```

### 使用项目自带的日志查看器

```bash
# 查看最近的交互日志
uv run log_viewer.py

# 查看详细信息
uv run log_viewer.py --detailed

# 查看统计信息
uv run log_viewer.py --stats

# 只查看 API 日志
uv run log_viewer.py --type openai

# 只查看 MCP 日志
uv run log_viewer.py --type mcp
```

### 使用 jq 美化 JSON 日志

```bash
# 美化显示最新的 API 交互
tail -n 1 openai_interactions.jsonl | jq .

# 美化显示最新的 MCP 交互
tail -n 1 mcp_interactions.jsonl | jq .
```

### 健康检查

```bash
# 检查 API 代理服务器状态
curl http://127.0.0.1:8000/health
```

## 🔧 开发

### 开发环境设置

```bash
# 安装开发依赖
uv sync --dev

# 代码格式化
uv run black .

# 导入排序
uv run isort .

# 运行测试
uv run pytest
```

### 添加新的依赖

```bash
# 添加运行时依赖
uv add package_name

# 添加开发依赖
uv add --dev package_name

# 更新依赖
uv sync
```

## 📝 协议学习要点

### OpenAI API 关键特征
- REST API 风格
- HTTP POST 请求
- JSON 格式的请求和响应
- 流式和非流式响应支持
- 认证通过 Authorization header

### MCP 协议关键特征
- 基于 JSON-RPC 2.0
- 通过 stdio 进行通信
- 三种核心功能：Resources、Tools、Prompts
- 客户端-服务器架构
- 支持工具调用和资源访问

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个学习工具！

## �� 许可证

MIT License 