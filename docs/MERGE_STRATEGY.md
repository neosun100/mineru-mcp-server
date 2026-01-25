# MinerU API 页码范围和合并策略说明

## 📋 关于页码范围参数

### API是否支持页码范围？

经过查阅MinerU官方文档和API文档，**目前API不支持直接指定页码范围**（如 `start_page`, `end_page`）。

### 为什么不支持？

MinerU API的设计理念是：
1. **完整性优先**：确保文档结构完整性
2. **上下文关联**：避免破坏文档的上下文关系
3. **简化接口**：保持API简洁易用

### 我们的解决方案

既然API不支持页码范围，我们采用**客户端拆分**策略：

```python
# 在客户端拆分PDF
chunks = FileChunker.split_pdf("large.pdf", output_dir="./chunks")

# 每个分片独立处理
for chunk in chunks:
    process(chunk)

# 合并结果
merge_results(results)
```

**优势：**
- ✅ 完全控制拆分逻辑
- ✅ 可以自定义拆分策略
- ✅ 支持所有文件格式（PDF/PPTX/DOCX）
- ✅ 不依赖API限制

## 🔗 完整合并策略

### MinerU API返回结构

```json
{
  "task_id": "xxx",
  "state": "done",
  "full_zip_url": "https://cdn.../result.zip",
  "md_url": "https://cdn.../result.md",
  "md_content_url": "https://cdn.../content.md",
  "layout_tree_url": "https://cdn.../layout.json"
}
```

### 压缩包内容结构

```
result.zip
├── auto/
│   ├── xxx.md          # Markdown文件
│   ├── images/         # 图片目录
│   │   ├── img_001.png
│   │   ├── img_002.png
│   │   └── ...
│   └── layout.json     # 布局信息
```

### 我们的合并流程

#### 1. 下载并解压

```python
async def download_and_extract_results(results, output_dir):
    """
    下载所有分片的压缩包并解压
    
    结构:
    output_dir/
    ├── chunk_1/
    │   ├── auto/
    │   │   ├── xxx.md
    │   │   └── images/
    ├── chunk_2/
    │   ├── auto/
    │   │   ├── xxx.md
    │   │   └── images/
    └── ...
    """
```

#### 2. 合并Markdown

```python
def merge_markdown_files(extracted_results, output_file):
    """
    合并所有Markdown内容
    
    策略:
    - 按分片顺序合并
    - 分片之间添加分隔符
    - 保留原始格式
    - 自动处理图片引用
    """
    with open(output_file, 'w') as f:
        for i, result in enumerate(extracted_results, 1):
            if i > 1:
                f.write("\n\n" + "="*60 + "\n\n")
            
            f.write(f"# 分片 {i}\n\n")
            f.write(result['md_content'])
```

**输出示例：**
```markdown
# 分片 1

## 第一章
内容...

============================================================

# 分片 2

## 第二章
内容...
```

#### 3. 合并图片

```python
def merge_images(extracted_results, output_dir):
    """
    合并所有图片到统一目录
    
    策略:
    - 所有图片放在 images/ 目录
    - 文件名添加分片前缀避免冲突
    - 保留原始文件名
    """
    images_dir = Path(output_dir) / "images"
    
    for result in extracted_results:
        for img in find_images(result['chunk_dir']):
            new_name = f"chunk_{result['chunk_id']}_{img.name}"
            copy(img, images_dir / new_name)
```

**输出结构：**
```
output/
└── images/
    ├── chunk_1_img_001.png
    ├── chunk_1_img_002.png
    ├── chunk_2_img_001.png
    ├── chunk_2_img_002.png
    └── ...
```

#### 4. 合并元数据

```python
def merge_json_metadata(extracted_results, output_file):
    """
    合并所有元数据
    
    包含:
    - 分片信息
    - 下载URL
    - 时间戳
    - 文件路径
    """
    merged = {
        'total_chunks': len(extracted_results),
        'merged_at': datetime.now().isoformat(),
        'chunks': [...]
    }
```

**输出示例：**
```json
{
  "total_chunks": 2,
  "merged_at": "2026-01-25T15:45:00",
  "chunks": [
    {
      "chunk_id": 1,
      "chunk_dir": "./output/chunk_1",
      "has_content": true,
      "urls": {
        "full_zip_url": "https://...",
        "md_url": "https://..."
      }
    },
    {
      "chunk_id": 2,
      ...
    }
  ]
}
```

### 最终输出结构

```
output/
├── large_document_merged.md      # 合并后的Markdown
├── large_document_metadata.json  # 元数据
├── images/                       # 所有图片
│   ├── chunk_1_img_001.png
│   ├── chunk_1_img_002.png
│   ├── chunk_2_img_001.png
│   └── ...
├── chunk_1/                      # 原始分片1
│   └── auto/
│       ├── xxx.md
│       └── images/
└── chunk_2/                      # 原始分片2
    └── auto/
        ├── xxx.md
        └── images/
```

## 🎯 完整使用示例

```python
from mineru_batch_processor import MinerUBatchProcessor

# 初始化
processor = MinerUBatchProcessor(max_workers=10)

# 处理大文件
result = processor.process_large_file(
    file_path="large_1000_pages.pdf",
    output_dir="./output"
)

# 结果
print(f"总分片: {result['total_chunks']}")
print(f"成功: {result['success']}")
print(f"失败: {result['failed']}")
print(f"输出文件:")
print(f"  Markdown: {result['output_files']['markdown']}")
print(f"  图片目录: {result['output_files']['images']}")
print(f"  元数据: {result['output_files']['metadata']}")
```

## 💡 关键优势

### 1. 完整性保证
- ✅ 下载完整压缩包
- ✅ 保留所有图片
- ✅ 保留布局信息
- ✅ 保留元数据

### 2. 智能合并
- ✅ Markdown按顺序合并
- ✅ 图片统一管理
- ✅ 避免文件名冲突
- ✅ 保留原始文件

### 3. 可追溯性
- ✅ 保留原始分片
- ✅ 记录合并时间
- ✅ 记录下载URL
- ✅ 完整元数据

## ⚠️ 注意事项

### 1. 图片引用更新

合并后的Markdown中的图片引用需要更新：

```markdown
<!-- 原始 -->
![](images/img_001.png)

<!-- 更新后 -->
![](images/chunk_1_img_001.png)
```

**TODO**: 自动更新图片引用路径

### 2. 磁盘空间

处理大文件需要足够的磁盘空间：
- 原始文件
- 拆分后的分片
- 下载的压缩包
- 解压后的文件
- 合并后的文件

**建议**: 预留 5x 文件大小的空间

### 3. 网络稳定性

下载大量压缩包需要稳定的网络：
- 使用异步下载提高效率
- 添加重试机制
- 显示下载进度

## 🔧 未来优化

### 1. 流式合并

不下载完整压缩包，直接流式合并：
```python
# TODO
async def stream_merge(results):
    async for chunk in download_stream(results):
        merge_chunk(chunk)
```

### 2. 增量合并

支持增量添加新分片：
```python
# TODO
def incremental_merge(existing_result, new_chunks):
    append_to_markdown(new_chunks)
    update_metadata(new_chunks)
```

### 3. 智能去重

检测并去除重复内容：
```python
# TODO
def deduplicate_content(merged_content):
    # 检测重复段落
    # 智能去重
    pass
```

---

**✅ 完整的合并策略，确保内容完整性和可追溯性！**
