"""
MCP 天气查询服务端
实现 MCP 协议，提供天气查询功能并记录交互数据
"""
import json
import sys
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import uuid
from pydantic import BaseModel

# MCP 协议相关的数据模型
class MCPMessage(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[int] = None
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None

class Tool(BaseModel):
    name: str
    description: str
    inputSchema: Dict[str, Any]

class MCPInteractionLog(BaseModel):
    """MCP 交互日志"""
    session_id: str
    timestamp: datetime
    direction: str  # "request" or "response"
    message: Dict[str, Any]

class WeatherMCPServer:
    def __init__(self, log_dir: Path = Path("logs/mcp_weather")):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.session_id = str(uuid.uuid4())
        self.message_id_counter = 0
        
        # 定义工具
        self.tools = [
            Tool(
                name="get_weather",
                description="获取指定城市的天气信息",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "城市名称，例如：北京、上海、深圳"
                        }
                    },
                    "required": ["city"]
                }
            ),
            Tool(
                name="get_forecast",
                description="获取指定城市未来几天的天气预报",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "城市名称"
                        },
                        "days": {
                            "type": "integer",
                            "description": "预报天数，1-7天",
                            "minimum": 1,
                            "maximum": 7
                        }
                    },
                    "required": ["city"]
                }
            )
        ]
    
    async def log_interaction(self, direction: str, message: Dict[str, Any]):
        """记录交互数据"""
        log_entry = MCPInteractionLog(
            session_id=self.session_id,
            timestamp=datetime.now(),
            direction=direction,
            message=message
        )
        
        # 保存到日志文件
        log_file = self.log_dir / f"{self.session_id}.jsonl"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry.model_dump(), ensure_ascii=False, default=str) + '\n')
    
    async def handle_initialize(self, message: MCPMessage) -> MCPMessage:
        """处理初始化请求"""
        return MCPMessage(
            jsonrpc="2.0",
            id=message.id,
            result={
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "prompts": {}
                },
                "serverInfo": {
                    "name": "weather-mcp-server",
                    "version": "1.0.0"
                }
            }
        )
    
    async def handle_list_tools(self, message: MCPMessage) -> MCPMessage:
        """处理列出工具请求"""
        tools_list = [tool.model_dump() for tool in self.tools]
        return MCPMessage(
            jsonrpc="2.0",
            id=message.id,
            result={"tools": tools_list}
        )
    
    async def handle_call_tool(self, message: MCPMessage) -> MCPMessage:
        """处理工具调用请求"""
        params = message.params or {}
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "get_weather":
            city = arguments.get("city", "未知")
            # 模拟天气数据
            weather_data = {
                "city": city,
                "temperature": "25°C",
                "weather": "晴天",
                "humidity": "65%",
                "wind": "东南风 3级",
                "air_quality": "良"
            }
            
            return MCPMessage(
                jsonrpc="2.0",
                id=message.id,
                result={
                    "content": [
                        {
                            "type": "text",
                            "text": f"{city}的天气信息：\n温度：{weather_data['temperature']}\n天气：{weather_data['weather']}\n湿度：{weather_data['humidity']}\n风力：{weather_data['wind']}\n空气质量：{weather_data['air_quality']}"
                        }
                    ]
                }
            )
        
        elif tool_name == "get_forecast":
            city = arguments.get("city", "未知")
            days = arguments.get("days", 3)
            
            # 模拟预报数据
            forecast = []
            weather_types = ["晴", "多云", "阴", "小雨", "中雨"]
            for i in range(days):
                forecast.append({
                    "date": f"第{i+1}天",
                    "weather": weather_types[i % len(weather_types)],
                    "temp_high": f"{20 + i}°C",
                    "temp_low": f"{15 + i}°C"
                })
            
            forecast_text = f"{city}未来{days}天天气预报：\n"
            for day in forecast:
                forecast_text += f"{day['date']}：{day['weather']}，{day['temp_low']} ~ {day['temp_high']}\n"
            
            return MCPMessage(
                jsonrpc="2.0",
                id=message.id,
                result={
                    "content": [
                        {
                            "type": "text",
                            "text": forecast_text
                        }
                    ]
                }
            )
        
        else:
            return MCPMessage(
                jsonrpc="2.0",
                id=message.id,
                error={
                    "code": -32601,
                    "message": f"Unknown tool: {tool_name}"
                }
            )
    
    async def handle_message(self, message: MCPMessage) -> MCPMessage:
        """处理单个消息"""
        method = message.method
        
        if method == "initialize":
            return await self.handle_initialize(message)
        elif method == "tools/list":
            return await self.handle_list_tools(message)
        elif method == "tools/call":
            return await self.handle_call_tool(message)
        else:
            return MCPMessage(
                jsonrpc="2.0",
                id=message.id,
                error={
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            )
    
    async def run_stdio(self):
        """通过 stdio 运行服务器"""
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        
        # 在 Windows 上使用不同的方法
        if sys.platform == 'win32':
            # Windows 特定的处理
            loop = asyncio.get_event_loop()
            await loop.connect_read_pipe(lambda: protocol, sys.stdin)
        else:
            # Unix/Linux/Mac
            await asyncio.get_event_loop().connect_read_pipe(
                lambda: protocol, sys.stdin)
        
        while True:
            try:
                # 读取一行
                line = await reader.readline()
                if not line:
                    break
                
                # 解析消息
                message_data = json.loads(line.decode('utf-8').strip())
                message = MCPMessage(**message_data)
                
                # 记录请求
                await self.log_interaction("request", message_data)
                
                # 处理消息
                response = await self.handle_message(message)
                
                # 记录响应
                response_data = response.model_dump(exclude_none=True)
                await self.log_interaction("response", response_data)
                
                # 发送响应
                sys.stdout.write(json.dumps(response_data) + '\n')
                sys.stdout.flush()
                
            except Exception as e:
                # 错误响应
                error_response = MCPMessage(
                    jsonrpc="2.0",
                    id=None,
                    error={
                        "code": -32700,
                        "message": f"Parse error: {str(e)}"
                    }
                )
                sys.stdout.write(json.dumps(error_response.model_dump()) + '\n')
                sys.stdout.flush()

async def main():
    """主函数"""
    server = WeatherMCPServer()
    await server.run_stdio()

if __name__ == "__main__":
    asyncio.run(main()) 