#!/usr/bin/env python3
"""
MinerU API 封装 - 负载均衡版本
自动从5个账户中随机选择Token，实现负载均衡
"""
import json
import requests
import random
from typing import Optional, Dict, Any

class MinerUAPI:
    """MinerU API 客户端 - 支持多账户负载均衡"""
    
    def __init__(self, tokens_file='all_tokens.json'):
        """
        初始化 MinerU API 客户端
        
        Args:
            tokens_file: Token配置文件路径
        """
        self.tokens_file = tokens_file
        self.tokens = self._load_tokens()
        self.base_url = 'https://mineru.net/api/v4'
        
        if not self.tokens:
            raise ValueError("未找到可用的Token，请先运行 batch_login.py")
        
        print(f"✅ 已加载 {len(self.tokens)} 个账户的Token")
    
    def _load_tokens(self) -> Dict:
        """加载所有Token"""
        try:
            with open(self.tokens_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def _get_random_token(self) -> tuple:
        """随机选择一个Token（负载均衡）"""
        email = random.choice(list(self.tokens.keys()))
        token_info = self.tokens[email]
        return email, token_info['token']
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        发送API请求（自动负载均衡）
        
        Args:
            method: HTTP方法（GET/POST/DELETE等）
            endpoint: API端点
            **kwargs: 其他请求参数
        """
        email, token = self._get_random_token()
        
        headers = kwargs.get('headers', {})
        headers['authorization'] = f'Bearer {token}'
        headers['accept'] = 'application/json'
        kwargs['headers'] = headers
        
        url = f"{self.base_url}/{endpoint}"
        
        print(f"🔄 使用账户: {email}")
        
        response = requests.request(method, url, **kwargs)
        return response
    
    def parse_pdf(self, pdf_url: str, **options) -> Dict[str, Any]:
        """
        解析PDF文档
        
        Args:
            pdf_url: PDF文件URL
            **options: 解析选项
        
        Returns:
            解析结果
        """
        print(f"📄 解析PDF: {pdf_url}")
        
        data = {
            'url': pdf_url,
            **options
        }
        
        response = self._make_request('POST', 'parse', json=data, timeout=300)
        
        if response.status_code == 200:
            print("✅ 解析成功")
            return response.json()
        else:
            print(f"❌ 解析失败: {response.status_code}")
            print(f"响应: {response.text}")
            return None
    
    def get_parse_status(self, task_id: str) -> Dict[str, Any]:
        """
        查询解析任务状态
        
        Args:
            task_id: 任务ID
        
        Returns:
            任务状态
        """
        response = self._make_request('GET', f'parse/{task_id}')
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    
    def list_tokens(self) -> Dict[str, Any]:
        """列出当前使用账户的所有Token"""
        response = self._make_request('GET', 'tokens')
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    
    def get_account_info(self) -> Dict[str, Any]:
        """获取当前使用账户的信息"""
        email, _ = self._get_random_token()
        return self.tokens[email]

# 使用示例
if __name__ == '__main__':
    # 初始化API客户端
    api = MinerUAPI()
    
    print("\n" + "="*60)
    print("MinerU API 测试")
    print("="*60)
    
    # 测试1: 列出Token
    print("\n测试1: 列出Token")
    result = api.list_tokens()
    if result and 'data' in result:
        print(f"✅ 当前账户有 {result['data']['total']} 个Token")
    else:
        print(f"⚠️  响应: {result}")
    
    # 测试2: 获取账户信息
    print("\n测试2: 获取账户信息")
    info = api.get_account_info()
    print(f"✅ 账户: {info['name']}")
    print(f"   Token: {info['token_name']}")
    print(f"   过期: {info['expired_at']}")
    
    # 测试3: 负载均衡测试
    print("\n测试3: 负载均衡测试（连续5次请求）")
    for i in range(5):
        print(f"\n请求 {i+1}:")
        api.list_tokens()
    
    print("\n" + "="*60)
    print("✅ 测试完成")
    print("="*60)
