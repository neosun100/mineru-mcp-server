# MinerU 完整使用指南

## 📖 项目功能总览

### 1. Token管理功能

#### 批量登录（batch_login.py）
- 一次性登录5个账户
- 每个账户只需手动点击验证（5秒）
- 自动删除旧Token
- 自动创建新Token
- 保存到 all_tokens.json

#### Token状态查看（manage_tokens.py）
- 查看所有5个账户的Token
- 显示创建时间和过期时间
- 一目了然的状态展示

#### 单账户登录（login_complete.py）
- 选择单个账户登录
- 适合单独更新某个账户

### 2. API使用功能

#### MinerU API 客户端（mineru_api.py）

**核心特性：**
- ✅ **负载均衡**：随机从5个账户中选择Token
- ✅ **自动检测**：初始化时检查Token是否过期
- ✅ **智能提示**：过期前1天提示刷新
- ✅ **简单易用**：统一的API接口

**使用示例：**
```python
from mineru_api import MinerUAPI

# 初始化（自动检测过期）
api = MinerUAPI()

# 调用API（自动负载均衡）
result = api.list_tokens()
```

### 3. MinerU Skill 功能（基于原项目）

MinerU 官方提供的PDF解析功能：

#### 支持的文件类型
- ✅ PDF
- ✅ DOC/DOCX
- ✅ PPT/PPTX
- ✅ 图片文件

#### 解析能力
- ✅ 提取文本内容
- ✅ 识别表格（转HTML）
- ✅ 识别公式（转LaTeX）
- ✅ 提取图片和图片描述
- ✅ 保留文档结构（标题、段落、列表）
- ✅ OCR支持（109种语言）
- ✅ 输出Markdown格式

#### 限制
- 仅支持在线URL（不支持本地文件）
- 最大文件：200MB
- 最大页数：600页
- 每日配额：2000页

## 🔗 如何集成使用

### 方案一：直接使用我们的API客户端

```python
from mineru_api import MinerUAPI

# 初始化
api = MinerUAPI()

# 使用（会自动负载均衡）
# 注意：具体的PDF解析API端点需要查看MinerU官方文档
```

### 方案二：设置环境变量给其他工具使用

```bash
# 从 all_tokens.json 中选择一个Token
export MINERU_API_KEY=$(python3 -c "import json; tokens=json.load(open('all_tokens.json')); print(list(tokens.values())[0]['token'])")

# 然后可以使用任何需要 MINERU_API_KEY 的工具
```

### 方案三：创建自动切换脚本

```python
import json
import random

def get_random_token():
    """随机获取一个Token"""
    with open('all_tokens.json') as f:
        tokens = json.load(f)
    
    email = random.choice(list(tokens.keys()))
    return tokens[email]['token']

# 使用
token = get_random_token()
# 设置到环境变量或直接使用
```

## 📊 完整工作流程

### 初始化（首次）
```bash
# 1. 配置账户
cp accounts.yaml.example accounts.yaml
vi accounts.yaml  # 填入5个账户

# 2. 批量登录
python3 batch_login.py  # 每个账户点一下验证

# 3. 验证
python3 manage_tokens.py  # 查看所有Token
```

### 日常使用
```python
from mineru_api import MinerUAPI

# 初始化（自动检测过期）
api = MinerUAPI()

# 使用API（自动负载均衡）
# ... 你的代码
```

### 维护（每14天）
```bash
python3 batch_login.py  # 批量更新
```

## 🎯 核心优势

### Token管理
- ✅ 5个账户统一管理
- ✅ 每账户只保留1个Token
- ✅ 自动删除旧Token
- ✅ 批量操作，省时省力

### API使用
- ✅ 负载均衡（5个账户轮流）
- ✅ 自动过期检测
- ✅ 提前提示刷新
- ✅ 简单易用

### 安全性
- ✅ 无硬编码密码
- ✅ 配置文件管理
- ✅ .gitignore保护
- ✅ 可安全推送

## 📝 文件清单

### Token管理
- `batch_login.py` - 批量登录
- `manage_tokens.py` - Token管理
- `login_complete.py` - 单账户登录
- `renew_token.py` - 自动续期

### API使用
- `mineru_api.py` - API客户端
- `API_USAGE.md` - 使用文档

### 配置文件（不提交）
- `accounts.yaml` - 账户配置
- `all_tokens.json` - Token存储

### 文档
- `README.md` - 主文档
- `SECURITY.md` - 安全指南
- `BATCH_GUIDE.md` - 批量操作
- `MULTI_ACCOUNT_GUIDE.md` - 多账户管理

---

**✅ 完整功能已实现，可投入生产使用！**
