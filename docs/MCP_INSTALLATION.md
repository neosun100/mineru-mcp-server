# MinerU MCP 服务器 - 完整安装和使用指南

## 📖 什么是MCP？

**Model Context Protocol (MCP)** 是Anthropic在2024年11月推出的开放标准，用于连接AI模型和外部工具/数据源。

### 核心概念

```
AI助手（Claude/ChatGPT等）
    ↓
MCP客户端
    ↓
MCP服务器（我们的mineru_mcp_server.py）
    ↓
MinerU API（文档处理）
```

### 类比理解

- **MCP = USB-C for AI** - 统一的连接标准
- **MCP Server = 插件** - 为AI提供特定能力
- **MCP Tools = 功能** - AI可以调用的具体操作

## 🛠️ 我们的MCP工具集

### Tool 1: process_document
**功能**: 处理单个文档（本地文件或URL）

**输入**:
- `file_path` - 文件路径或URL（必需）
- `model_version` - 模型版本（可选）
- `enable_formula` - 公式识别（可选）
- `enable_table` - 表格识别（可选）
- `is_ocr` - OCR开关（可选）
- `language` - 文档语言（可选）
- `output_dir` - 输出目录（可选）

**输出**:
```json
{
  "source": "原始路径或URL",
  "source_type": "file|url",
  "total_chunks": 2,
  "success": 2,
  "output": {
    "markdown": "/path/to/output.md",
    "images": "/path/to/images"
  }
}
```

**使用场景**:
- 处理本地PDF
- 处理在线PDF
- 处理网页
- 识别图片文字

### Tool 2: process_directory
**功能**: 批量处理目录下所有文档

**输入**:
- `directory` - 目录路径（必需）
- `file_pattern` - 文件过滤器（可选，如 *.pdf）
- `recursive` - 是否递归（可选）
- `max_workers` - 并行度（可选）

**输出**:
```json
{
  "total_files": 20,
  "success": 19,
  "failed": 1,
  "results": [...]
}
```

**使用场景**:
- 批量转换发票
- 批量处理合同
- 批量识别图片

### Tool 3: process_urls
**功能**: 批量处理URL列表

**输入**:
- `urls` - URL列表（必需）
- `max_workers` - 并行度（可选）

**输出**:
```json
{
  "total_urls": 10,
  "success": 9,
  "failed": 1,
  "results": [...]
}
```

**使用场景**:
- 批量下载论文
- 批量处理网页
- 批量识别在线图片

### Tool 4: extract_info
**功能**: 从文档中提取结构化信息

**输入**:
- `file_path` - 文件路径或URL（必需）
- `extract_type` - 提取类型（必需）
  - `invoice` - 发票信息
  - `contract` - 合同信息
  - `form` - 表单信息
  - `custom` - 自定义字段
- `fields` - 字段列表（custom类型时必需）

**输出**:
```json
{
  "extracted_data": {
    "invoice_number": "12345678",
    "amount": "1250.00",
    "date": "2026-01-20"
  }
}
```

**使用场景**:
- 发票信息提取
- 合同信息提取
- 表单数据提取

### Tool 5: get_token_status
**功能**: 查询Token状态

**输入**: 无

**输出**:
```json
[
  {
    "email": "user1@example.com",
    "name": "主账号",
    "token_name": "token-20260125013352",
    "expired_at": "2026-02-07T17:33:52Z"
  }
]
```

**使用场景**:
- 检查Token状态
- 查看过期时间

## 📦 安装步骤

### 1. 安装MCP SDK

```bash
cd /Users/jiasunm/Code/GenAI/MinerU-Token

# 激活虚拟环境
source .venv/bin/activate

# 安装MCP SDK
uv pip install mcp
```

### 2. 安装依赖

```bash
# 已安装的依赖
uv pip install aiohttp PyPDF2 python-pptx python-docx
```

### 3. 配置MCP服务器

创建或编辑 `~/.config/claude/claude_desktop_config.json`（Claude Desktop）：

```json
{
  "mcpServers": {
    "mineru": {
      "command": "python",
      "args": [
        "/Users/jiasunm/Code/GenAI/MinerU-Token/mineru_mcp_server.py"
      ],
      "env": {
        "PYTHONPATH": "/Users/jiasunm/Code/GenAI/MinerU-Token"
      }
    }
  }
}
```

或者对于其他MCP客户端（如Kiro CLI），配置方式类似。

### 4. 重启AI助手

重启Claude Desktop或其他MCP客户端，使配置生效。

### 5. 验证安装

