# 🧠 Cline 和大模型交互学习工具

<div align="center">

一个专为学习和分析 **Cline** 与大模型 API 以及 **MCP (Model Context Protocol)** 服务器交互过程而设计的完整工具集。

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

## 🎯 项目简介

这个项目通过两个核心组件帮助开发者深入理解现代 AI 编程助手的工作原理：

### 🔄 OpenAI API 代理服务器
- **透明代理**：拦截 Cline 发送给大模型的所有 API 请求
- **完整记录**：捕获请求/响应的完整内容，包括 headers、payload、响应时间
- **实时转发**：无缝转发到真实的 API 端点，不影响正常使用
- **多格式支持**：支持流式和非流式响应，兼容各种大模型 API

### 🛠️ MCP 学习服务器
- **协议实现**：完整实现 Model Context Protocol 规范
- **工具演示**：提供文件操作、系统查询等实用工具
- **资源管理**：展示资源访问和管理机制
- **交互记录**：详细记录 MCP 协议的所有交互过程

## 🌟 核心价值

- **🔍 深度学习**：通过实际交互数据理解 AI 编程助手的工作机制
- **📊 数据分析**：分析 API 调用模式、Token 使用、响应时间等关键指标
- **🧪 协议研究**：深入了解 MCP 协议的设计和实现细节
- **🔧 开发调试**：为开发自己的 AI 工具提供参考和调试基础

## 🚀 快速开始

### 前置要求

