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
    """MinerU API 客户端 - 支持多账户负载均衡 + 自动Token刷新"""
    
    def __init__(self, tokens_file='all_tokens.json', auto_refresh=True):
        """
        初始化 MinerU API 客户端
        
        Args:
            tokens_file: Token配置文件路径
            auto_refresh: 是否自动检测并刷新过期Token
        """
        self.tokens_file = tokens_file
        self.auto_refresh = auto_refresh
        self.tokens = self._load_tokens()
        self.base_url = 'https://mineru.net/api/v4'
        
        if not self.tokens:
            raise ValueError("未找到可用的Token，请先运行 batch_login.py")
        
        print(f"✅ 已加载 {len(self.tokens)} 个账户的Token")
        
        # 自动检测Token是否过期
        if self.auto_refresh:
            self._check_and_refresh_tokens()
    
    def _load_tokens(self) -> Dict:
        """加载所有Token"""
        try:
            with open(self.tokens_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def _check_token_expiry(self, token_name: str) -> bool:
        """
        检查Token是否过期
        Token名称格式: token-20260125013352
        从名称中提取创建时间，判断是否超过14天
        """
        try:
            # 提取时间戳: token-YYYYMMDDHHmmss
            timestamp_str = token_name.replace('token-', '')
            from datetime import datetime, timedelta
            
            # 解析创建时间
            created_time = datetime.strptime(timestamp_str, '%Y%m%d%H%M%S')
            
            # 计算是否过期（14天）
            now = datetime.now()
            days_passed = (now - created_time).days
            
            return days_passed >= 13  # 提前1天刷新
        except:
            return False
    
    def _check_and_refresh_tokens(self):
        """检查所有Token，如果有过期的则提示刷新"""
        expired_accounts = []
        
        for email, token_info in self.tokens.items():
            token_name = token_info['token_name']
            if self._check_token_expiry(token_name):
                expired_accounts.append(token_info['name'])
        
        if expired_accounts:
            print(f"\n⚠️  检测到 {len(expired_accounts)} 个账户Token即将过期:")
            for name in expired_accounts:
                print(f"   - {name}")
            print(f"\n💡 建议运行: python3 batch_login.py")
            print(f"   或运行: python3 login_complete.py 单独更新\n")
        else:
            print("✅ 所有Token有效期正常")
    
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