在AI助手中说：
```
"查看MinerU工具状态"
```

AI会调用 `get_token_status` 工具，显示Token信息。

## 🎯 使用示例

### 示例1: 处理本地PDF

**用户说**:
```
帮我处理这个PDF文件 ~/Documents/report.pdf
```

**AI自动执行**:
```
1. 调用 process_document 工具
2. 参数: {"file_path": "~/Documents/report.pdf"}
3. 等待处理完成
4. 读取Markdown结果
5. 生成摘要并回答
```

**AI回复**:
```
处理完成！文档共50页，已转换为Markdown。

主要内容：
- 第一章：项目概述
- 第二章：技术方案
- 第三章：实施计划

完整结果已保存到：~/Documents/report_merged.md

需要我帮你分析具体内容吗？
```

### 示例2: 处理在线PDF

**用户说**:
```
处理这个论文 https://arxiv.org/pdf/2401.12345.pdf
```

**AI自动执行**:
```
1. 检测到URL
2. 调用 process_document 工具
3. 参数: {"file_path": "https://arxiv.org/pdf/2401.12345.pdf"}
4. 自动选择vlm模型
5. 处理完成
6. 分析内容
```

**AI回复**:
```
处理完成！这是一篇关于深度学习的论文。

论文信息：
- 标题：A Novel Approach to...
- 作者：Zhang et al.
- 摘要：本文提出了一种新的方法...

主要贡献：
1. 提出了新的算法框架
2. 在3个数据集上验证
3. 性能提升15%

完整结果：./output/2401.12345_merged.md
```

### 示例3: 批量处理发票

**用户说**:
```
把 ~/Invoices 目录下所有PDF都处理一下，提取发票号和金额
```

**AI自动执行**:
```
1. 调用 process_directory 工具
2. 参数: {"directory": "~/Invoices"}
3. 扫描到20个PDF
4. 并行处理
5. 提取信息
6. 汇总结果
```

**AI回复**:
```
批量处理完成！

处理结果：
- 成功：19个
- 失败：1个（文件损坏）

提取的信息：
1. invoice_001.pdf - 发票号：12345678, 金额：¥1,250
2. invoice_002.pdf - 发票号：12345679, 金额：¥2,500
...

总金额：¥125,000
平均金额：¥6,579

需要我生成Excel报表吗？
```

### 示例4: 识别图片文字

**用户说**:
```
识别这张图片中的文字 https://example.com/receipt.jpg
```

**AI自动执行**:
```
1. 检测到图片URL
2. 调用 process_document 工具
3. 自动开启OCR
4. 识别文字
5. 返回结果
```

**AI回复**:
```
识别完成！

提取的文字：
─────────────
发票号码：12345678
金额：¥1,250.00
日期：2026-01-20
商家：某某公司
─────────────

需要我帮你整理成表格吗？
```

## 🔧 配置说明

### Claude Desktop配置

文件位置：`~/.config/claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "mineru": {
      "command": "python",
      "args": [
        "/Users/jiasunm/Code/GenAI/MinerU-Token/mineru_mcp_server.py"
      ],
      "env": {
        "PYTHONPATH": "/Users/jiasunm/Code/GenAI/MinerU-Token"
      }
    }
  }
}
```

### Kiro CLI配置

文件位置：`~/.kiro/mcp_config.json`

```json
{
  "mcpServers": {
    "mineru": {
      "command": "python",
      "args": [
        "/Users/jiasunm/Code/GenAI/MinerU-Token/mineru_mcp_server.py"
      ]
    }
  }
}
```

### 其他MCP客户端

任何支持MCP的客户端都可以使用，配置格式类似。

## 🎨 MCP工作流程

```
用户输入
    ↓
AI理解意图
    ↓
AI选择合适的MCP工具
    ↓
调用 mineru_mcp_server.py
    ↓
执行 mineru_production.py
    ↓
调用 MinerU API
    ↓
返回结果给AI
    ↓
AI分析结果
    ↓
AI回复用户
```

## 💡 核心优势

### 1. 零学习成本
```
用户: "处理这个PDF"
AI: 自动调用工具，无需了解技术细节
```

### 2. 智能参数选择
```
AI自动判断:
- PDF → vlm模型
- HTML → MinerU-HTML模型
- 图片 → 开启OCR
- 大文件 → 自动拆分
```

### 3. 自然语言交互
```
用户: "把这个1000页的PDF转成Markdown，提取所有公式"

AI理解:
- 文件：1000页PDF
- 操作：转Markdown
- 需求：提取公式

AI执行:
- 调用 process_document
- 设置 enable_formula=true
- 自动拆分（page_ranges）
- 返回结果和公式列表
```

