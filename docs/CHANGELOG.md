# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.0.0] - 2026-05-16

> **「最强最完善最健壮」全面升级版本。**
> 适配 MinerU 服务端 2026 年 API 升级（页数限制 600 → 200），新增 Agent 轻量 API
> 支持，重构错误处理 + Token 管理 + 路径修复，覆盖完整官方参数集。

### Breaking Changes

- **`FileValidator.MAX_PAGES`**: `600` → `200`（与服务端硬限制对齐）
- **删除伪 page_ranges 分支** in `mineru_async.py:417-449`（曾经只打日志不实际拆分，
  现统一交由 `auto_split` 协调器物理拆分 + 合并）
- `split_large_pdf()` 默认 `max_pages` 从 600 → 180（留 10% buffer）

### Added

- 🆕 **`src/api_errors.py`**：30+ 官方错误码完整映射，分 RETRYABLE / QUOTA / AUTH /
  PERMANENT 四类，含重试次数建议和中文友好提示
- 🆕 **`src/token_manager.py`**：单例 TokenManager，支持
  - `valid_tokens()` 过滤已过期 + 配额耗尽账号
  - `pick(strategy="least_used")` 智能负载均衡
  - `renew_if_needed()` / `renew_all()` 自动调用 batch_login.py 续期
- 🆕 **`src/agent_api.py`**：完整 Agent 轻量 API 客户端
  - `AgentAPIClient.parse_url()` / `parse_file()` 端到端流程
  - `can_use_lite_api()` 文件准入检查（≤10MB / ≤20 页）
- 🆕 **`src/path_fixer.py`**：抽离图片引用路径重写逻辑
  - `rewrite_md_image_refs()` 单文件修复
  - `rewrite_md_with_part_prefix()` chunks 合并时的多 part 前缀重写
- 🆕 **`src/progress.py`**：统一进度上报封装（ProgressStage / ProgressEvent /
  ProgressReporter）
- 🆕 **`src/auto_split.py`**：拆分协调器（上一轮已建）
  - `prepare_files()` 自动检测超页超大并物理拆分
  - `merge_results()` chunks → 完整 .md + 统一图片目录
- 🆕 **MCP 新增 3 个工具**：
  - `process_document_lite` — Agent 轻量 API（免 Token / IP 限频）
  - `query_task_status` — 异步查询任务进度
  - `renew_tokens` — 触发 Token 自动续期
- 🆕 **`tests/unit/`**：30 个单元测试（errors / path_fixer / splitter）

### Changed

- `process_document` MCP 工具参数从 7 个 → **11 个**，覆盖官方所有字段：
  `language`, `is_ocr`, `page_ranges`, `extra_formats`, `data_id`, `no_cache` 等
- `process_directory` MCP 工具参数从 4 个 → **10 个**，同上
- `mineru_async.upload_file()` 现在用 `_split_options()` 把参数正确分到 batch
  级 / file 级
- `mineru_async.process_file()` URL 处理：**优先服务端直传**（v4
  `/extract/task` 不下载），失败兜底走原下载-上传流程
- `mineru_batch_async.process_files_parallel()` 接收 `options` 字典向下透传
- Token 检查：从手工解析 → 用 TokenManager + 过期自动续期
- `get_token_status` 增加 `days_remaining` / `usage_count` /
  `quota_exhausted` 字段，返回 `needs_renewal` 总开关

### Fixed

- 🐛 **图片引用路径错位**（严重）：MinerU 返回 `![](images/x.jpg)` 但项目
  把图片复制到 `{stem}_images/`，导致渲染器找不到文件。已在 `mineru_async.py`
  和 `mineru_batch_async.py` 两处修复，且抽出 `path_fixer` 模块统一逻辑
- 🐛 服务端 200 页限制：从 600 → 200，并在 `auto_split` 协调器中默认拆 180
  页留 buffer，避免边界溢出
- 🐛 删除 `mineru_async.py` 中的死代码"伪 page_ranges 分支"
- 🐛 `split_large_file.py` 输出目录用 `path.stem` 时对 `PDF-A..pdf` 这种
  双点 stem 也兼容（生成 `PDF-A._chunks/`）

### Internal

- 类型注解：所有新模块使用 `from __future__ import annotations` + 完整类型签名
- 代码风格：保持模块化、单一职责、向后兼容
- 文档：新增 `docs/CHANGELOG.md`

---

## [3.2.0] - 2026-02-19

- ✨ URL 文件直接处理（自动下载→上传→处理）
- ✨ URL 格式智能识别（magic bytes fallback）
- ✨ Token 过期自动检测（处理前检查）
- 🔧 修复 `get_token_status` 路径错误
- 🔧 移除未实现的工具（`process_urls`、`extract_info`）
- 🔧 完善 requirements.txt（9 个依赖）

## [3.1.0] - 2026-02-19

- ✨ 默认 headless 模式（无需 UI，Linux 服务器可用）
- ✨ 自动点击阿里云验证码
- ✨ 完整 stealth JS 伪装
- ✨ `--headed` 参数可开启浏览器界面调试

## [3.0.0] - 2026-01-25

- ✨ 批量异步并行处理（性能提升 10 倍）
- ✨ Rich UI 增强版
- ✨ 一键安装脚本
- ✨ 所有场景完整覆盖

## [2.x / 1.x / 0.x]

详见 README.md 中的版本历史。
