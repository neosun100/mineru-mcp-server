#!/usr/bin/env python3
"""
MinerU API 完整封装 - 支持所有官方API
包含：智能解析、文档抽取、批量处理、负载均衡
"""
import json
import requests
import random
import time
from typing import Optional, Dict, Any, List
from datetime import datetime

class MinerUAPI:
    """MinerU API 完整客户端"""
    
    def __init__(self, tokens_file='all_tokens.json', auto_refresh=True):
        """初始化"""
        self.tokens_file = tokens_file
        self.auto_refresh = auto_refresh
        self.tokens = self._load_tokens()
        self.base_url = 'https://mineru.net/api/v4'
        
        if not self.tokens:
            raise ValueError("未找到Token，请先运行 batch_login.py")
        
        print(f"✅ 已加载 {len(self.tokens)} 个账户")
        
        if self.auto_refresh:
            self._check_and_refresh_tokens()
    
    def _load_tokens(self) -> Dict:
        """加载Token"""
        try:
            with open(self.tokens_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def _check_token_expiry(self, token_name: str) -> bool:
        """检查Token是否过期"""
        try:
            timestamp_str = token_name.replace('token-', '')
            created_time = datetime.strptime(timestamp_str, '%Y%m%d%H%M%S')
            days_passed = (datetime.now() - created_time).days
            return days_passed >= 13
        except:
            return False
    
    def _check_and_refresh_tokens(self):
        """检查Token过期"""
        expired = [info['name'] for email, info in self.tokens.items() 
                  if self._check_token_expiry(info['token_name'])]
        
        if expired:
            print(f"\n⚠️  {len(expired)} 个账户Token即将过期")
            print(f"💡 请运行: python3 batch_login.py\n")
        else:
            print("✅ 所有Token有效")
    
    def _get_random_token(self) -> tuple:
        """随机选择Token（负载均衡）"""
        email = random.choice(list(self.tokens.keys()))
        return email, self.tokens[email]['token']
    
    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """发送请求（自动负载均衡）"""
        email, token = self._get_random_token()
        
        headers = kwargs.get('headers', {})
        headers['authorization'] = f'Bearer {token}'
        headers['accept'] = 'application/json'
        kwargs['headers'] = headers
        
        url = f"{self.base_url}/{endpoint}"
        return requests.request(method, url, **kwargs)
    
    # ==================== 智能解析 API ====================
    
    def create_task(self, file_url: str, model_version='vlm', **options) -> Optional[str]:
        """
        创建单个文件解析任务
        
        Args:
            file_url: 文件URL（支持PDF/DOC/DOCX/PPT/PPTX/图片/HTML）
            model_version: 模型版本（pipeline/vlm/MinerU-HTML）
            **options: 其他选项（is_ocr, enable_formula, enable_table等）
        
        Returns:
            task_id 或 None
        """
        data = {
            'url': file_url,
            'model_version': model_version,
            **options
        }
        
        response = self._request('POST', 'extract/task', json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result['code'] == 0:
                task_id = result['data']['task_id']
                print(f"✅ 任务已创建: {task_id}")
                return task_id
        
        print(f"❌ 创建失败: {response.text}")
        return None
    
    def get_task_result(self, task_id: str) -> Optional[Dict]:
        """
        获取任务结果
        
        Args:
            task_id: 任务ID
        
        Returns:
            任务结果
        """
        response = self._request('GET', f'extract/task/{task_id}', timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result['code'] == 0:
                return result['data']
        
        return None
    
    def parse_and_wait(self, file_url: str, model_version='vlm', 
                       max_wait=300, **options) -> Optional[Dict]:
        """
        解析文件并等待结果
        
        Args:
            file_url: 文件URL
            model_version: 模型版本
            max_wait: 最大等待时间（秒）
            **options: 其他选项
        
        Returns:
            解析结果
        """
        print(f"📄 开始解析: {file_url}")
        
        # 创建任务
        task_id = self.create_task(file_url, model_version, **options)
        if not task_id:
            return None
        
        # 等待完成
        print("⏳ 等待解析完成...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            result = self.get_task_result(task_id)
            
            if result:
                state = result.get('state')
                
                if state == 'done':
                    print(f"✅ 解析完成")
                    print(f"📦 结果: {result.get('full_zip_url')}")
                    return result
                elif state == 'failed':
                    print(f"❌ 解析失败: {result.get('err_msg')}")
                    return None
                elif state == 'running':
                    progress = result.get('extract_progress', {})
                    print(f"  进度: {progress.get('extracted_pages', 0)}/{progress.get('total_pages', 0)}")
            
            time.sleep(5)
        
        print("❌ 超时")
        return None
    
    # ==================== 批量解析 API ====================
    
    def create_batch_task(self, files: List[Dict], model_version='vlm', **options) -> Optional[str]:
        """
        创建批量解析任务
        
        Args:
            files: 文件列表 [{"url": "...", "data_id": "..."}]
            model_version: 模型版本
            **options: 其他选项
        
        Returns:
            batch_id 或 None
        """
        data = {
            'files': files,
            'model_version': model_version,
            **options
        }
        
        response = self._request('POST', 'extract/task/batch', json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result['code'] == 0:
                batch_id = result['data']['batch_id']
                print(f"✅ 批量任务已创建: {batch_id}")
                return batch_id
        
        print(f"❌ 创建失败: {response.text}")
        return None
    
    def get_batch_result(self, batch_id: str) -> Optional[Dict]:
        """
        获取批量任务结果
        
        Args:
            batch_id: 批量任务ID
        
        Returns:
            批量结果
        """
        response = self._request('GET', f'extract-results/batch/{batch_id}', timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result['code'] == 0:
                return result['data']
        
        return None
    
    # ==================== 文件上传 API ====================
    
    def get_upload_urls(self, files: List[Dict], model_version='vlm', **options) -> Optional[Dict]:
        """
        获取文件上传链接
        
        Args:
            files: 文件列表 [{"name": "demo.pdf", "data_id": "..."}]
            model_version: 模型版本
            **options: 其他选项
        
        Returns:
            上传链接信息
        """
        data = {
            'files': files,
            'model_version': model_version,
            **options
        }
        
        response = self._request('POST', 'file-urls/batch', json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result['code'] == 0:
                return result['data']
        
        return None
    
    def upload_and_parse(self, file_path: str, model_version='vlm', **options) -> Optional[str]:
        """
        上传文件并解析
        
        Args:
            file_path: 本地文件路径
            model_version: 模型版本
            **options: 其他选项
        
        Returns:
            batch_id 或 None
        """
        import os
        file_name = os.path.basename(file_path)
        
        print(f"📤 上传文件: {file_name}")
        
        # 获取上传链接
        upload_info = self.get_upload_urls([{"name": file_name}], model_version, **options)
        
        if not upload_info:
            return None
        
        batch_id = upload_info['batch_id']
        upload_url = upload_info['file_urls'][0]
        
        # 上传文件
        with open(file_path, 'rb') as f:
            response = requests.put(upload_url, data=f, timeout=300)
        
        if response.status_code == 200:
            print(f"✅ 上传成功，batch_id: {batch_id}")
            return batch_id
        else:
            print(f"❌ 上传失败: {response.status_code}")
            return None

# 使用示例
if __name__ == '__main__':
    api = MinerUAPI()
    
    print("\n" + "="*60)
    print("MinerU API 功能演示")
    print("="*60)
    
    # 示例1: 解析在线PDF
    print("\n示例1: 解析在线PDF")
    pdf_url = "https://cdn-mineru.openxlab.org.cn/demo/example.pdf"
    result = api.parse_and_wait(pdf_url, model_version='vlm')
    
    if result:
        print(f"📦 下载结果: {result.get('full_zip_url')}")
    
    print("\n" + "="*60)
