#!/usr/bin/env python3
"""
日志查看器
用于格式化显示和分析 OpenAI API 代理和 MCP 服务器的交互日志
"""

import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import sys


class LogViewer:
    def __init__(self):
        self.openai_log = "openai_interactions.jsonl"
        self.mcp_log = "mcp_interactions.jsonl"
    
    def format_timestamp(self, timestamp_str: str) -> str:
        """格式化时间戳"""
        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.strftime('%H:%M:%S.%f')[:-3]  # 显示毫秒
        except:
            return timestamp_str
    
    def format_json(self, data: Any, indent: int = 2) -> str:
        """格式化 JSON 数据"""
        return json.dumps(data, ensure_ascii=False, indent=indent)
    
    def truncate_text(self, text: str, max_length: int = 100) -> str:
        """截断长文本"""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."
    
    def view_openai_logs(self, lines: int = 10, detailed: bool = False):
        """查看 OpenAI API 交互日志"""
        if not Path(self.openai_log).exists():
            print(f"❌ 日志文件 {self.openai_log} 不存在")
            return
        
        print(f"📡 OpenAI API 交互日志 (最近 {lines} 条)")
        print("=" * 80)
        
        with open(self.openai_log, 'r', encoding='utf-8') as f:
            log_lines = f.readlines()
        
        recent_logs = log_lines[-lines:] if len(log_lines) > lines else log_lines
        
        for i, line in enumerate(recent_logs):
            try:
                log_data = json.loads(line.strip())
                self.display_openai_interaction(log_data, i + 1, detailed)
                print("-" * 80)
            except json.JSONDecodeError:
                print(f"❌ 无法解析第 {i+1} 行日志")
    
    def display_openai_interaction(self, log_data: Dict[str, Any], index: int, detailed: bool):
        """显示单个 OpenAI API 交互"""
        request = log_data.get('request', {})
        response = log_data.get('response', {})
        error = log_data.get('error', {})
        
        print(f"🔄 交互 #{index}")
        
        # 请求信息
        if request:
            timestamp = self.format_timestamp(request.get('timestamp', ''))
            method = request.get('method', 'N/A')
            url = request.get('url', 'N/A')
            client_ip = request.get('client_ip', 'N/A')
            
            print(f"📤 请求 [{timestamp}]")
            print(f"   方法: {method}")
            print(f"   URL: {url}")
            print(f"   客户端: {client_ip}")
            
            if detailed and 'body' in request:
                body = request['body']
                if isinstance(body, dict):
                    model = body.get('model', 'N/A')
                    messages_count = len(body.get('messages', []))
                    print(f"   模型: {model}")
                    print(f"   消息数: {messages_count}")
                    
                    if 'messages' in body and body['messages']:
                        print(f"   最后消息: {self.truncate_text(str(body['messages'][-1]))}")
                else:
                    print(f"   请求体: {self.truncate_text(str(body))}")
        
        # 响应信息
        if response:
            timestamp = self.format_timestamp(response.get('timestamp', ''))
            status_code = response.get('status_code', 'N/A')
            response_time = response.get('response_time_seconds', 0)
            
            print(f"📥 响应 [{timestamp}]")
            print(f"   状态码: {status_code}")
            print(f"   响应时间: {response_time:.3f}s")
            
            if detailed and 'body' in response:
                body = response['body']
                if isinstance(body, dict):
                    if 'choices' in body and body['choices']:
                        choice = body['choices'][0]
                        message = choice.get('message', {})
                        content = message.get('content', '')
                        print(f"   响应内容: {self.truncate_text(content)}")
                    
                    if 'usage' in body:
                        usage = body['usage']
                        print(f"   Token 使用: {usage}")
                else:
                    print(f"   响应体: {self.truncate_text(str(body))}")
        
        # 错误信息
        if error:
            timestamp = self.format_timestamp(error.get('timestamp', ''))
            error_msg = error.get('error', 'N/A')
            print(f"❌ 错误 [{timestamp}]")
            print(f"   错误信息: {error_msg}")
    
    def view_mcp_logs(self, lines: int = 10, detailed: bool = False):
        """查看 MCP 交互日志"""
        if not Path(self.mcp_log).exists():
            print(f"❌ 日志文件 {self.mcp_log} 不存在")
            return
        
        print(f"🔧 MCP 交互日志 (最近 {lines} 条)")
        print("=" * 80)
        
        with open(self.mcp_log, 'r', encoding='utf-8') as f:
            log_lines = f.readlines()
        
        recent_logs = log_lines[-lines:] if len(log_lines) > lines else log_lines
        
        for i, line in enumerate(recent_logs):
            try:
                log_data = json.loads(line.strip())
                self.display_mcp_interaction(log_data, i + 1, detailed)
                print("-" * 80)
            except json.JSONDecodeError:
                print(f"❌ 无法解析第 {i+1} 行日志")
    
    def display_mcp_interaction(self, log_data: Dict[str, Any], index: int, detailed: bool):
        """显示单个 MCP 交互"""
        timestamp = self.format_timestamp(log_data.get('timestamp', ''))
        interaction_type = log_data.get('type', 'N/A')
        data = log_data.get('data', {})
        
        print(f"🔄 MCP 交互 #{index} [{timestamp}]")
        print(f"   类型: {interaction_type}")
        
        if interaction_type == "call_tool":
            tool_name = data.get('tool_name', 'N/A')
            arguments = data.get('arguments', {})
            print(f"   🛠️ 工具调用: {tool_name}")
            if detailed:
                print(f"   参数: {self.format_json(arguments)}")
            else:
                print(f"   参数: {self.truncate_text(str(arguments))}")
        
        elif interaction_type == "read_resource":
            uri = data.get('uri', 'N/A')
            print(f"   📄 资源读取: {uri}")
        
        elif interaction_type == "get_prompt":
            prompt_name = data.get('prompt_name', 'N/A')
            arguments = data.get('arguments', {})
            print(f"   💬 提示模板: {prompt_name}")
            if detailed and arguments:
                print(f"   参数: {self.format_json(arguments)}")
        
        elif interaction_type in ["list_tools", "list_resources", "list_prompts"]:
            action = data.get('action', 'N/A')
            print(f"   📋 列表操作: {action}")
        
        else:
            if detailed:
                print(f"   数据: {self.format_json(data)}")
            else:
                print(f"   数据: {self.truncate_text(str(data))}")
    
    def analyze_openai_stats(self):
        """分析 OpenAI API 使用统计"""
        if not Path(self.openai_log).exists():
            print(f"❌ 日志文件 {self.openai_log} 不存在")
            return
        
        print("📊 OpenAI API 使用统计")
        print("=" * 50)
        
        total_requests = 0
        total_tokens = 0
        models_used = {}
        status_codes = {}
        response_times = []
        
        with open(self.openai_log, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    log_data = json.loads(line.strip())
                    request = log_data.get('request', {})
                    response = log_data.get('response', {})
                    
                    if request:
                        total_requests += 1
                        
                        # 统计模型使用
                        body = request.get('body', {})
                        if isinstance(body, dict) and 'model' in body:
                            model = body['model']
                            models_used[model] = models_used.get(model, 0) + 1
                    
                    if response:
                        # 统计状态码
                        status = response.get('status_code', 'N/A')
                        status_codes[status] = status_codes.get(status, 0) + 1
                        
                        # 统计响应时间
                        response_time = response.get('response_time_seconds', 0)
                        if response_time > 0:
                            response_times.append(response_time)
                        
                        # 统计 Token 使用
                        body = response.get('body', {})
                        if isinstance(body, dict) and 'usage' in body:
                            usage = body['usage']
                            total_tokens += usage.get('total_tokens', 0)
                
                except json.JSONDecodeError:
                    continue
        
        print(f"总请求数: {total_requests}")
        print(f"总 Token 数: {total_tokens}")
        
        if models_used:
            print(f"\n使用的模型:")
            for model, count in models_used.items():
                print(f"  • {model}: {count} 次")
        
        if status_codes:
            print(f"\n状态码分布:")
            for code, count in status_codes.items():
                print(f"  • {code}: {count} 次")
        
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            print(f"\n响应时间统计:")
            print(f"  • 平均: {avg_time:.3f}s")
            print(f"  • 最快: {min_time:.3f}s")
            print(f"  • 最慢: {max_time:.3f}s")
    
    def analyze_mcp_stats(self):
        """分析 MCP 使用统计"""
        if not Path(self.mcp_log).exists():
            print(f"❌ 日志文件 {self.mcp_log} 不存在")
            return
        
        print("📊 MCP 使用统计")
        print("=" * 50)
        
        interaction_types = {}
        tools_used = {}
        resources_accessed = {}
        prompts_used = {}
        
        with open(self.mcp_log, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    log_data = json.loads(line.strip())
                    interaction_type = log_data.get('type', 'N/A')
                    data = log_data.get('data', {})
                    
                    # 统计交互类型
                    interaction_types[interaction_type] = interaction_types.get(interaction_type, 0) + 1
                    
                    # 统计工具使用
                    if interaction_type == "call_tool":
                        tool_name = data.get('tool_name', 'N/A')
                        tools_used[tool_name] = tools_used.get(tool_name, 0) + 1
                    
                    # 统计资源访问
                    elif interaction_type == "read_resource":
                        uri = data.get('uri', 'N/A')
                        resources_accessed[uri] = resources_accessed.get(uri, 0) + 1
                    
                    # 统计提示模板使用
                    elif interaction_type == "get_prompt":
                        prompt_name = data.get('prompt_name', 'N/A')
                        prompts_used[prompt_name] = prompts_used.get(prompt_name, 0) + 1
                
                except json.JSONDecodeError:
                    continue
        
        print(f"交互类型分布:")
        for itype, count in interaction_types.items():
            print(f"  • {itype}: {count} 次")
        
        if tools_used:
            print(f"\n工具使用统计:")
            for tool, count in tools_used.items():
                print(f"  • {tool}: {count} 次")
        
        if resources_accessed:
            print(f"\n资源访问统计:")
            for resource, count in resources_accessed.items():
                print(f"  • {resource}: {count} 次")
        
        if prompts_used:
            print(f"\n提示模板使用统计:")
            for prompt, count in prompts_used.items():
                print(f"  • {prompt}: {count} 次")


def main():
    parser = argparse.ArgumentParser(description='查看和分析交互日志')
    parser.add_argument('--type', choices=['openai', 'mcp', 'both'], default='both',
                       help='日志类型: openai(API日志), mcp(MCP日志), both(两种日志)')
    parser.add_argument('--lines', type=int, default=10, help='显示最近的行数')
    parser.add_argument('--detailed', action='store_true', help='显示详细信息')
    parser.add_argument('--stats', action='store_true', help='显示统计信息')
    parser.add_argument('--openai-log', default='openai_interactions.jsonl', help='OpenAI日志文件路径')
    parser.add_argument('--mcp-log', default='mcp_interactions.jsonl', help='MCP日志文件路径')
    
    args = parser.parse_args()
    
    viewer = LogViewer()
    viewer.openai_log = args.openai_log
    viewer.mcp_log = args.mcp_log
    
    if args.stats:
        if args.type in ['openai', 'both']:
            viewer.analyze_openai_stats()
            print()
        
        if args.type in ['mcp', 'both']:
            viewer.analyze_mcp_stats()
    else:
        if args.type in ['openai', 'both']:
            viewer.view_openai_logs(args.lines, args.detailed)
            print()
        
        if args.type in ['mcp', 'both']:
            viewer.view_mcp_logs(args.lines, args.detailed)


if __name__ == "__main__":
    main() 