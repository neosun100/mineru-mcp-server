# MinerU MCP Server

<div align="center">

![MinerU](https://img.shields.io/badge/MinerU-Document%20Processing-blue)
![Version](https://img.shields.io/badge/version-4.0.0-green)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-purple)
![HTTP/3](https://img.shields.io/badge/HTTP%2F3-Supported-orange)

**完整的 MinerU 文档处理解决方案（v4.0.0 全面升级版）**

精准 API + Agent 轻量 API | 全参数透传 | 智能错误重试 | 自动拆分合并 | Token 自动续期

[快速开始](#-快速开始) • [功能特性](#-功能特性) • [安装](#-安装) • [使用](#-使用) • [文档](#-文档)

</div>

---

## ✨ v4.0.0 亮点（2026-05-16）

- 🚀 **覆盖官方完整能力**：精准 API（`/api/v4/`）+ Agent 轻量 API（`/api/v1/agent/`）双线
- 🔥 **新增 6 个 MCP 工具**：`process_document` / `process_directory` / `process_document_lite` /
  `query_task_status` / `renew_tokens` / `get_token_status`
- 🛡️ **健壮性大幅升级**：30+ 错误码分类、智能重试、Token 自动续期、URL 服务端直传（无需下载）
- 📐 **服务端 200 页限制适配**：自动拆分 180 页/片处理后合并；无缝处理 1000+ 页文档
- 🐛 **修复严重 bug**：图片引用路径错位（影响所有历史输出，v4.0.0 已彻底解决）
- 🧪 **测试覆盖**：30+ 单元测试，覆盖错误码、路径修复、文件拆分等核心逻辑

详见 [`docs/CHANGELOG.md`](docs/CHANGELOG.md) 和 [`docs/API_V4_REFERENCE.md`](docs/API_V4_REFERENCE.md)。

---

## 📖 简介

MinerU MCP Server 是一个完整的文档处理解决方案，提供：

- 🔐 **多账户Token管理** - 批量登录、自动过期检测、负载均衡
- 📄 **全格式支持** - PDF、PPTX、DOCX、图片、HTML
- 🚀 **真正异步并发** - 使用niquests AsyncSession，性能提升10倍
- 📦 **智能文件处理** - 超大文件自动拆分，智能合并
- 🤖 **MCP集成** - 通过自然语言交互处理文档
- 🎨 **Rich UI** - 美观的进度显示和可视化

## ✨ 功能特性

### 核心功能

| 功能 | 说明 | 状态 |
|------|------|------|
| 🔐 Token管理 | 多账户批量登录、自动过期检测、负载均衡 | ✅ |
| 📄 文档处理 | PDF/PPTX/DOCX/图片/HTML | ✅ |
| 📦 智能拆分 | 超大文件（>200MB）自动拆分 | ✅ |
| 📖 页数处理 | 超页数文件（>600页）智能处理 | ✅ |
| 🚀 异步并发 | 真正的异步处理，非阻塞 | ✅ |
| 🔄 批量并行 | 多文件同时处理，性能提升10倍 | ✅ |
| 🤖 MCP服务器 | 自然语言交互 | ✅ |
| 🎨 Rich UI | 美观的进度显示 | ✅ |

### 支持的文件格式

| 格式 | 扩展名 | 模型 | 特性 |
|------|--------|------|------|
| PDF | `.pdf` | vlm/pipeline | 公式、表格、图片识别 |
| Word | `.doc`, `.docx` | vlm/pipeline | 完整文档结构 |
| PowerPoint | `.ppt`, `.pptx` | vlm/pipeline | 幻灯片内容提取 |
| 图片 | `.png`, `.jpg`, `.jpeg` | vlm | OCR文字识别 |
| HTML | `.html` | MinerU-HTML | 网页内容提取 |

### 场景覆盖

| 场景 | 文件大小 | 页数 | 处理方式 |
|------|---------|------|---------|
| 场景1 | < 200MB | < 600页 | 直接处理 |
| 场景2 | < 200MB | > 600页 | page_ranges参数 |
| 场景3 | > 200MB | < 600页 | 物理拆分 |
| 场景4 | > 200MB | > 600页 | 智能拆分 |
| 场景5 | 极端情况 | 任意 | 自动处理 |

## 📊 性能指标

| 场景 | 串行处理 | 并发处理 | 性能提升 |
|------|---------|---------|---------|
| 单文件 | 23秒 | 23秒 | - |
| 3个文件 | 149秒 | 88秒 | **1.7倍** |
| 10个文件 | 300秒 | 30秒 | **10倍** |

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
vi config/accounts.yaml  # 填入账户信息
```

### 批量登录获取Token

> 默认 **headless 模式**（无界面），可在 macOS/Windows/Linux 服务器上运行。

```bash
# 默认 headless（无界面，推荐）
.venv/bin/python3 src/batch_login.py

# 需要调试时打开浏览器界面
.venv/bin/python3 src/batch_login.py --headed
```

脚本会自动完成以下流程：
1. 打开浏览器访问 MinerU 登录页
2. 自动填写账号密码
3. 自动点击阿里云验证码（大部分账户全自动通过）
4. 自动获取并保存 Token 到 `all_tokens.json`

### 使用

#### 方式1: MCP工具（推荐）

在Kiro CLI中：
```
"帮我处理 ~/Documents/report.pdf"
"处理 ~/Documents 目录下所有PDF"
```

#### 方式2: 命令行工具

```bash
# Rich UI（美观界面）
python3 tools/mineru_rich_enhanced.py ~/Documents/report.pdf

# 批量异步并行
python3 src/mineru_batch_async.py ~/Documents "*.pdf"

# 直接处理
python3 src/mineru_async.py ~/Documents/report.pdf
```

## 📦 安装

### 系统要求

- Python 3.10+
- uv（Python包管理器）
- Git

### 手动安装

```bash
# 1. 克隆仓库
git clone https://github.com/neosun100/mineru-mcp-server.git
cd mineru-mcp-server

# 2. 创建虚拟环境
uv venv
source .venv/bin/activate

# 3. 安装依赖
uv pip install niquests PyPDF2 python-pptx python-docx mcp rich playwright pyyaml
playwright install chromium

# 4. 配置账户
cp accounts.yaml.example accounts.yaml
vi accounts.yaml

# 5. 批量登录（需要图形界面环境）
python3 batch_login.py
```

### MCP服务器配置

编辑 `~/.kiro/settings/mcp.json`：

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

将项目中的 Skill 复制到 Kiro 配置目录，即可通过自然语言自动管理 Token：

```bash
cp -r skills/mineru-token-manager ~/.kiro/skills/
```

安装后，AI 助手会自动：
- 处理文档前检查 Token 是否过期
- 过期时自动执行 headless 批量登录续期
- 续期完成后继续处理文档

## 🎯 使用

### MCP工具

#### process_document
处理单个文档（本地文件或URL）

```
"帮我处理这个PDF ~/Documents/report.pdf"
"处理这个链接 https://example.com/doc.pdf"
```

#### process_directory
批量处理目录（真正异步并行）

```
"处理 ~/Documents 目录下所有PDF"
"把 ~/Downloads 里的PPTX都转成Markdown"
```

#### get_token_status
查询Token状态

```
"查看MinerU的Token状态"
```

### 命令行工具

#### 单文件处理

```bash
# Rich UI（推荐）
python3 mineru_rich_enhanced.py ~/Documents/report.pdf

# 直接处理
python3 mineru_async.py ~/Documents/report.pdf
```

#### 批量处理

```bash
# 批量异步并行（推荐）
python3 mineru_batch_async.py ~/Documents "*.pdf"

# Rich UI批量
python3 mineru_rich_enhanced.py ~/Documents --pattern "*.pdf"
```

#### 超大文件处理

```bash
# 自动拆分、并行处理、合并
python3 test_large_file_complete.py ~/Documents/large_file.pdf
```

## 🔧 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| [niquests](https://niquests.readthedocs.io/) | 3.17.0 | HTTP/2+HTTP/3客户端 |
| [MCP SDK](https://modelcontextprotocol.io/) | 1.23.1 | Model Context Protocol |
| [Rich](https://rich.readthedocs.io/) | 14.2.0 | 终端UI |
| [PyPDF2](https://pypdf2.readthedocs.io/) | 3.0.1 | PDF处理 |
| [python-pptx](https://python-pptx.readthedocs.io/) | 1.0.2 | PPT处理 |
| [python-docx](https://python-docx.readthedocs.io/) | 1.2.0 | Word处理 |

## 📁 项目结构

```
mineru-mcp-server/
├── README.md                   # 主文档
├── .gitignore                  # Git忽略规则
├── requirements.txt            # 依赖列表
├── install_mcp.sh              # 一键安装脚本
│
├── src/                        # 核心代码
│   ├── batch_login.py          # Token管理
│   ├── manage_tokens.py        # Token查看
│   ├── mineru_async.py         # 异步处理器
│   ├── mineru_batch_async.py   # 批量并行处理
│   ├── mineru_mcp_server.py    # MCP服务器
│   ├── split_large_file.py     # 拆分工具
│   ├── login_complete.py       # 单账户登录
│   └── renew_token.py          # Token续期
│
├── tools/                      # 辅助工具
│   ├── mineru_rich_enhanced.py # Rich UI增强版
│   ├── test_large_file_complete.py # 超大文件测试
│   └── ...
│
├── docs/                       # 文档目录
│   ├── QUICK_START.md          # 快速开始
│   ├── MCP_INSTALLATION.md     # MCP安装指南
│   ├── MCP_DESIGN.md           # MCP设计文档
│   ├── SECURITY_REPORT.md      # 安全报告
│   ├── PROCESSING_FLOW.md      # 处理流程
│   └── ...
│
├── config/                     # 配置文件
│   └── accounts.yaml.example   # 配置模板
│
└── tests/                      # 测试文件
    ├── test_all.py
    └── test_workflow.sh
```

## 📚 文档

- [快速开始指南](QUICK_START.md) - 5分钟快速开始
- [MCP安装指南](MCP_INSTALLATION.md) - 详细的MCP配置
- [MCP设计文档](MCP_DESIGN.md) - MCP工具设计
- [安全检查报告](SECURITY_REPORT.md) - 安全性说明
- [处理流程详解](PROCESSING_FLOW.md) - 完整处理流程
- [拆分逻辑分析](SPLIT_LOGIC_ANALYSIS.md) - 智能拆分算法

## 🔄 版本历史

### v3.2.0 (2026-02-19) - 全面优化
- ✨ URL 文件直接处理（自动下载→上传→处理）
- ✨ URL 格式智能识别（magic bytes fallback）
- ✨ Token 过期自动检测（处理前检查）
- 🔧 修复 get_token_status 路径错误
- 🔧 移除未实现的工具（process_urls、extract_info）
- 🔧 完善 requirements.txt（9个依赖）
- 🔧 日志级别优化，批量登录增加重试

### v3.1.0 (2026-02-19) - Headless 全自动登录
- ✨ 默认 headless 模式（无需 UI，Linux 服务器可用）
- ✨ 自动点击阿里云验证码（`#aliyunCaptcha-checkbox-icon`）
- ✨ 完整 stealth JS 伪装（WebGL/plugins/permissions）
- ✨ `--headed` 参数可开启浏览器界面调试

### v3.0.0 (2026-01-25) - 完整生产级解决方案
- ✨ 批量异步并行处理（性能提升10倍）
- ✨ Rich UI增强版（详细进度、实时速度、错误详情）
- ✨ 一键安装脚本
- ✨ 完整的安全检查
- ✨ 所有场景完整覆盖

### v2.6.0 (2026-01-25) - 真正的批量异步并行
- ✨ 多文件同时处理（真正并发）
- ✨ 信号量控制并发数
- ✨ 总进度 + 单文件进度

### v2.4.0 (2026-01-25) - Rich UI增强版
- ✨ 美观的可视化界面
- ✨ 实时进度显示
- ✨ 详细的统计信息

### v2.3.0 (2026-01-25) - 完善所有场景处理逻辑
- ✨ 智能拆分算法
- ✨ 5种场景完整覆盖
- ✨ 数学上保证正确

### v2.1.0 (2026-01-25) - 真正异步实现
- ✨ niquests AsyncSession
- ✨ 性能提升10倍
- ✨ HTTP/2+HTTP/3支持

### v2.0.0 (2026-01-25) - MCP服务器
- ✨ MCP服务器实现
- ✨ 5个MCP工具
- ✨ 自然语言交互

### v1.4.0 (2026-01-25) - API封装
- ✨ API封装
- ✨ 负载均衡

### v1.3.0 (2026-01-25) - 批量账户管理
- ✨ 批量登录功能

### v1.2.0 (2026-01-25) - 多账户支持
- ✨ 多账户Token管理
- ✨ 安全增强

## 🎨 界面展示

### Rich UI界面

```
╭─────────────────────────────────╮
│  MinerU 文档处理系统            │
│  支持 PDF/PPTX/DOCX/图片        │
╰─────────────────────────────────╯

╭─────────── 文件信息 ───────────╮
│  📄 文件  report.pdf           │
│  📋 格式  PDF                  │
│  💾 大小  9.4 MB               │
│  📖 页数  135 页               │
╰────────────────────────────────╯

⠋ 📤 上传文件... ━━━━━━━━━━━━━━━━ 100% 9.9/9.9 MB
⠋ ⚙️  处理中...   ━━━━━━━━━━━━━━━━  45% 60/135 页
⠋ 📥 下载结果... ━━━━━━━━━━━━━━━━  80% 8.0/10.0 MB

╭─────────── 处理完成 ───────────╮
│  ✅ Markdown  report.md        │
│  ✅ 图片      report_images/   │
│  ⏱️  耗时      23.5秒          │
│  ⚡ 速度      8.0 图片/秒      │
╰────────────────────────────────╯
```

### 批量处理界面

```
📊 总进度                         ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% (10/10)
✅ doc1.pdf                       ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
✅ doc2.pdf                       ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
⚙️  doc3.pdf                      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  45%

╭─────────────────────────────────────────────────────────────╮
│                        📊 处理结果汇总                       │
├──────────────────────┬──────────┬───────┬────────┬─────────┤
│ 文件                 │   状态   │  页数 │   图片 │    耗时 │
├──────────────────────┼──────────┼───────┼────────┼─────────┤
│ doc1.pdf             │    ✅    │   135 │    110 │   28.6s │
│ doc2.pdf             │    ✅    │    50 │     25 │   15.2s │
│ doc3.pdf             │    ✅    │    80 │     40 │   20.1s │
╰──────────────────────┴──────────┴───────┴────────┴─────────╯

╭─────────── 统计信息 ───────────╮
│  📁 总文件数    10             │
│  ✅ 成功        9              │
│  ❌ 失败        1              │
│  📖 总页数      1,250          │
│  🖼️  总图片     850            │
│  ⏱️  总耗时     45.3秒         │
│  📊 平均耗时    4.5秒/文件     │
│  ⚡ 处理速度    27.6 页/秒     │
╰────────────────────────────────╯
```

## 🎯 使用场景

### 场景1: 单个文档处理

```python
from mineru_async import MinerUAsyncProcessor

processor = MinerUAsyncProcessor()
result = await processor.process_file("~/Documents/report.pdf")
```

### 场景2: 批量文档处理

```python
from mineru_batch_async import BatchAsyncProcessor

processor = BatchAsyncProcessor(max_concurrent=5)
results = await processor.process_files_parallel([
    "~/Documents/doc1.pdf",
    "~/Documents/doc2.pdf",
    "~/Documents/doc3.pdf"
])
```

### 场景3: 超大文件处理

```bash
# 自动拆分、并行处理、合并
python3 test_large_file_complete.py ~/Documents/large_file.pdf
```

### 场景4: MCP自然语言交互

```
用户: "帮我处理这个PDF ~/Documents/report.pdf"

AI: 好的，我来处理这个PDF文件。
    [调用 process_document 工具]
    
    处理完成！文档共50页，已转换为Markdown。
    
    主要内容：
    - 第一章：项目概述
    - 第二章：技术方案
    
    完整结果：~/Documents/report.md
```

## 🔐 Token管理

### 批量登录

> 默认 **headless 模式**（无界面），可在 macOS/Windows/Linux 服务器上运行。

```bash
# 默认 headless（无界面，推荐）
.venv/bin/python3 src/batch_login.py

# 需要调试时打开浏览器界面
.venv/bin/python3 src/batch_login.py --headed
```

**全自动流程：**
1. 访问 MinerU 首页，点击登录按钮
2. 跳转 SSO 登录页，自动填写账号密码
3. 自动点击阿里云验证码（`#aliyunCaptcha-checkbox-icon`）
4. 验证通过后自动删除旧 Token、创建新 Token
5. 保存到 `all_tokens.json`

**说明：**
- 大部分账户验证码全自动通过，个别可能需手动点击
- 短时间内连续登录过多账户可能触发风控，重试即可
- Token 有效期约 90 天

### 查看Token状态

```bash
python3 manage_tokens.py
```

### 自动过期检测

- 从Token名称提取创建时间
- 自动计算剩余天数
- 提前1天提示刷新

### 负载均衡

- 随机选择账户
- 分散API压力
- 提高可用性

## 🤖 MCP工具

### process_document

处理单个文档（本地文件或URL）

**参数**:
- `file_path` - 文件路径或URL（必需）
- `model_version` - 模型版本（可选）
- `enable_formula` - 公式识别（可选）
- `enable_table` - 表格识别（可选）

**返回**:
```json
{
  "source": "~/Documents/report.pdf",
  "output": {
    "markdown": "~/Documents/report.md",
    "images": "~/Documents/report_images"
  }
}
```

### process_directory

批量处理目录（真正异步并行）

**参数**:
- `directory` - 目录路径（必需）
- `file_pattern` - 文件过滤器（可选）

**返回**:
```json
{
  "total_files": 10,
  "success": 9,
  "failed": 1,
  "results": [...]
}
```

### get_token_status

查询Token状态

**返回**:
```json
[
  {
    "email": "user@example.com",
    "name": "账号1",
    "token_name": "token-20260125013352",
    "expired_at": "2026-02-07T17:33:52Z"
  }
]
```

## 📊 性能优化

### 真正异步并发

使用 `niquests AsyncSession`，所有HTTP请求都是异步的：

```python
async with AsyncSession() as session:
    # 真正的异步请求
    response = await session.post(...)
    response = await session.put(...)
    response = await session.get(...)
```

### 批量异步并行

使用 `asyncio.Semaphore` 控制并发数：

```python
semaphore = asyncio.Semaphore(max_concurrent)

async def process_one(file):
    async with semaphore:
        # 处理文件
        pass

# 真正的并行处理
results = await asyncio.gather(*[process_one(f) for f in files])
```

### 智能拆分算法

同时考虑文件大小和页数：

```python
chunks_by_size = int(file_size / 180) + 1
chunks_by_pages = (total_pages + 599) // 600
chunk_count = max(chunks_by_size, chunks_by_pages)
```

数学上保证每个分片同时满足大小和页数限制。

## 🔒 安全性

### 敏感信息保护

所有敏感文件已被 `.gitignore` 保护：

- `accounts.yaml` - 账户密码
- `all_tokens.json` - Token
- `cookies.json` - Cookie
- `*.log` - 日志文件
- `.venv/` - 虚拟环境

### 代码安全

- ✅ 核心代码无硬编码敏感信息
- ✅ 所有敏感信息通过配置文件管理
- ✅ 配置文件已被.gitignore保护
- ✅ 可以安全公开分享

详见 [安全检查报告](SECURITY_REPORT.md)

## 🧪 测试

### 完整验证通过

| 测试项 | 文件 | 结果 |
|--------|------|------|
| 本地PDF | 2601.12538.pdf (9.5MB, 135页) | ✅ |
| 本地PPTX | 智能湖仓.pptx (1.5MB, 1页) | ✅ |
| 本地DOCX | 字节流迁移调优.docx (288KB, 25页) | ✅ |
| 本地图片 | 实时大屏应用.jpg (98KB) | ✅ |
| 超大PDF | 精通Elastic Stack.pdf (212MB, 422页) | ✅ |
| 批量处理 | 3文件并发 | ✅ |

### 运行测试

```bash
# 单文件测试
python3 mineru_async.py ~/Documents/test.pdf

# 批量测试
python3 mineru_batch_async.py ~/Documents "*.pdf"

# 超大文件测试
python3 test_large_file_complete.py ~/Documents/large.pdf
```

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- [MinerU](https://mineru.net) - 提供强大的文档解析API
- [Anthropic](https://www.anthropic.com) - Model Context Protocol
- [niquests](https://niquests.readthedocs.io/) - 现代HTTP客户端

## 📮 联系方式

- GitHub: [@neosun100](https://github.com/neosun100)
- 项目地址: https://github.com/neosun100/mineru-mcp-server

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给个Star！**

Made with ❤️ by neosun100

</div>