- Python 3.8+
- [uv](https://docs.astral.sh/uv/) 包管理器
- 有效的 OpenAI API Key（或其他兼容的大模型 API）

### 1️⃣ 安装 uv

```bash
# macOS 和 Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 使用 brew (macOS)
brew install uv

# 使用 pip
pip install uv

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2️⃣ 克隆和初始化项目

```bash
# 克隆项目
git clone https://github.com/your-username/learn_mcp_log.git
cd learn_mcp_log

# 安装依赖
uv sync

# 配置项目（重要！）
uv run setup_config.py
```

### 3️⃣ 配置你的 API Key

项目支持多种配置方式，选择最适合你的：

#### 🎯 方法 1：使用配置向导（推荐）

```bash
uv run setup_config.py
```

按提示输入你的 OpenAI API Key 和其他配置。

#### 🎯 方法 2：手动配置文件

```bash
# 复制配置模板
cp config.example.json config.json

# 编辑配置文件
# 将 "your-openai-api-key-here" 替换为你的真实 API Key
```

#### 🎯 方法 3：环境变量

```bash
# 直接设置环境变量
export OPENAI_API_KEY="sk-your-actual-api-key-here"
export OPENAI_BASE_URL="https://api.openai.com/v1"

# 或者使用 .env 文件
cp env.example .env
# 编辑 .env 文件
```

### 4️⃣ 启动服务器

```bash
# 🚀 同时启动两个服务器（推荐）
uv run start_servers.py --mode both

# 或者分别启动
uv run openai_proxy.py --host 127.0.0.1 --port 8000  # API 代理
uv run mcp_server.py                                   # MCP 服务器
```

## 🔧 配置 Cline

### API 代理配置

在 Cline 的设置中：

1. 打开 Cline 扩展设置
2. 找到 **API 配置** 部分
3. 将 **Base URL** 设置为：`http://127.0.0.1:8000`
4. 输入你的 API Key（会通过代理转发）

### MCP 服务器配置

在 Cline 的 MCP 配置中添加：

```json
{
  "mcpServers": {
    "learning-mcp-server": {
      "command": "uv",
      "args": ["run", "mcp_server.py"],
      "cwd": "/path/to/learn_mcp_log"
    }
  }
}
```

或者使用绝对路径：

```json
{
  "mcpServers": {
    "learning-mcp-server": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/learn_mcp_log", "run", "mcp_server.py"]
    }
  }
}
```

## 📋 使用指南

### 基本使用流程

1. **启动服务器**：运行 API 代理和 MCP 服务器
2. **配置 Cline**：将 Cline 连接到你的本地服务器
3. **正常使用**：像平常一样使用 Cline 进行编程
4. **查看日志**：分析生成的交互记录

### 实时监控

```bash
# 📊 查看日志概览
uv run log_viewer.py

# 📈 查看详细统计
uv run log_viewer.py --stats

# 🔍 只看 API 交互
uv run log_viewer.py --type openai

# 🛠️ 只看 MCP 交互  
uv run log_viewer.py --type mcp

# 📝 查看详细信息
uv run log_viewer.py --detailed
```

### 实时日志监控

```bash
# 👀 实时查看 API 交互
tail -f openai_interactions.jsonl

# 🔧 实时查看 MCP 交互
tail -f mcp_interactions.jsonl

# 📋 查看服务器运行日志
tail -f mcp_server.log
```

## 📊 日志文件详解

### API 代理日志格式

**文件**：`openai_interactions.jsonl`

每行记录一个完整的请求-响应循环：

```json
{
  "request": {
    "timestamp": "2024-01-10T14:30:15.123456",
    "type": "request",
    "method": "POST",
    "url": "https://api.openai.com/v1/chat/completions",
    "headers": {
      "Authorization": "Bearer sk-...",
      "Content-Type": "application/json"
    },
    "body": {
      "model": "gpt-4",
      "messages": [
        {"role": "user", "content": "解释这段代码..."}
      ],
      "temperature": 0.7
    },
    "client_ip": "127.0.0.1"
  },
  "response": {
    "timestamp": "2024-01-10T14:30:17.456789",
    "type": "response",
    "status_code": 200,
    "headers": {
      "content-type": "application/json"
    },
    "body": {
      "choices": [
        {
          "message": {
            "role": "assistant",
            "content": "这段代码的作用是..."
          }
        }
      ],
      "usage": {
        "prompt_tokens": 25,
        "completion_tokens": 150,
        "total_tokens": 175
      }
    },
    "response_time_seconds": 2.333
  }
}
```

### MCP 交互日志格式

**文件**：`mcp_interactions.jsonl`

记录所有 MCP 协议交互：

```json
{
  "timestamp": "2024-01-10T14:30:20.123456",
  "type": "call_tool", 
  "data": {
    "tool_name": "read_file",
    "arguments": {
      "file_path": "src/main.py"
    }
  }
}
```

## 🛠️ MCP 服务器功能

### 📋 可用工具

| 工具名称 | 功能描述 | 参数 |
|---------|---------|------|
| `read_file` | 读取本地文件内容 | `file_path`: 文件路径 |
| `write_file` | 写入内容到文件 | `file_path`: 文件路径<br>`content`: 文件内容 |
| `list_directory` | 列出目录内容 | `directory_path`: 目录路径 |
| `get_system_info` | 获取系统信息 | 无参数 |
| `calculate` | 数学计算 | `expression`: 数学表达式 |

### 📚 可用资源

| 资源 URI | 描述 |
|---------|------|
| `file://README.md` | 项目说明文档 |
| `config://server-info` | 服务器配置和状态 |

### 使用示例

在 Cline 中，你可以这样使用 MCP 工具：

```
# 让 Cline 读取文件
"请读取 src/main.py 文件的内容"

# 让 Cline 获取系统信息  
"获取当前系统的基本信息"

# 让 Cline 执行计算
"计算 (25 + 30) * 1.2 的结果"
```

## 📈 学习路径

### 🎯 初学者路径

1. **基础设置**
   - 完成环境配置
   - 启动服务器
   - 配置 Cline

2. **基本观察**
   - 发送简单的代码问题
   - 查看生成的日志文件
   - 理解基本的请求-响应格式

3. **工具探索**
   - 尝试使用 MCP 工具
   - 观察工具调用的日志
   - 理解 MCP 协议结构

### 🚀 进阶学习

1. **深度分析**
   - 分析不同类型请求的模式
   - 研究 Token 使用情况
   - 优化 Prompt 效果

2. **协议研究**
   - 深入 MCP 协议规范
   - 实现自定义工具
   - 分析协议设计理念

3. **性能优化**
   - 监控响应时间
   - 分析 API 调用效率
   - 优化交互模式

### 🔬 专家级应用

1. **自定义开发**
   - 扩展 MCP 服务器功能
   - 实现专业领域工具
   - 集成外部服务

2. **数据挖掘**
   - 建立日志分析管道
   - 提取使用模式
   - 生成使用报告

## 🔍 故障排除

### 常见问题

#### ❓ 配置文件不存在

```bash
# 错误信息：配置文件 config.json 不存在
# 解决方案：
uv run setup_config.py
# 或者
cp config.example.json config.json
```

#### ❓ API Key 验证失败

```bash
# 检查 API Key 是否正确设置
uv run config.py

# 检查环境变量
echo $OPENAI_API_KEY
```

#### ❓ MCP 服务器连接失败

1. 确保 MCP 服务器正在运行
2. 检查 Cline 配置中的路径是否正确
3. 查看 `mcp_server.log` 获取详细错误信息

#### ❓ 代理服务器无法访问

```bash
# 检查服务器状态
curl http://127.0.0.1:8000/health

# 检查端口是否被占用
lsof -i :8000  # macOS/Linux
netstat -an | grep 8000  # Windows
```

### 日志分析

```bash
# 美化 JSON 输出（需要安装 jq）
tail -n 1 openai_interactions.jsonl | jq .

# 统计 API 调用次数
wc -l openai_interactions.jsonl

# 查找特定工具的调用
grep "read_file" mcp_interactions.jsonl
```

## 🔐 安全配置

### 配置管理特性

- ✅ **敏感信息保护**：API Key 等敏感信息不会提交到 Git
- ✅ **多层配置**：支持环境变量、配置文件、默认值
- ✅ **配置验证**：自动验证配置完整性
- ✅ **模板系统**：提供安全的配置模板

### 最佳实践

1. **使用环境变量**：生产环境推荐使用环境变量
2. **定期轮换**：定期更换 API Key
3. **权限最小化**：只给必要的 API 权限
4. **监控使用**：定期查看 API 使用情况

## 🤝 贡献指南

欢迎贡献代码和改进建议！

### 开发环境

```bash
# 安装开发依赖
uv sync --dev

# 代码格式化
uv run black .
uv run isort .

# 类型检查
uv run mypy .

# 运行测试
uv run pytest
```

### 提交规范

- 使用有意义的提交信息
- 遵循现有的代码风格
- 添加必要的测试
- 更新相关文档

## 📚 相关资源

- [Model Context Protocol 官方文档](https://modelcontextprotocol.io)
- [OpenAI API 文档](https://platform.openai.com/docs)
- [Cline 扩展](https://marketplace.visualstudio.com/items?itemName=saoudrizwan.claude-dev)
- [uv 包管理器](https://docs.astral.sh/uv/)

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

<div align="center">

**💡 Happy Learning!**

如果这个项目对你有帮助，请给个 ⭐️ 支持一下！

</div> 