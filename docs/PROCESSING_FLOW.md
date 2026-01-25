# MinerU 完整处理流程详解

## 🎯 核心问题

### 问题1: 文件超过200MB怎么办？
**答**: 需要物理拆分文件，分别上传

### 问题2: 文件超过600页怎么办？
**答**: 使用 `page_ranges` 参数，无需物理拆分

### 问题3: 返回的压缩包如何处理？
**答**: 自动下载、解压、合并

### 问题4: 结果放在哪里？
**答**: 与原文件相同目录，或指定输出目录

## 📋 完整处理流程

### 场景1: 单个小文件（< 200MB, < 600页）

```
输入: ~/Documents/report.pdf (50MB, 100页)

流程:
1. 验证文件
   ✅ 大小: 50MB < 200MB
   ✅ 页数: 100页 < 600页
   ✅ 无需拆分

2. 上传文件（如果是本地文件）
   方式1: 使用批量上传API获取上传链接
   方式2: 直接使用URL（如果已在线）

3. 创建解析任务
   POST /api/v4/extract/task
   {
       "url": "https://cdn.../report.pdf",
       "model_version": "vlm"
   }
   
   返回: task_id

4. 轮询结果
   GET /api/v4/extract/task/{task_id}
   
   返回:
   {
       "state": "done",
       "full_zip_url": "https://cdn.../result.zip"
   }

5. 下载压缩包
   下载到: ~/Documents/report_result.zip

6. 解压
   解压到: ~/Documents/report_result/
   
   结构:
   report_result/
   ├── auto/
   │   ├── report.md          # Markdown文件
   │   ├── images/            # 图片目录
   │   │   ├── img_001.png
   │   │   ├── img_002.png
   │   │   └── ...
   │   ├── layout.json        # 布局信息
   │   └── content_list.json  # 内容列表

7. 整理输出
   最终结构:
   ~/Documents/
   ├── report.pdf             # 原文件
   ├── report.md              # Markdown（从auto/复制）
   └── report_images/         # 图片（从auto/images/复制）
       ├── img_001.png
       ├── img_002.png
       └── ...
```

### 场景2: 单个大文件（> 600页，但 < 200MB）

```
输入: ~/Documents/large.pdf (150MB, 1000页)

流程:
1. 验证文件
   ✅ 大小: 150MB < 200MB
   ⚠️  页数: 1000页 > 600页
   ✅ 使用page_ranges参数拆分

2. 创建分片配置
   分片1: page_ranges="1-600"
   分片2: page_ranges="601-1000"

3. 上传文件（一次）
   上传到: https://cdn.../large.pdf

4. 并行创建2个解析任务
   任务1: {"url": "...", "page_ranges": "1-600"}
   任务2: {"url": "...", "page_ranges": "601-1000"}
   
   返回: task_id_1, task_id_2

5. 并行轮询结果
   任务1完成: full_zip_url_1
   任务2完成: full_zip_url_2

6. 并行下载压缩包
   下载到:
   ~/Documents/large_chunk_1.zip
   ~/Documents/large_chunk_2.zip

7. 并行解压
   解压到:
   ~/Documents/large_result/chunk_1/
   ~/Documents/large_result/chunk_2/

8. 合并结果
   合并Markdown:
   ~/Documents/large.md
   
   内容:
   # 分片 1 (1-600页)
   [内容...]
   
   ============================================================
   
   # 分片 2 (601-1000页)
   [内容...]
   
   合并图片:
   ~/Documents/large_images/
   ├── chunk_1_img_001.png
   ├── chunk_1_img_002.png
   ├── chunk_2_img_001.png
   └── ...

9. 清理临时文件
   删除:
   - large_chunk_1.zip
   - large_chunk_2.zip
   - large_result/ (可选保留)
```

### 场景3: 单个超大文件（> 200MB）

```
输入: ~/Documents/huge.pdf (300MB, 800页)

流程:
1. 验证文件
   ⚠️  大小: 300MB > 200MB
   ⚠️  页数: 800页 > 600页
   ✅ 需要物理拆分

2. 物理拆分文件
   使用PyPDF2拆分:
   
   huge_part_1.pdf (200MB, 533页)
   huge_part_2.pdf (100MB, 267页)

3. 上传所有分片
   上传到:
   https://cdn.../huge_part_1.pdf
   https://cdn.../huge_part_2.pdf

4. 创建解析任务（每个分片）
   任务1: {"url": "...huge_part_1.pdf"}
   任务2: {"url": "...huge_part_2.pdf"}

5. 并行处理
   任务1完成: full_zip_url_1
   任务2完成: full_zip_url_2

6. 下载并解压
   ~/Documents/huge_result/chunk_1/
   ~/Documents/huge_result/chunk_2/

7. 合并结果
   ~/Documents/huge.md
   ~/Documents/huge_images/

8. 清理
   删除临时文件:
   - huge_part_1.pdf
   - huge_part_2.pdf
   - huge_chunk_*.zip
```

