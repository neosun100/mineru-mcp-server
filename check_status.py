#!/usr/bin/env python3
"""
检查当前 Token 状态
"""
import json, requests
from datetime import datetime

try:
    with open('cookies.json') as f:
        cookies = json.load(f)
    
    uaa_token = cookies['uaa-token']
    
    # 获取 Token 列表
    r = requests.get('https://mineru.net/api/v4/tokens',
                    headers={'authorization': f'Bearer {uaa_token}'})
    
    if r.status_code == 200:
        data = r.json()['data']
        print(f"✅ 当前有 {data['total']} 个 Token:\n")
        
        for token in data['list']:
            name = token['token_name']
            expired = token['expired_at']
            
            # 简单处理：只显示过期时间
            print(f"  - {name}")
            print(f"    过期: {expired}")
        
        print(f"\n💡 建议：剩余天数 < 3 时运行 renew_token.py 创建新 Token")
    else:
        print(f"❌ 获取失败: {r.status_code}")
        print("💡 可能需要重新登录: python3 login_complete.py")
        
except FileNotFoundError:
    print("❌ 未找到 cookies.json")
    print("💡 请先运行: python3 login_complete.py")
except Exception as e:
    print(f"❌ 错误: {e}")
