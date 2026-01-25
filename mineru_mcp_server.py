#!/usr/bin/env python3
"""
MinerU MCP Server - 文档处理MCP服务器
提供完整的文档处理能力给AI助手
"""
import asyncio
import json
from pathlib import Path
from typing import Any, Sequence
from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
import mcp.server.stdio

# 导入我们的处理器
import sys
sys.path.append(str(Path(__file__).parent))
from mineru_production import MinerUProcessor, FileValidator

# 创建MCP服务器
app = Server("mineru-processor")

# 全局处理器实例
processor = None


@app.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用工具"""
    return [
        Tool(
            name="process_document",
            description="""处理单个文档，支持本地文件和URL。
            
支持的输入类型：
- 本地文件：/path/to/document.pdf
- 在线PDF：https://example.com/document.pdf
- 在线图片：https://example.com/image.png
- 网页：https://example.com/article.html

支持的格式：PDF, DOC, DOCX, PPT, PPTX, PNG, JPG, JPEG, HTML

自动功能：
- 自动检测输入类型
- 自动选择最佳模型
- 自动拆分大文件（使用page_ranges）
- 自动合并结果""",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "文件路径或URL"
                    },
                    "model_version": {
                        "type": "string",
                        "enum": ["vlm", "pipeline", "MinerU-HTML"],
                        "description": "模型版本（可选，自动选择）"
                    },
                    "enable_formula": {
                        "type": "boolean",
                        "description": "是否识别公式（默认true）"
                    },
                    "enable_table": {
                        "type": "boolean",
                        "description": "是否识别表格（默认true）"
                    },
                    "is_ocr": {
                        "type": "boolean",
                        "description": "是否开启OCR（图片自动开启）"
                    },
                    "language": {
                        "type": "string",
                        "description": "文档语言（ch/en等）"
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "输出目录（默认./output）"
                    }
                },
                "required": ["file_path"]
            }
        ),
        
        Tool(
            name="process_directory",
            description="""批量处理目录下所有文档。
            
功能：
- 自动扫描目录
- 支持文件过滤（*.pdf, *.docx等）
- 支持递归扫描子目录
- 并行处理所有文件
- 汇总处理结果

适用场景：
- 批量转换发票
- 批量处理合同
- 批量识别图片""",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "目录路径"
                    },
                    "file_pattern": {
                        "type": "string",
                        "description": "文件过滤器（如 *.pdf）"
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "是否递归扫描子目录"
                    },
                    "max_workers": {
                        "type": "number",
                        "description": "最大并行度（默认10）"
                    }
                },
                "required": ["directory"]
            }
        ),
        
        Tool(
            name="process_urls",
            description="""批量处理URL列表。
            
功能：
- 批量处理多个URL
- 自动验证URL可访问性
- 并行处理
- 汇总结果

适用场景：
- 批量下载论文
- 批量处理网页
- 批量识别在线图片""",
            inputSchema={
                "type": "object",
                "properties": {
                    "urls": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "URL列表"
                    },
                    "max_workers": {
                        "type": "number",
                        "description": "最大并行度（默认10）"
                    }
                },
                "required": ["urls"]
            }
        ),
        
        Tool(
            name="extract_info",
            description="""从文档中提取结构化信息。
            
支持的提取类型：
- invoice：发票信息（发票号、金额、日期等）
- contract：合同信息（签约方、金额、日期等）
- form：表单信息
- custom：自定义字段

功能：
- 使用KIE技术提取
- 结构化输出
- 支持批量提取""",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "文件路径或URL"
                    },
                    "extract_type": {
                        "type": "string",
                        "enum": ["invoice", "contract", "form", "custom"],
                        "description": "提取类型"
                    },
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "要提取的字段列表（custom类型时必需）"
                    }
                },
                "required": ["file_path", "extract_type"]
            }
        ),
        
        Tool(
            name="get_token_status",
            description="""查询Token状态。
            
功能：
- 查看所有账户Token
- 检查过期状态
- 显示剩余天数""",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """处理工具调用"""
    global processor
    
    try:
        # 初始化处理器（使用绝对路径）
        if processor is None:
            script_dir = Path(__file__).parent
            tokens_file = script_dir / 'all_tokens.json'
            
            if not tokens_file.exists():
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"Token文件不存在: {tokens_file}",
                        "hint": "请先运行: cd /Users/jiasunm/Code/GenAI/MinerU-Token && python3 batch_login.py"
                    }, ensure_ascii=False)
                )]
            
            processor = MinerUProcessor(max_workers=10)
    
    if name == "process_document":
        # 处理单个文档
        file_path = arguments["file_path"]
        options = {k: v for k, v in arguments.items() if k != "file_path"}
        
        result = await processor.process_file(file_path, **options)
        
        if result:
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False)
            )]
        else:
            return [TextContent(
                type="text",
                text=json.dumps({"status": "failed", "error": "处理失败"})
            )]
    
    elif name == "process_directory":
        # 批量处理目录
        directory = arguments["directory"]
        # TODO: 实现目录处理
        return [TextContent(
            type="text",
            text=json.dumps({"status": "todo", "message": "功能开发中"})
        )]
    
    elif name == "process_urls":
        # 批量处理URL
        urls = arguments["urls"]
        # TODO: 实现批量URL处理
        return [TextContent(
            type="text",
            text=json.dumps({"status": "todo", "message": "功能开发中"})
        )]
    
    elif name == "extract_info":
        # 提取结构化信息
        # TODO: 实现KIE提取
        return [TextContent(
            type="text",
            text=json.dumps({"status": "todo", "message": "功能开发中"})
        )]
    
    elif name == "get_token_status":
        # 查询Token状态
        try:
            with open('all_tokens.json', 'r') as f:
                tokens = json.load(f)
            
            status = []
            for email, info in tokens.items():
                status.append({
                    "email": email,
                    "name": info['name'],
                    "token_name": info['token_name'],
                    "expired_at": info['expired_at']
                })
            
            return [TextContent(
                type="text",
                text=json.dumps(status, indent=2, ensure_ascii=False)
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({"error": str(e)})
            )]
    
    return [TextContent(type="text", text=json.dumps({"error": "未知工具"}))]


async def main():
    """运行MCP服务器"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
