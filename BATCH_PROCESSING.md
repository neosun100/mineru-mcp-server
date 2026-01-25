# MinerU 批量处理器 - 生产级方案

## 🎯 核心功能

### 1. 并行处理
- ✅ 异步并发（asyncio + aiohttp）
- ✅ 可配置并行度（默认10）
- ✅ 信号量控制并发数
- ✅ 自动负载均衡（5账户轮换）

### 2. 文件拆分
- ✅ PDF拆分（PyPDF2）
- ✅ PPTX拆分（python-pptx）
- ✅ DOCX拆分（python-docx）
- ✅ 自动识别文件类型
- ✅ 600页限制自动处理

### 3. 结果合并
- ✅ Markdown合并
- ✅ JSON合并
- ✅ 保留分片信息
- ✅ 时间戳记录

### 4. 进度监控
- ✅ 实时进度显示
- ✅ 成功/失败统计
- ✅ 耗时统计
- ✅ 百分比显示

## 📦 安装依赖

```bash
# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
uv pip install aiohttp PyPDF2 python-pptx python-docx
```

## 🚀 使用方式

### 1. 批量处理多个文件

```python
from mineru_batch_processor import MinerUBatchProcessor

# 初始化（并行度10）
processor = MinerUBatchProcessor(max_workers=10)

# 准备文件列表
files = [
    {'id': 'file1', 'url': 'https://example.com/doc1.pdf'},
    {'id': 'file2', 'url': 'https://example.com/doc2.pdf'},
    {'id': 'file3', 'url': 'https://example.com/doc3.pdf'},
    # ... 最多20个文件
]

# 批量处理
results = processor.process_files(files)
```

### 2. 处理大文件（自动拆分）

```python
from mineru_batch_processor import MinerUBatchProcessor

processor = MinerUBatchProcessor(max_workers=10)

# 处理大文件（自动拆分、并行、合并）
result = processor.process_large_file(
    file_path="large_document.pdf",
    output_dir="./output"
)

print(f"处理完成: {result['success']}/{result['total_chunks']}")
```

### 3. 命令行使用

```bash
# 批量处理
python3 mineru_batch_processor.py batch file1.pdf file2.pdf file3.pdf

# 大文件处理
python3 mineru_batch_processor.py large large_document.pdf
```

## 🔧 核心组件

### FileChunker - 文件拆分器

```python
from mineru_batch_processor import FileChunker

# 自动识别并拆分
chunks = FileChunker.split_file("large.pdf", output_dir="./chunks")

# 手动拆分PDF
chunks = FileChunker.split_pdf("large.pdf", output_dir="./chunks")

# 手动拆分PPTX
chunks = FileChunker.split_pptx("large.pptx", output_dir="./chunks")

# 手动拆分DOCX
chunks = FileChunker.split_docx("large.docx", output_dir="./chunks")
```

### ResultMerger - 结果合并器

```python
from mineru_batch_processor import ResultMerger

# 合并Markdown
ResultMerger.merge_markdown(results, "output.md")

# 合并JSON
ResultMerger.merge_json(results, "output.json")
```

### ProgressMonitor - 进度监控

```python
from mineru_batch_processor import ProgressMonitor

monitor = ProgressMonitor(total=20)

for task in tasks:
    # 处理任务...
    monitor.update(success=True)  # 或 False
```

## 📊 处理流程

### 批量处理流程

```
输入文件列表
    ↓
创建异步任务池
    ↓
信号量控制并发（max_workers）
    ↓
每个任务:
  - 随机选择Token（负载均衡）
  - 创建解析任务
  - 轮询结果
  - 更新进度
    ↓
收集所有结果
    ↓
统计输出
```

### 大文件处理流程

```
输入大文件
    ↓
检测文件类型
    ↓
拆分文件（600页/分片）
    ↓
上传所有分片
    ↓
并行处理所有分片
    ↓
收集所有结果
    ↓
合并结果（MD + JSON）
    ↓
输出合并文件
```

## 🎯 并行度配置

### 推荐配置

| 文件数量 | 推荐并行度 | 说明 |
|---------|-----------|------|
| 1-5 | 5 | 小批量 |
| 6-10 | 10 | 中批量 |
| 11-20 | 10 | 大批量（受限于账户数） |
| 20+ | 10 | 分批处理 |

