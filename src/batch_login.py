#!/usr/bin/env python3
"""
批量登录 - 全自动版本（支持 headless）
自动点击登录、自动点击阿里云验证码、自动检测登录成功
默认 headless 模式，可用 --headed 参数打开浏览器界面
"""
import json, time, requests, random, yaml, sys
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).parent.parent
HEADED = '--headed' in sys.argv

STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
delete navigator.__proto__.webdriver;
Object.defineProperty(navigator, 'plugins', {
    get: () => {
        const p = [
            {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer'},
            {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
            {name: 'Native Client', filename: 'internal-nacl-plugin'},
        ];
        p.length = 3; return p;
    }
});
Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en-US', 'en']});
window.chrome = {runtime: {}, loadTimes: function(){}, csi: function(){}};
const origQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (p) => (
    p.name === 'notifications' ? Promise.resolve({state: Notification.permission}) : origQuery(p)
);
Object.defineProperty(navigator, 'platform', {get: () => 'MacIntel'});
Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
const getParam = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = function(p) {
    if (p === 37445) return 'Intel Inc.';
    if (p === 37446) return 'Intel Iris OpenGL Engine';
    return getParam.call(this, p);
};
"""

def load_accounts():
    with open(PROJECT_ROOT / 'accounts.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)['accounts']

def save_all_tokens(tokens):
    with open(PROJECT_ROOT / 'all_tokens.json', 'w') as f:
        json.dump(tokens, f, indent=2, ensure_ascii=False)

def type_human(page, selector, text):
    page.locator(selector).click()
    time.sleep(random.uniform(0.3, 0.6))
    for char in text:
        page.keyboard.type(char)
        time.sleep(random.uniform(0.08, 0.18))
    time.sleep(random.uniform(0.4, 0.8))

def click_captcha(page):
    """点击阿里云验证码 checkbox"""
    for attempt in range(15):
        try:
            el = page.locator('#aliyunCaptcha-checkbox-icon')
            if el.is_visible(timeout=2000):
                el.click()
                print(f"  🤖 点击验证码 (第{attempt+1}次)")
                time.sleep(3)
                if not page.locator('#aliyunCaptcha-window-popup.window-show').is_visible(timeout=3000):
                    print("  ✅ 验证通过！")
                    return True
        except:
            pass
        time.sleep(1)
    return False

def login_account(account, browser, all_tokens):
    email, password, name = account['email'], account['password'], account['name']

    print(f"\n{'='*60}")
    print(f"[{name}] {email}")
    print(f"{'='*60}")

    context = browser.new_context(
        viewport={'width': 1280, 'height': 720},
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        locale='zh-CN',
        timezone_id='Asia/Shanghai',
    )
    page = context.new_page()
    page.add_init_script(STEALTH_JS)

    print("🌐 访问...")
    page.goto('https://mineru.net/apiManage/token', wait_until='networkidle')
    time.sleep(2)

    print("🖱️  点击登录...")
    try:
        page.get_by_text("登录", exact=True).first.click(timeout=10000)
        time.sleep(3)
    except:
        print("  ⚠️  未找到登录按钮")
        context.close()
        return False

    try:
        page.wait_for_selector('input[placeholder="邮箱/手机号/用户名"]', timeout=10000)
    except:
        print("  ⚠️  登录表单未出现")
        context.close()
        return False

    print("📝 输入...")
    type_human(page, 'input[placeholder="邮箱/手机号/用户名"]', email)
    time.sleep(0.5)
    type_human(page, 'input[type="password"]', password)
    time.sleep(1)

    print("🖱️  提交...")
    page.locator('button.loginButton--wFHGh').click()
    time.sleep(4)

    print("🔍 处理验证码...")
    captcha_ok = click_captcha(page)
    if not captcha_ok:
        print(f"  ⏸️  验证码未自动通过 - {name}")

    print("🔄 检测中（最多60秒）...")
    for i in range(60):
        time.sleep(1)
        cookies = {c['name']: c['value'] for c in context.cookies()
                  if c['name'] in ['uaa-token', 'opendatalab_session']}

        if len(cookies) >= 2:
            print(f"✅ 登录成功！（{i+1}秒）")
            uaa_token = cookies['uaa-token']
            headers = {'authorization': f'Bearer {uaa_token}', 'content-type': 'application/json'}

            r = requests.get('https://mineru.net/api/v4/tokens', headers=headers, timeout=10)
            if r.status_code == 200:
                token_list = r.json()['data'].get('list', [])
                if token_list:
                    print(f"🗑️  删除 {len(token_list)} 个旧 Token...")
                    for token in token_list:
                        requests.delete(f'https://mineru.net/api/v4/tokens/{token["id"]}', headers=headers)

            ts = datetime.now().strftime("%Y%m%d%H%M%S")
            token_name = f"token-{ts}"
            r = requests.post('https://mineru.net/api/v4/tokens', headers=headers,
                            json={"token_name": token_name}, timeout=10)

            if r.status_code == 200:
                result = r.json()['data']
                print(f"✅ Token: {token_name}")
                all_tokens[email] = {
                    'name': name, 'token_name': token_name, 'token': result['token'],
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'expired_at': result['expired_at']
                }
                context.close()
                return True
            else:
                print(f"❌ Token 创建失败: {r.status_code}")

        if (i+1) % 15 == 0:
            click_captcha(page)
            print(f"  [{i+1}s]...")

    print("❌ 超时")
    context.close()
    return False

def main():
    mode = "headed（有界面）" if HEADED else "headless（无界面）"
    print("="*60)
    print(f"批量登录（全自动 - {mode}）")
    print("="*60)

    accounts = load_accounts()
    all_tokens = {}
    print(f"\n共 {len(accounts)} 个账户\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=not HEADED,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
            ]
        )

        success_count = 0
        for i, account in enumerate(accounts, 1):
            print(f"\n[{i}/{len(accounts)}]")
            if login_account(account, browser, all_tokens):
                success_count += 1
                save_all_tokens(all_tokens)
            if i < len(accounts):
                time.sleep(2)

        browser.close()

    print(f"\n{'='*60}")
    print(f"完成: {success_count}/{len(accounts)}")
    print(f"Token 已保存: all_tokens.json")
    print(f"{'='*60}")
    for email, info in all_tokens.items():
        print(f"\n{info['name']} ({email})")
        print(f"  Token: {info['token_name']}")
        print(f"  过期: {info['expired_at']}")

if __name__ == '__main__':
    main()
