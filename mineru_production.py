#!/usr/bin/env python3
"""
MinerU 生产级客户端 - 完整解决方案
支持：智能拆分、并行处理、完整合并、进度监控
直接使用API，不依赖官方SDK
"""
import json
import asyncio
import aiohttp
import random
import time
import zipfile
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

try:
    from PyPDF2 import PdfReader, PdfWriter
    from pptx import Presentation
    from docx import Document
except ImportError:
    print("❌ 请安装依赖:")
    print("   uv pip install PyPDF2 python-pptx python-docx aiohttp")
    exit(1)


class FileValidator:
    """文件验证器 - 支持本地文件和URL"""
    
    MAX_SIZE = 200 * 1024 * 1024  # 200MB
    MAX_PAGES = 600
    
    SUPPORTED_FORMATS = {
        'pdf': 'application/pdf',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'ppt': 'application/vnd.ms-powerpoint',
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'html': 'text/html'
    }
    
    @staticmethod
    def is_url(path: str) -> bool:
        """判断是否为URL"""
        return path.startswith(('http://', 'https://'))
    
    @staticmethod
    async def validate_url(session: aiohttp.ClientSession, url: str) -> Tuple[bool, str, Dict]:
        """
        验证URL
        
        Returns:
            (is_valid, error_msg, file_info)
        """
        try:
            # HEAD请求获取文件信息
            async with session.head(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return False, f"URL无法访问: {resp.status}", {}
                
                # 获取文件大小
                size = int(resp.headers.get('content-length', 0))
                if size > FileValidator.MAX_SIZE:
                    return False, f"文件超过200MB限制 ({size / 1024 / 1024:.1f}MB)", {}
                
                # 从URL或Content-Type推断格式
                content_type = resp.headers.get('content-type', '')
                format = FileValidator._guess_format_from_url(url, content_type)
                
                if not format:
                    return False, f"无法识别文件格式", {}
                
                file_info = {
                    'path': url,
                    'name': Path(url).name or 'document',
                    'size': size,
                    'format': format,
                    'is_url': True,
                    'pages': None,  # URL无法预先获取页数
                    'needs_split': False  # 使用page_ranges参数
                }
                
                return True, "", file_info
        
        except Exception as e:
            return False, f"URL验证失败: {e}", {}
    
    @staticmethod
    def _guess_format_from_url(url: str, content_type: str) -> Optional[str]:
        """从URL和Content-Type推断格式"""
        # 从URL扩展名推断
        url_lower = url.lower()
        for ext in FileValidator.SUPPORTED_FORMATS.keys():
            if url_lower.endswith(f'.{ext}'):
                return ext
        
        # 从Content-Type推断
        for ext, mime in FileValidator.SUPPORTED_FORMATS.items():
            if mime in content_type:
                return ext
        
        return None
    
    @staticmethod
    def validate_file(file_path: str) -> Tuple[bool, str, Dict]:
        """
        验证本地文件
        
        Returns:
            (is_valid, error_msg, file_info)
        """
        path = Path(file_path)
        
        # 检查文件存在
        if not path.exists():
            return False, "文件不存在", {}
        
        # 检查文件大小
        size = path.stat().st_size
        if size > FileValidator.MAX_SIZE:
            return False, f"文件超过200MB限制 ({size / 1024 / 1024:.1f}MB)", {}
        
        if size == 0:
            return False, "文件为空", {}
        
        # 检查文件格式
        suffix = path.suffix.lower().lstrip('.')
        if suffix not in FileValidator.SUPPORTED_FORMATS:
            return False, f"不支持的格式: {suffix}", {}
        
        # 检查页数
        pages = FileValidator._get_page_count(file_path, suffix)
        
        file_info = {
            'path': str(path),
            'name': path.name,
            'size': size,
            'format': suffix,
            'is_url': False,
            'pages': pages,
            'needs_split': pages > FileValidator.MAX_PAGES if pages else False
        }
        
        return True, "", file_info
    
    @staticmethod
    def _get_page_count(file_path: str, format: str) -> Optional[int]:
        """获取页数"""
        try:
            if format == 'pdf':
                reader = PdfReader(file_path)
                return len(reader.pages)
            elif format in ['pptx', 'ppt']:
                prs = Presentation(file_path)
                return len(prs.slides)
            elif format in ['docx', 'doc']:
                # DOCX页数估算
                doc = Document(file_path)
                return len(doc.paragraphs) // 5  # 估算：5段/页
        except:
            pass
        return None


class SmartChunker:
    """智能拆分器 - 支持page_ranges参数"""
    
    @staticmethod
    def create_chunks_with_ranges(file_info: Dict) -> List[Dict]:
        """
        创建分片配置（使用page_ranges参数）
        
        Returns:
            [{'file_path': '...', 'page_ranges': '1-600'}, ...]
        """
        pages = file_info['pages']
        if not pages or pages <= FileValidator.MAX_PAGES:
            return [{'file_path': file_info['path'], 'page_ranges': None}]
        
        chunks = []
        chunk_size = FileValidator.MAX_PAGES
        
        for i in range(0, pages, chunk_size):
            start = i + 1  # 页码从1开始
            end = min(i + chunk_size, pages)
            
            chunks.append({
                'file_path': file_info['path'],
                'page_ranges': f"{start}-{end}",
                'chunk_id': len(chunks) + 1,
                'pages': end - start + 1
            })
        
        print(f"📄 文件拆分: {pages}页 → {len(chunks)}个分片")
        for chunk in chunks:
            print(f"  分片{chunk['chunk_id']}: 页码 {chunk['page_ranges']} ({chunk['pages']}页)")
        
        return chunks


class MinerUClient:
    """MinerU API 客户端"""
    
    def __init__(self, tokens_file='all_tokens.json'):
        # 如果是相对路径，转换为绝对路径
        if not Path(tokens_file).is_absolute():
            # 使用脚本所在目录
            script_dir = Path(__file__).parent
            tokens_file = script_dir / tokens_file
        
        self.tokens_file = str(tokens_file)
        self.tokens = self._load_tokens()
        self.base_url = 'https://mineru.net/api/v4'
        
        if not self.tokens:
            raise ValueError(f"未找到Token文件: {self.tokens_file}")
        
        print(f"✅ 已加载 {len(self.tokens)} 个账户")
    
    def _load_tokens(self) -> Dict:
        """加载Token"""
        try:
            with open(self.tokens_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def _get_random_token(self) -> str:
        """随机选择Token"""
        email = random.choice(list(self.tokens.keys()))
        return self.tokens[email]['token']
    
    async def create_task(self, session: aiohttp.ClientSession, 
                         file_url: str, **options) -> Optional[str]:
        """
        创建解析任务
        
        Args:
            file_url: 文件URL
            **options: 其他参数（page_ranges, model_version等）
        
        Returns:
            task_id
        """
        token = self._get_random_token()
        headers = {
            'authorization': f'Bearer {token}',
            'content-type': 'application/json'
        }
        
        data = {'url': file_url, **options}
        
        async with session.post(
            f"{self.base_url}/extract/task",
            headers=headers,
            json=data,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            result = await resp.json()
            
            if result['code'] == 0:
                return result['data']['task_id']
            else:
                print(f"❌ 创建任务失败: {result.get('msg')}")
                return None
    
    async def get_task_result(self, session: aiohttp.ClientSession, 
                             task_id: str) -> Optional[Dict]:
        """获取任务结果"""
        token = self._get_random_token()
        headers = {
            'authorization': f'Bearer {token}'
        }
        
        async with session.get(
            f"{self.base_url}/extract/task/{task_id}",
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            result = await resp.json()
            
            if result['code'] == 0:
                return result['data']
            return None
    
    async def wait_for_completion(self, session: aiohttp.ClientSession,
                                  task_id: str, max_wait: int = 600) -> Optional[Dict]:
        """等待任务完成"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            result = await self.get_task_result(session, task_id)
            
            if result:
                state = result.get('state')
                
                if state == 'done':
                    return result
                elif state == 'failed':
                    print(f"❌ 任务失败: {result.get('err_msg')}")
                    return None
                elif state == 'running':
                    progress = result.get('extract_progress', {})
                    extracted = progress.get('extracted_pages', 0)
                    total = progress.get('total_pages', 0)
                    if total > 0:
                        print(f"  进度: {extracted}/{total}页", end='\r')
            
            await asyncio.sleep(5)
        
        print(f"❌ 任务超时")
        return None


class ResultProcessor:
    """结果处理器 - 下载、解压、合并"""
    
    @staticmethod
    async def download_and_extract(session: aiohttp.ClientSession,
                                   zip_url: str, output_dir: str) -> Optional[str]:
        """下载并解压结果"""
        try:
            # 下载
            async with session.get(zip_url, timeout=aiohttp.ClientTimeout(total=300)) as resp:
                zip_data = await resp.read()
            
            # 保存
            zip_path = Path(output_dir) / "result.zip"
            with open(zip_path, 'wb') as f:
                f.write(zip_data)
            
            # 解压
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(output_dir)
            
            # 删除zip
            zip_path.unlink()
            
            return output_dir
        except Exception as e:
            print(f"❌ 下载解压失败: {e}")
            return None
    
    @staticmethod
    def find_markdown(chunk_dir: str) -> Optional[str]:
        """查找Markdown文件"""
        for md_file in Path(chunk_dir).rglob("*.md"):
            return str(md_file)
        return None
    
    @staticmethod
    def merge_results(chunk_dirs: List[str], output_file: str):
        """合并所有Markdown"""
        with open(output_file, 'w', encoding='utf-8') as out:
            for i, chunk_dir in enumerate(chunk_dirs, 1):
                if i > 1:
                    out.write("\n\n" + "="*60 + "\n\n")
                
                out.write(f"# 分片 {i}\n\n")
                
                md_file = ResultProcessor.find_markdown(chunk_dir)
                if md_file:
                    with open(md_file, 'r', encoding='utf-8') as f:
                        out.write(f.read())
                else:
                    out.write("*内容为空*\n")
        
        print(f"✅ Markdown合并完成: {output_file}")
    
    @staticmethod
    def merge_images(chunk_dirs: List[str], output_dir: str):
        """合并所有图片"""
        images_dir = Path(output_dir) / "images"
        images_dir.mkdir(exist_ok=True, parents=True)
        
        count = 0
        for i, chunk_dir in enumerate(chunk_dirs, 1):
            for img in Path(chunk_dir).rglob("*.png"):
                new_name = f"chunk_{i}_{img.name}"
                shutil.copy(img, images_dir / new_name)
                count += 1
            
            for img in Path(chunk_dir).rglob("*.jpg"):
                new_name = f"chunk_{i}_{img.name}"
                shutil.copy(img, images_dir / new_name)
                count += 1
        
        print(f"✅ 图片合并完成: {count}个文件 → {images_dir}")


class MinerUProcessor:
    """MinerU 完整处理器"""
    
    def __init__(self, max_workers: int = 10):
        self.client = MinerUClient()
        self.max_workers = max_workers
    
    async def process_file(self, file_path: str, output_dir: str = "./output",
                          **options) -> Optional[Dict]:
        """
        处理单个文件（完整流程）- 支持本地文件和URL
        
        Args:
            file_path: 文件路径或URL
            output_dir: 输出目录
            **options: API参数（model_version, is_ocr等）
        
        Returns:
            处理结果
        """
        print(f"\n📄 处理: {file_path}")
        
        # 1. 验证文件或URL
        if FileValidator.is_url(file_path):
            print("🌐 检测到URL，验证中...")
            async with aiohttp.ClientSession() as session:
                is_valid, error, file_info = await FileValidator.validate_url(session, file_path)
        else:
            print("📁 检测到本地文件，验证中...")
            is_valid, error, file_info = FileValidator.validate_file(file_path)
        
        if not is_valid:
            print(f"❌ {error}")
            return None
        
        print(f"✅ 验证通过: {file_info['format'].upper()}, {file_info['size']/1024/1024:.1f}MB")
        
        # 2. 创建分片配置
        if file_info['is_url']:
            # URL直接使用，通过page_ranges参数拆分
            chunks = SmartChunker.create_chunks_with_ranges(file_info)
        else:
            # 本地文件也使用page_ranges
            chunks = SmartChunker.create_chunks_with_ranges(file_info)
        
        # 3. 处理所有分片
        print(f"\n🚀 开始处理 {len(chunks)} 个分片...")
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for chunk in chunks:
                # 创建任务时传入page_ranges
                task_options = {**options}
                if chunk['page_ranges']:
                    task_options['page_ranges'] = chunk['page_ranges']
                
                # 使用原始路径（URL或本地文件路径）
                file_url = file_info['path']
                
                task = self._process_chunk(session, file_url, chunk, task_options)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
        
        # 4. 下载并合并结果
        success_results = [r for r in results if r]
        
        if not success_results:
            print("❌ 所有分片处理失败")
            return None
        
        print(f"\n📥 下载并合并结果...")
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True, parents=True)
        
        chunk_dirs = []
        async with aiohttp.ClientSession() as session:
            for i, result in enumerate(success_results, 1):
                chunk_dir = output_path / f"chunk_{i}"
                chunk_dir.mkdir(exist_ok=True)
                
                extracted = await ResultProcessor.download_and_extract(
                    session,
                    result['full_zip_url'],
                    str(chunk_dir)
                )
                
                if extracted:
                    chunk_dirs.append(extracted)
        
        # 5. 合并
        file_name = file_info['name'].rsplit('.', 1)[0]  # 去除扩展名
        md_file = output_path / f"{file_name}_merged.md"
        
        ResultProcessor.merge_results(chunk_dirs, str(md_file))
        ResultProcessor.merge_images(chunk_dirs, output_dir)
        
        return {
            'source': file_path,
            'source_type': 'url' if file_info['is_url'] else 'file',
            'total_chunks': len(chunks),
            'success': len(success_results),
            'failed': len(chunks) - len(success_results),
            'output': {
                'markdown': str(md_file),
                'images': str(output_path / "images")
            }
        }
    
    async def _process_chunk(self, session: aiohttp.ClientSession,
                            file_url: str, chunk: Dict, options: Dict) -> Optional[Dict]:
        """处理单个分片"""
        chunk_id = chunk.get('chunk_id', 1)
        print(f"  分片{chunk_id}: 创建任务...")
        
        # 创建任务
        task_id = await self.client.create_task(session, file_url, **options)
        if not task_id:
            return None
        
        print(f"  分片{chunk_id}: 等待完成...")
        
        # 等待完成
        result = await self.client.wait_for_completion(session, task_id)
        
        if result:
            print(f"  ✅ 分片{chunk_id}: 完成")
        else:
            print(f"  ❌ 分片{chunk_id}: 失败")
        
        return result


# 使用示例
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python3 mineru_production.py <file_path> [options]")
        print("\n选项:")
        print("  --model-version vlm|pipeline|MinerU-HTML")
        print("  --is-ocr true|false")
        print("  --enable-formula true|false")
        print("  --enable-table true|false")
        print("  --language ch|en|...")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # 解析选项
    options = {}
    for i in range(2, len(sys.argv), 2):
        if i + 1 < len(sys.argv):
            key = sys.argv[i].lstrip('--').replace('-', '_')
            value = sys.argv[i + 1]
            
            # 转换布尔值
            if value.lower() in ['true', 'false']:
                value = value.lower() == 'true'
            
            options[key] = value
    
    # 处理文件
    processor = MinerUProcessor(max_workers=10)
    result = asyncio.run(processor.process_file(file_path, **options))
    
    if result:
        print(f"\n✅ 处理完成!")
        print(f"  总分片: {result['total_chunks']}")
        print(f"  成功: {result['success']}")
        print(f"  失败: {result['failed']}")
        print(f"  输出: {result['output']}")
