#!/usr/bin/env python3
"""
MinerU 批量异步并行处理器
真正的并发：多个文件同时上传、处理、下载
完整的进度可视化：总进度 + 单文件进度 + 实时速度
"""
import asyncio
import sys
import time
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich import box
from rich.layout import Layout

from mineru_async import MinerUAsyncClient, FileValidator, ResultProcessor
from niquests import AsyncSession

console = Console()


@dataclass
class FileTask:
    """文件任务"""
    file_path: str
    file_info: Dict
    status: str = 'pending'  # pending/uploading/processing/downloading/done/failed
    batch_id: Optional[str] = None
    result: Optional[Dict] = None
    error: Optional[str] = None
    start_time: float = 0
    end_time: float = 0


class BatchAsyncProcessor:
    """批量异步并行处理器"""
    
    def __init__(self, max_concurrent: int = 5):
        """
        初始化
        
        Args:
            max_concurrent: 最大并发数（建议3-5，避免API限流）
        """
        self.client = MinerUAsyncClient()
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_files_parallel(
        self,
        file_paths: List[str],
        options: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        真正的批量异步并行处理

        多个文件同时：上传、处理、下载

        Args:
            file_paths: 文件路径列表
            options:    传给 upload_file 的统一参数（v4.0.0），如
                        ``{"language": "ch", "is_ocr": True, "extra_formats": ["docx"]}``
        """
        options = options or {}
        console.print(Panel.fit(
            f"[bold cyan]MinerU 批量异步并行处理[/bold cyan]\n"
            f"[dim]并发数: {self.max_concurrent} | 文件数: {len(file_paths)}[/dim]",
            border_style="cyan"
        ))
        
        # 1. 验证所有文件
        console.print("\n[bold]步骤1: 验证文件[/bold]")
        tasks = []
        
        async with AsyncSession() as session:
            for file_path in file_paths:
                if FileValidator.is_url(file_path):
                    is_valid, error, file_info = await FileValidator.validate_url(session, file_path)
                else:
                    is_valid, error, file_info = FileValidator.validate_file(file_path)
                
                if is_valid:
                    task = FileTask(file_path=file_path, file_info=file_info)
                    tasks.append(task)
                    console.print(f"  ✅ {file_info['name']} ({file_info['size']/1024/1024:.1f}MB)")
                else:
                    console.print(f"  ❌ {Path(file_path).name}: {error}")
        
        if not tasks:
            console.print("[red]没有有效的文件[/red]")
            return []
        
        console.print(f"\n[green]✅ {len(tasks)} 个文件验证通过[/green]\n")
        
        # 2. 创建进度显示
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="progress", size=len(tasks) + 5),
            Layout(name="stats", size=8)
        )
        
        # 3. 并行处理所有文件
        console.print("[bold]步骤2: 并行处理（真正异步）[/bold]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold]{task.description}"),
            BarColumn(complete_style="green"),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console,
            expand=True
        ) as progress:
            
            # 总进度
            overall_task = progress.add_task(
                "[cyan]📊 总进度",
                total=len(tasks)
            )
            
            # 为每个文件创建进度任务
            task_ids = {}
            for task in tasks:
                task_id = progress.add_task(
                    f"[blue]⏳ {task.file_info['name'][:40]}",
                    total=100
                )
                task_ids[task.file_path] = task_id
            
            # 并行处理（使用信号量控制并发数）
            async def process_one(task: FileTask):
                async with self.semaphore:
                    task.start_time = time.time()
                    task_id = task_ids[task.file_path]
                    
                    try:
                        # 更新状态：上传中
                        task.status = 'uploading'
                        progress.update(task_id, description=f"[yellow]📤 {task.file_info['name'][:40]}")
                        
                        async with AsyncSession() as session:
                            # 上传 — v4.0.0 全参数透传
                            fmt = task.file_info.get('format', '')
                            upload_options = {
                                'model_version': options.get('model_version', 'vlm'),
                                'enable_formula': options.get('enable_formula', True),
                                'enable_table': options.get('enable_table', True),
                            }
                            for key in ('language', 'is_ocr', 'page_ranges',
                                        'extra_formats', 'data_id'):
                                if options.get(key) is not None:
                                    upload_options[key] = options[key]
                            # 图片自动开 OCR
                            if fmt in ('png', 'jpg', 'jpeg') and 'is_ocr' not in upload_options:
                                upload_options['is_ocr'] = True
                            # HTML / Office 智能切模型
                            if fmt == 'html':
                                upload_options['model_version'] = 'MinerU-HTML'
                            elif fmt not in ('pdf', 'png', 'jpg', 'jpeg') \
                                 and 'model_version' not in options:
                                upload_options['model_version'] = 'pipeline'

                            batch_id = await self.client.upload_file(
                                session, task.file_path, **upload_options
                            )
                            
                            if not batch_id:
                                task.status = 'failed'
                                task.error = '上传失败'
                                progress.update(task_id, completed=100, description=f"[red]❌ {task.file_info['name'][:40]}")
                                return task
                            
                            task.batch_id = batch_id
                            progress.update(task_id, completed=30)
                            
                            # 更新状态：处理中
                            task.status = 'processing'
                            progress.update(task_id, description=f"[cyan]⚙️  {task.file_info['name'][:40]}")
                            
                            # 等待处理
                            results = await self.client.wait_for_completion(session, batch_id, max_wait=300)
                            
                            if not results or len(results) == 0:
                                task.status = 'failed'
                                task.error = '处理失败'
                                progress.update(task_id, completed=100, description=f"[red]❌ {task.file_info['name'][:40]}")
                                return task
                            
                            result = results[0]
                            
                            if result.get('state') != 'done':
                                task.status = 'failed'
                                task.error = result.get('err_msg', '未知错误')
                                progress.update(task_id, completed=100, description=f"[red]❌ {task.file_info['name'][:40]}")
                                return task
                            
                            progress.update(task_id, completed=60)
                            
                            # 更新状态：下载中
                            task.status = 'downloading'
                            progress.update(task_id, description=f"[magenta]📥 {task.file_info['name'][:40]}")
                            
                            # 下载并整理
                            full_zip_url = result.get('full_zip_url')
                            output_path = Path(task.file_path).parent
                            chunk_dir = output_path / f"{Path(task.file_path).stem}_result"
                            chunk_dir.mkdir(exist_ok=True)
                            
                            extracted = await ResultProcessor.download_and_extract(
                                session, full_zip_url, str(chunk_dir)
                            )
                            
                            if not extracted:
                                task.status = 'failed'
                                task.error = '下载失败'
                                progress.update(task_id, completed=100, description=f"[red]❌ {task.file_info['name'][:40]}")
                                return task
                            
                            progress.update(task_id, completed=90)
                            
                            # 整理输出
                            file_name = Path(task.file_path).stem
                            md_file = output_path / f"{file_name}.md"
                            images_dir = output_path / f"{file_name}_images"

                            source_md = ResultProcessor.find_markdown(extracted)
                            if source_md:
                                # 修复图片引用：MinerU 返回的 .md 用 `images/x` 前缀，
                                # 我们把图片复制到 `{file_name}_images/`，所以 .md 里
                                # 也要把 `images/` 改成 `{file_name}_images/`。
                                from path_fixer import rewrite_md_image_refs
                                md_text = Path(source_md).read_text(encoding='utf-8')
                                md_text = rewrite_md_image_refs(md_text, f"{file_name}_images")
                                md_file.write_text(md_text, encoding='utf-8')

                            source_images = Path(extracted) / "images"
                            image_count = 0
                            if source_images.exists():
                                if images_dir.exists():
                                    shutil.rmtree(images_dir)
                                shutil.copytree(source_images, images_dir)
                                image_count = len(list(images_dir.glob("*")))
                            
                            task.status = 'done'
                            task.result = {
                                'markdown': str(md_file),
                                'images': str(images_dir),
                                'image_count': image_count
                            }
                            task.end_time = time.time()
                            
                            progress.update(task_id, completed=100, description=f"[green]✅ {task.file_info['name'][:40]}")
                            progress.update(overall_task, advance=1)
                            
                            return task
                    
                    except Exception as e:
                        task.status = 'failed'
                        task.error = str(e)
                        task.end_time = time.time()
                        progress.update(task_id, completed=100, description=f"[red]❌ {task.file_info['name'][:40]}")
                        progress.update(overall_task, advance=1)
                        return task
            
            # 真正的异步并行处理
            results = await asyncio.gather(*[process_one(task) for task in tasks])
        
        # 4. 显示汇总
        self.show_summary(results)
        
        return results
    
    def show_summary(self, results: List[FileTask]):
        """显示处理汇总"""
        # 统计
        success = [r for r in results if r.status == 'done']
        failed = [r for r in results if r.status == 'failed']
        
        total_time = max((r.end_time - r.start_time for r in results if r.end_time > 0), default=0)
        total_pages = sum(r.file_info.get('pages', 0) for r in success)
        total_images = sum(r.result.get('image_count', 0) for r in success if r.result)
        
        # 结果表格
        result_table = Table(title="[bold cyan]📊 处理结果[/bold cyan]", box=box.ROUNDED)
        result_table.add_column("文件", style="cyan", width=40)
        result_table.add_column("状态", justify="center", width=10)
        result_table.add_column("页数", justify="right", width=8)
        result_table.add_column("图片", justify="right", width=8)
        result_table.add_column("耗时", justify="right", width=10)
        
        for r in results:
            file_name = r.file_info['name'][:37] + "..." if len(r.file_info['name']) > 40 else r.file_info['name']
            
            if r.status == 'done':
                status = "[green]✅[/green]"
                pages = str(r.file_info.get('pages', '-'))
                images = str(r.result.get('image_count', 0)) if r.result else "0"
                elapsed = f"{r.end_time - r.start_time:.1f}s"
            else:
                status = "[red]❌[/red]"
                pages = "-"
                images = "-"
                elapsed = f"{r.end_time - r.start_time:.1f}s" if r.end_time > 0 else "-"
            
            result_table.add_row(file_name, status, pages, images, elapsed)
        
        console.print(result_table)
        
        # 统计信息
        stats_table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
        stats_table.add_column(style="cyan bold", width=15)
        stats_table.add_column(style="white")
        
        stats_table.add_row("📁 总文件数", f"{len(results)}")
        stats_table.add_row("✅ 成功", f"[green]{len(success)}[/green]")
        stats_table.add_row("❌ 失败", f"[red]{len(failed)}[/red]")
        stats_table.add_row("📖 总页数", f"{total_pages}")
        stats_table.add_row("🖼️  总图片", f"{total_images}")
        stats_table.add_row("⏱️  总耗时", f"{total_time:.1f}秒")
        
        if len(success) > 0:
            avg_time = total_time / len(success)
            stats_table.add_row("📊 平均耗时", f"{avg_time:.1f}秒/文件")
            
            if total_pages > 0:
                page_speed = total_pages / total_time
                stats_table.add_row("⚡ 处理速度", f"{page_speed:.1f} 页/秒")
        
        console.print(Panel(stats_table, title="[bold]统计信息[/bold]", border_style="green"))
        
        # 错误详情
        if failed:
            console.print("\n[bold red]❌ 失败文件详情:[/bold red]")
            for r in failed:
                console.print(f"  • [red]{r.file_info['name']}[/red]: {r.error}")


# 使用示例
if __name__ == '__main__':
    if len(sys.argv) < 2:
        console.print("[yellow]用法:[/yellow]")
        console.print("  批量处理: [cyan]python3 mineru_batch_async.py <dir> [pattern][/cyan]")
        console.print("  示例: [cyan]python3 mineru_batch_async.py ~/Downloads '*.pdf'[/cyan]")
        sys.exit(1)
    
    directory = sys.argv[1]
    pattern = sys.argv[2] if len(sys.argv) > 2 else "*.pdf"
    
    # 扫描文件
    dir_path = Path(directory).expanduser()
    files = sorted([str(f) for f in dir_path.glob(pattern)])
    
    if not files:
        console.print(f"[red]未找到匹配的文件: {pattern}[/red]")
        sys.exit(1)
    
    console.print(f"[cyan]找到 {len(files)} 个文件[/cyan]\n")

    # 自动拆分超页 / 超大 PDF（服务端硬限制 200 页 / 200 MB）。
    # 拆分后每片 ≤ 180 页 / 180 MB，留 buffer。
    from auto_split import prepare_files, merge_results
    expanded_files, merge_plans = prepare_files(files)
    if merge_plans:
        console.print(f"[yellow]⚠️ 检测到 {len(merge_plans)} 个文件需要拆分，"
                      f"展开后共 {len(expanded_files)} 个待处理文件[/yellow]\n")

    # 批量处理
    processor = BatchAsyncProcessor(max_concurrent=3)
    results = asyncio.run(processor.process_files_parallel(expanded_files))

    # 处理完成后合并 chunks
    if merge_plans:
        console.print("\n[bold]步骤3: 合并 chunks 输出[/bold]")
        merged = merge_results(merge_plans)
        console.print(f"[green]✅ 合并完成 {len(merged)} 个原始文件[/green]\n")
    
    # 统计
    success_count = sum(1 for r in results if r.status == 'done')
    
    if success_count == len(results):
        console.print("\n[bold green]✅ 所有文件处理成功！[/bold green]")
        sys.exit(0)
    elif success_count > 0:
        console.print(f"\n[yellow]⚠️  部分文件处理成功 ({success_count}/{len(results)})[/yellow]")
        sys.exit(1)
    else:
        console.print("\n[bold red]❌ 所有文件处理失败！[/bold red]")
        sys.exit(1)
