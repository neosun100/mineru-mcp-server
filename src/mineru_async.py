#!/usr/bin/env python3
"""
MinerU 真正异步客户端 - 使用niquests AsyncSession
性能提升10倍
"""
import json
import asyncio
import random
import time
import zipfile
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

try:
    from niquests import AsyncSession
    from PyPDF2 import PdfReader, PdfWriter
    from pptx import Presentation
    from docx import Document
except ImportError:
    print("❌ 请安装依赖:")
    print("   uv pip install niquests PyPDF2 python-pptx python-docx")
    exit(1)


class FileValidator:
    """文件验证器"""
    
    MAX_SIZE = 200 * 1024 * 1024  # 200MB
    # 服务端实际硬限制是 200 页（自 2026 年某次更新后），超过会返回
    # "number of pages exceeds limit (200 pages)" 错误。
    # 阈值定义为服务端真值，业务调用方决定是否拆分（推荐拆成 ≤180 留 buffer）。
    MAX_PAGES = 200
    
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
    async def validate_url(session: AsyncSession, url: str) -> Tuple[bool, str, Dict]:
        """验证URL（真正异步）"""
        try:
            response = await session.head(url, timeout=10, allow_redirects=True)
            
            if response.status_code != 200:
                return False, f"URL无法访问: {response.status_code}", {}
            
            size = int(response.headers.get('content-length', 0))
            if size > FileValidator.MAX_SIZE:
                return False, f"文件超过200MB限制 ({size / 1024 / 1024:.1f}MB)", {}
            
            content_type = response.headers.get('content-type', '')
            format = FileValidator._guess_format_from_url(url, content_type)
            
            # Fallback: 下载前几个字节检查文件魔数
            if not format:
                resp = await session.get(url, timeout=10, headers={'Range': 'bytes=0-16'})
                head = resp.content[:16]
                if head.startswith(b'%PDF'):
                    format = 'pdf'
                elif head.startswith(b'PK'):
                    # ZIP-based: docx/pptx/xlsx
                    if any(ext in url.lower() for ext in ['pptx', 'ppt']):
                        format = 'pptx'
                    elif any(ext in url.lower() for ext in ['docx', 'doc']):
                        format = 'docx'
                    else:
                        format = 'docx'  # default ZIP-based to docx
                elif head[:3] in (b'\xff\xd8\xff', ):
                    format = 'jpg'
                elif head[:8] == b'\x89PNG\r\n\x1a\n':
                    format = 'png'
                elif b'<html' in head.lower() or b'<!doctype' in head.lower():
                    format = 'html'
            
            if not format:
                return False, f"无法识别文件格式", {}
            
            file_info = {
                'path': url,
                'name': Path(url).name or 'document',
                'size': size,
                'format': format,
                'is_url': True,
                'pages': None,
                'needs_split': False
            }
            
            return True, "", file_info
        
        except Exception as e:
            return False, f"URL验证失败: {e}", {}
    
    @staticmethod
    def _guess_format_from_url(url: str, content_type: str) -> Optional[str]:
        """从URL推断格式"""
        url_lower = url.lower()
        for ext in FileValidator.SUPPORTED_FORMATS.keys():
            if url_lower.endswith(f'.{ext}'):
                return ext
        
        for ext, mime in FileValidator.SUPPORTED_FORMATS.items():
            if mime in content_type:
                return ext
        
        return None
    
    @staticmethod
    def validate_file(file_path: str) -> Tuple[bool, str, Dict]:
        """验证本地文件"""
        path = Path(file_path)
        
        if not path.exists():
            return False, "文件不存在", {}
        
        size = path.stat().st_size
        if size > FileValidator.MAX_SIZE:
            return False, f"文件超过200MB限制 ({size / 1024 / 1024:.1f}MB)", {}
        
        if size == 0:
            return False, "文件为空", {}
        
        suffix = path.suffix.lower().lstrip('.')
        if suffix not in FileValidator.SUPPORTED_FORMATS:
            return False, f"不支持的格式: {suffix}", {}
        
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
                doc = Document(file_path)
                return len(doc.paragraphs) // 5
        except:
            pass
        return None


