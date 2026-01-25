# MinerU API 使用指南

## 🎯 功能特性

### 1. 负载均衡
- 自动从5个账户中随机选择Token
- 分散API调用压力
- 提高可用性

### 2. 统一管理
- 所有Token集中管理
- 一次更新，全部可用
- 自动Token轮换

### 3. 简单易用
```python
from mineru_api import MinerUAPI

# 初始化（自动加载5个账户）
api = MinerUAPI()

# 调用API（自动负载均衡）
result = api.list_tokens()
```

## 📖 使用方法

### 基础使用

```python
from mineru_api import MinerUAPI

# 初始化
api = MinerUAPI()

# 列出Token
tokens = api.list_tokens()

# 获取账户信息
info = api.get_account_info()
```

### 负载均衡演示

```python
# 连续调用会自动使用不同账户
for i in range(10):
    api.list_tokens()  # 每次随机选择账户
```

## 🔧 维护

### 更新所有Token（每14天）

```bash
python3 batch_login.py
```

### 查看Token状态

```bash
python3 manage_tokens.py
```

## 📊 当前状态

- ✅ 5个账户
- ✅ 5个Token
- ✅ 负载均衡
- ✅ 统一管理

---

**✅ MinerU API 已封装完成，可以直接使用！**
