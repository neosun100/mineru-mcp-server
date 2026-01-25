#!/usr/bin/env python3
"""
批量登录 - 智能检测版本
自动检测登录成功，无需按回车
"""
import json, time, requests, random, yaml
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

def load_accounts():
    # 配置文件在项目根目录
    project_root = Path(__file__).parent.parent
    config_file = project_root / 'accounts.yaml'
    with open(config_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)['accounts']

def save_all_tokens(tokens):
    # Token文件在项目根目录
    project_root = Path(__file__).parent.parent
    token_file = project_root / 'all_tokens.json'
    with open(token_file, 'w') as f:
        json.dump(tokens, f, indent=2, ensure_ascii=False)

def type_human(page, selector, text):
    page.locator(selector).click()
    time.sleep(random.uniform(0.3, 0.6))
    for char in text:
        page.keyboard.type(char)
        time.sleep(random.uniform(0.08, 0.18))
    time.sleep(random.uniform(0.4, 0.8))

def login_account(account, browser, all_tokens):
    """登录单个账户"""
    email, password, name = account['email'], account['password'], account['name']
    
    print(f"\n{'='*60}")
    print(f"[{name}] {email}")
    print(f"{'='*60}")
    
    page = browser.new_page()
    page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    print("🌐 访问...")
    page.goto('https://mineru.net/apiManage/token')
    time.sleep(2)
    
    print("📝 输入...")
    type_human(page, 'input[placeholder="邮箱/手机号/用户名"]', email)
    time.sleep(0.5)
    type_human(page, 'input[type="password"]', password)
    time.sleep(1)
    
    print("🖱️  登录...")
    page.locator('button:has-text("登录")').click()
    time.sleep(3)
    
    print(f"⏸️  请手动点击验证 - {name}")
    print("🔄 自动检测中（最多60秒）...")
    
    # 智能检测
    for i in range(60):
        time.sleep(1)
        
        cookies = {c['name']: c['value'] for c in page.context.cookies() 
                  if c['name'] in ['uaa-token', 'opendatalab_session']}
        url = page.url
        
        if len(cookies) >= 2 and 'apiManage/token' in url and 'login' not in url:
            print(f"✅ 登录成功！（{i+1}秒）")
            
            uaa_token = cookies['uaa-token']
            headers = {'authorization': f'Bearer {uaa_token}', 'content-type': 'application/json'}
            
            # 删除旧 Token（如果有）
            r = requests.get('https://mineru.net/api/v4/tokens', headers=headers, timeout=10)
            if r.status_code == 200:
                token_list = r.json()['data'].get('list', [])
                if token_list:
                    print(f"🗑️  删除 {len(token_list)} 个旧 Token...")
                    for token in token_list:
                        requests.delete(f'https://mineru.net/api/v4/tokens/{token["id"]}', headers=headers)
            
            # 创建新 Token
            ts = datetime.now().strftime("%Y%m%d%H%M%S")
            token_name = f"token-{ts}"
            
            r = requests.post('https://mineru.net/api/v4/tokens', headers=headers, json={"token_name": token_name}, timeout=10)
            
            if r.status_code == 200:
                result = r.json()['data']
                print(f"✅ Token: {token_name}")
                
                all_tokens[email] = {
                    'name': name,
                    'token_name': token_name,
                    'token': result['token'],
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'expired_at': result['expired_at']
                }
                
                page.close()
                return True
            else:
                print(f"❌ Token 创建失败: {r.status_code}")
        
        if (i+1) % 10 == 0:
            print(f"  [{i+1}s]...")
    
    print("❌ 超时")
    page.close()
    return False

def main():
    print("="*60)
    print("批量登录所有账户（智能检测）")
    print("="*60)
    
    accounts = load_accounts()
    all_tokens = {}
    
    print(f"\n共 {len(accounts)} 个账户")
    print("每个账户只需手动点击验证，无需按回车\n")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
        
        success_count = 0
        for i, account in enumerate(accounts, 1):
            print(f"\n[{i}/{len(accounts)}]")
            
            if login_account(account, browser, all_tokens):
                success_count += 1
                save_all_tokens(all_tokens)
            
            if i < len(accounts):
                time.sleep(2)
        
        browser.close()
    
    print("\n" + "="*60)
    print("批量登录完成")
    print("="*60)
    print(f"成功: {success_count}/{len(accounts)}")
    print(f"Token 已保存到: all_tokens.json")
    
    # 显示结果
    print("\n" + "="*60)
    print("所有 Token:")
    print("="*60)
    for email, info in all_tokens.items():
        print(f"\n{info['name']} ({email})")
        print(f"  Token: {info['token_name']}")
        print(f"  过期: {info['expired_at']}")

if __name__ == '__main__':
    main()
