# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [4.0.0] - 2026-05-16

> **「最强最完善最健壮」全面升级版本。**
> 适配 MinerU 服务端 2026 年 API 升级（页数限制 600 → 200），新增 Agent 轻量 API
> 支持，重构错误处理 + Token 管理 + 路径修复，新增 87 个测试覆盖完整三层（unit /
> integration / regression / e2e）。

### 🔥 主要更新

#### 服务端 API 适配

- **MAX_PAGES**: `600` → `200`（与 MinerU 服务端 2026 年硬限制对齐）
- **MAX_SIZE**: 200 MB（保持不变）
- **新增 Agent 轻量 API 完整客户端**（`/api/v1/agent/parse/...`）：免 Token / IP 限频 / ≤10MB / ≤20 页
- **URL 输入优先服务端直传**（v4 `/extract/task` 直接抓 URL，无需本地下载），失败兜底走下载-上传

#### 完整官方参数透传

| 参数 | 用途 | v3.x | v4.0.0 |
|---|---|---|---|
| `language` | 文档语言（ch/en/japan/...） | ❌ 静默忽略 | ✅ |
| `is_ocr` | 启用 OCR | ❌ | ✅ |
| `page_ranges` | 页码范围（"1-50" / "2,4-6"） | ❌ | ✅ |
| `extra_formats` | 额外导出（docx/html/latex） | ❌ | ✅ |
| `data_id` | 业务标识 | ❌ | ✅ |
| `no_cache` | URL 跳过缓存 | ❌ | ✅ |
| `cache_tolerance` | URL 缓存容忍时间 | ❌ | ✅ |

#### 6 个 MCP 工具（3 增强 + 3 新增）

- **`process_document`** ⬆️ 参数 7 → 11（覆盖官方所有字段）
- **`process_directory`** ⬆️ 参数 4 → 10（同上 + `max_workers`）
- **`get_token_status`** ⬆️ 增加 `days_remaining` / `usage_count` / `quota_exhausted` / `needs_renewal`
- **`process_document_lite`** 🆕 Agent 轻量 API（免 Token / 小文件场景）
- **`query_task_status`** 🆕 异步查询任务进度
- **`renew_tokens`** 🆕 触发 Token 自动续期

#### 5 个新增源码模块

| 模块 | 行数 | 职责 |
|---|---:|---|
| `src/api_errors.py` | 323 | 30+ 官方错误码 + 4 类分类（RETRYABLE / QUOTA / AUTH / PERMANENT）+ 重试策略 + 中文友好提示 |
| `src/token_manager.py` | 288 | 单例 + 负载均衡（`pick(least_used)`）+ 自动续期（`renew_if_needed`）+ 配额标记 |
| `src/agent_api.py` | 316 | Agent 轻量 API 完整客户端 + `can_use_lite_api()` 准入检查 |
| `src/path_fixer.py` | 108 | Markdown 图片路径重写（单文件 + 合并 chunks 两种模式） |
| `src/progress.py` | 133 | 统一进度上报封装（ProgressStage / ProgressEvent / ProgressReporter） |
| `src/auto_split.py` | 173 | 拆分协调器：`prepare_files()` + `merge_results()` |

#### 修复严重 Bug

- 🐛 **图片引用路径错位**（最严重 bug）：MinerU 返回 `![](images/x.jpg)` 但项目把图片复制到 `{stem}_images/`，渲染器找不到。v3.x 全部历史输出受影响。
  在 `mineru_async.py` + `mineru_batch_async.py` 双处用 `path_fixer` 模块统一修复。
- 🐛 **服务端 200 页限制不一致**：v3.x 阈值 600，超 200 页文件直接失败但代码不知道。
  v4.0.0 阈值 200，自动 `auto_split` 拆 180 页/片。
- 🐛 **伪 page_ranges 死代码分支**：v3.x `mineru_async.py:417-449` 有"if pages > 600: 拆分"分支，
  实际只打日志不真拆。已删除。
- 🐛 **`output_dir` 被本地文件强制忽略**：v4.0.0 早期 `mineru_async.py` 第 676-678 行
  `if not is_url: output_path = file.parent` 导致用户传的 `output_dir` 被静默覆盖。
  发现于 e2e 测试时 `page_ranges='1-5'` + `output_dir='/tmp/...'` 5 页结果覆盖了完整 .md。
  现在只在默认 `'./output'` 时才用 file.parent。
- 🐛 **`split_large_file.py` 默认 600 页拆分**：与服务端 200 页限制不匹配。
  默认改为 180 页（留 10% buffer）+ 加 `max_pages` 参数。

### 🧪 测试体系（87 个测试，100% 通过）

