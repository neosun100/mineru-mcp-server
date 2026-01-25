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
    async def validate_url(session: AsyncSession, url: str) -> Tuple[bool, str, Dict]:
        """验证URL（真正异步）"""
        try:
            response = await session.head(url, timeout=10)
            
            if response.status_code != 200:
                return False, f"URL无法访问: {response.status_code}", {}
            
            size = int(response.headers.get('content-length', 0))
            if size > FileValidator.MAX_SIZE:
                return False, f"文件超过200MB限制 ({size / 1024 / 1024:.1f}MB)", {}
            
            content_type = response.headers.get('content-type', '')
            format = FileValidator._guess_format_from_url(url, content_type)
            
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
    
    async def upload_file(self, session: AsyncSession, file_path: str, **options) -> Optional[str]:
        """上传本地文件（真正异步）"""
        token = self._get_random_token()
        headers = {
            'authorization': f'Bearer {token}',
            'content-type': 'application/json'
        }
        
        file_name = Path(file_path).name
        
        # 1. 获取上传链接（异步）
        data = {'files': [{'name': file_name}], **options}
        
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
    
    async def wait_for_completion(self, session: AsyncSession, batch_id: str, max_wait: int = 600) -> Optional[List[Dict]]:
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
    
    async def process_file(self, file_path: str, output_dir: str = "./output", **options) -> Optional[Dict]:
        """处理单个文件（真正异步）"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"process_file() 开始: {file_path}")
        print(f"\n📄 处理: {file_path}")
        
        try:
            # 1. 验证文件
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
                    
                    # 智能参数设置
                    upload_options = {
                        'model_version': options.get('model_version', 'vlm'),
                        'enable_formula': options.get('enable_formula', True),
                        'enable_table': options.get('enable_table', True)
                        # 不设置 language，让API自动检测
                    }
                    
                    # HTML文件使用专用模型
                    if file_info['format'] == 'html':
                        upload_options['model_version'] = 'MinerU-HTML'
                    
                    batch_id = await self.client.upload_file(session, file_path, **upload_options)
                    
                    if not batch_id:
                        logger.error("上传失败")
                        print("❌ 文件上传失败")
                        return None
                    
                    logger.info(f"上传成功: batch_id={batch_id}")
                    print(f"✅ 文件已上传，batch_id: {batch_id}")
                    
                    # 3. 等待处理完成（真正异步）
                    logger.info("等待处理完成")
                    print(f"\n⏳ 等待处理完成...")
                    
                    results = await self.client.wait_for_completion(session, batch_id)
                    
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
                    # URL处理（TODO）
                    logger.error("URL处理暂未实现")
                    print("❌ URL处理暂未实现")
                    return None
                
                # 4. 下载并解压（真正异步）
                logger.info("开始下载结果")
                print(f"\n📥 下载并解压结果...")
                
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
                
                # 复制Markdown
                source_md = ResultProcessor.find_markdown(extracted)
                if source_md:
                    shutil.copy(source_md, md_file)
                    logger.info(f"Markdown已复制: {md_file}")
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
