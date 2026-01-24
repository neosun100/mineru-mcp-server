#!/usr/bin/env python3
"""
MinerU 人机协作登录 - 支持多账号
从配置文件读取账号，不再硬编码
"""
import json, time, requests, random, yaml, sys, os
from datetime import datetime
from playwright.sync_api import sync_playwright

def load_accounts():
    """从配置文件加载账号"""
    try:
        with open('accounts.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config['accounts']
    except FileNotFoundError:
        print("❌ 未找到 accounts.yaml")
        print("💡 请复制 accounts.yaml.example 为 accounts.yaml 并填入账号信息")
        sys.exit(1)

def select_account(accounts):
    """选择账号"""
    if len(accounts) == 1:
        return accounts[0]
    
    print("\n请选择账号:")
    for i, acc in enumerate(accounts, 1):
        print(f"  {i}. {acc['name']} ({acc['email']})")
    
    while True:
        try:
            choice = int(input("\n输入序号: "))
            if 1 <= choice <= len(accounts):
                return accounts[choice - 1]
        except:
            pass
        print("❌ 无效选择")

def type_human(page, selector, text):
    """之前成功的打字方式"""
    page.locator(selector).click()
    time.sleep(random.uniform(0.4, 0.8))
    for i, char in enumerate(text):
        if i > 0 and random.random() < 0.12: 
            time.sleep(random.uniform(0.5, 1.2))
        page.keyboard.type(char)
        time.sleep(random.uniform(0.08, 0.22))
    time.sleep(random.uniform(0.5, 1))

print("="*60)
print("MinerU 登录助手")
print("="*60)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
    page = browser.new_page()
    page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    print("\n🌐 访问...")
    page.goto('https://mineru.net/apiManage/token')
    time.sleep(3)
    
    # 滚动（之前成功的方式）
    page.mouse.wheel(0, random.randint(80, 150))
    time.sleep(1)
    page.mouse.wheel(0, -random.randint(50, 100))
    time.sleep(1.5)
    
    print("📝 输入账号...")
    type_human(page, 'input[placeholder="邮箱/手机号/用户名"]', email)
    
    print("📝 输入密码...")
    type_human(page, 'input[type="password"]', password)
    
    print("🖱️  点击登录...")
    page.locator('button:has-text("登录")').click()
    time.sleep(3)
    
    print("\n" + "="*60)
    print("⏸️  请手动完成验证")
    print("="*60)
    print("👉 点击【确认您不是机器人】")
    print("👉 等待跳转到 Token 页面")
    print("👉 我会自动检测，不用管终端")
    print("="*60)
    
    print("\n🔄 智能检测中（最多90秒）...\n")
    
    success = False
    for i in range(90):
        time.sleep(1)
        
        # 提取所有相关 Cookie
        all_cookies = page.context.cookies()
        cookies = {}
        for c in all_cookies:
            if c['name'] in ['uaa-token', 'opendatalab_session', 'acw_tc', 'ssouid', 'MINERU_LOCALE', 'i18next']:
                cookies[c['name']] = c['value']
        
        url = page.url
        
        # 成功条件
        has_main_cookies = 'uaa-token' in cookies and 'opendatalab_session' in cookies
        on_token_page = 'apiManage/token' in url and 'login' not in url
        
        if has_main_cookies and on_token_page:
            print(f"✅ 登录成功！（{i+1}秒）\n")
            success = True
            break
        
        if (i + 1) % 5 == 0:
            status = f"Cookie:{len(cookies)} | "
            status += "Token页✓" if on_token_page else "登录页"
            print(f"  [{i+1:2d}s] {status}")
    
    if success:
        # 保存所有 Cookie
        with open('cookies.json', 'w') as f:
            json.dump(cookies, f, indent=2)
        print(f"✅ 已保存 {len(cookies)} 个 Cookie\n")
        
        # 准备请求头
        uaa_token = cookies.get('uaa-token')
        headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
            'authorization': f'Bearer {uaa_token}'
        }
        
        # 删除所有旧 Token
        print("🗑️  删除所有旧 Token...")
        r = requests.get('https://mineru.net/api/v4/tokens', headers=headers)
        if r.status_code == 200:
            tokens = r.json()['data'].get('list', [])
            if tokens:
                print(f"   发现 {len(tokens)} 个旧 Token")
                for token in tokens:
                    requests.delete(f'https://mineru.net/api/v4/tokens/{token["id"]}', headers=headers)
                    print(f"   ✅ 已删除: {token['token_name']}")
                print("✅ 所有旧 Token 已删除\n")
        
        # 创建新 Token
        print("📝 创建新 Token...")
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        name = f"token-{ts}"
        
        r = requests.post('https://mineru.net/api/v4/tokens',
                         headers=headers,
                         json={"token_name": name})
        
        if r.status_code == 200:
            result = r.json()['data']
            token = result['token']
            print(f"\n{'='*60}")
            print("🎉 完全成功！")
            print(f"{'='*60}")
            print(f"📝 名称: {name}")
            print(f"⏰ 过期: {result['expired_at']}")
            print(f"🔑 Token: {token}")
            print(f"💡 现在只有 1 个有效 Token")
            print(f"{'='*60}\n")
            
            with open(f'token_{ts}.txt', 'w') as f:
                f.write(f"名称: {name}\n")
                f.write(f"创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"过期时间: {result['expired_at']}\n")
                f.write(f"Token: {token}\n")
            
            print(f"✅ 已保存到 token_{ts}.txt")
        else:
            print(f"\n❌ Token 创建失败: {r.status_code}")
            print(f"响应: {r.text}")
            print(f"\n💡 Cookie 已保存到 cookies.json")
    else:
        print(f"\n❌ 超时未检测到登录成功")
    
    print("\n按回车关闭...")
    input()
    browser.close()

if __name__ == '__main__':
    print("="*60)
    print("MinerU 人机协作登录（多账号支持）")
    print("="*60)
    
    # 加载并选择账号
    accounts = load_accounts()
    account = select_account(accounts)
    
    email = account['email']
    password = account['password']
    
    print(f"\n使用账号: {account['name']} ({email})")
    print("="*60)
    
    # 执行登录流程（原有代码会继续执行）