### 4. 结果理解
```
AI可以:
- 阅读处理后的Markdown
- 提取关键信息
- 生成摘要
- 回答问题
- 进一步分析
```

## 🚀 快速开始

### 1. 安装

```bash
cd /Users/jiasunm/Code/GenAI/MinerU-Token
source .venv/bin/activate
uv pip install mcp aiohttp PyPDF2 python-pptx python-docx
```

### 2. 配置

编辑 `~/.config/claude/claude_desktop_config.json`，添加MCP服务器配置。

### 3. 使用

在Claude Desktop中：
```
"帮我处理这个PDF ~/Documents/report.pdf"
```

## 📊 MCP工具对比

### 常见的MCP工具

| 工具名 | 功能 | 类似度 |
|--------|------|--------|
| filesystem | 文件系统操作 | 基础 |
| brave-search | 网页搜索 | 基础 |
| github | GitHub操作 | 中等 |
| postgres | 数据库查询 | 中等 |
| **mineru** | **文档处理** | **高级** |

### 我们的MCP工具特点

| 特性 | 其他MCP工具 | 我们的工具 |
|------|------------|-----------|
| 输入类型 | 单一 | ✅ 多样（文件+URL） |
| 智能识别 | ❌ | ✅ 自动检测 |
| 批量处理 | ❌ | ✅ 支持 |
| 大文件处理 | ❌ | ✅ 自动拆分 |
| 结果合并 | ❌ | ✅ 自动 |
| Token管理 | ❌ | ✅ 多账户 |

## 🎯 实用的MCP工具推荐

### 1. 文件系统工具
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed"]
    }
  }
}
```

### 2. GitHub工具
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "your_token"
      }
    }
  }
}
```

### 3. 我们的MinerU工具
```json
{
  "mcpServers": {
    "mineru": {
      "command": "python",
      "args": ["/path/to/mineru_mcp_server.py"]
    }
  }
}
```

## 📝 完整配置示例

`~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", 
               "/Users/jiasunm/Documents"]
    },
    "mineru": {
      "command": "python",
      "args": [
        "/Users/jiasunm/Code/GenAI/MinerU-Token/mineru_mcp_server.py"
      ],
      "env": {
        "PYTHONPATH": "/Users/jiasunm/Code/GenAI/MinerU-Token"
      }
    }
  }
}
```

## 🎓 使用流程

### 1. 启动AI助手

```bash
# Claude Desktop
# 启动应用即可

# 或者使用Kiro CLI
kiro-cli chat
```

### 2. 使用工具

```
用户: "帮我处理 ~/Documents/report.pdf"

AI: 好的，我来处理这个PDF文件。
    [调用 mineru.process_document]
    
    处理完成！文档共50页...
```

### 3. 查看工具列表

```
用户: "你有哪些工具可以用？"

AI: 我可以使用以下工具：
    1. mineru.process_document - 处理文档
    2. mineru.process_directory - 批量处理
    3. mineru.process_urls - 批量URL
    4. mineru.extract_info - 信息提取
    5. mineru.get_token_status - Token状态
```

## ⚠️ 注意事项

### 1. Python环境

MCP服务器需要Python 3.10+：
```bash
python3 --version  # 确保 >= 3.10
```

### 2. 虚拟环境

建议使用虚拟环境：
```bash
source .venv/bin/activate
```

### 3. Token管理

确保Token有效：
```bash
python3 manage_tokens.py  # 查看状态
python3 batch_login.py    # 刷新Token
```

### 4. 日志调试

查看MCP服务器日志：
```bash
# Claude Desktop日志
~/Library/Logs/Claude/mcp*.log

# 或者直接运行服务器测试
python3 mineru_mcp_server.py
```

## 🔍 故障排查

### 问题1: MCP服务器无法启动

**检查**:
```bash
# 测试Python脚本
python3 mineru_mcp_server.py

# 检查依赖
pip list | grep mcp
```

### 问题2: 工具调用失败

**检查**:
```bash
# 验证Token
python3 manage_tokens.py

# 测试处理器
python3 mineru_production.py test.pdf
```

### 问题3: 找不到工具

**检查配置文件**:
```bash
cat ~/.config/claude/claude_desktop_config.json
```

## 📚 相关资源

- [MCP官方文档](https://modelcontextprotocol.io)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP服务器列表](https://github.com/modelcontextprotocol/servers)

---

**✅ 完整的MCP服务器实现，让AI助手可以直接处理文档！**