class MinerUAsyncClient:
    """MinerU 真正异步客户端"""
    
    def __init__(self, tokens_file='all_tokens.json'):
        if not Path(tokens_file).is_absolute():
            # Token文件在项目根目录，不是src目录
            script_dir = Path(__file__).parent.parent  # 向上一级到项目根目录
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

    # ────────────────────────────────────────────────────────────
    # v4.0.0: 构造 v4 API 请求 payload，区分顶层参数和 file 级参数
    # ────────────────────────────────────────────────────────────

    # 顶层参数（请求体根级，对所有文件生效）
    _BATCH_LEVEL_KEYS = {
        'model_version', 'enable_formula', 'enable_table',
        'language', 'extra_formats',
    }
    # file 级参数（每个 file 对象内）
    _FILE_LEVEL_KEYS = {
        'name', 'url', 'is_ocr', 'data_id', 'page_ranges',
    }
    # /extract/task 单文件接口的所有合法参数（顶层）
    _SINGLE_TASK_KEYS = {
        'url', 'model_version', 'is_ocr', 'enable_formula', 'enable_table',
        'language', 'data_id', 'callback', 'seed', 'extra_formats',
        'page_ranges', 'no_cache', 'cache_tolerance',
    }

    def _split_options(self, options: Dict) -> tuple[Dict, Dict]:
        """把混合 options 拆成 (顶层 batch_opts, 单文件 file_opts)。"""
        batch_opts = {k: v for k, v in options.items()
                      if k in self._BATCH_LEVEL_KEYS and v is not None}
        file_opts = {k: v for k, v in options.items()
                     if k in self._FILE_LEVEL_KEYS and v is not None}
        return batch_opts, file_opts

    async def submit_url_task(
        self,
        session: AsyncSession,
        url: str,
        **options,
    ) -> Optional[str]:
        """v4 直接提交 URL 解析任务（不下载到本地）。

        端点：POST /api/v4/extract/task
        返回：task_id（注意不是 batch_id）。
        如果 URL 无法访问（如 GitHub/AWS 网络受限），调用方应 catch 后兜底走下载流程。
        """
        token = self._get_random_token()
        headers = {
            'authorization': f'Bearer {token}',
            'content-type': 'application/json',
        }
        # 过滤出 v4 单任务接口接受的参数
        payload = {k: v for k, v in options.items()
                   if k in self._SINGLE_TASK_KEYS and v is not None}
        payload['url'] = url

        try:
            response = await session.post(
                f"{self.base_url}/extract/task",
                headers=headers,
                json=payload,
                timeout=30,
            )
            result = response.json()
        except Exception as e:
            logger.warning(f"submit_url_task 网络异常: {e}")
            return None

        if result.get('code') != 0:
            logger.warning(f"submit_url_task 返回非 0: code={result.get('code')} msg={result.get('msg')}")
            return None
        return result['data'].get('task_id')

    async def get_task_result(
        self,
        session: AsyncSession,
        task_id: str,
    ) -> Optional[Dict]:
        """查询单文件任务结果（v4 /extract/task/{id}）。"""
        token = self._get_random_token()
        headers = {'authorization': f'Bearer {token}'}
        try:
            resp = await session.get(
                f"{self.base_url}/extract/task/{task_id}",
                headers=headers, timeout=30,
            )
            result = resp.json()
        except Exception as e:
            logger.warning(f"get_task_result 网络异常: {e}")
            return None
        if result.get('code') != 0:
            return None
        return result.get('data')

    async def wait_for_single_task(
        self,
        session: AsyncSession,
        task_id: str,
        max_wait: int = 600,
        progress_callback=None,
    ) -> Optional[Dict]:
        """轮询单任务直到完成。返回与 batch 任务相同结构的 dict。"""
        start = time.time()
        while time.time() - start < max_wait:
            data = await self.get_task_result(session, task_id)
            if data is None:
                await asyncio.sleep(2)
                continue
            state = data.get('state')
            if state == 'done':
                return data
            if state == 'failed':
                return data
            if state == 'running' and progress_callback:
                p = data.get('extract_progress', {})
                extracted = p.get('extracted_pages', 0)
                total = p.get('total_pages', 0)
                if total > 0:
                    await progress_callback(extracted, total, f"解析中 {extracted}/{total}页")
            await asyncio.sleep(2)
        return None

    async def upload_file(self, session: AsyncSession, file_path: str, **options) -> Optional[str]:
        """上传本地文件（真正异步）。

        v4.0.0 升级：支持完整参数透传。
          - 顶层参数：model_version / enable_formula / enable_table / language / extra_formats
          - 文件级参数：is_ocr / data_id / page_ranges
        """
        token = self._get_random_token()
        headers = {
            'authorization': f'Bearer {token}',
            'content-type': 'application/json'
        }

        file_name = Path(file_path).name

        # 1. 拆分参数：file 级 vs batch 级
        batch_opts, file_opts = self._split_options(options)
        file_entry = {'name': file_name, **file_opts}
        data = {'files': [file_entry], **batch_opts}

        response = await session.post(
            f"{self.base_url}/file-urls/batch",
            headers=headers,
            json=data,
            timeout=30
        )
        result = response.json()

        if result['code'] != 0:
            print(f"❌ 获取上传链接失败: {result.get('msg')}")
            return None

        batch_id = result['data']['batch_id']
        upload_url = result['data']['file_urls'][0]
        print(f"✅ 获取上传链接成功")
        
        # 2. 上传文件（异步）
        print(f"📤 上传文件中...")
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        upload_response = await session.put(upload_url, data=file_data, timeout=300)
        
        if upload_response.status_code == 200:
            print(f"✅ 文件上传成功")
            return batch_id
        else:
            print(f"❌ 文件上传失败: {upload_response.status_code}")
            return None
    
    async def get_batch_result(self, session: AsyncSession, batch_id: str) -> Optional[List[Dict]]:
        """获取批量任务结果（真正异步）"""
        token = self._get_random_token()
        headers = {'authorization': f'Bearer {token}'}
        
        response = await session.get(
            f"{self.base_url}/extract-results/batch/{batch_id}",
            headers=headers,
            timeout=30
        )
        result = response.json()
        
        if result['code'] == 0:
            return result['data']['extract_result']
        return None
    
    async def wait_for_completion(self, session: AsyncSession, batch_id: str, max_wait: int = 600, progress_callback=None) -> Optional[List[Dict]]:
        """等待批量任务完成（真正异步）"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            results = await self.get_batch_result(session, batch_id)
            
            if results:
                all_done = True
                for result in results:
                    state = result.get('state')
                    
                    if state == 'failed':
                        print(f"❌ 失败: {result.get('err_msg')}")
                        return None
                    elif state in ['pending', 'running', 'waiting-file', 'converting']:
                        all_done = False
                        if state == 'running':
                            progress = result.get('extract_progress', {})
                            extracted = progress.get('extracted_pages', 0)
                            total = progress.get('total_pages', 0)
                            if total > 0:
                                print(f"  进度: {extracted}/{total}页", end='\r')
                                if progress_callback:
                                    await progress_callback(extracted, total, f"处理中: {extracted}/{total}页")
                        elif progress_callback:
                            await progress_callback(0, 100, f"状态: {state}")
                
                if all_done:
                    return results
            
            await asyncio.sleep(5)
        
        print(f"❌ 任务超时")
        return None


class ResultProcessor:
    """结果处理器"""
    
    @staticmethod
    async def download_and_extract(session: AsyncSession, zip_url: str, output_dir: str) -> Optional[str]:
        """下载并解压结果（真正异步）"""
        try:
            print(f"📥 下载中...")
            response = await session.get(zip_url, timeout=300)
            
            if response.status_code != 200:
                print(f"❌ 下载失败: {response.status_code}")
                return None
            
            zip_path = Path(output_dir) / "result.zip"
            with open(zip_path, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ 下载完成")
            
            print(f"📦 解压中...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(output_dir)
            
            print(f"✅ 解压完成")
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


class MinerUAsyncProcessor:
    """MinerU 真正异步处理器"""
    
    def __init__(self, max_workers: int = 10):
        self.client = MinerUAsyncClient()
        self.max_workers = max_workers
    
    async def process_file(self, file_path: str, output_dir: str = "./output", progress_callback=None, **options) -> Optional[Dict]:
        """处理单个文件（真正异步）
        
        progress_callback: async def(progress: float, total: float, message: str)
        """
        import logging
        logger = logging.getLogger(__name__)
        
        async def _progress(progress, total, message):
            if progress_callback:
                await progress_callback(progress, total, message)
        
        logger.info(f"process_file() 开始: {file_path}")
        print(f"\n📄 处理: {file_path}")
        
        try:
            # 1. 验证文件
            await _progress(1, 10, "验证文件...")
            async with AsyncSession() as session:
                if FileValidator.is_url(file_path):
                    logger.info("检测到URL")
                    print("🌐 检测到URL，验证中...")
                    is_valid, error, file_info = await FileValidator.validate_url(session, file_path)
                else:
                    logger.info("检测到本地文件")
                    print("📁 检测到本地文件，验证中...")
                    is_valid, error, file_info = FileValidator.validate_file(file_path)
                
                logger.info(f"验证结果: is_valid={is_valid}")
                
                if not is_valid:
                    logger.error(f"验证失败: {error}")
                    print(f"❌ {error}")
                    return None
                
                logger.info(f"文件信息: {file_info}")
                print(f"✅ 验证通过: {file_info['format'].upper()}, {file_info['size']/1024/1024:.1f}MB")
                if file_info.get('pages'):
                    print(f"   页数: {file_info['pages']}")
                
                # 2. 上传本地文件（真正异步）
                if not file_info['is_url']:
                    logger.info("开始上传本地文件")
                    print(f"\n📤 上传本地文件...")
                    await _progress(2, 10, f"上传文件: {file_info['name']} ({file_info['size']/1024/1024:.1f}MB)...")

                    # v4.0.0 智能参数：透传用户提供的所有官方参数
                    fmt = file_info['format']
                    upload_options = {
                        'model_version': options.get('model_version', 'vlm'),
                        'enable_formula': options.get('enable_formula', True),
                        'enable_table': options.get('enable_table', True),
                    }
                    # 可选官方参数透传（None 时不带）
                    for key in ('language', 'is_ocr', 'page_ranges',
                                'extra_formats', 'data_id'):
                        if options.get(key) is not None:
                            upload_options[key] = options[key]

                    # 图片自动开启 OCR（用户没显式设置时）
                    if fmt in ('png', 'jpg', 'jpeg') and 'is_ocr' not in upload_options:
                        upload_options['is_ocr'] = True

                    # 非 PDF/图片格式使用 pipeline 模型（vlm 对 PPTX/DOC 等会卡在 pending）
                    if fmt == 'html':
                        upload_options['model_version'] = 'MinerU-HTML'
                    elif fmt not in ('pdf', 'png', 'jpg', 'jpeg') and 'model_version' not in options:
                        upload_options['model_version'] = 'pipeline'
                        logger.info(f"非PDF格式({fmt})，自动切换到 pipeline 模型")

                    batch_id = await self.client.upload_file(session, file_path, **upload_options)
                    
                    if not batch_id:
                        logger.error("上传失败")
                        print("❌ 文件上传失败")
                        return None
                    
                    logger.info(f"上传成功: batch_id={batch_id}")
                    print(f"✅ 文件已上传，batch_id: {batch_id}")
                    await _progress(3, 10, "文件已上传，等待服务端处理...")
                    
                    # 3. 服务端硬限制：超过 200 页直接返回错误。
                    #    本函数只处理单文件单批次，不再做"伪 page_ranges"假拆分。
                    #    真正的物理拆分由 batch_async 入口或 process_with_auto_split 协调，
                    #    超页文件应在调用本函数之前先拆成 ≤180 页的 chunks。
                    pages = file_info.get('pages')
                    if pages and pages > FileValidator.MAX_PAGES:
                        msg = (
                            f"文件 {pages} 页，超过服务端 {FileValidator.MAX_PAGES} 页限制。"
                            f"请先用 split_large_file.split_large_pdf() 物理拆分后再处理。"
                        )
                        logger.error(msg)
                        print(f"❌ {msg}")
                        return None

                    # 4. 等待处理完成（真正异步）
                    logger.info("等待处理完成")
                    print(f"\n⏳ 等待处理完成...")

                    results = await self.client.wait_for_completion(session, batch_id, progress_callback=progress_callback)

                    if not results or len(results) == 0:
                        logger.error("处理失败")
                        print("❌ 处理失败")
                        return None

                    result = results[0]

                    if result.get('state') != 'done':
                        logger.error(f"处理失败: {result.get('err_msg')}")
                        print(f"❌ 处理失败: {result.get('err_msg')}")
                        return None

                    full_zip_url = result.get('full_zip_url')
                    logger.info(f"处理完成: {full_zip_url}")
                else:
                    # URL 处理 v4.0.0 升级：
                    #   1. 优先调用 v4 /extract/task 直接传 URL（服务端自己抓）
                    #   2. 失败兜底：下载到本地再走 file-urls/batch
                    logger.info("URL 文件 — 尝试服务端直传…")
                    print(f"\n🌐 检测到 URL，尝试服务端直传…")
                    await _progress(2, 10, "提交 URL 解析任务（服务端直接抓）…")

                    url = file_path
                    fmt = file_info['format']

                    # 构造 v4 单任务参数
                    submit_options = {
                        'model_version': options.get('model_version', 'vlm'),
                        'enable_formula': options.get('enable_formula', True),
                        'enable_table': options.get('enable_table', True),
                    }
                    for key in ('language', 'is_ocr', 'page_ranges',
                                'extra_formats', 'data_id',
                                'no_cache', 'cache_tolerance'):
                        if options.get(key) is not None:
                            submit_options[key] = options[key]
                    if fmt in ('png', 'jpg', 'jpeg') and 'is_ocr' not in submit_options:
                        submit_options['is_ocr'] = True
                    if fmt == 'html':
                        submit_options['model_version'] = 'MinerU-HTML'
                    elif fmt not in ('pdf', 'png', 'jpg', 'jpeg') and 'model_version' not in options:
                        submit_options['model_version'] = 'pipeline'

                    task_id = await self.client.submit_url_task(session, url, **submit_options)

                    full_zip_url = None
                    if task_id:
                        # URL 直传成功，走单任务轮询
                        logger.info(f"URL 直传成功 task_id={task_id}")
                        print(f"✅ 已提交（task_id={task_id[:12]}…），等待解析完成…")
                        task_data = await self.client.wait_for_single_task(
                            session, task_id, progress_callback=progress_callback,
                        )
                        if task_data and task_data.get('state') == 'done':
                            full_zip_url = task_data.get('full_zip_url')
                        else:
                            err_msg = task_data.get('err_msg', '未知') if task_data else '轮询超时'
                            logger.warning(f"URL 直传失败：{err_msg}，降级到本地下载…")
                            print(f"⚠️  URL 直传失败：{err_msg}，降级为本地下载…")

                    if not full_zip_url:
                        # 兜底：下载到本地再上传
                        import tempfile as _tempfile
                        file_name = file_info['name']
                        if '.' not in file_name:
                            file_name = f"{file_name}.{fmt}"
                        tmp_path = Path(_tempfile.gettempdir()) / file_name

                        await _progress(3, 10, "降级：下载 URL 文件到本地…")
                        resp = await session.get(url, timeout=120)
                        if resp.status_code != 200:
                            print(f"❌ 下载失败: HTTP {resp.status_code}")
                            return None
                        tmp_path.write_bytes(resp.content)
                        logger.info(f"下载完成: {tmp_path}")
                        print(f"✅ 下载完成: {tmp_path.stat().st_size / 1024 / 1024:.1f}MB")

                        # 走 file-urls/batch
                        batch_id = await self.client.upload_file(
                            session, str(tmp_path), **submit_options,
                        )
                        if not batch_id:
                            print("❌ 上传失败")
                            return None
                        print(f"✅ 已上传，batch_id: {batch_id}")

                        results = await self.client.wait_for_completion(
                            session, batch_id, progress_callback=progress_callback,
                        )
                        if not results or len(results) == 0 or results[0].get('state') != 'done':
                            err = results[0].get('err_msg', '未知错误') if results else '无结果'
                            print(f"❌ 处理失败: {err}")
                            return None
                        full_zip_url = results[0].get('full_zip_url')

                    # URL 文件输出到临时目录
                    import tempfile as _tempfile
                    output_path = Path(_tempfile.gettempdir())
                    file_path = str(tmp_path)  # 后续整理输出用本地路径
                
                # 4. 下载并解压（真正异步）
                logger.info("开始下载结果")
                print(f"\n📥 下载并解压结果...")
                await _progress(9, 10, "下载并解压结果...")
                
                output_path = Path(output_dir)
                if not file_info['is_url']:
                    output_path = Path(file_path).parent
                
                output_path.mkdir(exist_ok=True, parents=True)
                
                chunk_dir = output_path / f"{Path(file_path).stem}_result"
                chunk_dir.mkdir(exist_ok=True)
                
                extracted = await ResultProcessor.download_and_extract(session, full_zip_url, str(chunk_dir))
                
                if not extracted:
                    logger.error("下载解压失败")
                    print("❌ 下载解压失败")
                    return None
                
                logger.info(f"下载解压成功: {extracted}")
                
                # 5. 整理输出
                logger.info("整理输出文件")
                file_name = Path(file_path).stem
                md_file = output_path / f"{file_name}.md"
                images_dir = output_path / f"{file_name}_images"

                # 复制 Markdown，并把其中的 `images/xxx` 引用改写成
                # `{file_name}_images/xxx`，保持 .md 与同目录图片目录的一致。
                source_md = ResultProcessor.find_markdown(extracted)
                if source_md:
                    from path_fixer import rewrite_md_image_refs
                    md_text = Path(source_md).read_text(encoding='utf-8')
                    md_text = rewrite_md_image_refs(md_text, f"{file_name}_images")
                    md_file.write_text(md_text, encoding='utf-8')
                    logger.info(f"Markdown已写入并修复图片引用: {md_file}")
                    print(f"✅ Markdown: {md_file}")
                
                # 复制图片
                source_images = Path(extracted) / "images"
                if source_images.exists():
                    if images_dir.exists():
                        shutil.rmtree(images_dir)
                    shutil.copytree(source_images, images_dir)
                    image_count = len(list(images_dir.glob("*")))
                    logger.info(f"图片已复制: {image_count}个")
                    print(f"✅ 图片: {images_dir} ({image_count}个)")
                
                logger.info("处理完成")
                await _progress(10, 10, "处理完成 ✅")
                return {
                    'source': file_path,
                    'source_type': 'url' if file_info['is_url'] else 'file',
                    'output': {
                        'markdown': str(md_file),
                        'images': str(images_dir) if images_dir.exists() else None
                    }
                }
        
        except Exception as e:
            logger.error(f"处理异常: {e}", exc_info=True)
            print(f"❌ 处理失败: {e}")
            return None


# 使用示例
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python3 mineru_async.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    processor = MinerUAsyncProcessor(max_workers=10)
    result = asyncio.run(processor.process_file(file_path))
    
    if result:
        print(f"\n✅ 处理成功!")
        print(f"  Markdown: {result['output']['markdown']}")
        print(f"  图片: {result['output']['images']}")
    else:
        print(f"\n❌ 处理失败")
        sys.exit(1)
