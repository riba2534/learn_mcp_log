#!/usr/bin/env python
"""
启动 Web 界面服务
"""
import uvicorn
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.web.app import app

if __name__ == "__main__":
    print("🌐 启动 Web 界面服务...")
    print("🔗 访问地址: http://localhost:8080")
    print("\n📊 功能说明:")
    print("   - 查看 LLM API 交互记录")
    print("   - 查看 MCP 服务交互记录")
    print("   - 实时更新，自动刷新\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    ) 