### 场景4: 批量处理多个文件

```
输入: ~/Documents/invoices/ (20个PDF)

文件列表:
- invoice_001.pdf (10MB, 5页)
- invoice_002.pdf (15MB, 8页)
- large_invoice.pdf (250MB, 100页) ⚠️ 超大
- huge_invoice.pdf (180MB, 800页) ⚠️ 超页数
- ...

流程:
1. 扫描目录
   找到20个PDF文件

2. 分类处理
   小文件（18个）: 直接处理
   超大文件（1个）: 物理拆分
   超页数文件（1个）: page_ranges拆分

3. 预处理
   - large_invoice.pdf → 拆分成2个物理文件
   - huge_invoice.pdf → 创建2个page_ranges配置
   
   实际任务数: 18 + 2 + 2 = 22个任务

4. 并行处理（并行度10）
   第1批: 10个任务
   第2批: 10个任务
   第3批: 2个任务

5. 下载所有结果
   并行下载22个压缩包

6. 解压所有结果
   ~/Documents/invoices_result/
   ├── invoice_001/
   ├── invoice_002/
   ├── large_invoice_chunk_1/
   ├── large_invoice_chunk_2/
   ├── huge_invoice_chunk_1/
   ├── huge_invoice_chunk_2/
   └── ...

7. 合并结果
   每个原始文件对应一个输出:
   
   ~/Documents/invoices/
   ├── invoice_001.pdf
   ├── invoice_001.md ⭐
   ├── invoice_001_images/ ⭐
   ├── invoice_002.pdf
   ├── invoice_002.md ⭐
   ├── invoice_002_images/ ⭐
   ├── large_invoice.pdf
   ├── large_invoice.md ⭐ (合并后)
   ├── large_invoice_images/ ⭐ (合并后)
   └── ...

8. 生成汇总报告
   ~/Documents/invoices_summary.json
   
   {
       "total_files": 20,
       "success": 19,
       "failed": 1,
       "total_pages": 1500,
       "processing_time": 180,
       "results": [...]
   }
```

## 🔧 详细实现逻辑

### 1. 输出路径策略

```python
def get_output_path(input_path: str, output_dir: Optional[str] = None) -> str:
    """
    确定输出路径
    
    规则:
    1. 如果指定output_dir，使用output_dir
    2. 如果是本地文件，使用文件所在目录
    3. 如果是URL，使用当前目录
    """
    if output_dir:
        return output_dir
    
    if FileValidator.is_url(input_path):
        return "./output"
    else:
        return str(Path(input_path).parent)
```

### 2. 文件命名策略

```python
def get_output_names(input_path: str) -> Dict[str, str]:
    """
    生成输出文件名
    
    返回:
    {
        'markdown': 'report.md',
        'images_dir': 'report_images',
        'temp_dir': 'report_result'
    }
    """
    if FileValidator.is_url(input_path):
        # URL: 从URL提取文件名
        name = Path(input_path).name or 'document'
    else:
        # 本地文件: 使用文件名
        name = Path(input_path).name
    
    base_name = name.rsplit('.', 1)[0]
    
    return {
        'markdown': f"{base_name}.md",
        'images_dir': f"{base_name}_images",
        'temp_dir': f"{base_name}_result"
    }
```

### 3. 压缩包处理流程

```python
async def process_zip_result(zip_url: str, output_dir: str, chunk_id: int) -> Dict:
    """
    处理单个压缩包
    
    流程:
    1. 下载压缩包
    2. 解压到临时目录
    3. 提取Markdown和图片
    4. 返回路径信息
    """
    # 1. 下载
    zip_path = Path(output_dir) / f"chunk_{chunk_id}.zip"
    await download_file(zip_url, zip_path)
    
    # 2. 解压
    extract_dir = Path(output_dir) / f"chunk_{chunk_id}"
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    
    # 3. 查找内容
    # 压缩包结构: auto/xxx.md, auto/images/, auto/layout.json
    auto_dir = extract_dir / "auto"
    
    md_file = None
    images_dir = None
    
    if auto_dir.exists():
        # 查找Markdown
        for f in auto_dir.glob("*.md"):
            md_file = f
            break
        
        # 查找图片目录
        img_dir = auto_dir / "images"
        if img_dir.exists():
            images_dir = img_dir
    
    # 4. 返回信息
    return {
        'chunk_id': chunk_id,
        'extract_dir': str(extract_dir),
        'md_file': str(md_file) if md_file else None,
        'images_dir': str(images_dir) if images_dir else None,
        'zip_path': str(zip_path)
    }
```

