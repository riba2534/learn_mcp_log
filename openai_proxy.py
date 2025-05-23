#!/usr/bin/env python3
"""
OpenAI API 代理服务器
拦截和记录 Cline 与大模型 API 的交互过程，然后转发给真实的 API
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional

import aiohttp
from aiohttp import web, ClientSession
from aiohttp.web import Request, Response, StreamResponse
import argparse


class OpenAIProxy:
    def __init__(self, target_url: str = "https://api.openai.com", log_file: str = "openai_interactions.jsonl"):
        self.target_url = target_url.rstrip('/')
        self.log_file = log_file
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志记录"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def log_interaction(self, interaction_data: Dict[str, Any]):
        """记录交互数据到 JSONL 文件"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(interaction_data, ensure_ascii=False) + '\n')
            
    async def proxy_request(self, request: Request) -> Response:
        """代理请求到目标 API"""
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        
        # 读取请求体
        request_body = await request.read()
        request_json = None
        if request_body:
            try:
                request_json = json.loads(request_body)
            except json.JSONDecodeError:
                pass
        
        # 构建目标 URL
        target_url = f"{self.target_url}{request.path_qs}"
        
        # 记录请求信息
        interaction_data = {
            "timestamp": timestamp,
            "type": "request",
            "method": request.method,
            "url": target_url,
            "headers": dict(request.headers),
            "body": request_json if request_json else request_body.decode('utf-8', errors='ignore'),
            "client_ip": request.remote
        }
        
        self.logger.info(f"收到请求: {request.method} {request.path}")
        self.logger.info(f"请求体大小: {len(request_body)} 字节")
        
        try:
            # 创建 HTTP 客户端会话
            async with ClientSession() as session:
                # 转发请求到目标 API
                async with session.request(
                    method=request.method,
                    url=target_url,
                    headers={k: v for k, v in request.headers.items() 
                            if k.lower() not in ['host', 'content-length']},
                    data=request_body if request_body else None
                ) as response:
                    
                    # 读取响应
                    response_body = await response.read()
                    response_json = None
                    if response_body:
                        try:
                            response_json = json.loads(response_body)
                        except json.JSONDecodeError:
                            pass
                    
                    # 计算响应时间
                    response_time = time.time() - start_time
                    
                    # 记录响应信息
                    response_data = {
                        "timestamp": datetime.now().isoformat(),
                        "type": "response",
                        "status_code": response.status,
                        "headers": dict(response.headers),
                        "body": response_json if response_json else response_body.decode('utf-8', errors='ignore'),
                        "response_time_seconds": response_time
                    }
                    
                    # 合并请求和响应数据
                    full_interaction = {
                        "request": interaction_data,
                        "response": response_data
                    }
                    
                    # 记录完整交互
                    self.log_interaction(full_interaction)
                    
                    self.logger.info(f"响应状态: {response.status}, 耗时: {response_time:.3f}s")
                    
                    # 创建响应对象
                    proxy_response = Response(
                        body=response_body,
                        status=response.status,
                        headers={k: v for k, v in response.headers.items() 
                                if k.lower() not in ['content-length', 'transfer-encoding']}
                    )
                    
                    return proxy_response
                    
        except Exception as e:
            self.logger.error(f"代理请求失败: {str(e)}")
            
            # 记录错误
            error_data = {
                "timestamp": datetime.now().isoformat(),
                "type": "error",
                "error": str(e),
                "response_time_seconds": time.time() - start_time
            }
            
            full_interaction = {
                "request": interaction_data,
                "error": error_data
            }
            
            self.log_interaction(full_interaction)
            
            return Response(
                text=json.dumps({"error": "代理服务器错误", "details": str(e)}),
                status=500,
                content_type='application/json'
            )
    
    async def health_check(self, request: Request) -> Response:
        """健康检查端点"""
        return Response(
            text=json.dumps({
                "status": "healthy",
                "target_url": self.target_url,
                "timestamp": datetime.now().isoformat()
            }),
            content_type='application/json'
        )
    
    def create_app(self) -> web.Application:
        """创建 aiohttp 应用"""
        app = web.Application()
        
        # 健康检查路由
        app.router.add_get('/health', self.health_check)
        
        # 代理所有其他请求
        app.router.add_route('*', '/{path:.*}', self.proxy_request)
        
        return app


async def main():
    parser = argparse.ArgumentParser(description='OpenAI API 代理服务器')
    parser.add_argument('--host', default='127.0.0.1', help='监听主机 (默认: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8000, help='监听端口 (默认: 8000)')
    parser.add_argument('--target', default='https://api.openai.com', 
                       help='目标 API URL (默认: https://api.openai.com)')
    parser.add_argument('--log-file', default='openai_interactions.jsonl',
                       help='日志文件路径 (默认: openai_interactions.jsonl)')
    
    args = parser.parse_args()
    
    # 创建代理服务器
    proxy = OpenAIProxy(target_url=args.target, log_file=args.log_file)
    app = proxy.create_app()
    
    print(f"""
🚀 OpenAI API 代理服务器启动成功！

📝 配置信息:
   监听地址: http://{args.host}:{args.port}
   目标 API: {args.target}
   日志文件: {args.log_file}

💡 使用方法:
   1. 将 Cline 的 API 端点配置为: http://{args.host}:{args.port}
   2. 所有请求将自动转发到目标 API 并记录交互过程
   3. 查看 {args.log_file} 文件了解完整的交互记录

🏥 健康检查: http://{args.host}:{args.port}/health
""")
    
    # 启动服务器
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, args.host, args.port)
    await site.start()
    
    try:
        # 保持服务器运行
        await asyncio.Future()  # 永远等待
    except KeyboardInterrupt:
        print("\n👋 正在关闭服务器...")
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 