#!/usr/bin/env python3
"""
PDF 物理拆分工具

服务端硬限制（自 2026 年某次更新后）：
  - 单文件大小 ≤ 200 MB
  - 单文件页数 ≤ 200 页（超过会返回 "number of pages exceeds limit (200 pages)"）

本工具按"大小"和"页数"双约束拆分，默认每片 ≤ 180 页 + ≤ 180 MB（留 buffer
以便上传/编码膨胀），保证拆出的每个分片都能被 MinerU 服务端接受。
"""
import sys
from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter


# 服务端真实硬限制（与 mineru_async.py.FileValidator 保持一致）
SERVER_MAX_PAGES = 200
SERVER_MAX_SIZE_MB = 200

# 业务安全阈值（留 buffer）
DEFAULT_MAX_PAGES = 180
DEFAULT_MAX_SIZE_MB = 180


def split_large_pdf(
    file_path: str,
    max_size_mb: int = DEFAULT_MAX_SIZE_MB,
    max_pages: int = DEFAULT_MAX_PAGES,
) -> list:
    """按"大小或页数"任一超限触发拆分，输出 chunks。

    参数：
        file_path:    PDF 文件路径
        max_size_mb:  每个分片最大大小（MB），默认 180
        max_pages:    每个分片最大页数，默认 180

    返回：
        分片文件路径列表。如果原文件已经在限制内，返回 [原文件路径]。
    """
    path = Path(file_path)
    reader = PdfReader(file_path)
    total_pages = len(reader.pages)
    file_size = path.stat().st_size / 1024 / 1024  # MB

    print(f"原文件: {path.name}")
    print(f"  大小: {file_size:.1f} MB")
    print(f"  页数: {total_pages} 页")

    # 在限制内：直接返回，无需拆分
    if file_size <= max_size_mb and total_pages <= max_pages:
        print("✅ 文件大小和页数均在限制内，无需拆分")
        return [file_path]

    # 同时考虑大小和页数限制，取严格一方
    chunks_by_size = int(file_size / max_size_mb) + 1 if file_size > max_size_mb else 1
    chunks_by_pages = (total_pages + max_pages - 1) // max_pages

    chunk_count = max(chunks_by_size, chunks_by_pages)
    pages_per_chunk = (total_pages + chunk_count - 1) // chunk_count  # 向上取整

    print(f"\n📦 拆分策略 (max_size={max_size_mb}MB, max_pages={max_pages}):")
    print(f"  按大小需要: {chunks_by_size} 个分片")
    print(f"  按页数需要: {chunks_by_pages} 个分片")
    print(f"  实际拆分为: {chunk_count} 个分片")
    print(f"  每片最多: {pages_per_chunk} 页")

    chunks = []
    output_dir = path.parent / f"{path.stem}_chunks"
    output_dir.mkdir(exist_ok=True)

    for i in range(chunk_count):
        start_page = i * pages_per_chunk
        end_page = min((i + 1) * pages_per_chunk, total_pages)
        if start_page >= total_pages:
            break

        writer = PdfWriter()
        for page_num in range(start_page, end_page):
            writer.add_page(reader.pages[page_num])

        chunk_path = output_dir / f"{path.stem}_part{i+1}of{chunk_count}.pdf"
        with open(chunk_path, 'wb') as f:
            writer.write(f)

        chunk_size = chunk_path.stat().st_size / 1024 / 1024
        chunk_pages = end_page - start_page

        # 用服务端真值校验（不是业务阈值），确保分片确实能被服务端接受
        size_ok = chunk_size < SERVER_MAX_SIZE_MB
        pages_ok = chunk_pages <= SERVER_MAX_PAGES
        status = "✅" if size_ok and pages_ok else "⚠️"
        print(f"  {status} 分片{i+1}: {start_page+1}-{end_page}页 "
              f"({chunk_size:.1f}MB, {chunk_pages}页)")

        if not pages_ok:
            print(f"     ⚠️  警告: 分片{i+1}超过 {SERVER_MAX_PAGES} 页限制，"
                  f"应减小 max_pages 参数后重试")
        if not size_ok:
            print(f"     ⚠️  警告: 分片{i+1}超过 {SERVER_MAX_SIZE_MB} MB 限制，"
                  f"应减小 max_size_mb 参数后重试")

        chunks.append(str(chunk_path))

    return chunks


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python3 split_large_file.py <file_path> [max_size_mb] [max_pages]")
        print(f"默认: max_size_mb={DEFAULT_MAX_SIZE_MB}, max_pages={DEFAULT_MAX_PAGES}")
        sys.exit(1)

    file_path = sys.argv[1]
    kwargs = {}
    if len(sys.argv) >= 3:
        kwargs['max_size_mb'] = int(sys.argv[2])
    if len(sys.argv) >= 4:
        kwargs['max_pages'] = int(sys.argv[3])

    chunks = split_large_pdf(file_path, **kwargs)

    print(f"\n✅ 拆分完成!")
    print(f"分片文件:")
    for chunk in chunks:
        print(f"  {chunk}")
