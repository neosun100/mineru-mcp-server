# MinerU 完整输入支持说明

## 📋 支持的所有输入类型

### 1. 本地文件
```python
# 绝对路径
processor.process_file("/Users/user/Documents/report.pdf")

# 相对路径
processor.process_file("./documents/report.pdf")

# 用户目录
processor.process_file("~/Documents/report.pdf")
```

### 2. 在线PDF
```python
processor.process_file("https://example.com/document.pdf")
processor.process_file("http://cdn.example.com/files/report.pdf")
```

### 3. 在线Word/PPT
```python
processor.process_file("https://example.com/presentation.pptx")
processor.process_file("https://example.com/document.docx")
```

### 4. 在线图片
```python
processor.process_file("https://example.com/image.png")
processor.process_file("https://example.com/photo.jpg")
```

### 5. 网页URL
```python
processor.process_file(
    "https://example.com/article.html",
    model_version="MinerU-HTML"
)
```

### 6. 目录（批量处理）
```python
processor.process_directory("~/Documents/invoices")
processor.process_directory("/path/to/pdfs", pattern="*.pdf")
```

### 7. URL列表（批量处理）
```python
urls = [
    "https://example.com/doc1.pdf",
    "https://example.com/doc2.pdf",
    "https://example.com/doc3.pdf"
]
processor.process_urls(urls)
```

## 🎯 智能识别逻辑

### 自动检测输入类型

```python
def detect_input_type(input_path: str) -> str:
    """
    自动检测输入类型
    
    Returns:
        'url' | 'file' | 'directory'
    """
    if input_path.startswith(('http://', 'https://')):
        return 'url'
    
    path = Path(input_path).expanduser()
    
    if path.is_dir():
        return 'directory'
    elif path.is_file():
        return 'file'
    else:
        # 可能是URL或不存在的文件
        return 'unknown'
```

### 自动选择模型

```python
def auto_select_model(file_info: Dict) -> str:
    """
    根据文件类型自动选择模型
    
    Returns:
        'vlm' | 'pipeline' | 'MinerU-HTML'
    """
    format = file_info['format']
    
    if format == 'html':
        return 'MinerU-HTML'
    elif format in ['pdf', 'doc', 'docx', 'ppt', 'pptx']:
        return 'vlm'  # 推荐使用vlm
    elif format in ['png', 'jpg', 'jpeg']:
        return 'vlm'  # 图片使用vlm
    else:
        return 'pipeline'
```

### 自动选择参数

```python
def auto_select_options(file_info: Dict) -> Dict:
    """
    根据文件类型自动选择参数
    
    Returns:
        API参数字典
    """
    options = {
        'model_version': auto_select_model(file_info)
    }
    
    # 图片自动开启OCR
    if file_info['format'] in ['png', 'jpg', 'jpeg']:
        options['is_ocr'] = True
    
    # PDF/DOC/PPT开启公式和表格识别
    if file_info['format'] in ['pdf', 'doc', 'docx', 'ppt', 'pptx']:
        options['enable_formula'] = True
        options['enable_table'] = True
    
    return options
```

## 🎨 MCP使用场景（完整版）

### 场景1: 处理本地PDF
```
用户: 帮我处理 ~/Documents/report.pdf

AI: 好的，我来处理这个PDF文件。
    [检测到本地文件]
    [验证: 50页, 15MB]
    [调用 process_document]
    
    处理完成！文档共50页，已转换为Markdown。
    
    主要内容：
    - 第一章：项目概述
    - 第二章：技术方案
    
    完整结果：~/Documents/report_merged.md
```

### 场景2: 处理在线PDF
```
用户: 处理这个PDF https://arxiv.org/pdf/2401.12345.pdf

AI: 好的，我来处理这个在线PDF。
    [检测到URL]
    [验证: 可访问, 25MB]
    [调用 process_document]
    
    处理完成！这是一篇关于机器学习的论文。
    
    主要内容：
    - 摘要：提出了一种新的算法...
    - 实验结果：准确率提升15%
    
    完整结果：./output/2401.12345_merged.md
```

### 场景3: 处理网页
```
用户: 把这个网页转成Markdown https://blog.example.com/article

AI: 好的，我来处理这个网页。
    [检测到HTML URL]
    [自动选择 MinerU-HTML 模型]
    [调用 process_document]
    
    处理完成！已提取网页正文。
    
    文章标题：如何使用MinerU
    作者：张三
    发布时间：2026-01-20
    
    完整结果：./output/article_merged.md
```

### 场景4: 识别图片文字
```
用户: 识别这张图片中的文字 https://example.com/receipt.jpg

AI: 好的，我来识别这张图片。
    [检测到图片URL]
    [自动开启OCR]
    [调用 process_document]
    
    识别完成！
    
    提取的文字：
    ─────────────
    发票号码：12345678
    金额：¥1,250.00
    日期：2026-01-20
    ─────────────
    
    完整结果：./output/receipt_merged.md
```

### 场景5: 批量处理本地文件
```
用户: 把 ~/Invoices 目录下所有PDF都处理一下

AI: 好的，我来批量处理发票。
    [扫描目录]
    [找到20个PDF文件]
    [调用 process_directory]
    
    处理完成！
    - 成功：19个
    - 失败：1个（文件损坏）
    
    已提取关键信息：
    - 总金额：¥125,000
    - 发票数量：19张
```

### 场景6: 批量处理URL列表
```
用户: 处理这些论文：
      https://arxiv.org/pdf/2401.001.pdf
      https://arxiv.org/pdf/2401.002.pdf
      https://arxiv.org/pdf/2401.003.pdf

AI: 好的，我来批量处理这些论文。
    [解析URL列表]
    [验证所有URL]
    [调用 process_urls]
    
    处理完成！已处理3篇论文。
    
    论文1: 深度学习新方法
    论文2: 计算机视觉应用
    论文3: 自然语言处理
    
    所有结果已保存到：./output/
```

### 场景7: 混合输入
```
用户: 处理这些文档：
      ~/Documents/local.pdf
      https://example.com/online.pdf
      ~/Images/scan.jpg

AI: 好的，我来处理这些文档。
    [检测到混合输入]
    [分别验证]
    [批量处理]
    
    处理完成！
    - 本地PDF：50页
    - 在线PDF：30页
    - 扫描图片：OCR识别完成
```

### 场景8: 大文件URL
```
用户: 处理这个大文件 https://example.com/large_1000_pages.pdf

AI: 好的，我来处理这个大文件。
    [检测到URL]
    [验证: 150MB, 估计1000页]
    [自动拆分: page_ranges]
    [并行处理2个分片]
    
    处理完成！
    - 分片1: 1-600页
    - 分片2: 601-1000页
    
    已合并为完整Markdown。
```