| 层 | 数量 | 用时 | 说明 |
|---|---:|---:|---|
| **unit** | 30 | 0.4s | 毫秒级、无依赖（errors / path_fixer / splitter） |
| **integration** | 31 | 0.4s | 不调真网，用 tmp_path / 临时 token 文件 |
| **regression** | 24 | 0.6s | 防止已修 bug 复发（图片路径 / 200 页 / 伪分支 / output_dir） |
| **e2e** | 2 | ~30s | 真调 MinerU API（默认 skip，`RUN_E2E=1` 启用） |

回归测试覆盖的 v4.0.0 所有已修 bug：
- `test_image_path_fix.py` — 防图片引用路径错位
- `test_max_pages_200.py` — 防 600/200 不一致
- `test_dead_branch_and_passthrough.py` — 防伪 page_ranges 复活 + 参数透传断链
- `test_output_dir_respect.py` — 防 output_dir 被忽略

### 📚 新增文档

- `docs/CHANGELOG.md` — 本文件
- `docs/API_V4_REFERENCE.md` — 官方 API 完整参数参考（含 language 取值、错误码表）
- `tests/README.md` — 测试运行手册（按 marker / 按目录 / RUN_E2E 三种用法）
- `docs/images/` — 4 张架构/流程图（已托管到 `img.aws.xin` CDN）
  - `architecture.png` — 5 层 / 10 模块架构
  - `processing-flow.png` — 文档处理完整流程
  - `auto-split-flow.png` — 自动拆分协调流程（496 页 PDF → 3 片 实战示例）
  - `mcp-tools-decision.png` — 6 个 MCP 工具决策树

### 🔧 工程优化

- **强制 uv 安装**：`requirements.txt` 顶部加警告注释，`install_mcp.sh` / `README` 全部
  改为 `uv pip install -r requirements.txt`，禁止裸 `pip install`
- **新增 `requirements-dev.txt`**：pytest + pytest-asyncio
- **`.gitignore` 修正**：`tests/{unit,integration,regression,e2e}/test_*.py` 加白名单（之前
  全局 `test_*.py` 忽略导致测试文件未入版本控制）
- **`pytest.ini`**：注册 4 个 markers + asyncio mode auto + testpaths 精确指定

### 📊 真实数据验证（5 个文档 1229 页 OCR 全量）

| 文件 | 页数 | 处理方式 | MD 字符 | 图片 | 缺失 |
|---|---:|---|---:|---:|---:|
| PDF-A | 91 | 直接处理 | 48,117 | 23 | 0 |
| PDF-B | 143 | 直接处理 | 82,443 | 1 | 0 |
| PDF-C | 190 | 直接处理 | 243,271 | 519 | 0 |
| PDF-D | 309 | 自动拆 2 片 | 247,435 | 30 | 0 |
| PDF-E | 496 | 自动拆 3 片 | 209,471 | 0 | 0 |
| **合计** | **1,229** | — | **830,737** | **573** | **0** |

总耗时 ~10 分钟（含 OCR）；并发处理 vs 串行预估 ~2-3× 加速。

### 🎯 OCR A/B 实测发现

只有 GBK 字体的古籍 PDF 才显著受益于 OCR：

| PDF | 异体字（无 OCR） | 异体字（有 OCR） | 收益 |
|---|---:|---:|---|
| PDF-A | **5,063** | **0** | 🟢 巨大 |
| 其他 4 本 | 0 | 0 | 🟡 微小 |

`process_document` 默认 `is_ocr=False`，扫描型/古籍 PDF 显式传 `is_ocr=True`。

### 📦 累积 commit（v4.0.0 共 5 个 commit）

```
a8fbe7f docs: 重写 README + 完善 CHANGELOG + 4 张架构流程图（CDN 托管）
2bcbe1c fix: 修 output_dir 被本地文件强制忽略 + 重跑测试样本
104c73e test: 建立完整三层测试体系（unit + integration + regression + e2e）
f703ebc fix: 安装强制使用 uv pip 避免环境冲突
08c513b feat(v4.0.0): 全面升级 - 覆盖 MinerU 官方完整 API + 健壮性大幅提升
```

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

---

## 版本对比一览

| 版本 | 关键能力 | API 覆盖 | 健壮性 | 测试 |
|---|---|---|---|---|
| **v4.0.0** | 双 API + 6 MCP 工具 + 自动拆分合并 + 智能错误重试 | 官方 100% | 30+ 错误码分类 + Token 自动续期 | 87 测试 |
| v3.2.0 | 单 API + 3 MCP 工具 + Token 过期检测 | 部分 | 基础 | 0 |
| v3.1.0 | headless 自动登录 | 基础 | 基础 | 0 |
| v3.0.0 | 批量并行 + Rich UI | 基础 | 基础 | 0 |
| v2.x | 同步处理 | 基础 | 弱 | 0 |
| v1.x | 单文件处理 | 基础 | 弱 | 0 |

---

> 历史更早版本详见 git log：`git log --oneline --all`
