<div align="center">

# MinerU MCP Server

**完整的 MinerU 文档处理解决方案 — v4.0.0 全面升级版**

精准 API + Agent 轻量 API · 全参数透传 · 智能错误重试 · 自动拆分合并 · Token 自动续期

![MinerU](https://img.shields.io/badge/MinerU-Document%20Processing-blue)
![Version](https://img.shields.io/badge/version-4.0.0-green)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-purple)
![Tests](https://img.shields.io/badge/tests-87%20passed-brightgreen)

[快速开始](#-快速开始) • [架构](#-架构) • [处理流程](#-处理流程) • [MCP 工具](#-mcp-工具) • [文档](#-文档)

</div>

---

## ✨ v4.0.0 亮点（2026-05-16）

- 🚀 **覆盖官方完整能力**：精准 API（`/api/v4/`）+ Agent 轻量 API（`/api/v1/agent/`）双线
- 🔥 **6 个 MCP 工具**：`process_document` / `process_directory` / `process_document_lite` /
  `query_task_status` / `renew_tokens` / `get_token_status`
- 🛡️ **健壮性大幅升级**：30+ 错误码分类、智能重试、Token 自动续期、URL 服务端直传（无需下载）
- 📐 **服务端 200 页限制适配**：自动拆分 180 页/片处理后合并；无缝处理 1000+ 页文档
- 🐛 **修复严重 bug**：图片引用路径错位（影响所有历史输出，v4.0.0 已彻底解决）
- 🧪 **测试体系**：30 unit + 31 integration + 24 regression + 2 e2e = **87 tests, 100% pass**

详见 [`docs/CHANGELOG.md`](docs/CHANGELOG.md) 和 [`docs/API_V4_REFERENCE.md`](docs/API_V4_REFERENCE.md)。

---

## 🏗️ 架构

5 层 / 10 模块 / 6 个 MCP 工具 / 双 API 客户端 — 一图看懂：

<p align="center">
  <img src="https://img.aws.xin/uPic/architecture.png" alt="架构层次图" width="100%"/>
</p>

| 层 | 模块 | 职责 |
|---|---|---|
| ① MCP 接入层 | `mineru_mcp_server.py` | 6 个 MCP 工具的 schema + 调度 |
| ② 协调编排层 | `auto_split.py` / `mineru_batch_async.py` / `mineru_async.py` / `progress.py` | 拆分→处理→合并的本地协调（无网） |
| ③ API 客户端层 | `MinerUAsyncClient` / `AgentAPIClient` | 调 MinerU 服务端的两套 API |
| ④ 基础设施 | `api_errors.py` / `token_manager.py` / `path_fixer.py` / `split_large_file.py` | 错误处理、Token 管理、路径修复、PDF 物理拆分 |
| ⑤ 外部依赖 | MinerU 服务端 / `batch_login.py` / `all_tokens.json` | 6 个账号配额 6000 页/天 |

---

## 🔄 处理流程

输入 → 验证 → 拆分判断 → 提交 → 错误处理 → 轮询 → 下载 → 合并 → Markdown 输出：

<p align="center">
  <img src="https://img.aws.xin/uPic/processing-flow.png" alt="处理流程图" width="100%"/>
</p>

**关键能力**：

- **URL 优先服务端直传**（不下载到本地），失败兜底走下载-上传
- **图片自动开 OCR**，HTML 自动切 `MinerU-HTML` 模型，Office 自动切 `pipeline`
- **30+ 错误码分类**：RETRYABLE / AUTH / QUOTA / PERMANENT，分别配重试策略
- **path_fixer 修复 v3.x 严重 bug**：`images/x.jpg` → `{stem}_images/x.jpg`，593 张图片缺失 0

---

## 🔪 自动拆分协调流程

服务端硬限制 200 页 / 200 MB。超规格文件**全自动**拆分→并发处理→智能合并，对调用方完全透明：

<p align="center">
  <img src="https://img.aws.xin/uPic/auto-split-flow.png" alt="自动拆分流程" width="100%"/>
</p>

**真实案例**：《PDF-E》496 页 → 自动拆 3 片（166+166+164）→ 3 片同时处理 → 合并为单 .md 209,955 字符。总耗时 ~3 分钟（vs 串行单线程预估 ~9 分钟）。

---

## 🛠️ MCP 工具

6 个 MCP 工具 · 决策树：

<p align="center">
  <img src="https://img.aws.xin/uPic/mcp-tools-decision.png" alt="MCP 工具决策树" width="100%"/>
</p>

| # | 工具 | 用途 | 关键参数 |
|---|---|---|---|
| 1 | `process_document` | 精准 API 单文件处理 | 11 参数（含 `language` / `is_ocr` / `page_ranges` / `extra_formats` / `data_id` 等） |
| 2 | `process_directory` | 精准 API 批量并行 | 10 参数 + `max_workers` |
| 3 | `process_document_lite` | Agent 轻量 API（≤10MB / 20 页 / 免 Token） | 6 参数 |
| 4 | `query_task_status` | 异步查询任务进度 | `task_id`, `lite` |
| 5 | `get_token_status` | Token 状态报告 | — |
| 6 | `renew_tokens` | 触发 Token 自动续期 | `force`, `headless` |

完整参数参考：[`docs/API_V4_REFERENCE.md`](docs/API_V4_REFERENCE.md)

---

## 📊 性能与实测

### 真实数据（5 本古籍 1229 页）

| 文件 | 页数 | 处理方式 | MD 字符 | 图片 | 缺失 |
|---|---:|---|---:|---:|---:|
| PDF-A | 91 | 直接处理 | 48,117 | 23 | 0 |
| PDF-B | 143 | 直接处理 | 82,443 | 1 | 0 |
| PDF-C | 190 | 直接处理 | 243,271 | 519 | 0 |
| PDF-D | 309 | 自动拆 2 片 | 247,435 | 30 | 0 |
| PDF-E | 496 | 自动拆 3 片 | 209,471 | 0 | 0 |
| **合计** | **1,229** | — | **830,737** | **573** | **0** |

总耗时（含 OCR 全部 5 个文件）：**约 10 分钟**。

### 异步并发性能对比

| 场景 | 串行处理 | v4 并发处理 | 提升 |
|---|---:|---:|---:|
| 单文件 | 23 秒 | 23 秒 | — |
| 3 文件 | 149 秒 | 88 秒 | 1.7× |
| 10 文件 | 300 秒 | 30 秒 | **10×** |

### OCR 收益分布（A/B 实测）

| PDF | 异体字（无 OCR） | 异体字（有 OCR） | OCR 收益 |
|---|---:|---:|---|
| PDF-A | **5,063** | **0** | 🟢 巨大（GBK 字体异体字 → 标准中文） |
| 其他 4 本 | 0 | 0 | 🟡 微小（PDF 已用标准字体） |

**结论**：OCR 对 GBK 古籍 PDF 收益巨大；对标准 Unicode PDF 收益不显著。`process_document` 默认 `is_ocr=False`，扫描型 PDF 显式传 `is_ocr=True` 即可。

---

## 🚀 快速开始

### 一键安装

```bash
git clone https://github.com/neosun100/mineru-mcp-server.git
cd mineru-mcp-server
./install_mcp.sh
```

### 配置账户

```bash
cp config/accounts.yaml.example config/accounts.yaml
vi config/accounts.yaml  # 填入账号信息
```

### 批量登录获取 Token（默认 headless）

```bash
.venv/bin/python3 src/batch_login.py
```

脚本会自动：访问登录页 → 填账号密码 → 自动通过阿里云验证码 → 保存 Token 到 `all_tokens.json`。Token 有效期约 90 天。

### 使用

#### 方式 1: MCP 工具（推荐，在 Kiro CLI / Claude Desktop 中）

```
"帮我处理 ~/Documents/report.pdf"
"处理 ~/Documents 目录下所有 PDF"
"查看 MinerU 的 Token 状态"
```

#### 方式 2: 命令行批量

```bash
# 批量异步并行
.venv/bin/python3 src/mineru_batch_async.py ~/Documents '*.pdf'
```

---

## 📦 安装

### 系统要求

- Python 3.10+
- uv（Python 包管理器）
- Git

### 手动安装

```bash
# 1. 克隆仓库
git clone https://github.com/neosun100/mineru-mcp-server.git
cd mineru-mcp-server

# 2. 创建虚拟环境（必须用 uv，避免环境冲突）
uv venv
source .venv/bin/activate

# 3. 安装运行时依赖（必须用 uv pip）
uv pip install -r requirements.txt
.venv/bin/playwright install chromium

# 4. 安装开发依赖（可选，跑测试时需要）
uv pip install -r requirements-dev.txt

# 5. 配置账户
cp config/accounts.yaml.example config/accounts.yaml
vi config/accounts.yaml

# 6. 批量登录
.venv/bin/python3 src/batch_login.py
```

> **⚠️ 重要：所有 Python 包安装必须使用 `uv pip install`，不要用裸 `pip install`。**
> uv 严格隔离虚拟环境，避免与系统 Python 冲突。

### MCP 服务器配置

编辑 `~/.kiro/settings/mcp.json`（或 Claude Desktop 配置）：

```json
{
  "mcpServers": {
    "mineru": {
      "command": "/path/to/mineru-mcp-server/.venv/bin/python3",
      "args": ["/path/to/mineru-mcp-server/src/mineru_mcp_server.py"],
      "env": {
        "PYTHONPATH": "/path/to/mineru-mcp-server/src"
      }
    }
  }
}
```

### Kiro Skill 安装（可选）

```bash
cp -r skills/mineru-token-manager ~/.kiro/skills/
```

安装后，AI 助手会自动：处理文档前检查 Token 是否过期 → 过期时自动触发 headless 续期 → 续期完成继续处理。

---

## 🧪 测试

### 测试体系

| 类型 | 数量 | 用时 | 说明 |
|---|---:|---:|---|
| `unit` | 30 | 0.4s | 毫秒级、无依赖 |
| `integration` | 31 | 0.4s | 不调真网，用 tmp/mock |
| `regression` | 24 | 0.6s | 防已修 bug 复发 |
| `e2e` | 2 | ~30s | 真调 MinerU API |
| **合计** | **87** | — | **100% 通过** |

### 运行方式

```bash
# 默认（不调网络）
.venv/bin/python3 -m pytest

# 全量含 e2e（真调 API）
RUN_E2E=1 .venv/bin/python3 -m pytest

# 按 marker
.venv/bin/python3 -m pytest -m unit
.venv/bin/python3 -m pytest -m regression
```

详见 [`tests/README.md`](tests/README.md)。

---

## 🔧 技术栈

| 技术 | 版本 | 用途 |
|---|---|---|
| [niquests](https://niquests.readthedocs.io/) | 3.10+ | HTTP/2+HTTP/3 异步客户端 |
| [MCP SDK](https://modelcontextprotocol.io/) | 1.0+ | Model Context Protocol |
| [Rich](https://rich.readthedocs.io/) | 13.0+ | 终端 UI |
| [PyPDF2](https://pypdf2.readthedocs.io/) | 3.0+ | PDF 解析 + 物理拆分 |
| [Playwright](https://playwright.dev) | 1.40+ | 自动登录（headless） |
| [pytest](https://docs.pytest.org) | 8.0+ | 测试框架 |

---

## 📁 项目结构

```
mineru-mcp-server/
├── src/                                # 核心代码（10 个模块）
│   ├── mineru_mcp_server.py            # ① MCP 接入层
│   ├── auto_split.py                   # ② 拆分协调
│   ├── mineru_batch_async.py           # ② 批量协调
│   ├── mineru_async.py                 # ② 单文件协调 + ③ 精准 API 客户端
│   ├── agent_api.py                    # ③ Agent 轻量 API 客户端
│   ├── progress.py                     # ② 进度回调
│   ├── api_errors.py                   # ④ 错误码表 + 重试策略
│   ├── token_manager.py                # ④ Token 管理
│   ├── path_fixer.py                   # ④ Markdown 路径修复
│   ├── split_large_file.py             # ④ PDF 物理拆分
│   └── batch_login.py                  # ⑤ headless 自动登录
│
├── tests/                              # 87 个测试
│   ├── unit/                           # 30 单元测试
│   ├── integration/                    # 31 集成测试
│   ├── regression/                     # 24 回归测试（防 bug 复发）
│   ├── e2e/                            # 2 端到端测试（真调 API）
│   └── README.md                       # 测试运行手册
│
├── docs/                               # 完整文档
│   ├── CHANGELOG.md                    # 详细变更日志
│   ├── API_V4_REFERENCE.md             # 官方 API 参数完整参考
│   ├── images/                         # 4 张架构 / 流程图
│   └── ...
│
├── config/
│   └── accounts.yaml.example           # 账号配置模板
│
├── skills/
│   └── mineru-token-manager/           # Kiro Skill
│
├── requirements.txt                    # 运行时依赖
├── requirements-dev.txt                # 开发依赖
├── install_mcp.sh                      # 一键安装脚本
└── README.md                           # 本文档
```

---

## 📚 文档

- [`docs/CHANGELOG.md`](docs/CHANGELOG.md) — 详细变更日志（v4.0.0 全部修改）
- [`docs/API_V4_REFERENCE.md`](docs/API_V4_REFERENCE.md) — 官方 API 完整参数参考
- [`tests/README.md`](tests/README.md) — 测试运行手册
- 历史文档：[`docs/PROCESSING_FLOW.md`](docs/PROCESSING_FLOW.md) / [`docs/MCP_DESIGN.md`](docs/MCP_DESIGN.md)

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

提交前请确保：
1. `uv pip install -r requirements-dev.txt`
2. `.venv/bin/python3 -m pytest` 全过
3. 涉及 bug 修复时新增 regression 测试

---

## 📄 许可证

MIT License

---

## 🙏 致谢

- [MinerU](https://mineru.net) — 提供强大的文档解析 API
- [Anthropic](https://www.anthropic.com) — Model Context Protocol
- [niquests](https://niquests.readthedocs.io/) — 现代 HTTP 客户端

---

<div align="center">

**⭐ 如果对你有帮助，请给个 Star！**

[GitHub](https://github.com/neosun100/mineru-mcp-server) · Made with ❤️ by neosun100

</div>
