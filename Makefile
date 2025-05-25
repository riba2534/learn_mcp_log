# MCP Proxy Logger Makefile
# 默认目标 API 为 OpenRouter
TARGET_URL ?= https://openrouter.ai/api/v1
PROXY_PORT ?= 8000
WEB_PORT ?= 8080

# 颜色定义
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

.PHONY: help install run run-proxy run-web stop clean logs test

# 默认目标：显示帮助
help:
	@echo "$(GREEN)MCP Proxy Logger - Makefile 命令$(NC)"
	@echo "================================================"
	@echo "$(YELLOW)启动命令:$(NC)"
	@echo "  make run          - 启动所有服务 (代理到 OpenRouter)"
	@echo "  make run-openai   - 启动所有服务 (代理到 OpenAI)"
	@echo "  make run-proxy    - 仅启动代理服务"
	@echo "  make run-web      - 仅启动 Web 界面"
	@echo ""
	@echo "$(YELLOW)管理命令:$(NC)"
	@echo "  make stop         - 停止所有服务"
	@echo "  make clean        - 清理日志文件"
	@echo "  make logs         - 查看日志目录"
	@echo "  make install      - 安装项目依赖"
	@echo ""
	@echo "$(YELLOW)环境变量:$(NC)"
	@echo "  TARGET_URL        - 目标 API URL (默认: $(TARGET_URL))"
	@echo "  PROXY_PORT        - 代理端口 (默认: $(PROXY_PORT))"
	@echo "  WEB_PORT          - Web 端口 (默认: $(WEB_PORT))"

# 安装依赖
install:
	@echo "$(GREEN)正在安装项目依赖...$(NC)"
	@uv sync
	@echo "$(GREEN)✅ 依赖安装完成$(NC)"

# 运行所有服务（默认 OpenRouter）
run: stop
	@echo "$(GREEN)🚀 启动 MCP Proxy Logger$(NC)"
	@echo "$(YELLOW)目标 API: $(TARGET_URL)$(NC)"
	@echo "$(YELLOW)清理旧日志...$(NC)"
	@rm -rf logs/
	@mkdir -p logs/llm_proxy logs/mcp_weather
	@echo "$(GREEN)启动代理服务...$(NC)"
	@TARGET_BASE_URL=$(TARGET_URL) uv run python run_proxy.py --port $(PROXY_PORT) > logs/proxy.log 2>&1 & \
		echo $$! > .proxy.pid
	@sleep 2
	@echo "$(GREEN)启动 Web 界面...$(NC)"
	@uv run python run_web.py --port $(WEB_PORT) > logs/web.log 2>&1 & \
		echo $$! > .web.pid
	@sleep 2
	@echo ""
	@echo "$(GREEN)✅ 所有服务已启动!$(NC)"
	@echo ""
	@echo "📌 访问地址:"
	@echo "   - LLM 代理: http://localhost:$(PROXY_PORT)"
	@echo "   - Web 界面: http://localhost:$(WEB_PORT)"
	@echo ""
	@echo "💡 使用提示:"
	@echo "   - 在客户端设置 API Base URL: http://localhost:$(PROXY_PORT)/v1"
	@echo "   - 使用对应的 API Key"
	@echo "   - 运行 'make stop' 停止服务"
	@echo ""

# 运行所有服务（OpenAI 模式）
run-openai:
	@$(MAKE) run TARGET_URL=https://api.openai.com

# 仅运行代理服务
run-proxy: stop-proxy
	@echo "$(GREEN)启动代理服务...$(NC)"
	@echo "$(YELLOW)目标 API: $(TARGET_URL)$(NC)"
	@mkdir -p logs/llm_proxy
	@TARGET_BASE_URL=$(TARGET_URL) uv run python run_proxy.py --port $(PROXY_PORT)

# 仅运行 Web 服务
run-web: stop-web
	@echo "$(GREEN)启动 Web 界面...$(NC)"
	@mkdir -p logs
	@uv run python run_web.py --port $(WEB_PORT)

# 停止所有服务
stop: stop-proxy stop-web
	@echo "$(GREEN)✅ 所有服务已停止$(NC)"

# 停止代理服务
stop-proxy:
	@if [ -f .proxy.pid ]; then \
		kill `cat .proxy.pid` 2>/dev/null || true; \
		rm -f .proxy.pid; \
		echo "$(YELLOW)代理服务已停止$(NC)"; \
	fi
	@pkill -f "run_proxy.py" 2>/dev/null || true

# 停止 Web 服务
stop-web:
	@if [ -f .web.pid ]; then \
		kill `cat .web.pid` 2>/dev/null || true; \
		rm -f .web.pid; \
		echo "$(YELLOW)Web 服务已停止$(NC)"; \
	fi
	@pkill -f "run_web.py" 2>/dev/null || true

# 清理日志
clean:
	@echo "$(YELLOW)清理日志文件...$(NC)"
	@rm -rf logs/
	@rm -f .proxy.pid .web.pid
	@echo "$(GREEN)✅ 清理完成$(NC)"

# 查看日志
logs:
	@echo "$(GREEN)日志文件:$(NC)"
	@if [ -d logs ]; then \
		echo "$(YELLOW)LLM 代理日志:$(NC)"; \
		ls -la logs/llm_proxy/ 2>/dev/null | tail -5 || echo "  (空)"; \
		echo ""; \
		echo "$(YELLOW)MCP 服务日志:$(NC)"; \
		ls -la logs/mcp_weather/ 2>/dev/null | tail -5 || echo "  (空)"; \
		echo ""; \
		echo "$(YELLOW)服务日志:$(NC)"; \
		ls -la logs/*.log 2>/dev/null || echo "  (空)"; \
	else \
		echo "  日志目录不存在"; \
	fi

# 测试服务状态
test:
	@echo "$(GREEN)测试服务状态...$(NC)"
	@echo -n "代理服务: "
	@curl -s http://localhost:$(PROXY_PORT)/ > /dev/null && echo "$(GREEN)✅ 运行中$(NC)" || echo "$(RED)❌ 未运行$(NC)"
	@echo -n "Web 界面: "
	@curl -s http://localhost:$(WEB_PORT)/ > /dev/null && echo "$(GREEN)✅ 运行中$(NC)" || echo "$(RED)❌ 未运行$(NC)"

# 开发模式（前台运行，显示日志）
dev:
	@echo "$(GREEN)开发模式启动（Ctrl+C 停止）$(NC)"
	@$(MAKE) stop
	@echo "$(YELLOW)清理旧日志...$(NC)"
	@rm -rf logs/
	@mkdir -p logs/llm_proxy logs/mcp_weather
	@echo "$(YELLOW)启动代理服务 (端口: $(PROXY_PORT))$(NC)"
	@TARGET_BASE_URL=$(TARGET_URL) uv run python run_proxy.py --port $(PROXY_PORT) &
	@PROXY_PID=$$!; \
	sleep 2; \
	echo "$(YELLOW)启动 Web 界面 (端口: $(WEB_PORT))$(NC)"; \
	uv run python run_web.py --port $(WEB_PORT) & \
	WEB_PID=$$!; \
	trap "kill $$PROXY_PID $$WEB_PID 2>/dev/null; exit" INT; \
	wait 