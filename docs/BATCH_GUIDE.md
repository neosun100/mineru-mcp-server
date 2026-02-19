# 批量账户管理指南

## ✅ 已完成

5个账户全部登录成功，Token 已创建并统一管理。

## 📁 文件说明

### accounts.yaml
包含5个账户的配置：
- 主账号: user1@example.com
- 账号2: user2@example.com
- 账号3: user3@example.com
- 账号4: user4@example.com
- 账号5: user5@example.com

### all_tokens.json
统一管理所有账户的 Token：
- 每个账户的 Token 名称
- Token 值
- 创建时间
- 过期时间

## 🚀 使用方式

### 批量登录（每14天一次）

```bash
python3 batch_login.py
```

**流程：**
- 自动依次登录5个账户
- 每个账户只需手动点击验证（5秒）
- 自动检测登录成功，无需按回车
- 自动删除旧 Token
- 自动创建新 Token
- 总耗时：< 3 分钟

### 查看所有 Token

```bash
python3 manage_tokens.py
```

### 单个账户登录

```bash
python3 login_complete.py
```

会提示选择账户。

## 📊 当前状态

```
✅ 主账号 - token-20260125013352 (过期: 2026-02-07)
✅ 账号2 - token-20260125013411 (过期: 2026-02-07)
✅ 账号3 - token-20260125013431 (过期: 2026-02-07)
✅ 账号4 - token-20260125013454 (过期: 2026-02-07)
✅ 账号5 - token-20260125013513 (过期: 2026-02-07)
```

## 🔒 安全说明

以下文件包含敏感信息，已被 .gitignore 保护：
- ✅ accounts.yaml - 账号密码
- ✅ all_tokens.json - 所有Token
- ✅ cookies.json - Cookie
- ✅ token_*.txt - 单个Token记录

## 💡 最佳实践

### 每14天维护

```bash
# 批量更新所有账户
python3 batch_login.py

# 查看状态
python3 manage_tokens.py
```

### 使用某个账户的 Token

```python
import json

# 读取所有Token
with open('all_tokens.json') as f:
    tokens = json.load(f)

# 使用主账号的Token
main_token = tokens['user1@example.com']['token']

# 调用API
import requests
headers = {'authorization': f'Bearer {main_token}'}
# ...
```

## 🎯 优势

- ✅ 统一管理5个账户
- ✅ 一次操作，全部更新
- ✅ Token 集中存储
- ✅ 方便查看和使用
- ✅ 安全可靠

---

**✅ 批量账户管理已完成！**
