"""
LLM API 中间人代理
用于拦截和记录客户端与大模型 API 之间的通信
"""
import json
import time
import uuid
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import httpx
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import StreamingResponse
import asyncio
from pydantic import BaseModel

class ProxyConfig(BaseModel):
    """代理配置"""
    target_base_url: str = os.getenv("TARGET_BASE_URL", "https://api.openai.com")
    log_dir: Path = Path("logs/llm_proxy")
    enable_logging: bool = True

class RequestLog(BaseModel):
    """请求日志模型"""
    id: str
    timestamp: datetime
    method: str
    path: str
    headers: Dict[str, str]
    body: Optional[Dict[str, Any]]
    response_status: Optional[int] = None
    response_headers: Optional[Dict[str, str]] = None
    response_body: Optional[Any] = None
    response_chunks: list = []
    duration_ms: Optional[float] = None

class LLMProxy:
    def __init__(self, config: ProxyConfig):
        self.config = config
        self.config.log_dir.mkdir(parents=True, exist_ok=True)
        self.client = httpx.AsyncClient(timeout=60.0)
        print(f"🎯 代理目标 URL: {self.config.target_base_url}")
        
    async def log_request(self, log_data: RequestLog):
        """保存请求日志"""
        if not self.config.enable_logging:
            return
            
        log_file = self.config.log_dir / f"{log_data.id}.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data.model_dump(), f, ensure_ascii=False, indent=2, default=str)
    
    async def proxy_request(self, request: Request) -> Response:
        """代理请求到目标 API"""
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # 读取请求体
        body = await request.body()
        body_json = None
        if body:
            try:
                body_json = json.loads(body)
            except:
                body_json = body.decode('utf-8', errors='ignore')
        
        # 构建请求日志
        log_data = RequestLog(
            id=request_id,
            timestamp=datetime.now(),
            method=request.method,
            path=str(request.url.path),
            headers=dict(request.headers),
            body=body_json
        )
        
        # 构建目标 URL
        target_url = f"{self.config.target_base_url}{request.url.path}"
        if request.url.query:
            target_url += f"?{request.url.query}"
        
        # 转发请求头（排除 host 相关）
        headers = {}
        for key, value in request.headers.items():
            if key.lower() not in ['host', 'content-length']:
                headers[key] = value
        
        try:
            # 发送请求到目标 API
            response = await self.client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                follow_redirects=True
            )
            
            # 记录响应信息
            log_data.response_status = response.status_code
            log_data.response_headers = dict(response.headers)
            
            # 检查是否是流式响应
            is_stream = 'text/event-stream' in response.headers.get('content-type', '')
            
            if is_stream:
                # 处理流式响应
                async def stream_generator():
                    chunks = []
                    async for chunk in response.aiter_bytes():
                        chunks.append(chunk.decode('utf-8', errors='ignore'))
                        yield chunk
                    
                    # 保存所有块
                    log_data.response_chunks = chunks
                    log_data.duration_ms = (time.time() - start_time) * 1000
                    await self.log_request(log_data)
                
                return StreamingResponse(
                    stream_generator(),
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.headers.get('content-type')
                )
            else:
                # 处理普通响应
                response_body = response.text
                try:
                    log_data.response_body = json.loads(response_body)
                except:
                    log_data.response_body = response_body
                
                log_data.duration_ms = (time.time() - start_time) * 1000
                await self.log_request(log_data)
                
                return Response(
                    content=response_body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.headers.get('content-type')
                )
                
        except Exception as e:
            log_data.response_status = 500
            log_data.response_body = {"error": str(e)}
            log_data.duration_ms = (time.time() - start_time) * 1000
            await self.log_request(log_data)
            
            raise HTTPException(status_code=500, detail=str(e))

# 创建 FastAPI 应用
app = FastAPI(title="LLM Proxy Logger")

# 全局变量，延迟初始化
llm_proxy = None

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化代理"""
    global llm_proxy
    # 此时环境变量已经设置
    proxy_config = ProxyConfig(
        target_base_url=os.getenv("TARGET_BASE_URL", "https://api.openai.com")
    )
    llm_proxy = LLMProxy(proxy_config)

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_endpoint(request: Request, path: str):
    """通用代理端点"""
    if llm_proxy is None:
        raise HTTPException(status_code=500, detail="Proxy not initialized")
    return await llm_proxy.proxy_request(request)

@app.on_event("shutdown")
async def shutdown_event():
    """关闭时清理资源"""
    if llm_proxy:
        await llm_proxy.client.aclose() 