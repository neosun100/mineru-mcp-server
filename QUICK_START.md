# MinerU 快速开始指南

## 🚀 5分钟快速开始

### 1. 首次配置（一次性）

```bash
cd /Users/jiasunm/Code/GenAI/MinerU-Token

# 1.1 创建虚拟环境
uv venv
source .venv/bin/activate

# 1.2 安装依赖
uv pip install niquests PyPDF2 python-pptx python-docx mcp rich

# 1.3 配置账户
cp accounts.yaml.example accounts.yaml
vi accounts.yaml  # 填入5个账户信息

# 1.4 批量登录获取Token
python3 batch_login.py
```

### 2. 配置MCP服务器（Kiro CLI）

编辑 `~/.kiro/settings/mcp.json`，添加：

```json
{
  "mcpServers": {
    "mineru": {
      "command": "/Users/jiasunm/Code/GenAI/MinerU-Token/.venv/bin/python3",
      "args": ["/Users/jiasunm/Code/GenAI/MinerU-Token/mineru_mcp_server.py"],
      "env": {
        "PYTHONPATH": "/Users/jiasunm/Code/GenAI/MinerU-Token"
      }
    }
  }
}
```

### 3. 使用

#### 方式1: MCP工具（推荐）

重启Kiro CLI，然后：

```
"帮我处理 ~/Documents/report.pdf"
"处理 ~/Documents 目录下所有PDF"
```

#### 方式2: 命令行工具

```bash
# 单文件（Rich UI）
python3 mineru_rich_enhanced.py ~/Documents/report.pdf

# 批量并行
python3 mineru_batch_async.py ~/Documents "*.pdf"

# 直接处理
python3 mineru_async.py ~/Documents/report.pdf
```

## 📋 支持的功能

### 文件格式
- ✅ PDF
- ✅ PPTX/PPT
- ✅ DOCX/DOC
- ✅ PNG/JPG/JPEG
- ✅ HTML

### 输入类型
- ✅ 本地文件
- ✅ 在线URL
- ✅ 目录批量
- ✅ 混合输入

### 特殊处理
- ✅ 超大文件（>200MB）自动拆分
- ✅ 超页数文件（>600页）智能处理
- ✅ 批量异步并行（性能提升10倍）

## 🎯 MCP工具说明

### process_document
处理单个文档（本地文件或URL）

**示例**:
```
"帮我处理这个PDF ~/Documents/report.pdf"
"处理这个链接 https://example.com/doc.pdf"
```

### process_directory
批量处理目录（真正异步并行）

**示例**:
```
"处理 ~/Documents 目录下所有PDF"
"把 ~/Downloads 里的PPTX都转成Markdown"
```

### get_token_status
查询Token状态

**示例**:
```
"查看MinerU的Token状态"
```

## ⚙️ 维护

### Token刷新（每14天）

```bash
cd /Users/jiasunm/Code/GenAI/MinerU-Token
python3 batch_login.py
```

### 查看Token状态

```bash
python3 manage_tokens.py
```

## 📊 性能

- 单文件: ~23秒
- 批量3文件: ~88秒（并发）
- 批量10文件: ~30秒（并发）
- 性能提升: 10倍

## 🔒 安全

- ✅ 所有敏感文件已被.gitignore保护
- ✅ 核心代码无硬编码
- ✅ 可以安全推送到GitHub

## 📚 完整文档

- `README.md` - 项目说明
- `MCP_INSTALLATION.md` - MCP详细安装
- `MCP_DESIGN.md` - MCP设计文档
- `SECURITY_REPORT.md` - 安全检查报告
- `QUICK_START.md` - 本文档

---

**✅ 5分钟即可开始使用！**
