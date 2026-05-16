"""自动拆分协调器

封装"超页 PDF → 物理拆分 → 单批处理 → 合并 .md 和图片"的完整流程，
供 mineru_batch_async.py 和 mineru_mcp_server.py 调用，避免重复实现。

服务端硬限制：单文件 ≤ 200 页 / ≤ 200 MB（自 2026 年某次更新后）。
拆分阈值默认 180 / 180，留 10% buffer。
"""
import re
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

from PyPDF2 import PdfReader

from split_large_file import (
    split_large_pdf,
    SERVER_MAX_PAGES,
    SERVER_MAX_SIZE_MB,
    DEFAULT_MAX_PAGES,
    DEFAULT_MAX_SIZE_MB,
)


def _file_needs_split(file_path: str) -> Tuple[bool, int, float]:
    """检测 PDF 是否需要拆分。返回 (needs_split, pages, size_mb)。"""
    p = Path(file_path)
    if p.suffix.lower() != '.pdf':
        # 非 PDF 不在本协调器拆分范围内
        return False, 0, p.stat().st_size / 1024 / 1024
    try:
        pages = len(PdfReader(file_path).pages)
    except Exception:
        pages = 0
    size_mb = p.stat().st_size / 1024 / 1024
    needs = pages > SERVER_MAX_PAGES or size_mb > SERVER_MAX_SIZE_MB
    return needs, pages, size_mb


def prepare_files(
    file_paths: List[str],
    max_size_mb: int = DEFAULT_MAX_SIZE_MB,
    max_pages: int = DEFAULT_MAX_PAGES,
) -> Tuple[List[str], List[Dict]]:
    """检测并拆分超页 / 超大 PDF。

    返回：
        (展开后的文件列表, 合并计划列表)

    合并计划元素结构::

        {
            "original": "/abs/path/to/big.pdf",
            "chunks": ["/abs/.../big_chunks/big_part1of3.pdf", ...],
            "stem": "big",
            "n": 3,
        }

    没被拆分的文件不会出现在合并计划里。
    """
    expanded: List[str] = []
    plans: List[Dict] = []

    for fp in file_paths:
        needs, pages, size_mb = _file_needs_split(fp)
        if not needs:
            expanded.append(fp)
            continue

        print(f"\n🔪 自动拆分: {Path(fp).name} ({pages}页, {size_mb:.1f}MB)")
        chunks = split_large_pdf(fp, max_size_mb=max_size_mb, max_pages=max_pages)
        if len(chunks) == 1:
            # split 决定不拆，直接加入
            expanded.append(fp)
            continue

        expanded.extend(chunks)
        plans.append({
            "original": fp,
            "chunks": chunks,
            "stem": Path(fp).stem,
            "n": len(chunks),
        })

    return expanded, plans


def merge_results(plans: List[Dict]) -> List[Dict]:
    """根据 prepare_files 返回的合并计划，把 chunks 输出合并成最终文件。

    每个 plan 处理后，会在原 PDF 同目录生成：
      - {stem}.md          —— 拼接后的完整 markdown，分片间用 HTML 注释分隔
      - {stem}_images/     —— 所有 chunks 的图片，按 part 加前缀避免冲突

    返回：
        合并完成清单::

            [
                {"original": "...pdf", "markdown": "...md", "images": "..._images",
                 "image_count": 30, "n_parts": 3},
                ...
            ]
    """
    results: List[Dict] = []

    for plan in plans:
        original = Path(plan["original"])
        stem = plan["stem"]
        n = plan["n"]
        out_dir = original.parent
        chunks_dir = out_dir / f"{stem}_chunks"

        final_md = out_dir / f"{stem}.md"
        final_imgs = out_dir / f"{stem}_images"
        if final_imgs.exists():
            shutil.rmtree(final_imgs)
        final_imgs.mkdir()

        merged: List[str] = []
        total_imgs = 0
        for i in range(1, n + 1):
            part_stem = f"{stem}_part{i}of{n}"
            part_md = chunks_dir / f"{part_stem}.md"
            part_imgs = chunks_dir / f"{part_stem}_images"

            if not part_md.exists():
                # 该分片处理失败，跳过但保留标记
                merged.append(f"\n\n<!-- ===== Part {i}/{n} (FAILED) ===== -->\n\n")
                continue

            content = part_md.read_text(encoding='utf-8')

            # 把 .md 中所有指向该 chunk 自己 _images 目录的引用，
            # 重写成统一的 {stem}_images/part{i}_xxx，并复制图片到统一目录。
            prefix = f"part{i}_"
            if part_imgs.exists():
                for img in sorted(part_imgs.iterdir()):
                    if img.is_file():
                        new_name = prefix + img.name
                        shutil.copy2(img, final_imgs / new_name)
                        total_imgs += 1

            # 替换两种可能的引用形式：
            #   ![](images/x)                               —— mineru 原始
            #   ![](part_stem_images/x)                     —— mineru_async.py 修复后
            content = re.sub(
                r'!\[([^\]]*)\]\(images/([^)]+)\)',
                lambda m: f'![{m.group(1)}]({stem}_images/{prefix}{m.group(2)})',
                content,
            )
            esc_part_imgs = re.escape(f'{part_stem}_images/')
            content = re.sub(
                rf'!\[([^\]]*)\]\({esc_part_imgs}([^)]+)\)',
                lambda m: f'![{m.group(1)}]({stem}_images/{prefix}{m.group(2)})',
                content,
            )

            merged.append(f"\n\n<!-- ===== Part {i}/{n} ===== -->\n\n")
            merged.append(content)

        final_md.write_text(''.join(merged), encoding='utf-8')

        results.append({
            "original": str(original),
            "markdown": str(final_md),
            "images": str(final_imgs) if total_imgs else None,
            "image_count": total_imgs,
            "n_parts": n,
        })
        print(f"✅ 合并完成: {final_md.name} "
              f"({final_md.stat().st_size:,} bytes, {total_imgs} 张图片, {n} 片)")

    return results
