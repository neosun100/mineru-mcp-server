#!/usr/bin/env python3
"""
MinerU Rich UI - 美化的用户界面
使用Rich库提供漂亮的进度条和日志输出
"""
import asyncio
import sys
from pathlib import Path
from typing import Optional, Dict

sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich import print as rprint

from mineru_async import MinerUAsyncProcessor, FileValidator

console = Console()


class RichMinerUProcessor:
    """带Rich UI的MinerU处理器"""
    
    def __init__(self):
        self.processor = MinerUAsyncProcessor()
    
    async def process_file_with_ui(self, file_path: str, **options) -> Optional[Dict]:
        """处理文件（带Rich UI）"""
        
        # 显示标题
        console.print(Panel.fit(
            "[bold cyan]MinerU 文档处理[/bold cyan]",
            border_style="cyan"
        ))
        
        # 1. 验证文件
        with console.status("[bold green]验证文件中...") as status:
            if FileValidator.is_url(file_path):
                from niquests import AsyncSession
                async with AsyncSession() as session:
                    is_valid, error, file_info = await FileValidator.validate_url(session, file_path)
            else:
                is_valid, error, file_info = FileValidator.validate_file(file_path)
            
            if not is_valid:
                console.print(f"[bold red]❌ {error}[/bold red]")
                return None
        
        # 显示文件信息
        info_table = Table(show_header=False, box=None)
        info_table.add_row("[cyan]文件[/cyan]", file_info['name'])
        info_table.add_row("[cyan]格式[/cyan]", file_info['format'].upper())
        info_table.add_row("[cyan]大小[/cyan]", f"{file_info['size']/1024/1024:.1f} MB")
        if file_info.get('pages'):
            info_table.add_row("[cyan]页数[/cyan]", f"{file_info['pages']} 页")
        
        console.print(Panel(info_table, title="[bold]文件信息[/bold]", border_style="green"))
        
        # 2. 处理文件（带进度条）
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            
            # 上传任务
            upload_task = progress.add_task("[cyan]上传文件...", total=100)
            
            # 调用实际处理（这里简化，实际需要集成到mineru_async.py）
            result = await self.processor.process_file(file_path, **options)
            
            progress.update(upload_task, completed=100)
        
        # 3. 显示结果
        if result:
            result_table = Table(show_header=False, box=None)
            result_table.add_row("[green]✅ Markdown[/green]", result['output']['markdown'])
            if result['output'].get('images'):
                result_table.add_row("[green]✅ 图片[/green]", result['output']['images'])
            
            console.print(Panel(result_table, title="[bold green]处理完成[/bold green]", border_style="green"))
            return result
        else:
            console.print("[bold red]❌ 处理失败[/bold red]")
            return None
    
    async def process_directory_with_ui(self, directory: str, pattern: str = "*.pdf"):
        """批量处理目录（带Rich UI）"""
        
        console.print(Panel.fit(
            "[bold cyan]MinerU 批量处理[/bold cyan]",
            border_style="cyan"
        ))
        
        # 扫描文件
        dir_path = Path(directory).expanduser()
        files = list(dir_path.glob(pattern))
        
        if not files:
            console.print(f"[yellow]未找到匹配的文件: {pattern}[/yellow]")
            return
        
        console.print(f"[cyan]找到 {len(files)} 个文件[/cyan]\n")
        
        # 创建进度条
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("({task.completed}/{task.total})"),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            
            overall_task = progress.add_task(
                "[cyan]总进度",
                total=len(files)
            )
            
            results = []
            
            for i, file in enumerate(files, 1):
                file_task = progress.add_task(
                    f"[green]处理 {file.name}",
                    total=100
                )
                
                try:
                    result = await self.processor.process_file(str(file))
                    
                    if result:
                        results.append({'file': file.name, 'status': 'success', 'result': result})
                        progress.update(file_task, completed=100, description=f"[green]✅ {file.name}")
                    else:
                        results.append({'file': file.name, 'status': 'failed'})
                        progress.update(file_task, completed=100, description=f"[red]❌ {file.name}")
                
                except Exception as e:
                    results.append({'file': file.name, 'status': 'error', 'error': str(e)})
                    progress.update(file_task, completed=100, description=f"[red]❌ {file.name}")
                
                progress.update(overall_task, advance=1)
                
                # 移除完成的任务
                progress.remove_task(file_task)
        
        # 显示汇总
        summary_table = Table(title="[bold]处理结果汇总[/bold]")
        summary_table.add_column("文件", style="cyan")
        summary_table.add_column("状态", style="green")
        
        for r in results:
            status = "✅ 成功" if r['status'] == 'success' else "❌ 失败"
            summary_table.add_row(r['file'], status)
        
        console.print(summary_table)
        
        success_count = sum(1 for r in results if r['status'] == 'success')
        console.print(f"\n[bold green]成功: {success_count}/{len(files)}[/bold green]")


# 使用示例
if __name__ == '__main__':
    processor = RichMinerUProcessor()
    
    if len(sys.argv) < 2:
        console.print("[yellow]用法: python3 mineru_rich.py <file_path|directory>[/yellow]")
        console.print("[yellow]示例: python3 mineru_rich.py ~/Documents/report.pdf[/yellow]")
        console.print("[yellow]批量: python3 mineru_rich.py ~/Documents/ --pattern '*.pdf'[/yellow]")
        sys.exit(1)
    
    input_path = sys.argv[1]
    path = Path(input_path).expanduser()
    
    if path.is_dir():
        # 批量处理
        pattern = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2].startswith('--pattern') else "*.pdf"
        if pattern.startswith('--pattern'):
            pattern = sys.argv[3] if len(sys.argv) > 3 else "*.pdf"
        
        asyncio.run(processor.process_directory_with_ui(str(path), pattern))
    else:
        # 单文件处理
        result = asyncio.run(processor.process_file_with_ui(str(path)))
        sys.exit(0 if result else 1)
