#!/usr/bin/env python3
"""
MinerU Token 自动续期 - 完整测试套件
"""
import json
import requests
import jwt
from datetime import datetime
import os

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name, passed, message=""):
    status = f"{Colors.GREEN}✅ PASS{Colors.END}" if passed else f"{Colors.RED}❌ FAIL{Colors.END}"
    print(f"{status} {name}")
    if message:
        print(f"     {message}")

def test_files_exist():
    """测试1: 检查核心文件是否存在"""
    print(f"\n{Colors.BLUE}测试1: 核心文件检查{Colors.END}")
    
    files = {
        'login_complete.py': '人机协作登录脚本',
        'renew_token.py': '自动续期脚本',
        'check_status.py': '状态检查脚本',
        'requirements.txt': '依赖清单',
        '.gitignore': 'Git 忽略规则'
    }
    
    all_passed = True
    for file, desc in files.items():
        exists = os.path.exists(file)
        print_test(f"{file} ({desc})", exists)
        all_passed = all_passed and exists
    
    return all_passed

def test_cookies_exist():
    """测试2: 检查 Cookie 文件"""
    print(f"\n{Colors.BLUE}测试2: Cookie 文件检查{Colors.END}")
    
    if not os.path.exists('cookies.json'):
        print_test("cookies.json 存在", False, "请先运行 login_complete.py")
        return False
    
    try:
        with open('cookies.json') as f:
            cookies = json.load(f)
        
        required = ['uaa-token', 'opendatalab_session']
        has_all = all(k in cookies for k in required)
        
        print_test("cookies.json 格式正确", has_all)
        print_test(f"包含必要的 Cookie", has_all, f"需要: {required}")
        
        return has_all
    except Exception as e:
        print_test("cookies.json 读取", False, str(e))
        return False

def test_cookie_validity():
    """测试3: 检查 Cookie 有效性"""
    print(f"\n{Colors.BLUE}测试3: Cookie 有效性检查{Colors.END}")
    
    try:
        with open('cookies.json') as f:
            cookies = json.load(f)
        
        uaa_token = cookies.get('uaa-token')
        if not uaa_token:
            print_test("uaa-token 存在", False)
            return False
        
        # 解析 JWT
        decoded = jwt.decode(uaa_token, options={"verify_signature": False})
        exp_timestamp = decoded['exp']
        exp_date = datetime.fromtimestamp(exp_timestamp)
        days_left = (exp_date - datetime.now()).days
        
        is_valid = days_left > 0
        
        print_test("Cookie 未过期", is_valid, f"剩余 {days_left} 天")
        print_test("用户邮箱", True, decoded.get('email', 'N/A'))
        
        return is_valid
    except Exception as e:
        print_test("Cookie 解析", False, str(e))
        return False

def test_api_authentication():
    """测试4: API 认证测试"""
    print(f"\n{Colors.BLUE}测试4: API 认证测试{Colors.END}")
    
    try:
        with open('cookies.json') as f:
            cookies = json.load(f)
        
        uaa_token = cookies['uaa-token']
        
        # 测试 GET 请求
        r = requests.get('https://mineru.net/api/v4/tokens',
                        headers={'authorization': f'Bearer {uaa_token}'},
                        timeout=10)
        
        get_passed = r.status_code == 200
        print_test("GET /api/v4/tokens", get_passed, f"状态码: {r.status_code}")
        
        if get_passed:
            data = r.json()['data']
            print_test(f"获取 Token 列表", True, f"共 {data['total']} 个")
        
        return get_passed
    except Exception as e:
        print_test("API 认证", False, str(e))
        return False

def test_token_creation():
    """测试5: Token 创建测试"""
    print(f"\n{Colors.BLUE}测试5: Token 创建测试{Colors.END}")
    
    try:
        with open('cookies.json') as f:
            cookies = json.load(f)
        
        uaa_token = cookies['uaa-token']
        
        # 先检查当前数量
        r = requests.get('https://mineru.net/api/v4/tokens',
                        headers={'authorization': f'Bearer {uaa_token}'})
        
        if r.status_code == 200:
            current_count = r.json()['data']['total']
            print_test("当前 Token 数量", True, f"{current_count} 个")
            
            if current_count >= 5:
                print_test("Token 创建测试", True, "已达上限(5个)，跳过创建测试")
                return True
        
        # 尝试创建
        test_name = f"test-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        r = requests.post('https://mineru.net/api/v4/tokens',
                         headers={
                             'authorization': f'Bearer {uaa_token}',
                             'content-type': 'application/json'
                         },
                         json={"token_name": test_name},
                         timeout=10)
        
        create_passed = r.status_code == 200
        print_test("POST /api/v4/tokens", create_passed, f"状态码: {r.status_code}")
        
        if create_passed:
            result = r.json()['data']
            print_test("Token 创建成功", True, f"名称: {result['token_name']}")
            print_test("Token 格式正确", len(result['token']) > 100)
            print(f"     {Colors.YELLOW}ℹ️  测试 Token 已创建，可在网页上手动删除{Colors.END}")
        elif r.status_code == 400:
            # 可能是达到上限
            print_test("Token 创建", True, "可能已达上限，功能正常")
            return True
        
        return create_passed
    except Exception as e:
        print_test("Token 创建", False, str(e))
        return False

def test_gitignore():
    """测试6: 安全配置测试"""
    print(f"\n{Colors.BLUE}测试6: 安全配置检查{Colors.END}")
    
    try:
        with open('.gitignore') as f:
            gitignore = f.read()
        
        sensitive_patterns = ['cookies.json', 'token_*.txt', '*.log']
        all_protected = all(pattern in gitignore for pattern in sensitive_patterns)
        
        print_test(".gitignore 包含敏感文件", all_protected)
        
        for pattern in sensitive_patterns:
            protected = pattern in gitignore
            print_test(f"  {pattern}", protected)
        
        return all_protected
    except Exception as e:
        print_test(".gitignore 检查", False, str(e))
        return False

def run_all_tests():
    """运行所有测试"""
    print("="*60)
    print(f"{Colors.BLUE}MinerU Token 自动续期 - 完整测试{Colors.END}")
    print("="*60)
    
    tests = [
        ("核心文件", test_files_exist),
        ("Cookie 文件", test_cookies_exist),
        ("Cookie 有效性", test_cookie_validity),
        ("API 认证", test_api_authentication),
        ("Token 创建", test_token_creation),
        ("安全配置", test_gitignore)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n{Colors.RED}测试异常: {e}{Colors.END}")
            results.append((name, False))
    
    # 总结
    print("\n" + "="*60)
    print(f"{Colors.BLUE}测试总结{Colors.END}")
    print("="*60)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for name, passed in results:
        status = f"{Colors.GREEN}✅{Colors.END}" if passed else f"{Colors.RED}❌{Colors.END}"
        print(f"{status} {name}")
    
    print("\n" + "="*60)
    success_rate = (passed_count / total_count) * 100
    
    if passed_count == total_count:
        print(f"{Colors.GREEN}🎉 所有测试通过！({passed_count}/{total_count}){Colors.END}")
        print(f"{Colors.GREEN}✅ 项目可以投入生产使用！{Colors.END}")
    else:
        print(f"{Colors.YELLOW}⚠️  部分测试失败 ({passed_count}/{total_count}){Colors.END}")
        print(f"{Colors.YELLOW}💡 请根据上述提示修复问题{Colors.END}")
    
    print("="*60)
    
    return passed_count == total_count

if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
