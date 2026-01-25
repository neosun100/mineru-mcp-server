#!/usr/bin/env python3
"""
MinerU MCP Server - 文档处理MCP服务器
提供完整的文档处理能力给AI助手
"""
import asyncio
import json
import sys
import traceback
from pathlib import Path
from typing import Any, Sequence

# 添加详细日志
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('/tmp/mineru_mcp_debug.log'),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

logger.info("="*60)
logger.info("MinerU MCP Server 启动")
logger.info("="*60)

try:
    logger.info("步骤1: 导入MCP模块...")
    from mcp.server import Server
    from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
    import mcp.server.stdio
    logger.info("✅ MCP模块导入成功")
except Exception as e:
    logger.error(f"❌ MCP模块导入失败: {e}")
    logger.error(traceback.format_exc())
    sys.exit(1)

# 添加项目路径
logger.info("步骤2: 添加项目路径...")
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))
logger.info(f"✅ 项目路径: {script_dir}")

# 延迟导入mineru_async
logger.info("步骤3: 准备延迟导入mineru_async...")
processor = None

# 创建MCP服务器
logger.info("步骤4: 创建MCP服务器...")
app = Server("mineru-processor")
logger.info("✅ MCP服务器创建成功")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用工具"""
    logger.info("list_tools() 被调用")
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
    
    logger.info(f"call_tool() 被调用: {name}")
    logger.info(f"参数: {arguments}")
    
    try:
        # 延迟导入处理器
        if processor is None:
            logger.info("首次调用，导入处理器...")
            try:
                from mineru_async import MinerUAsyncProcessor
                from mineru_batch_async import BatchAsyncProcessor
                logger.info("✅ 处理器导入成功")
                
                processor = {
                    'single': MinerUAsyncProcessor(max_workers=10),
                    'batch': BatchAsyncProcessor(max_concurrent=3)
                }
                logger.info("✅ 处理器初始化成功")
            except Exception as e:
                logger.error(f"❌ 处理器导入/初始化失败: {e}")
                logger.error(traceback.format_exc())
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"处理器初始化失败: {str(e)}",
                        "traceback": traceback.format_exc()
                    }, ensure_ascii=False)
                )]
        
        if name == "process_document":
            logger.info("处理 process_document 工具调用")
            # 处理单个文档
            file_path = arguments["file_path"]
            logger.info(f"文件路径: {file_path}")
            
            options = {k: v for k, v in arguments.items() if k != "file_path"}
            logger.info(f"选项: {options}")
            
            logger.info("开始处理文件...")
            result = await processor['single'].process_file(file_path, **options)
            logger.info(f"处理结果: {result}")
            
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
            logger.info("处理 process_directory 工具调用")
            # 批量处理目录（使用批量异步并行）
            directory = arguments["directory"]
            pattern = arguments.get("file_pattern", "*.pdf")
            
            logger.info(f"目录: {directory}, 模式: {pattern}")
            
            # 扫描文件
            dir_path = Path(directory).expanduser()
            files = sorted([str(f) for f in dir_path.glob(pattern)])
            
            if not files:
                return [TextContent(
                    type="text",
                    text=json.dumps({"status": "no_files", "message": f"未找到匹配的文件: {pattern}"})
                )]
            
            logger.info(f"找到 {len(files)} 个文件")
            
            # 批量异步并行处理
            results = await processor['batch'].process_files_parallel(files)
            
            # 汇总结果
            summary = {
                "total_files": len(results),
                "success": sum(1 for r in results if r.status == 'done'),
                "failed": sum(1 for r in results if r.status == 'failed'),
                "results": [
                    {
                        "file": r.file_info['name'],
                        "status": r.status,
                        "output": r.result if r.result else None,
                        "error": r.error if r.error else None
                    }
                    for r in results
                ]
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(summary, indent=2, ensure_ascii=False)
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
            logger.info("处理 get_token_status 工具调用")
            # 查询Token状态
            script_dir = Path(__file__).parent
            tokens_file = script_dir / 'all_tokens.json'
            logger.info(f"Token文件路径: {tokens_file}")
            
            with open(tokens_file, 'r') as f:
                tokens = json.load(f)
            
            logger.info(f"读取到 {len(tokens)} 个账户")
            
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
        
        logger.warning(f"未知工具: {name}")
        return [TextContent(type="text", text=json.dumps({"error": "未知工具"}))]
    
    except Exception as e:
        logger.error(f"工具调用异常: {e}")
        logger.error(traceback.format_exc())
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e), "traceback": traceback.format_exc()}, ensure_ascii=False)
        )]


async def main():
    """运行MCP服务器"""
    logger.info("步骤5: 启动MCP服务器...")
    try:
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            logger.info("✅ stdio通道已建立")
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
            logger.info("MCP服务器正常退出")
    except Exception as e:
        logger.error(f"❌ MCP服务器运行失败: {e}")
        logger.error(traceback.format_exc())
        raise


if __name__ == "__main__":
    logger.info("步骤6: 运行主函数...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("收到中断信号，退出")
    except Exception as e:
        logger.error(f"主函数异常: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)
