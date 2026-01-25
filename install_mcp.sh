#!/bin/bash
"""
MinerU MCP 一键安装脚本
自动完成所有配置
"""

set -e  # 遇到错误立即退出

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║              MinerU MCP 一键安装                             ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# 获取项目路径
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📁 项目路径: $PROJECT_DIR"
echo ""

# 步骤1: 创建虚拟环境
echo "步骤1: 创建虚拟环境"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ! -d "$PROJECT_DIR/.venv" ]; then
    echo "创建虚拟环境..."
    cd "$PROJECT_DIR"
    uv venv
    echo "✅ 虚拟环境创建成功"
else
    echo "✅ 虚拟环境已存在"
fi
echo ""

# 步骤2: 安装依赖
echo "步骤2: 安装依赖"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

source "$PROJECT_DIR/.venv/bin/activate"

echo "安装Python依赖..."
uv pip install niquests PyPDF2 python-pptx python-docx mcp rich selenium pyyaml

echo "✅ 依赖安装完成"
echo ""

# 步骤3: 配置账户
echo "步骤3: 配置账户"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ! -f "$PROJECT_DIR/accounts.yaml" ]; then
    if [ -f "$PROJECT_DIR/accounts.yaml.example" ]; then
        cp "$PROJECT_DIR/accounts.yaml.example" "$PROJECT_DIR/accounts.yaml"
        echo "✅ 已创建 accounts.yaml"
        echo "⚠️  请编辑 accounts.yaml 填入账户信息"
        echo "   vi $PROJECT_DIR/accounts.yaml"
    else
        echo "⚠️  未找到 accounts.yaml.example"
    fi
else
    echo "✅ accounts.yaml 已存在"
fi
echo ""

# 步骤4: 配置MCP服务器
echo "步骤4: 配置MCP服务器（Kiro CLI）"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

MCP_CONFIG="$HOME/.kiro/settings/mcp.json"

if [ -f "$MCP_CONFIG" ]; then
    echo "检查MCP配置..."
    
    if grep -q '"mineru"' "$MCP_CONFIG"; then
        echo "✅ MCP服务器已配置"
    else
        echo "添加MCP服务器配置..."
        
        # 备份原配置
        cp "$MCP_CONFIG" "$MCP_CONFIG.backup"
        
        # 使用Python添加配置
        python3 << PYEOF
import json

config_file = "$MCP_CONFIG"

with open(config_file, 'r') as f:
    config = json.load(f)

if 'mcpServers' not in config:
    config['mcpServers'] = {}

config['mcpServers']['mineru'] = {
    'command': '$PROJECT_DIR/.venv/bin/python3',
    'args': ['$PROJECT_DIR/mineru_mcp_server.py'],
    'env': {
        'PYTHONPATH': '$PROJECT_DIR'
    }
}

with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)

print("✅ MCP配置已添加")
PYEOF
    fi
else
    echo "⚠️  未找到Kiro CLI配置文件"
    echo "   请手动配置: $MCP_CONFIG"
fi
echo ""

# 步骤5: 验证安装
echo "步骤5: 验证安装"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "检查Python模块..."
python3 -c "from mineru_async import MinerUAsyncProcessor; print('✅ mineru_async')"
python3 -c "from mineru_batch_async import BatchAsyncProcessor; print('✅ mineru_batch_async')"
python3 -c "import mineru_mcp_server; print('✅ mineru_mcp_server')"

echo ""
echo "检查MCP服务器..."
python3 -m py_compile "$PROJECT_DIR/mineru_mcp_server.py" && echo "✅ MCP服务器语法正确"

echo ""

# 完成
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║              ✅ 安装完成！                                   ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "下一步:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. 配置账户（如果还没配置）"
echo "   vi $PROJECT_DIR/accounts.yaml"
echo ""
echo "2. 批量登录获取Token"
echo "   cd $PROJECT_DIR"
echo "   python3 batch_login.py"
echo ""
echo "3. 重启Kiro CLI"
echo "   /quit"
echo "   kiro-cli chat"
echo ""
echo "4. 测试MCP工具"
echo "   \"帮我处理 ~/Documents/report.pdf\""
echo ""
echo "✅ 安装完成！"
