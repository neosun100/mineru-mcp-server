#!/usr/bin/env python3
"""
MinerU Rich UI 增强版 - 完整的可视化界面
包含：详细进度、实时速度、错误详情、批量处理
"""
import asyncio
import sys
import time
import shutil
import zipfile
from pathlib import Path
from typing import Optional, Dict, List

sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.progress import (
    Progress, SpinnerColumn, TextColumn, BarColumn, 
    TaskProgressColumn, TimeRemainingColumn, TransferSpeedColumn,
    DownloadColumn
)
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich import box

from mineru_async import MinerUAsyncClient, FileValidator, ResultProcessor

console = Console()


class RichProgressTracker:
    """Rich进度跟踪器"""
    
    def __init__(self):
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(complete_style="green", finished_style="bold green"),
            TaskProgressColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console,
            expand=True
        )
        self.tasks = {}
    
    def add_task(self, name: str, total: int = 100) -> int:
        """添加任务"""
        task_id = self.progress.add_task(name, total=total)
        self.tasks[name] = task_id
        return task_id
    
    def update(self, name: str, advance: int = None, completed: int = None, description: str = None):
        """更新任务"""
        if name in self.tasks:
            kwargs = {}
            if advance is not None:
                kwargs['advance'] = advance
            if completed is not None:
                kwargs['completed'] = completed
            if description is not None:
                kwargs['description'] = description
            
            self.progress.update(self.tasks[name], **kwargs)
    
    def remove_task(self, name: str):
        """移除任务"""
        if name in self.tasks:
            self.progress.remove_task(self.tasks[name])
            del self.tasks[name]


