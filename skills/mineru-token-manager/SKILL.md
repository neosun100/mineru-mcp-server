---
name: mineru-token-manager
description: |
  **TRIGGER KEYWORDS - Use this skill when user request contains ANY of these patterns:**
  - "MinerU" AND ("token" OR "Token" OR "TOKEN")
  - "MinerU" AND ("过期" OR "状态" OR "续期" OR "刷新" OR "更新" OR "登录")
  - "token" AND ("过期" OR "检查" OR "查看" OR "状态")
  - "批量登录" OR "batch login"
  - "处理文档" OR "处理PDF" OR "process document"
  - "mineru" (case insensitive)

  **What this skill does:**
  Manages MinerU API tokens - checks expiration, auto-refreshes when needed, and processes documents. Integrates with the mineru-mcp-server project.

  **CRITICAL INSTRUCTION:**
  When ANY trigger pattern matches, you MUST immediately use this skill. Always check token status BEFORE processing documents.
---

# MinerU Token Manager Skill

管理 MinerU API Token 的完整生命周期：检查状态、自动续期、处理文档。

## 项目路径

```
/Users/jiasunm/Code/mineru-mcp-server
```

## 核心文件

| 文件 | 用途 |
|------|------|
| `all_tokens.json` | 所有账户的 Token 存储 |
| `src/batch_login.py` | 批量登录获取 Token（默认 headless，`--headed` 开启 UI，失败自动重试） |
| `src/mineru_mcp_server.py` | MCP 服务器（3个工具：process_document、process_directory、get_token_status） |
| `config/accounts.yaml` | 账户配置 |

## 注意事项

- MCP 工具已支持 URL 文件直接处理（自动下载→上传→处理）
- URL 格式识别支持 magic bytes fallback（无后缀的 URL 也能识别）
- MCP 服务器处理文档前会自动检查 Token 过期，过期会返回提示
- `process_urls` 和 `extract_info` 工具已移除（未实现，避免误导）

## 工作流程

### ⚡ 处理文档前必须先检查 Token

**每次处理文档之前，必须执行以下检查流程：**

1. 读取 `all_tokens.json`，检查所有 Token 的 `expired_at`
2. 只要有任意一个 Token 过期 → 自动执行 `batch_login.py` 全部续期
3. 全部有效 → 直接使用 MCP 工具处理文档

### 1. 检查 Token 状态

```bash
cd /Users/jiasunm/Code/mineru-mcp-server && python3 -c "
import json, sys
from datetime import datetime, timezone

with open('all_tokens.json', 'r') as f:
    tokens = json.load(f)

now = datetime.now(timezone.utc)
expired = 0
for email, info in tokens.items():
    exp = datetime.fromisoformat(info['expired_at'].replace('Z', '+00:00'))
    days = (exp - now).days
    status = '❌ 已过期' if days <= 0 else f'⚠️ {days}天' if days <= 3 else f'✅ {days}天'
    print(f'{info[\"name\"]} ({email}) {status}')
    if days <= 0: expired += 1

print(f'\n{\"⚠️ 需要续期！\" if expired else \"✅ 全部有效\"}')
sys.exit(1 if expired else 0)
"
```

### 2. 自动续期（headless，无需 UI）

当检查发现任意 Token 过期时，立即执行：

```bash
cd /Users/jiasunm/Code/mineru-mcp-server && .venv/bin/python3 src/batch_login.py
```

**说明：**
- 默认 headless 模式，无需图形界面，可在 Linux 服务器上运行
- 自动点击阿里云验证码（`#aliyunCaptcha-checkbox-icon`）
- 一次性更新所有账户的 Token
- 如需打开浏览器界面调试：`.venv/bin/python3 src/batch_login.py --headed`
- Token 有效期约 90 天

### 3. 处理文档

Token 有效时，使用 MCP 工具：

- `process_document` - 处理单个文档
- `process_directory` - 批量处理目录
- `get_token_status` - 查询 Token 状态

## 完整自动化流程示例

当用户说"帮我处理这个 PDF"时：

```
1. 检查 Token → 发现过期
2. 自动执行 batch_login.py（headless）→ 全部续期
3. 续期成功 → 调用 MCP 工具处理文档
4. 返回处理结果
```

## 回复模板

### Token 全部有效

```
MinerU Token 状态：
✅ 主账号 - 剩余 XX 天
✅ 账号2 - 剩余 XX 天
...
所有 Token 有效，可以正常处理文档。
```

### Token 过期 → 自动续期

```
⚠️ 发现 Token 已过期，正在自动续期...
[执行 batch_login.py headless 模式]
✅ 全部续期完成！
继续处理您的文档...
```
