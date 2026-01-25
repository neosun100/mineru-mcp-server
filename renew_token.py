#!/usr/bin/env python3
"""
MinerU API Token 自动续期脚本
策略：删除所有旧 Token，只保留一个新的
"""
import json
import requests
from datetime import datetime
import jwt

def load_cookies():
    """加载保存的 cookies"""
    try:
        with open('cookies.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ 未找到 cookies.json，请先运行 login_complete.py")
        exit(1)

def check_cookie_expiry(token):
    """检查 Cookie 是否即将过期"""
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        exp_timestamp = decoded['exp']
        exp_date = datetime.fromtimestamp(exp_timestamp)
        days_left = (exp_date - datetime.now()).days
        
        print(f"🕐 Cookie 过期时间: {exp_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏳ 剩余天数: {days_left} 天")
        
        if days_left < 2:
            print("❌ Cookie 即将过期，请重新登录: python3 login_complete.py")
            return False
        return True
    except Exception as e:
        print(f"❌ Cookie 解析失败: {e}")
        return False

def delete_all_tokens(headers):
    """删除所有现有 Token"""
    try:
        # 获取所有 Token
        response = requests.get(
            'https://mineru.net/api/v4/tokens',
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"⚠️  获取 Token 列表失败: {response.status_code}")
            return False
        
        data = response.json()['data']
        tokens = data.get('list', [])
        
        if not tokens:
            print("ℹ️  没有现有 Token")
            return True
        
        print(f"🗑️  发现 {len(tokens)} 个旧 Token，开始删除...")
        
        deleted_count = 0
        for token in tokens:
            token_id = token['id']
            token_name = token['token_name']
            
            delete_response = requests.delete(
                f'https://mineru.net/api/v4/tokens/{token_id}',
                headers=headers,
                timeout=10
            )
            
            if delete_response.status_code == 200:
                print(f"   ✅ 已删除: {token_name}")
                deleted_count += 1
            else:
                print(f"   ⚠️  删除失败: {token_name} ({delete_response.status_code})")
        
        print(f"✅ 成功删除 {deleted_count}/{len(tokens)} 个 Token")
        return True
        
    except Exception as e:
        print(f"❌ 删除过程出错: {e}")
        return False

def create_new_token(headers):
    """创建新的 Token"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    token_name = f"token-{timestamp}"
    
    try:
        response = requests.post(
            'https://mineru.net/api/v4/tokens',
            headers=headers,
            json={"token_name": token_name},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()['data']
            token_value = result['token']
            
            print(f"\n✅ 新 Token 创建成功")
            print(f"📝 名称: {token_name}")
            print(f"⏰ 过期: {result['expired_at']}")
            print(f"🔑 Token: {token_value}")
            
            # 保存到文件
            with open(f'token_{timestamp}.txt', 'w') as f:
                f.write(f"名称: {token_name}\n")
                f.write(f"创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"过期时间: {result['expired_at']}\n")
                f.write(f"Token: {token_value}\n")
            
            return token_value
        else:
            print(f"❌ 创建失败: {response.status_code}")
            print(f"响应: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 创建过程出错: {e}")
        return None

def main():
    print("=" * 60)
    print("MinerU API Token 自动续期")
    print("策略：删除所有旧 Token，只保留一个新的")
    print("=" * 60)
    
    # 加载 cookies
    cookies = load_cookies()
    
    # 检查 Cookie 有效期
    if not check_cookie_expiry(cookies['uaa-token']):
        exit(1)
    
    print("\n" + "=" * 60)
    
    # 准备请求头
    headers = {
        'accept': 'application/json',
        'content-type': 'application/json',
        'authorization': f'Bearer {cookies["uaa-token"]}'
    }
    
    # 删除所有旧 Token
    if delete_all_tokens(headers):
        print("\n" + "=" * 60)
        
        # 创建新 Token
        token = create_new_token(headers)
        
        if token:
            print("\n" + "=" * 60)
            print("✅ Token 续期成功！")
            print("💡 现在只有 1 个有效 Token")
            print("=" * 60)
        else:
            print("\n❌ Token 创建失败")
    else:
        print("\n❌ 删除旧 Token 失败")

if __name__ == '__main__':
    main()
