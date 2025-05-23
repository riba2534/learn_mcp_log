.PHONY: help proxy mcp both stop clean logs status

# 默认目标
help:
	@echo "🚀 MCP 学习工具 - 命令帮助"
	@echo ""
	@echo "使用方法:"
	@echo "  make proxy    - 启动代理服务器"
	@echo "  make mcp      - 启动 MCP 服务器"
	@echo "  make both     - 同时启动两个服务器（后台）"
	@echo "  make stop     - 停止所有服务"
	@echo "  make logs     - 查看日志"
	@echo "  make status   - 查看服务状态"
	@echo "  make clean    - 清理日志文件"
	@echo ""
	@echo "配置文件: .env"

# 启动代理服务器（前台）
proxy:
	@echo "🚀 启动代理服务器..."
	uv run proxy.py

# 启动 MCP 服务器（前台）
mcp:
	@echo "🔧 启动 MCP 服务器..."
	uv run mcp_server.py

# 同时启动两个服务器（后台）
both:
	@echo "🚀 启动代理服务器（后台）..."
	@nohup uv run proxy.py > proxy.log 2>&1 & echo $$! > proxy.pid
	@sleep 2
	@echo "🔧 启动 MCP 服务器（后台）..."
	@nohup uv run mcp_server.py > mcp.log 2>&1 & echo $$! > mcp.pid
	@sleep 1
	@echo "✅ 两个服务器已在后台启动"
	@echo "   代理服务器: http://127.0.0.1:8000"
	@echo "   查看状态: make status"
	@echo "   停止服务: make stop"

# 停止所有服务
stop:
	@echo "🛑 停止所有服务..."
	@if [ -f proxy.pid ]; then \
		kill `cat proxy.pid` 2>/dev/null || true; \
		rm -f proxy.pid; \
		echo "   ✅ 代理服务器已停止"; \
	fi
	@if [ -f mcp.pid ]; then \
		kill `cat mcp.pid` 2>/dev/null || true; \
		rm -f mcp.pid; \
		echo "   ✅ MCP 服务器已停止"; \
	fi
	@pkill -f "proxy.py" 2>/dev/null || true
	@pkill -f "mcp_server.py" 2>/dev/null || true

# 查看服务状态
status:
	@echo "📊 服务状态检查"
	@echo ""
	@if pgrep -f "proxy.py" > /dev/null; then \
		echo "✅ 代理服务器: 运行中"; \
		curl -s http://127.0.0.1:8000/health | python3 -c "import sys,json; data=json.load(sys.stdin); print(f'   目标: {data[\"target\"]}')"; \
	else \
		echo "❌ 代理服务器: 未运行"; \
	fi
	@if pgrep -f "mcp_server.py" > /dev/null; then \
		echo "✅ MCP 服务器: 运行中"; \
	else \
		echo "❌ MCP 服务器: 未运行"; \
	fi

# 查看日志
logs:
	@echo "📝 最新日志（按 Ctrl+C 退出）"
	@echo ""
	@echo "=== 代理服务器日志 ==="
	@tail -n 5 proxy_logs.jsonl 2>/dev/null | python3 -c "import sys,json; [print(f'{json.loads(line)[\"timestamp\"]} - {json.loads(line)[\"request\"][\"method\"]} {json.loads(line)[\"response\"][\"status\"]}') for line in sys.stdin if line.strip()]" || echo "暂无日志"
	@echo ""
	@echo "=== MCP 服务器日志 ==="
	@tail -n 5 mcp_logs.jsonl 2>/dev/null | python3 -c "import sys,json; [print(f'{json.loads(line)[\"timestamp\"]} - {json.loads(line)[\"type\"]}') for line in sys.stdin if line.strip()]" || echo "暂无日志"

# 实时查看日志
logs-live:
	@echo "📝 实时日志（按 Ctrl+C 退出）"
	@tail -f proxy_logs.jsonl mcp_logs.jsonl

# 清理日志文件
clean:
	@echo "🧹 清理日志文件..."
	@rm -f proxy_logs.jsonl mcp_logs.jsonl proxy.log mcp.log proxy.pid mcp.pid
	@echo "✅ 清理完成"

# 测试 API
test:
	@echo "🧪 测试 API 连接..."
	@curl -s http://127.0.0.1:8000/health || echo "❌ 代理服务器未响应" 