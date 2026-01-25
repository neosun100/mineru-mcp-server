#!/usr/bin/env python3
"""
MinerU KIE SDK 封装 - 集成Token管理和负载均衡
"""
import json
import random
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

try:
    from mineru_kie_sdk import MineruKIEClient
except ImportError:
    print("❌ 请先安装: uv pip install mineru-kie-sdk")
    exit(1)


class MinerUKIEWrapper:
    """MinerU KIE SDK 封装 - 自动Token管理"""
    
    def __init__(self, pipeline_id: str, tokens_file='all_tokens.json'):
        """
        初始化
        
        Args:
            pipeline_id: Pipeline ID（从MinerU网站获取）
            tokens_file: Token文件路径
        """
        self.pipeline_id = pipeline_id
        self.tokens_file = tokens_file
        self.tokens = self._load_tokens()
        self.base_url = "https://mineru.net/api/kie"
        
        if not self.tokens:
            raise ValueError("未找到Token，请先运行 batch_login.py")
        
        print(f"✅ 已加载 {len(self.tokens)} 个账户")
        self._check_tokens()
    
    def _load_tokens(self) -> Dict:
        """加载Token"""
        try:
            with open(self.tokens_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def _check_tokens(self):
        """检查Token过期"""
        expired = []
        for email, info in self.tokens.items():
            try:
                token_name = info['token_name']
                timestamp_str = token_name.replace('token-', '')
                created_time = datetime.strptime(timestamp_str, '%Y%m%d%H%M%S')
                days_passed = (datetime.now() - created_time).days
                if days_passed >= 13:
                    expired.append(info['name'])
            except:
                pass
        
        if expired:
            print(f"⚠️  {len(expired)} 个账户Token即将过期")
            print(f"💡 请运行: python3 batch_login.py\n")
        else:
            print("✅ 所有Token有效")
    
    def _get_random_token(self) -> str:
        """随机选择Token（负载均衡）"""
        email = random.choice(list(self.tokens.keys()))
        print(f"🔄 使用账户: {email}")
        return self.tokens[email]['token']
    
    def create_client(self) -> MineruKIEClient:
        """
        创建KIE客户端（自动负载均衡）
        
        Returns:
            MineruKIEClient实例
        """
        token = self._get_random_token()
        
        # 创建客户端时传入token
        client = MineruKIEClient(
            base_url=self.base_url,
            pipeline_id=self.pipeline_id,
            timeout=300
        )
        
        # 设置token到headers
        client.session.headers['Authorization'] = f'Bearer {token}'
        
        return client
    
    def process_file(self, file_path: str, timeout: int = 60, 
                     poll_interval: int = 5) -> Optional[Dict]:
        """
        处理单个文件（上传 + 解析 + 提取）
        
        Args:
            file_path: 文件路径
            timeout: 超时时间（秒）
            poll_interval: 轮询间隔（秒）
        
        Returns:
            处理结果
        """
        print(f"\n📄 处理文件: {file_path}")
        
        # 创建客户端
        client = self.create_client()
        
        try:
            # 上传文件
            print("📤 上传中...")
            file_ids = client.upload_file(file_path)
            print(f"✅ 上传成功，文件ID: {file_ids}")
            
            # 获取结果
            print("⏳ 等待处理...")
            results = client.get_result(timeout=timeout, poll_interval=poll_interval)
            
            # 显示结果
            if results.get('parse'):
                print("✅ 解析完成")
            if results.get('split'):
                print("✅ 分割完成")
            if results.get('extract'):
                print("✅ 提取完成")
            
            return results
            
        except ValueError as e:
            print(f"❌ 参数错误: {e}")
        except TimeoutError as e:
            print(f"⏱️  超时: {e}")
        except Exception as e:
            print(f"❌ 处理失败: {e}")
        
        return None


# 使用示例
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("用法: python3 mineru_kie_wrapper.py <pipeline_id> <file_path>")
        print("示例: python3 mineru_kie_wrapper.py 12345 document.pdf")
        sys.exit(1)
    
    pipeline_id = sys.argv[1]
    file_path = sys.argv[2]
    
    # 创建封装
    wrapper = MinerUKIEWrapper(pipeline_id=pipeline_id)
    
    # 处理文件
    results = wrapper.process_file(file_path, timeout=120)
    
    if results:
        print("\n" + "="*60)
        print("处理结果:")
        print("="*60)
        
        if results.get('parse'):
            print("\n📋 解析结果:")
            print(json.dumps(results['parse'], indent=2, ensure_ascii=False))
        
        if results.get('split'):
            print("\n✂️  分割结果:")
            print(json.dumps(results['split'], indent=2, ensure_ascii=False))
        
        if results.get('extract'):
            print("\n📊 提取结果:")
            print(json.dumps(results['extract'], indent=2, ensure_ascii=False))