class EnhancedRichProcessor:
    """增强的Rich UI处理器"""
    
    def __init__(self):
        self.client = MinerUAsyncClient()
        self.stats = {
            'total_files': 0,
            'success': 0,
            'failed': 0,
            'total_pages': 0,
            'total_images': 0,
            'total_time': 0,
            'errors': []
        }
    
    def show_header(self):
        """显示标题"""
        console.print(Panel.fit(
            "[bold cyan]MinerU 文档处理系统[/bold cyan]\n"
            "[dim]支持 PDF/PPTX/DOCX/图片 | 真正异步并发 | 智能拆分合并[/dim]",
            border_style="cyan",
            padding=(1, 2)
        ))
    
    def show_file_info(self, file_info: Dict):
        """显示文件信息"""
        info_table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
        info_table.add_column(style="cyan bold", width=12)
        info_table.add_column(style="white")
        
        info_table.add_row("📄 文件", file_info['name'])
        info_table.add_row("📋 格式", file_info['format'].upper())
        info_table.add_row("💾 大小", f"{file_info['size']/1024/1024:.2f} MB")
        
        if file_info.get('pages'):
            info_table.add_row("📖 页数", f"{file_info['pages']} 页")
            
            # 判断是否需要拆分
            if file_info['size'] > 200 * 1024 * 1024:
                info_table.add_row("⚠️  提示", "[yellow]文件超过200MB，将自动拆分[/yellow]")
            elif file_info['pages'] > 600:
                info_table.add_row("⚠️  提示", "[yellow]页数超过600页，将使用page_ranges[/yellow]")
        
        console.print(Panel(info_table, title="[bold]文件信息[/bold]", border_style="blue"))
    
    async def process_file_enhanced(self, file_path: str, **options) -> Optional[Dict]:
        """处理文件（增强版）"""
        import logging
        logger = logging.getLogger(__name__)
        
        self.show_header()
        
        start_time = time.time()
        
        try:
            # 1. 验证文件
            with console.status("[bold green]🔍 验证文件中...") as status:
                from niquests import AsyncSession
                
                async with AsyncSession() as session:
                    if FileValidator.is_url(file_path):
                        is_valid, error, file_info = await FileValidator.validate_url(session, file_path)
                    else:
                        is_valid, error, file_info = FileValidator.validate_file(file_path)
                
                if not is_valid:
                    console.print(f"[bold red]❌ 验证失败: {error}[/bold red]")
                    self.stats['errors'].append({'stage': '验证', 'error': error})
                    return None
            
            self.show_file_info(file_info)
            
            # 2. 处理文件（带详细进度）
            progress = Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(complete_style="green"),
                TaskProgressColumn(),
                DownloadColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
                console=console,
                expand=True
            )
            
            with progress:
                # 创建主任务
                main_task = progress.add_task(
                    "[cyan]📤 上传文件",
                    total=file_info['size']
                )
                
                async with AsyncSession() as session:
                    if not file_info['is_url']:
                        # 上传
                        upload_options = {
                            'model_version': options.get('model_version', 'vlm'),
                            'enable_formula': options.get('enable_formula', True),
                            'enable_table': options.get('enable_table', True)
                        }
                        
                        if file_info['format'] == 'html':
                            upload_options['model_version'] = 'MinerU-HTML'
                        
                        batch_id = await self.client.upload_file(session, file_path, **upload_options)
                        
                        if not batch_id:
                            console.print("[bold red]❌ 上传失败[/bold red]")
                            self.stats['errors'].append({'stage': '上传', 'error': '上传失败'})
                            return None
                        
                        progress.update(main_task, completed=file_info['size'], description="[green]✅ 上传完成")
                        
                        # 处理任务
                        process_task = progress.add_task(
                            "[cyan]⚙️  处理中",
                            total=file_info.get('pages', 100)
                        )
                        
                        # 等待处理（带进度更新）
                        results = await self._wait_with_progress(
                            session, batch_id, progress, process_task
                        )
                        
                        if not results or len(results) == 0:
                            console.print("[bold red]❌ 处理失败[/bold red]")
                            self.stats['errors'].append({'stage': '处理', 'error': '处理失败'})
                            return None
                        
                        result = results[0]
                        
                        if result.get('state') != 'done':
                            error_msg = result.get('err_msg', '未知错误')
                            console.print(f"[bold red]❌ 处理失败: {error_msg}[/bold red]")
                            self.stats['errors'].append({'stage': '处理', 'error': error_msg})
                            return None
                        
                        full_zip_url = result.get('full_zip_url')
                        progress.update(process_task, completed=file_info.get('pages', 100), description="[green]✅ 处理完成")
                        
                        # 下载任务
                        download_task = progress.add_task(
                            "[cyan]📥 下载结果",
                            total=100
                        )
                        
                        # 下载并解压
                        output_path = Path(file_path).parent
                        chunk_dir = output_path / f"{Path(file_path).stem}_result"
                        chunk_dir.mkdir(exist_ok=True)
                        
                        extracted = await ResultProcessor.download_and_extract(
                            session, full_zip_url, str(chunk_dir)
                        )
                        
                        if not extracted:
                            console.print("[bold red]❌ 下载失败[/bold red]")
                            self.stats['errors'].append({'stage': '下载', 'error': '下载失败'})
                            return None
                        
                        progress.update(download_task, completed=100, description="[green]✅ 下载完成")
                        
                        # 整理输出
                        file_name = Path(file_path).stem
                        md_file = output_path / f"{file_name}.md"
                        images_dir = output_path / f"{file_name}_images"
                        
                        source_md = ResultProcessor.find_markdown(extracted)
                        if source_md:
                            shutil.copy(source_md, md_file)
                        
                        source_images = Path(extracted) / "images"
                        if source_images.exists():
                            if images_dir.exists():
                                shutil.rmtree(images_dir)
                            shutil.copytree(source_images, images_dir)
                            image_count = len(list(images_dir.glob("*")))
                            self.stats['total_images'] += image_count
                        else:
                            image_count = 0
                        
                        self.stats['total_pages'] += file_info.get('pages', 0)
                        
                        elapsed = time.time() - start_time
                        self.stats['total_time'] += elapsed
                        
                        # 显示结果
                        self.show_result(md_file, images_dir, image_count, elapsed)
                        
                        return {
                            'source': file_path,
                            'source_type': 'file',
                            'output': {
                                'markdown': str(md_file),
                                'images': str(images_dir) if images_dir.exists() else None
                            },
                            'stats': {
                                'pages': file_info.get('pages', 0),
                                'images': image_count,
                                'time': elapsed
                            }
                        }
                    else:
                        console.print("[yellow]URL处理暂未实现[/yellow]")
                        return None
        
        except Exception as e:
            console.print(f"[bold red]❌ 异常: {e}[/bold red]")
            self.stats['errors'].append({'stage': '未知', 'error': str(e)})
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
            return None
    
    async def _wait_with_progress(self, session, batch_id, progress, task_id):
        """等待处理完成（带进度更新）"""
        start_time = time.time()
        max_wait = 600
        
        while time.time() - start_time < max_wait:
            results = await self.client.get_batch_result(session, batch_id)
            
            if results:
                all_done = True
                for result in results:
                    state = result.get('state')
                    
                    if state == 'failed':
                        return None
                    elif state in ['pending', 'running', 'waiting-file', 'converting']:
                        all_done = False
                        if state == 'running':
                            prog = result.get('extract_progress', {})
                            extracted = prog.get('extracted_pages', 0)
                            total = prog.get('total_pages', 0)
                            if total > 0:
                                progress.update(task_id, completed=extracted, total=total)
                
                if all_done:
                    return results
            
            await asyncio.sleep(2)
        
        return None
    
    def show_result(self, md_file, images_dir, image_count, elapsed):
        """显示处理结果"""
        result_table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
        result_table.add_column(style="green bold", width=12)
        result_table.add_column(style="white")
        
        result_table.add_row("✅ Markdown", str(md_file))
        result_table.add_row("✅ 图片", f"{images_dir} ({image_count}个)")
        result_table.add_row("⏱️  耗时", f"{elapsed:.1f}秒")
        
        if elapsed > 0 and image_count > 0:
            speed = image_count / elapsed
            result_table.add_row("⚡ 速度", f"{speed:.1f} 图片/秒")
        
        console.print(Panel(result_table, title="[bold green]处理完成[/bold green]", border_style="green"))
    
    async def process_directory_enhanced(self, directory: str, pattern: str = "*.pdf"):
        """批量处理目录（增强版）"""
        self.show_header()
        
        # 扫描文件
        dir_path = Path(directory).expanduser()
        files = sorted(list(dir_path.glob(pattern)))
        
        if not files:
            console.print(f"[yellow]未找到匹配的文件: {pattern}[/yellow]")
            return
        
        console.print(f"[cyan]📁 找到 {len(files)} 个文件[/cyan]\n")
        
        self.stats['total_files'] = len(files)
        batch_start_time = time.time()
        
        # 创建进度显示
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(complete_style="green"),
            TaskProgressColumn(),
            TextColumn("({task.completed}/{task.total})"),
            TimeRemainingColumn(),
            console=console,
            expand=True
        ) as progress:
            
            overall_task = progress.add_task(
                "[cyan]📊 总进度",
                total=len(files)
            )
            
            results = []
            
            for i, file in enumerate(files, 1):
                file_task = progress.add_task(
                    f"[blue]📄 {file.name[:40]}...",
                    total=100
                )
                
                try:
                    file_start = time.time()
                    result = await self.process_file_silent(str(file))
                    file_elapsed = time.time() - file_start
                    
                    if result:
                        self.stats['success'] += 1
                        results.append({
                            'file': file.name,
                            'status': 'success',
                            'time': file_elapsed,
                            'result': result
                        })
                        progress.update(
                            file_task,
                            completed=100,
                            description=f"[green]✅ {file.name[:40]}"
                        )
                    else:
                        self.stats['failed'] += 1
                        results.append({
                            'file': file.name,
                            'status': 'failed',
                            'time': file_elapsed
                        })
                        progress.update(
                            file_task,
                            completed=100,
                            description=f"[red]❌ {file.name[:40]}"
                        )
                
                except Exception as e:
                    self.stats['failed'] += 1
                    self.stats['errors'].append({
                        'file': file.name,
                        'error': str(e)
                    })
                    results.append({
                        'file': file.name,
                        'status': 'error',
                        'error': str(e)
                    })
                    progress.update(
                        file_task,
                        completed=100,
                        description=f"[red]❌ {file.name[:40]}"
                    )
                
                progress.update(overall_task, advance=1)
                progress.remove_task(file_task)
                
                # 短暂延迟，避免API限流
                await asyncio.sleep(1)
        
        batch_elapsed = time.time() - batch_start_time
        
        # 显示汇总
        self.show_batch_summary(results, batch_elapsed)
    
    async def process_file_silent(self, file_path: str) -> Optional[Dict]:
        """静默处理文件（用于批量处理）"""
        try:
            from niquests import AsyncSession
            
            async with AsyncSession() as session:
                # 验证
                if FileValidator.is_url(file_path):
                    is_valid, error, file_info = await FileValidator.validate_url(session, file_path)
                else:
                    is_valid, error, file_info = FileValidator.validate_file(file_path)
                
                if not is_valid:
                    return None
                
                # 上传
                if not file_info['is_url']:
                    upload_options = {
                        'model_version': 'vlm',
                        'enable_formula': True,
                        'enable_table': True
                    }
                    
                    batch_id = await self.client.upload_file(session, file_path, **upload_options)
                    
                    if not batch_id:
                        return None
                    
                    # 等待处理
                    results = await self.client.wait_for_completion(session, batch_id, max_wait=300)
                    
                    if not results or len(results) == 0:
                        return None
                    
                    result = results[0]
                    
                    if result.get('state') != 'done':
                        return None
                    
                    full_zip_url = result.get('full_zip_url')
                    
                    # 下载
                    output_path = Path(file_path).parent
                    chunk_dir = output_path / f"{Path(file_path).stem}_result"
                    chunk_dir.mkdir(exist_ok=True)
                    
                    extracted = await ResultProcessor.download_and_extract(
                        session, full_zip_url, str(chunk_dir)
                    )
                    
                    if not extracted:
                        return None
                    
                    # 整理输出
                    file_name = Path(file_path).stem
                    md_file = output_path / f"{file_name}.md"
                    images_dir = output_path / f"{file_name}_images"
                    
                    source_md = ResultProcessor.find_markdown(extracted)
                    if source_md:
                        shutil.copy(source_md, md_file)
                    
                    source_images = Path(extracted) / "images"
                    image_count = 0
                    if source_images.exists():
                        if images_dir.exists():
                            shutil.rmtree(images_dir)
                        shutil.copytree(source_images, images_dir)
                        image_count = len(list(images_dir.glob("*")))
                    
                    return {
                        'output': {
                            'markdown': str(md_file),
                            'images': str(images_dir)
                        },
                        'stats': {
                            'pages': file_info.get('pages', 0),
                            'images': image_count
                        }
                    }
                else:
                    return None
        
        except Exception as e:
            return None
    
    def show_batch_summary(self, results: List[Dict], elapsed: float):
        """显示批量处理汇总"""
        # 统计表格
        summary_table = Table(title="[bold cyan]📊 处理结果汇总[/bold cyan]", box=box.ROUNDED)
        summary_table.add_column("文件", style="cyan", width=40)
        summary_table.add_column("状态", justify="center", width=10)
        summary_table.add_column("耗时", justify="right", width=10)
        
        for r in results:
            file_name = r['file'][:37] + "..." if len(r['file']) > 40 else r['file']
            
            if r['status'] == 'success':
                status = "[green]✅ 成功[/green]"
                time_str = f"{r['time']:.1f}s"
            else:
                status = "[red]❌ 失败[/red]"
                time_str = f"{r.get('time', 0):.1f}s" if 'time' in r else "-"
            
            summary_table.add_row(file_name, status, time_str)
        
        console.print(summary_table)
        
        # 统计信息
        stats_table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
        stats_table.add_column(style="cyan bold", width=15)
        stats_table.add_column(style="white")
        
        stats_table.add_row("📁 总文件数", f"{self.stats['total_files']}")
        stats_table.add_row("✅ 成功", f"[green]{self.stats['success']}[/green]")
        stats_table.add_row("❌ 失败", f"[red]{self.stats['failed']}[/red]")
        stats_table.add_row("⏱️  总耗时", f"{elapsed:.1f}秒")
        
        if self.stats['success'] > 0:
            avg_time = elapsed / self.stats['success']
            stats_table.add_row("📊 平均耗时", f"{avg_time:.1f}秒/文件")
        
        console.print(Panel(stats_table, title="[bold]统计信息[/bold]", border_style="cyan"))
        
        # 错误详情
        if self.stats['errors']:
            console.print("\n[bold red]❌ 错误详情:[/bold red]")
            for i, err in enumerate(self.stats['errors'], 1):
                if 'file' in err:
                    console.print(f"  {i}. [red]{err['file']}[/red]: {err['error']}")
                else:
                    console.print(f"  {i}. [red]{err['stage']}阶段[/red]: {err['error']}")


# 使用示例
if __name__ == '__main__':
    processor = EnhancedRichProcessor()
    
    if len(sys.argv) < 2:
        console.print("[yellow]用法:[/yellow]")
        console.print("  单文件: [cyan]python3 mineru_rich_enhanced.py <file_path>[/cyan]")
        console.print("  批量: [cyan]python3 mineru_rich_enhanced.py <directory> --pattern '*.pdf'[/cyan]")
        sys.exit(1)
    
    input_path = sys.argv[1]
    path = Path(input_path).expanduser()
    
    if path.is_dir():
        # 批量处理
        pattern = "*.pdf"
        if len(sys.argv) > 2 and '--pattern' in sys.argv:
            idx = sys.argv.index('--pattern')
            if idx + 1 < len(sys.argv):
                pattern = sys.argv[idx + 1]
        
        asyncio.run(processor.process_directory_enhanced(str(path), pattern))
    else:
        # 单文件处理
        result = asyncio.run(processor.process_file_enhanced(str(path)))
        sys.exit(0 if result else 1)
