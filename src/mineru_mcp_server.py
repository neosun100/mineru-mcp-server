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
    level=logging.INFO,
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
            description="""【精准 API】处理单个文档，支持本地文件和URL。

支持的输入类型：
- 本地文件：/path/to/document.pdf
- 在线PDF：https://example.com/document.pdf
- 在线图片：https://example.com/image.png
- 网页：https://example.com/article.html

支持的格式：PDF, DOC, DOCX, PPT, PPTX, PNG, JPG, JPEG, HTML, XLSX

服务端硬限制：单文件 ≤ 200 页 / ≤ 200 MB。
超过会自动拆分（auto_split），并合并 markdown + 图片。

自动功能：
- URL 优先服务端直传（不走本地下载）
- 自动检测输入类型 + 选择最佳模型
- 自动拆分超页文件 + 合并结果""",
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
                        "description": "模型版本（vlm 推荐 / pipeline 通用 / MinerU-HTML 网页专用）"
                    },
                    "enable_formula": {
                        "type": "boolean",
                        "description": "是否识别公式（默认 true，仅 pipeline/vlm 有效）"
                    },
                    "enable_table": {
                        "type": "boolean",
                        "description": "是否识别表格（默认 true，仅 pipeline/vlm 有效）"
                    },
                    "is_ocr": {
                        "type": "boolean",
                        "description": "是否开启 OCR（默认 false；图片自动开启）"
                    },
                    "language": {
                        "type": "string",
                        "description": "文档语言（默认 ch）。可选：ch/en/japan/korean/latin/arabic/cyrillic 等"
                    },
                    "page_ranges": {
                        "type": "string",
                        "description": "页码范围，例 '1-50' 或 '2,4-6,10-20'（逗号分隔）"
                    },
                    "extra_formats": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["docx", "html", "latex"]},
                        "description": "额外导出格式（在默认 markdown+json 之外）"
                    },
                    "data_id": {
                        "type": "string",
                        "description": "业务标识（≤128 字符，便于追溯）"
                    },
                    "no_cache": {
                        "type": "boolean",
                        "description": "URL 模式下是否跳过缓存（默认 false）"
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "输出目录（默认与原文件同目录）"
                    }
                },
                "required": ["file_path"]
            }
        ),
        
        Tool(
            name="process_directory",
            description="""【精准 API】批量处理目录下所有文档（异步并行）。

功能：
- 自动扫描目录（支持 file_pattern 过滤）
- 并行上传 / 解析 / 下载
- 超页 PDF 自动拆分 + 处理后合并

适用场景：批量发票 / 合同 / 文献处理。""",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "目录路径"
                    },
                    "file_pattern": {
                        "type": "string",
                        "description": "文件过滤器（如 *.pdf，默认 *.pdf）"
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "是否递归扫描子目录（暂未实现，默认 false）"
                    },
                    "max_workers": {
                        "type": "number",
                        "description": "最大并行度（默认 3，过高易触发 API 限流）"
                    },
                    "model_version": {
                        "type": "string",
                        "enum": ["vlm", "pipeline", "MinerU-HTML"],
                    },
                    "enable_formula": {"type": "boolean"},
                    "enable_table": {"type": "boolean"},
                    "is_ocr": {"type": "boolean"},
                    "language": {"type": "string"},
                    "extra_formats": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["docx", "html", "latex"]},
                    }
                },
                "required": ["directory"]
            }
        ),

        Tool(
            name="get_token_status",
            description="""查询所有账号 Token 的过期状态、剩余天数、本次进程使用次数。

如果有任意 Token 已过期或即将过期（≤3 天），会标红提示。
建议配合 renew_tokens 工具使用。""",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),

        Tool(
            name="process_document_lite",
            description="""【Agent 轻量 API】处理单个文档（免 Token / IP 限频）。

适用场景：
- 小文档（≤ 10MB / ≤ 20 页）
- 快速预览 / 提取
- 主账号每日 1000 页配额耗尽时的兜底

特点：
- 无需 Token（IP 限频）
- 仅输出 Markdown
- 不支持 HTML
- 文件类型：PDF / 图片 / Doc(x) / PPT(x) / Excel""",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "文件路径或URL"
                    },
                    "language": {"type": "string", "description": "默认 ch"},
                    "page_range": {
                        "type": "string",
                        "description": "页码范围，例 '1-10' 或 '5'（不支持逗号分隔）"
                    },
                    "enable_table": {"type": "boolean"},
                    "is_ocr": {"type": "boolean"},
                    "enable_formula": {"type": "boolean"}
                },
                "required": ["file_path"]
            }
        ),

        Tool(
            name="query_task_status",
            description="""查询已提交任务的实时状态（v4 单任务接口）。

适用场景：
- 用 process_document 提交后想异步查询进度
- 长任务跑过程中检查 extracted_pages / total_pages

输入需要 task_id（精准 API）或 lite=true 时传 lite_task_id（轻量 API）。""",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "任务 ID（精准 API 返回的 task_id）"},
                    "lite": {"type": "boolean", "description": "是否查询轻量 API 任务（默认 false）"}
                },
                "required": ["task_id"]
            }
        ),

        Tool(
            name="renew_tokens",
            description="""触发 Token 自动续期（headless 批量登录）。

适用场景：
- get_token_status 显示有 Token 过期 / 即将过期
- 处理报 A0211（Token 过期）

行为：调用 src/batch_login.py，默认 headless 模式自动登录所有账号刷新 Token。
完成后 Token 文件会被覆盖写入。""",
            inputSchema={
                "type": "object",
                "properties": {
                    "force": {
                        "type": "boolean",
                        "description": "强制全部续期（默认 false，仅过期或即将过期才续）"
                    },
                    "headless": {
                        "type": "boolean",
                        "description": "无 UI 模式（默认 true，调试时可设 false）"
                    }
                }
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """处理工具调用"""
    global processor
    
    logger.info(f"call_tool() 被调用: {name}")
    logger.info(f"参数: {arguments}")
    
    # 创建 MCP 进度通知回调
    async def mcp_progress_callback(progress: float, total: float, message: str):
        try:
            ctx = app.request_context
            if ctx.meta and ctx.meta.progressToken is not None:
                await ctx.session.send_progress_notification(
                    progress_token=ctx.meta.progressToken,
                    progress=progress,
                    total=total,
                    message=message
                )
        except Exception as e:
            logger.debug(f"进度通知发送失败(可忽略): {e}")
    
    try:
        # v4.0.0 Token 检查 + 自动续期（处理文档前）
        if name in ("process_document", "process_directory"):
            from token_manager import get_default_manager
            mgr = get_default_manager()

            if not mgr.all_tokens():
                return [TextContent(type="text", text=json.dumps({
                    "status": "no_tokens",
                    "message": "未找到 Token，请先执行: .venv/bin/python3 src/batch_login.py",
                }, ensure_ascii=False))]

            if mgr.has_expired():
                logger.info("检测到 Token 已过期，尝试自动续期…")
                ok, summary = mgr.renew_all()
                if not ok:
                    return [TextContent(type="text", text=json.dumps({
                        "status": "token_expired_renew_failed",
                        "message": "Token 已过期且自动续期失败，请手动跑 src/batch_login.py",
                        "renew_summary": summary[-500:],  # 只取最后 500 字符避免太长
                    }, ensure_ascii=False))]
                logger.info("Token 自动续期成功")

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
            # 处理单个文档（自动处理超大文件 / 超页文件）
            file_path = arguments["file_path"]
            logger.info(f"文件路径: {file_path}")
            
            options = {k: v for k, v in arguments.items() if k != "file_path"}
            logger.info(f"选项: {options}")
            
            # 检查文件大小
            if not file_path.startswith(('http://', 'https://')):
                file_size = Path(file_path).stat().st_size / 1024 / 1024
                logger.info(f"文件大小: {file_size:.1f}MB")
                
                if file_size > 200:
                    logger.info("文件超过200MB，需要拆分处理")
                    
                    # 获取项目根目录
                    project_root = Path(__file__).parent.parent
                    venv_python = project_root / '.venv' / 'bin' / 'python3'
                    
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "status": "large_file",
                            "file_size_mb": round(file_size, 1),
                            "error": f"文件超过200MB限制 ({file_size:.1f}MB)",
                            "suggestion": "请使用命令行工具处理超大文件",
                            "command": f"cd {project_root} && {venv_python} tools/test_large_file_complete.py \"{file_path}\"",
                            "project_path": str(project_root)
                        }, ensure_ascii=False)
                    )]

                # 检测超页 PDF：自动走拆分+批量+合并流程
                if file_path.lower().endswith('.pdf'):
                    try:
                        from PyPDF2 import PdfReader
                        pages = len(PdfReader(file_path).pages)
                    except Exception:
                        pages = 0
                    if pages > 200:  # 服务端硬限制
                        logger.info(f"PDF 有 {pages} 页，超过 200 页限制，自动拆分处理")
                        from auto_split import prepare_files, merge_results
                        expanded_files, merge_plans = prepare_files([file_path])
                        results = await processor['batch'].process_files_parallel(expanded_files)
                        merged = merge_results(merge_plans) if merge_plans else []
                        if merged:
                            return [TextContent(
                                type="text",
                                text=json.dumps({
                                    "status": "ok",
                                    "source": file_path,
                                    "pages": pages,
                                    "n_parts": merged[0]["n_parts"],
                                    "output": {
                                        "markdown": merged[0]["markdown"],
                                        "images": merged[0]["images"],
                                        "image_count": merged[0]["image_count"],
                                    },
                                }, indent=2, ensure_ascii=False)
                            )]
                        return [TextContent(
                            type="text",
                            text=json.dumps({"status": "failed", "error": "拆分后处理仍失败"}, ensure_ascii=False)
                        )]
            
            logger.info("开始处理文件...")
            result = await processor['single'].process_file(file_path, progress_callback=mcp_progress_callback, **options)
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
            max_workers = arguments.get("max_workers")

            # 提取处理参数（v4.0.0 全参数透传）
            opt_keys = ('model_version', 'enable_formula', 'enable_table',
                        'is_ocr', 'language', 'extra_formats', 'data_id',
                        'page_ranges')
            batch_options = {k: arguments[k] for k in opt_keys if k in arguments}

            logger.info(f"目录: {directory}, 模式: {pattern}, options: {batch_options}")

            # 扫描文件
            dir_path = Path(directory).expanduser()
            files = sorted([str(f) for f in dir_path.glob(pattern)])

            if not files:
                return [TextContent(
                    type="text",
                    text=json.dumps({"status": "no_files", "message": f"未找到匹配的文件: {pattern}"})
                )]

            logger.info(f"找到 {len(files)} 个文件")

            # 自动拆分超页 / 超大 PDF（服务端硬限制 200 页 / 200 MB）
            from auto_split import prepare_files, merge_results
            expanded_files, merge_plans = prepare_files(files)
            if merge_plans:
                logger.info(
                    f"检测到 {len(merge_plans)} 个文件需拆分，"
                    f"展开后共 {len(expanded_files)} 个待处理文件"
                )

            # 如果用户指定 max_workers，临时覆盖 processor 的 semaphore
            batch_processor = processor['batch']
            if max_workers and isinstance(max_workers, (int, float)):
                import asyncio as _asyncio
                batch_processor.max_concurrent = int(max_workers)
                batch_processor.semaphore = _asyncio.Semaphore(int(max_workers))

            # 批量异步并行处理（v4.0.0 透传 options）
            results = await batch_processor.process_files_parallel(
                expanded_files, options=batch_options,
            )

            # 处理完成后合并 chunks
            merged_files = []
            if merge_plans:
                logger.info("合并 chunks 输出...")
                merged_files = merge_results(merge_plans)
            
            # 汇总结果
            summary = {
                "total_files": len(results),
                "success": sum(1 for r in results if r.status == 'done'),
                "failed": sum(1 for r in results if r.status == 'failed'),
                "merged_originals": merged_files,
                "options_used": batch_options,
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
        
        elif name == "get_token_status":
            logger.info("处理 get_token_status 工具调用")
            # v4.0.0: 用 TokenManager 替代手工解析
            from token_manager import get_default_manager
            mgr = get_default_manager()
            mgr.reload()  # 确保最新

            status = mgr.status_report()
            summary = {
                "total": len(status),
                "expired": sum(1 for s in status if s["days_remaining"] < 0),
                "expiring_soon": sum(1 for s in status if 0 <= s["days_remaining"] <= 3),
                "tokens": status,
                "needs_renewal": mgr.has_expired() or mgr.has_expiring_soon(),
            }
            return [TextContent(
                type="text",
                text=json.dumps(summary, indent=2, ensure_ascii=False)
            )]

        elif name == "process_document_lite":
            logger.info("处理 process_document_lite（Agent 轻量 API）")
            from agent_api import AgentAPIClient, can_use_lite_api, AgentParseError

            file_path = arguments["file_path"]
            opts = {k: v for k, v in arguments.items() if k != "file_path"}

            # URL 直接走，本地文件先做能力检查
            is_url = file_path.startswith(("http://", "https://"))
            if not is_url:
                ok, reason = can_use_lite_api(file_path)
                if not ok:
                    return [TextContent(type="text", text=json.dumps({
                        "status": "rejected",
                        "reason": reason,
                        "suggestion": "用 process_document（精准 API）",
                    }, ensure_ascii=False))]

            client = AgentAPIClient()
            try:
                if is_url:
                    result = await client.parse_url(file_path, **opts)
                else:
                    result = await client.parse_file(file_path, **opts)
            except AgentParseError as e:
                return [TextContent(type="text", text=json.dumps({
                    "status": "failed",
                    "error_code": e.code,
                    "error_message": str(e),
                    "task_id": e.task_id,
                }, ensure_ascii=False))]

            return [TextContent(type="text", text=json.dumps({
                "status": "ok",
                "task_id": result.task_id,
                "markdown_url": result.markdown_url,
                "markdown_text": result.markdown_text,
                "elapsed_seconds": round(result.elapsed_seconds, 1),
            }, indent=2, ensure_ascii=False))]

        elif name == "query_task_status":
            logger.info("处理 query_task_status")
            task_id = arguments["task_id"]
            lite = arguments.get("lite", False)

            from niquests import AsyncSession
            async with AsyncSession() as session:
                if lite:
                    from agent_api import AgentAPIClient
                    data = await AgentAPIClient(session).query(task_id)
                else:
                    data = await processor['client'].get_task_result(session, task_id) \
                        if 'client' in processor else None
                    if data is None:
                        # 兼容：通过 single processor 的内部 client 拿
                        data = await processor['single'].client.get_task_result(session, task_id)

            if not data:
                return [TextContent(type="text", text=json.dumps({
                    "status": "not_found",
                    "task_id": task_id,
                }, ensure_ascii=False))]

            return [TextContent(type="text", text=json.dumps({
                "status": "ok",
                "task_id": task_id,
                "lite": lite,
                "data": data,
            }, indent=2, ensure_ascii=False))]

        elif name == "renew_tokens":
            logger.info("处理 renew_tokens")
            from token_manager import get_default_manager
            mgr = get_default_manager()
            force = arguments.get("force", False)
            headless = arguments.get("headless", True)

            if force:
                ok, summary = mgr.renew_all(headless=headless)
            else:
                ok, summary = mgr.renew_if_needed()

            mgr.reload()
            return [TextContent(type="text", text=json.dumps({
                "status": "ok" if ok else "failed",
                "force": force,
                "headless": headless,
                "summary": summary,
                "tokens_after": mgr.status_report(),
            }, indent=2, ensure_ascii=False))]
        
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
