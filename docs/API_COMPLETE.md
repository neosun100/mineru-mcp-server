# MinerU API 完整功能文档

## 📋 API 功能对比

### 官方提供的API功能

| 功能 | 端点 | 说明 |
|------|------|------|
| **智能解析** | | |
| 创建单文件任务 | POST /extract/task | 解析PDF/DOC/PPT/图片/HTML |
| 获取任务结果 | GET /extract/task/{task_id} | 查询解析状态和结果 |
| 创建批量任务 | POST /extract/task/batch | 批量解析多个文件 |
| 获取批量结果 | GET /extract-results/batch/{batch_id} | 查询批量任务结果 |
| **文件上传** | | |
| 获取上传链接 | POST /file-urls/batch | 获取文件上传URL |
| **文档抽取（KIE）** | | |
| 创建抽取任务 | POST /kie/task | 结构化信息抽取 |
| 获取抽取结果 | GET /kie/task/{task_id} | 查询抽取结果 |

### 我们的封装功能

| 功能 | 方法 | 说明 |
|------|------|------|
| **Token管理** | | |
| 批量登录 | batch_login.py | 5个账户统一登录 |
| Token查看 | manage_tokens.py | 查看所有Token状态 |
| 自动检测 | _check_token_expiry() | 检测Token是否过期 |
| **API调用** | | |
| 负载均衡 | _get_random_token() | 随机选择账户 |
| 单文件解析 | create_task() | 创建解析任务 |
| 等待结果 | parse_and_wait() | 解析并等待完成 |
| 批量解析 | create_batch_task() | 批量创建任务 |
| 文件上传 | upload_and_parse() | 上传本地文件并解析 |

## 🎯 完整功能清单

### 1. 智能解析功能

#### 支持的文件类型
- ✅ PDF
- ✅ DOC/DOCX
- ✅ PPT/PPTX
- ✅ PNG/JPG/JPEG
- ✅ HTML

#### 解析能力
- ✅ 文本提取
- ✅ 表格识别（转HTML）
- ✅ 公式识别（转LaTeX）
- ✅ 图片提取和描述
- ✅ 文档结构保留
- ✅ OCR（109种语言）
- ✅ 输出Markdown

#### 模型版本
- `pipeline` - 传统流水线模型
- `vlm` - 视觉语言模型（推荐）
- `MinerU-HTML` - HTML专用模型

### 2. 文档抽取功能（KIE）

#### 支持的场景
- ✅ 发票信息抽取
- ✅ 合同信息抽取
- ✅ 表单信息抽取
- ✅ 自定义字段抽取

#### 抽取方式
- Schema模式：预定义字段
- Prompt模式：自然语言描述

### 3. 批量处理功能

#### 批量解析
- 一次提交多个文件
- 统一管理任务
- 批量下载结果

#### 文件上传
- 获取上传链接
- 直接上传本地文件
- 自动触发解析

## 📊 限制说明

| 限制项 | 值 |
|--------|-----|
| 单文件大小 | 200MB |
| 最大页数 | 600页 |
| 每日高优先级额度 | 2000页 |
| 文件有效期 | 30天 |
| 批量任务最大文件数 | 100个 |

## 🚀 使用示例

### 示例1: 解析在线PDF

```python
from mineru_api import MinerUAPI

api = MinerUAPI()

# 解析并等待结果
result = api.parse_and_wait(
    file_url="https://example.com/demo.pdf",
    model_version="vlm",
    is_ocr=False,
    enable_formula=True,
    enable_table=True
)

if result:
    print(f"下载结果: {result['full_zip_url']}")
    print(f"Markdown: {result['md_url']}")
```

### 示例2: 上传本地文件

```python
api = MinerUAPI()

# 上传并解析
batch_id = api.upload_and_parse(
    file_path="/path/to/document.pdf",
    model_version="vlm"
)

# 等待结果
if batch_id:
    time.sleep(10)
    result = api.get_batch_result(batch_id)
```

### 示例3: 批量解析

```python
api = MinerUAPI()

# 批量创建任务
files = [
    {"url": "https://example.com/file1.pdf", "data_id": "1"},
    {"url": "https://example.com/file2.pdf", "data_id": "2"},
    {"url": "https://example.com/file3.pdf", "data_id": "3"}
]

batch_id = api.create_batch_task(files, model_version="vlm")

# 查询结果
if batch_id:
    result = api.get_batch_result(batch_id)
```

### 示例4: 解析HTML

```python
api = MinerUAPI()

# HTML专用模型
result = api.parse_and_wait(
    file_url="https://example.com/page.html",
    model_version="MinerU-HTML"
)
```

## 🔧 高级选项

### 解析选项

```python
options = {
    'is_ocr': False,              # 是否启用OCR
    'enable_formula': True,       # 是否识别公式
    'enable_table': True,         # 是否识别表格
    'enable_image_caption': True, # 是否生成图片描述
    'enable_layout_tree': True,   # 是否保留布局树
    'lang': 'auto'               # OCR语言（auto/chi_sim/eng等）
}

api.create_task(file_url, **options)
```

### 返回结果结构

```json
{
    "task_id": "xxx",
    "state": "done",
    "extract_progress": {
        "total_pages": 10,
        "extracted_pages": 10
    },
    "full_zip_url": "https://...",
    "md_url": "https://...",
    "md_content_url": "https://...",
    "layout_tree_url": "https://..."
}
```

## 💡 最佳实践

### 1. Token管理
```bash
# 每14天刷新一次
python3 batch_login.py
```

### 2. 负载均衡
```python
# API会自动从5个账户中随机选择
api = MinerUAPI()  # 自动负载均衡
```

### 3. 错误处理
```python
try:
    result = api.parse_and_wait(file_url)
    if result:
        # 处理结果
        pass
except Exception as e:
    print(f"错误: {e}")
```

### 4. 大文件处理
```python
# 对于大文件，使用上传方式
batch_id = api.upload_and_parse(
    file_path="/path/to/large.pdf",
    model_version="vlm"
)
```

## 🆚 与原Skill对比

| 特性 | 原Skill | 我们的封装 |
|------|---------|-----------|
| Token管理 | 手动 | ✅ 自动批量管理 |
| 负载均衡 | ❌ 无 | ✅ 5账户轮换 |
| 过期检测 | ❌ 无 | ✅ 自动检测 |
| 本地文件 | ❌ 不支持 | ✅ 支持上传 |
| 批量处理 | ❌ 无 | ✅ 完整支持 |
| 等待结果 | ❌ 需手动 | ✅ 自动等待 |

## 📝 完整API列表

### 智能解析
- `create_task()` - 创建单文件任务
- `get_task_result()` - 获取任务结果
- `parse_and_wait()` - 解析并等待完成
- `create_batch_task()` - 创建批量任务
- `get_batch_result()` - 获取批量结果

### 文件上传
- `get_upload_urls()` - 获取上传链接
- `upload_and_parse()` - 上传并解析

### Token管理
- `_load_tokens()` - 加载Token
- `_check_token_expiry()` - 检查过期
- `_get_random_token()` - 随机选择

---

**✅ 完整功能已实现，覆盖所有官方API！**