### 配置示例

```python
# 小批量（5个文件）
processor = MinerUBatchProcessor(max_workers=5)

# 中批量（10个文件）
processor = MinerUBatchProcessor(max_workers=10)

# 大批量（20个文件）
processor = MinerUBatchProcessor(max_workers=10)
```

## 📝 文件拆分规则

### PDF拆分
- 限制：600页/文件
- 方法：按页数拆分
- 工具：PyPDF2

### PPTX拆分
- 限制：600页/文件
- 方法：按幻灯片拆分
- 工具：python-pptx

### DOCX拆分
- 限制：~600页/文件
- 方法：按段落估算（5段/页）
- 工具：python-docx

## 🔍 进度监控示例

```
⏳ 进度: 15/20 (75.0%) | ✅ 14 | ❌ 1 | ⏱️  45.3s
```

说明：
- `15/20`: 已完成15个，总共20个
- `75.0%`: 完成百分比
- `✅ 14`: 成功14个
- `❌ 1`: 失败1个
- `⏱️  45.3s`: 已耗时45.3秒

## 🎨 完整示例

### 示例1: 处理20个PDF文件

```python
from mineru_batch_processor import MinerUBatchProcessor

# 初始化
processor = MinerUBatchProcessor(max_workers=10)

# 准备20个文件
files = [
    {'id': f'doc_{i}', 'url': f'https://cdn.example.com/doc{i}.pdf'}
    for i in range(1, 21)
]

# 批量处理
print("开始处理20个文件...")
results = processor.process_files(files)

# 分析结果
success = [r for r in results if r['status'] == 'success']
failed = [r for r in results if r['status'] != 'success']

print(f"\n成功: {len(success)}")
print(f"失败: {len(failed)}")

# 保存结果
import json
with open('batch_results.json', 'w') as f:
    json.dump(results, f, indent=2)
```

### 示例2: 处理1000页PDF

```python
from mineru_batch_processor import MinerUBatchProcessor

# 初始化
processor = MinerUBatchProcessor(max_workers=10)

# 处理大文件
print("处理1000页PDF...")
result = processor.process_large_file(
    file_path="large_1000_pages.pdf",
    output_dir="./output"
)

print(f"\n拆分: {result['total_chunks']} 个分片")
print(f"成功: {result['success']} 个")
print(f"失败: {result['failed']} 个")
print(f"输出: {result['output_files']}")
```

### 示例3: 混合处理

```python
from mineru_batch_processor import MinerUBatchProcessor, FileChunker

processor = MinerUBatchProcessor(max_workers=10)

# 处理多个大文件
large_files = ["doc1_800pages.pdf", "doc2_1200pages.pdf"]

all_chunks = []
for file in large_files:
    chunks = FileChunker.split_file(file, "./chunks")
    all_chunks.extend(chunks)

print(f"总共拆分: {len(all_chunks)} 个分片")

# 批量处理所有分片
files = [
    {'id': f'chunk_{i}', 'url': f'https://cdn.example.com/{Path(c).name}'}
    for i, c in enumerate(all_chunks)
]

results = processor.process_files(files)
```

## ⚠️ 注意事项

### 1. 并行度限制
- 最大并行度受Token数量限制（5个账户）
- 建议并行度 ≤ 10

### 2. 文件大小限制
- 单文件最大200MB
- 单文件最大600页
- 超过限制自动拆分

### 3. 网络稳定性
- 使用异步请求提高效率
- 自动重试机制（TODO）
- 超时时间可配置

### 4. 结果合并
- 保留原始分片顺序
- 包含时间戳和元数据
- 支持多种格式输出

## 🔧 高级配置

### 自定义超时时间

```python
# TODO: 添加超时配置
processor = MinerUBatchProcessor(
    max_workers=10,
    timeout=300  # 5分钟
)
```

### 自定义重试次数

```python
# TODO: 添加重试配置
processor = MinerUBatchProcessor(
    max_workers=10,
    max_retries=3
)
```

## 📚 相关文档

- `README.md` - 项目主文档
- `API_COMPLETE.md` - API完整文档
- `KIE_SDK_GUIDE.md` - KIE SDK指南
- `BATCH_PROCESSING.md` - 本文档

---

**✅ 生产级批量处理方案，支持并行、拆分、合并、监控！**