### 4. 合并策略

```python
def merge_all_results(chunk_results: List[Dict], output_base: str):
    """
    合并所有分片结果
    
    输入:
    chunk_results = [
        {
            'chunk_id': 1,
            'md_file': '/path/chunk_1/auto/xxx.md',
            'images_dir': '/path/chunk_1/auto/images'
        },
        {
            'chunk_id': 2,
            'md_file': '/path/chunk_2/auto/xxx.md',
            'images_dir': '/path/chunk_2/auto/images'
        }
    ]
    
    输出:
    output_base.md
    output_base_images/
    
    流程:
    """
    # 1. 合并Markdown
    md_output = f"{output_base}.md"
    with open(md_output, 'w', encoding='utf-8') as out:
        for result in chunk_results:
            if result['md_file']:
                # 添加分片标题
                out.write(f"\n\n{'='*60}\n")
                out.write(f"# 分片 {result['chunk_id']}\n")
                out.write(f"{'='*60}\n\n")
                
                # 读取并写入内容
                with open(result['md_file'], 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # 更新图片引用路径
                    content = update_image_paths(content, result['chunk_id'])
                    
                    out.write(content)
    
    # 2. 合并图片
    images_output = f"{output_base}_images"
    Path(images_output).mkdir(exist_ok=True)
    
    for result in chunk_results:
        if result['images_dir']:
            images_dir = Path(result['images_dir'])
            
            for img in images_dir.glob("*"):
                if img.is_file():
                    # 添加分片前缀避免冲突
                    new_name = f"chunk_{result['chunk_id']}_{img.name}"
                    shutil.copy(img, Path(images_output) / new_name)
    
    # 3. 清理临时文件
    for result in chunk_results:
        # 删除压缩包
        if result.get('zip_path'):
            Path(result['zip_path']).unlink(missing_ok=True)
        
        # 删除解压目录（可选）
        if result.get('extract_dir'):
            shutil.rmtree(result['extract_dir'], ignore_errors=True)
    
    return {
        'markdown': md_output,
        'images': images_output
    }
```

### 5. 图片路径更新

```python
def update_image_paths(markdown_content: str, chunk_id: int) -> str:
    """
    更新Markdown中的图片引用路径
    
    原始:
    ![](images/img_001.png)
    
    更新后:
    ![](report_images/chunk_1_img_001.png)
    """
    import re
    
    # 匹配图片引用: ![...](images/xxx.png)
    pattern = r'!\[([^\]]*)\]\(images/([^)]+)\)'
    
    def replace_func(match):
        alt_text = match.group(1)
        img_name = match.group(2)
        new_path = f"chunk_{chunk_id}_{img_name}"
        return f'![{alt_text}]({new_path})'
    
    return re.sub(pattern, replace_func, markdown_content)
```

## 📊 完整示例

### 示例: 处理1000页PDF

```python
from mineru_production import MinerUProcessor

processor = MinerUProcessor(max_workers=10)

# 输入
file_path = "~/Documents/large_1000_pages.pdf"

# 处理
result = await processor.process_file(file_path)

# 完整流程:
# ─────────────────────────────────────────
# 1. 验证文件
#    ✅ 大小: 150MB < 200MB
#    ⚠️  页数: 1000页 > 600页
#    → 使用page_ranges拆分
#
# 2. 创建分片配置
#    分片1: page_ranges="1-600"
#    分片2: page_ranges="601-1000"
#
# 3. 上传文件（一次）
#    → https://cdn.../large_1000_pages.pdf
#
# 4. 并行创建2个任务
#    任务1: task_id_1
#    任务2: task_id_2
#
# 5. 并行轮询（实时进度）
#    任务1: 进度 350/600页
#    任务2: 进度 200/400页
#
# 6. 并行下载压缩包
#    下载1: chunk_1.zip (50MB)
#    下载2: chunk_2.zip (35MB)
#
# 7. 并行解压
#    解压1: chunk_1/auto/
#    解压2: chunk_2/auto/
#
# 8. 合并Markdown
#    ~/Documents/large_1000_pages.md
#    
#    内容:
#    ============================================================
#    # 分片 1 (1-600页)
#    ============================================================
#    
#    ## 第一章
#    [内容...]
#    
#    ![](chunk_1_img_001.png)
#    
#    ============================================================
#    # 分片 2 (601-1000页)
#    ============================================================
#    
#    ## 第五章
#    [内容...]
#    
#    ![](chunk_2_img_001.png)
#
# 9. 合并图片
#    ~/Documents/large_1000_pages_images/
#    ├── chunk_1_img_001.png
#    ├── chunk_1_img_002.png
#    ├── chunk_2_img_001.png
#    └── ...
#
# 10. 清理临时文件
#     删除: chunk_*.zip
#     保留: chunk_*/（可选）
#
# 最终输出:
# ~/Documents/
# ├── large_1000_pages.pdf          # 原文件
# ├── large_1000_pages.md           # 合并后的Markdown
# └── large_1000_pages_images/      # 所有图片
#     ├── chunk_1_img_001.png
#     ├── chunk_1_img_002.png
#     ├── chunk_2_img_001.png
#     └── ...
```

