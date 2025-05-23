#!/usr/bin/env python3
"""OpenAI API 代理服务器 - 拦截并记录 API 调用，支持流式响应"""

import asyncio
import json
import os
import time
from datetime import datetime

import aiohttp
from aiohttp import web
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置
TARGET_URL = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com').rstrip('/')
HOST = os.getenv('SERVER_HOST', '127.0.0.1')
PORT = int(os.getenv('SERVER_PORT', '8000'))
LOG_FILE = 'proxy_logs.jsonl'


def is_streaming_request(body):
    """检查是否为流式请求"""
    if not body:
        return False
    try:
        data = json.loads(body)
        return data.get('stream', False)
    except:
        return False


async def handle_streaming_response(response, log_entry, start_time, request):
    """处理流式响应"""
    stream_response = web.StreamResponse(
        status=response.status,
        headers={k: v for k, v in response.headers.items()
                if k.lower() not in ['content-length', 'transfer-encoding']}
    )
    
    await stream_response.prepare(request)
    
    chunks = []
    async for chunk in response.content.iter_chunked(8192):
        chunks.append(chunk)
        await stream_response.write(chunk)
    
    # 记录完整的流式响应
    full_body = b''.join(chunks)
    log_entry['response'] = {
        'status': response.status,
        'headers': dict(response.headers),
        'body': '[STREAMING_RESPONSE]',
        'streaming': True,
        'chunks_count': len(chunks),
        'total_bytes': len(full_body),
        'time': time.time() - start_time
    }
    
    # 写入日志
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
    
    return stream_response


async def handle_regular_response(response, log_entry, start_time):
    """处理常规响应"""
    response_body = await response.read()
    
    # 记录响应
    log_entry['response'] = {
        'status': response.status,
        'headers': dict(response.headers),
        'body': json.loads(response_body) if response_body else None,
        'streaming': False,
        'time': time.time() - start_time
    }
    
    # 写入日志
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
    
    # 返回响应
    return web.Response(
        body=response_body,
        status=response.status,
        headers={k: v for k, v in response.headers.items()
                if k.lower() not in ['content-length', 'transfer-encoding']}
    )


async def proxy_handler(request):
    """处理所有代理请求"""
    start_time = time.time()
    
    # 读取请求
    body = await request.read()
    
    # 构建目标 URL
    target_url = f"{TARGET_URL}{request.path_qs}"
    
    # 检查是否为流式请求
    is_streaming = is_streaming_request(body)
    
    # 记录请求
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'request': {
            'method': request.method,
            'url': target_url,
            'headers': dict(request.headers),
            'body': json.loads(body) if body else None,
            'streaming': is_streaming
        }
    }
    
    try:
        # 转发请求
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=request.method,
                url=target_url,
                headers={k: v for k, v in request.headers.items() 
                        if k.lower() not in ['host', 'content-length']},
                data=body
            ) as response:
                
                # 根据响应类型选择处理方式
                if is_streaming or 'text/event-stream' in response.headers.get('content-type', ''):
                    return await handle_streaming_response(response, log_entry, start_time, request)
                else:
                    return await handle_regular_response(response, log_entry, start_time)
                
    except Exception as e:
        log_entry['error'] = str(e)
        log_entry['time'] = time.time() - start_time
        
        with open(LOG_FILE, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        return web.Response(
            text=json.dumps({'error': str(e)}),
            status=500,
            content_type='application/json'
        )


async def health_handler(request):
    """健康检查"""
    return web.Response(
        text=json.dumps({
            'status': 'healthy',
            'target': TARGET_URL,
            'features': ['http', 'sse', 'streaming'],
            'timestamp': datetime.now().isoformat()
        }),
        content_type='application/json'
    )


def main():
    app = web.Application()
    app.router.add_get('/health', health_handler)
    app.router.add_route('*', '/{path:.*}', proxy_handler)
    
    print(f"🚀 代理服务器启动")
    print(f"   地址: http://{HOST}:{PORT}")
    print(f"   目标: {TARGET_URL}")
    print(f"   日志: {LOG_FILE}")
    print(f"   功能: HTTP, SSE, 流式响应")
    
    web.run_app(app, host=HOST, port=PORT)


if __name__ == '__main__':
    main() 