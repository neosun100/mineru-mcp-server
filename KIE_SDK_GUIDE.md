# MinerU KIE SDK 使用指南

## 📖 什么是 KIE SDK

MinerU KIE (Knowledge Information Extraction) SDK 是官方提供的文档信息抽取工具，支持：
- 📄 文档解析（Parse）
- ✂️ 文档分割（Split）
- 📊 信息提取（Extract）

## 🎯 我们的封装优势

### 官方SDK
```python
from mineru_kie_sdk import MineruKIEClient

# 需要手动管理Token
client = MineruKIEClient(
    base_url="https://mineru.net/api/kie",
    pipeline_id=YOUR_PIPELINE_ID
)
# 需要手动设置Token...
```

### 我们的封装
```python
from mineru_kie_wrapper import MinerUKIEWrapper

# 自动Token管理 + 负载均衡
wrapper = MinerUKIEWrapper(pipeline_id=YOUR_PIPELINE_ID)
results = wrapper.process_file("document.pdf")
```

## 🚀 快速开始

### 1. 安装依赖（虚拟环境）

```bash
# 创建虚拟环境
cd /Users/jiasunm/Code/GenAI/MinerU-Token
uv venv

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
uv pip install mineru-kie-sdk requests pyyaml selenium
```

### 2. 获取 Pipeline ID

1. 访问 https://mineru.net/apiManage/kie-usage
2. 创建或选择一个 Pipeline
3. 点击"部署"
4. 复制 Pipeline ID

### 3. 使用封装

#### 方式一：命令行

```bash
source .venv/bin/activate
python3 mineru_kie_wrapper.py <pipeline_id> <file_path>

# 示例
python3 mineru_kie_wrapper.py 12345 invoice.pdf
```

#### 方式二：Python代码

```python
from mineru_kie_wrapper import MinerUKIEWrapper

# 初始化（自动Token管理）
wrapper = MinerUKIEWrapper(pipeline_id="12345")

# 处理文件
results = wrapper.process_file("invoice.pdf", timeout=120)

if results:
    # 解析结果
    parse_result = results.get('parse')
    
    # 分割结果
    split_result = results.get('split')
    
    # 提取结果
    extract_result = results.get('extract')
```

## 📊 功能对比

| 功能 | 官方SDK | 我们的封装 |
|------|---------|-----------|
| Token管理 | ❌ 手动 | ✅ 自动 |
| 负载均衡 | ❌ 无 | ✅ 5账户 |
| 过期检测 | ❌ 无 | ✅ 自动 |
| 文件上传 | ✅ | ✅ |
| 结果轮询 | ✅ | ✅ |
| 错误处理 | 基础 | ✅ 完整 |

## 🔧 支持的文件类型

- ✅ PDF
- ✅ JPEG
- ✅ PNG

## 📝 限制说明

| 限制项 | 值 |
|--------|-----|
| 单文件大小 | 100MB |
| 最大页数 | 10页 |
| Pipeline最大文件数 | 10个 |

## 💡 使用场景

### 场景1: 发票信息抽取

```python
wrapper = MinerUKIEWrapper(pipeline_id="invoice_pipeline")
results = wrapper.process_file("invoice.pdf")

# 提取发票信息
extract_result = results.get('extract')
if extract_result:
    invoice_no = extract_result.get('invoice_number')
    amount = extract_result.get('amount')
    print(f"发票号: {invoice_no}, 金额: {amount}")
```

### 场景2: 合同信息抽取

```python
wrapper = MinerUKIEWrapper(pipeline_id="contract_pipeline")
results = wrapper.process_file("contract.pdf")

# 提取合同信息
extract_result = results.get('extract')
if extract_result:
    parties = extract_result.get('parties')
    date = extract_result.get('date')
    print(f"签约方: {parties}, 日期: {date}")
```

### 场景3: 批量处理

```python
wrapper = MinerUKIEWrapper(pipeline_id="batch_pipeline")

files = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]

for file in files:
    print(f"\n处理: {file}")
    results = wrapper.process_file(file)
    # 处理结果...
```

## 🔍 结果结构

```json
{
  "parse": {
    "status": "success",
    "pages": 5,
    "text": "..."
  },
  "split": {
    "status": "success",
    "sections": [...]
  },
  "extract": {
    "status": "success",
    "fields": {
      "field1": "value1",
      "field2": "value2"
    }
  }
}
```

## ⚠️ 常见问题

### Q: requests.RequestException 错误？

A: 可能原因：
1. Pipeline未部署 → 在网页上点击"部署"
2. Pipeline已有10个文件 → 创建新Pipeline
3. 文件超过限制 → 检查大小和页数
4. Token过期 → 运行 `python3 batch_login.py`

### Q: 如何查看处理进度？

A: SDK会自动轮询，可以设置轮询间隔：

```python
results = wrapper.process_file(
    "file.pdf",
    timeout=120,
    poll_interval=5  # 每5秒查询一次
)
```

### Q: 虚拟环境如何管理？

A: 
```bash
# 激活
source .venv/bin/activate

# 退出
deactivate

# 删除
rm -rf .venv
```

## 🎯 完整工作流程

```bash
# 1. 首次配置（一次性）
cd /Users/jiasunm/Code/GenAI/MinerU-Token
uv venv
source .venv/bin/activate
uv pip install mineru-kie-sdk requests pyyaml selenium

# 2. Token管理（每14天）
python3 batch_login.py

# 3. 使用KIE SDK
python3 mineru_kie_wrapper.py <pipeline_id> <file.pdf>
```

## 📚 相关文档

- `README.md` - 项目主文档
- `API_COMPLETE.md` - 完整API文档
- `COMPLETE_GUIDE.md` - 完整使用指南
- `KIE_SDK_GUIDE.md` - 本文档

---

**✅ KIE SDK封装完成，支持自动Token管理和负载均衡！**