## 🎯 批量处理完整流程

### 输入: 目录包含多种文件

```
~/Documents/mixed/
├── small.pdf (50MB, 100页)
├── large.pdf (150MB, 1000页)
├── huge.pdf (300MB, 800页)
├── doc.docx (20MB, 50页)
└── image.png (5MB)
```

### 处理流程

```
1. 扫描和分类
   小文件: small.pdf, doc.docx, image.png (3个)
   超页数: large.pdf (1个 → 2个分片)
   超大: huge.pdf (1个 → 2个物理分片)
   
   总任务数: 3 + 2 + 2 = 7个任务

2. 预处理
   - huge.pdf → 物理拆分 → huge_part_1.pdf, huge_part_2.pdf
   - large.pdf → 创建page_ranges配置

3. 上传文件
   - small.pdf → 上传
   - large.pdf → 上传（一次）
   - huge_part_1.pdf → 上传
   - huge_part_2.pdf → 上传
   - doc.docx → 上传
   - image.png → 上传

4. 并行处理（并行度10）
   任务1: small.pdf
   任务2: large.pdf (page_ranges="1-600")
   任务3: large.pdf (page_ranges="601-1000")
   任务4: huge_part_1.pdf
   任务5: huge_part_2.pdf
   任务6: doc.docx
   任务7: image.png

5. 并行下载和解压
   下载7个压缩包
   解压到7个目录

6. 合并结果
   small.pdf → small.md + small_images/
   large.pdf → large.md + large_images/ (合并2个分片)
   huge.pdf → huge.md + huge_images/ (合并2个分片)
   doc.docx → doc.md + doc_images/
   image.png → image.md + image_images/

7. 最终输出
   ~/Documents/mixed/
   ├── small.pdf
   ├── small.md ⭐
   ├── small_images/ ⭐
   ├── large.pdf
   ├── large.md ⭐
   ├── large_images/ ⭐
   ├── huge.pdf
   ├── huge.md ⭐
   ├── huge_images/ ⭐
   ├── doc.docx
   ├── doc.md ⭐
   ├── doc_images/ ⭐
   ├── image.png
   ├── image.md ⭐
   └── image_images/ ⭐
```

## ⚠️ 关键细节

### 1. 文件大小处理

| 大小 | 策略 | 说明 |
|------|------|------|
| < 200MB | 直接处理 | 无需拆分 |
| > 200MB | 物理拆分 | 使用PyPDF2拆分 |

### 2. 页数处理

| 页数 | 策略 | 说明 |
|------|------|------|
| < 600页 | 直接处理 | 无需拆分 |
| > 600页 | page_ranges | 无需物理拆分 |

### 3. 输出路径

| 输入类型 | 输出位置 | 说明 |
|---------|---------|------|
| 本地文件 | 同目录 | ~/Documents/file.pdf → ~/Documents/file.md |
| URL | ./output | https://... → ./output/file.md |
| 指定output_dir | output_dir | 使用指定目录 |

### 4. 图片处理

```
原始结构:
chunk_1/auto/images/img_001.png
chunk_2/auto/images/img_001.png

合并后:
output_images/
├── chunk_1_img_001.png
└── chunk_2_img_001.png

Markdown引用:
![](output_images/chunk_1_img_001.png)
```

### 5. 临时文件清理

```
保留:
✅ 原文件
✅ 合并后的Markdown
✅ 合并后的图片目录

删除:
❌ 压缩包（*.zip）
❌ 解压目录（可选保留用于调试）
❌ 物理拆分的临时文件
```

---

**✅ 完整的处理流程，考虑所有边界情况！**
