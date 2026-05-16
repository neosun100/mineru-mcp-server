"""Markdown 图片引用路径重写工具。

MinerU 返回的 .md 里图片用 `![](images/<hash>.jpg)` 引用，但本项目把图片
复制到 `<file_stem>_images/` 目录后，引用路径需要相应调整。

提供两个核心函数：
  - rewrite_md_image_refs()      —— 单个 .md 改写到 `{stem}_images/`
  - rewrite_md_with_part_prefix() —— 合并 chunks 时给每张图加 `partN_` 前缀
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Iterable, Optional

logger = logging.getLogger(__name__)


# 匹配 ![alt](images/xxx.jpg) 形式（MinerU 默认输出）
# 不匹配 https:// 开头的远程图，也不匹配已带子目录前缀的路径
_PATTERN_RAW = re.compile(r"!\[([^\]]*)\]\(images/([^)]+)\)")


def rewrite_md_image_refs(md_text: str, target_dir_name: str) -> str:
    """把 ``![](images/x.jpg)`` 替换为 ``![](target_dir_name/x.jpg)``。

    Args:
        md_text:           原始 markdown 文本
        target_dir_name:   目标图片目录名（通常是 `{stem}_images`）

    Returns:
        重写后的 markdown 文本
    """
    if not md_text:
        return md_text
    return _PATTERN_RAW.sub(
        lambda m: f"![{m.group(1)}]({target_dir_name}/{m.group(2)})",
        md_text,
    )


def rewrite_md_with_part_prefix(
    md_text: str,
    final_dir_name: str,
    part_index: int,
    chunk_dir_name: Optional[str] = None,
) -> str:
    """合并 chunks 时使用：把 .md 中的图片引用统一改写到 `final_dir_name/partN_x.jpg`。

    会处理两种 chunk .md 中可能出现的引用形式：
      1. ``![](images/x.jpg)``          —— MinerU 原始格式
      2. ``![](<chunk_dir_name>/x.jpg)`` —— 经过 rewrite_md_image_refs 后的格式

    Args:
        md_text:         chunk 的 .md 原始文本
        final_dir_name:  合并后的统一图片目录名（如 ``PDF-E_images``）
        part_index:      该 chunk 是第几片（1-based）
        chunk_dir_name:  该 chunk 自身的图片目录名（如 ``PDF-E_part1of3_images``），
                         可省略；省略时只处理形式 1。
    """
    if not md_text:
        return md_text

    prefix = f"part{part_index}_"

    # 形式 1: ![](images/x.jpg) → ![](<final>/partN_x.jpg)
    md_text = _PATTERN_RAW.sub(
        lambda m: f"![{m.group(1)}]({final_dir_name}/{prefix}{m.group(2)})",
        md_text,
    )

    # 形式 2: ![](chunk_dir_name/x.jpg) → ![](<final>/partN_x.jpg)
    if chunk_dir_name:
        esc = re.escape(chunk_dir_name + "/")
        pattern2 = re.compile(rf"!\[([^\]]*)\]\({esc}([^)]+)\)")
        md_text = pattern2.sub(
            lambda m: f"![{m.group(1)}]({final_dir_name}/{prefix}{m.group(2)})",
            md_text,
        )

    return md_text


def list_image_refs(md_text: str) -> Iterable[str]:
    """提取 .md 中所有图片引用路径（不含 alt）。供测试 / 验证使用。"""
    return [m.group(0) for m in re.finditer(r"!\[[^\]]*\]\(([^)]+)\)", md_text)]


def verify_refs_exist(md_path: str | Path, base_dir: str | Path | None = None) -> tuple[int, list[str]]:
    """验证 .md 中所有图片引用都能在磁盘上找到对应文件。

    Returns:
        (引用总数, 缺失列表)
    """
    md_path = Path(md_path)
    base = Path(base_dir) if base_dir else md_path.parent
    text = md_path.read_text(encoding="utf-8")

    refs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text)
    missing = []
    for r in refs:
        # 跳过 http(s) 开头的远程图
        if r.startswith(("http://", "https://", "data:")):
            continue
        if not (base / r).exists():
            missing.append(r)
    return len(refs), missing
