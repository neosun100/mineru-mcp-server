# MinerU Token 自动续期 + API 封装

## 🎯 项目简介

完整的 MinerU API Token 管理和使用解决方案，支持：
- ✅ 5个账户批量管理
- ✅ 智能Token续期
- ✅ 负载均衡API调用
- ✅ 自动过期检测

## ✨ 核心功能

### 1. Token管理

#### 批量登录（每14天）
```bash
python3 batch_login.py
```
- 自动登录5个账户
- 每个账户只需手动点击验证（5秒）
- 自动删除旧Token
- 自动创建新Token
- 保存到 all_tokens.json

#### 查看Token状态
```bash
python3 manage_tokens.py
```

#### 单账户登录
```bash
python3 login_complete.py
```

### 2. API使用（负载均衡）

```python
from mineru_api import MinerUAPI

# 初始化（自动检测Token过期）
api = MinerUAPI()

# API会自动：
# 1. 检查Token是否过期（从token名称判断）
# 2. 如果过期，提示刷新
# 3. 随机选择账户（负载均衡）
# 4. 调用API

# 使用示例
result = api.list_tokens()
```

### 3. 自动过期检测

API初始化时会自动检测：
- 从Token名称提取创建时间（token-20260125013352）
- 计算距今天数
- 如果 >= 13天，提示刷新

### 4. 负载均衡

每次API调用随机选择账户：
- 5个账户轮流使用
- 分散API压力
- 提高可用性

## 📁 文件说明

### Token管理
- `batch_login.py` - 批量登录5个账户 ⭐
- `manage_tokens.py` - 查看所有Token状态
- `login_complete.py` - 单账户登录
- `renew_token.py` - 自动续期（单账户）

### API使用
- `mineru_api.py` - API客户端（负载均衡）⭐
- `API_USAGE.md` - 使用文档

### 配置文件（不提交）
- `accounts.yaml` - 5个账户配置
- `all_tokens.json` - 所有Token统一管理

### 测试
- `test_all.py` - 完整测试套件
- `check_status.py` - 状态检查

## 🚀 快速开始

### 1. 首次配置

```bash
# 创建账户配置
cp accounts.yaml.example accounts.yaml
vi accounts.yaml  # 填入5个账户

# 批量登录
python3 batch_login.py
```

### 2. 使用API

```python
from mineru_api import MinerUAPI

# 初始化
api = MinerUAPI()

# 调用API（自动负载均衡）
result = api.list_tokens()
```

### 3. 维护（每14天）

```bash
python3 batch_login.py
```

## 🔧 技术特性

### Token管理策略
- 每个账户只保留1个Token
- 自动删除所有旧Token
- Token命名：token-年月日时分秒
- 有效期：14天

### 负载均衡策略
- 随机选择账户
- 自动Token轮换
- 分散API压力

### 自动检测
- 从Token名称提取时间
- 自动计算剩余天数
- 提前1天提示刷新

## 📊 当前状态

```
✅ 5个账户全部就绪
✅ 5个Token全部有效
✅ 负载均衡正常工作
✅ 自动检测正常
```

## 🔒 安全说明

以下文件包含敏感信息，已被.gitignore保护：
- accounts.yaml - 账户配置
- all_tokens.json - 所有Token
- cookies.json - Cookie
- token_*.txt - Token记录

## 📖 完整文档

- README.md - 本文档
- SECURITY.md - 安全指南
- MULTI_ACCOUNT_GUIDE.md - 多账户管理
- BATCH_GUIDE.md - 批量操作指南
- API_USAGE.md - API使用文档

## 🏷️ 版本

- v1.2.0 - 安全增强 + 多账户支持
- v1.3.0 - 批量账户管理
- v1.4.0 - API封装 + 负载均衡 ⭐

---

**✅ 项目完成，可投入生产使用！**
