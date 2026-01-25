#!/usr/bin/env python3
"""
处理超大文件（>200MB）- 自动拆分
"""
import sys
from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter

def split_large_pdf(file_path: str, max_size_mb: int = 180) -> list:
    """
    按文件大小拆分PDF（同时考虑页数限制）
    
    Args:
        file_path: PDF文件路径
        max_size_mb: 每个分片最大大小（MB）
    
    Returns:
        分片文件路径列表
    """
    path = Path(file_path)
    reader = PdfReader(file_path)
    total_pages = len(reader.pages)
    file_size = path.stat().st_size / 1024 / 1024  # MB
    
    print(f"原文件: {path.name}")
    print(f"  大小: {file_size:.1f} MB")
    print(f"  页数: {total_pages} 页")
    
    if file_size <= 200:
        print("✅ 文件大小在限制内，无需拆分")
        return [file_path]
    
    # 同时考虑大小和页数限制
    chunks_by_size = int(file_size / max_size_mb) + 1
    chunks_by_pages = (total_pages + 599) // 600  # 确保每个分片 ≤ 600页
    
    # 取较大值，确保同时满足两个限制
    chunk_count = max(chunks_by_size, chunks_by_pages)
    pages_per_chunk = total_pages // chunk_count
    
    print(f"\n📦 拆分策略:")
    print(f"  按大小需要: {chunks_by_size} 个分片")
    print(f"  按页数需要: {chunks_by_pages} 个分片")
    print(f"  实际拆分为: {chunk_count} 个分片")
    print(f"  每个约: {pages_per_chunk} 页")
    
    chunks = []
    output_dir = path.parent / f"{path.stem}_chunks"
    output_dir.mkdir(exist_ok=True)
    
    for i in range(chunk_count):
        start_page = i * pages_per_chunk
        end_page = min((i + 1) * pages_per_chunk, total_pages) if i < chunk_count - 1 else total_pages
        
        writer = PdfWriter()
        for page_num in range(start_page, end_page):
            writer.add_page(reader.pages[page_num])
        
        chunk_path = output_dir / f"{path.stem}_part{i+1}.pdf"
        with open(chunk_path, 'wb') as f:
            writer.write(f)
        
        chunk_size = chunk_path.stat().st_size / 1024 / 1024
        chunk_pages = end_page - start_page
        
        # 验证分片
        status = "✅" if chunk_size < 200 and chunk_pages <= 600 else "⚠️"
        print(f"  {status} 分片{i+1}: {start_page+1}-{end_page}页 ({chunk_size:.1f}MB, {chunk_pages}页)")
        
        if chunk_pages > 600:
            print(f"     ⚠️  警告: 分片{i+1}超过600页，需要使用page_ranges")
        
        chunks.append(str(chunk_path))
    
    return chunks

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python3 split_large_file.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    chunks = split_large_pdf(file_path)
    
    print(f"\n✅ 拆分完成!")
    print(f"分片文件:")
    for chunk in chunks:
        print(f"  {chunk}")
