#!/usr/bin/env python3
"""
批量管理所有账户的 Token
"""
import json, yaml, sys
from datetime import datetime

def load_accounts():
    with open('accounts.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)['accounts']

def load_all_tokens():
    """加载所有账户的 Token"""
    try:
        with open('all_tokens.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_all_tokens(tokens):
    """保存所有账户的 Token"""
    with open('all_tokens.json', 'w') as f:
        json.dump(tokens, f, indent=2, ensure_ascii=False)

def show_all_tokens():
    """显示所有账户的 Token 状态"""
    tokens = load_all_tokens()
    accounts = load_accounts()
    
    print("="*60)
    print("所有账户 Token 状态")
    print("="*60)
    
    if not tokens:
        print("❌ 暂无 Token，请先运行 batch_login.py")
        return
    
    for account in accounts:
        email = account['email']
        name = account['name']
        
        if email in tokens:
            token_info = tokens[email]
            print(f"\n✅ {name} ({email})")
            print(f"   Token: {token_info['token_name']}")
            print(f"   创建: {token_info['created_at']}")
            print(f"   过期: {token_info['expired_at']}")
        else:
            print(f"\n❌ {name} ({email})")
            print(f"   未登录")
    
    print("\n" + "="*60)

if __name__ == '__main__':
    show_all_tokens()
