"""回归测试：防止"伪 page_ranges 分支"和"参数透传断链"问题复发。

历史背景：
  v3.x mineru_async.py L417-449 有一段"if pages > 600: 拆分处理"的分支，
  但里面只是打印 "将拆分为 N 个请求"，实际还是直接调 wait_for_completion，
  没有真拆分 → 用户以为有保护实际无保护。
  v4.0.0 已删除该分支，改由 auto_split 协调器物理拆分。

  另外 v3.x mineru_async.py 的 upload_options 只透传 model_version /
  enable_formula / enable_table，把 language/is_ocr/page_ranges 全部
  静默丢弃，导致用户传参没用。v4.0.0 通过 _split_options 全量透传。
"""
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.regression


SRC = Path(__file__).resolve().parents[2] / "src"


def test_no_pseudo_page_ranges_branch():
    """不能有"if pages > 600: ... 实际没拆分 ..." 这种死代码。"""
    text = (SRC / "mineru_async.py").read_text(encoding="utf-8")
    # 旧的伪分支特征字符串
    bad_signatures = [
        "需要使用page_ranges处理",
        "使用page_ranges参数拆分处理",
        "将拆分为",  # 该字符串只出现在伪分支
    ]
    for sig in bad_signatures:
        assert sig not in text, \
            f"mineru_async.py 中发现伪分支残留：{sig!r}"


def test_split_options_has_all_official_keys():
    """_split_options 必须能识别官方所有参数，否则用户传了也丢。"""
    from mineru_async import MinerUAsyncClient

    expected_batch = {
        "model_version", "enable_formula", "enable_table",
        "language", "extra_formats",
    }
    expected_file = {
        "name", "url", "is_ocr", "data_id", "page_ranges",
    }

    assert expected_batch.issubset(MinerUAsyncClient._BATCH_LEVEL_KEYS)
    assert expected_file.issubset(MinerUAsyncClient._FILE_LEVEL_KEYS)


def test_single_task_keys_complete():
    """submit_url_task 接受的 v4 单任务参数必须完整。"""
    from mineru_async import MinerUAsyncClient

    must_support = {
        "url", "model_version", "is_ocr", "enable_formula", "enable_table",
        "language", "data_id", "callback", "seed", "extra_formats",
        "page_ranges", "no_cache", "cache_tolerance",
    }
    assert must_support.issubset(MinerUAsyncClient._SINGLE_TASK_KEYS)


def test_submit_url_task_method_exists():
    """v4.0.0 新加的 URL 直传方法不能被误删。"""
    from mineru_async import MinerUAsyncClient
    import inspect
    m = getattr(MinerUAsyncClient, "submit_url_task", None)
    assert m is not None, "submit_url_task 不能丢"
    assert inspect.iscoroutinefunction(m)


def test_get_task_result_method_exists():
    from mineru_async import MinerUAsyncClient
    import inspect
    m = getattr(MinerUAsyncClient, "get_task_result", None)
    assert m is not None
    assert inspect.iscoroutinefunction(m)


def test_wait_for_single_task_method_exists():
    from mineru_async import MinerUAsyncClient
    import inspect
    m = getattr(MinerUAsyncClient, "wait_for_single_task", None)
    assert m is not None
    assert inspect.iscoroutinefunction(m)


def test_batch_async_accepts_options_kwarg():
    """process_files_parallel 必须接受 options 字典（v4.0.0 引入）。"""
    from mineru_batch_async import BatchAsyncProcessor
    import inspect
    sig = inspect.signature(BatchAsyncProcessor.process_files_parallel)
    assert "options" in sig.parameters, \
        "process_files_parallel 必须接受 options 参数"


def test_mcp_server_exports_six_tools():
    """v4.0.0 共 6 个 MCP 工具，少一个都不行。"""
    import asyncio
    import mineru_mcp_server
    tools = asyncio.run(mineru_mcp_server.list_tools())
    names = {t.name for t in tools}
    expected = {
        "process_document",
        "process_directory",
        "get_token_status",
        "process_document_lite",
        "query_task_status",
        "renew_tokens",
    }
    assert names == expected, f"工具集合不一致：{names ^ expected}"


def test_process_document_has_full_param_schema():
    """process_document 必须暴露完整官方参数。"""
    import asyncio
    import mineru_mcp_server
    tools = asyncio.run(mineru_mcp_server.list_tools())
    pd = next(t for t in tools if t.name == "process_document")
    props = set(pd.inputSchema["properties"].keys())
    must = {
        "file_path", "model_version", "enable_formula", "enable_table",
        "is_ocr", "language", "page_ranges", "extra_formats", "data_id",
        "no_cache",
    }
    missing = must - props
    assert not missing, f"process_document 缺参数：{missing}"
