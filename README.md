# MinerU API Token 自动续期工具

## ✅ 问题已解决

通过人机协作 + 正确的 API 调用方式，实现了 Token 的自动续期。

## 核心发现

1. **认证方式**：API 使用 `Authorization: Bearer <uaa-token>` 而不是 Cookie
2. **参数字段**：创建 Token 时使用 `token_name` 而不是 `name`
3. **人机验证**：阿里云验证需要真人点击，但只需点一次（每14天）
4. **智能管理**：每次自动删除所有旧 Token，只保留一个新的

## 快速使用

### 方式一：完全自动化（推荐）⭐

```bash
python3 login_auto_final.py
```

**完全自动，无需任何人工操作！**
- 🤖 自动填写账号密码
- 🤖 自动点击登录
- 🤖 **自动通过人机验证**
- 🤖 自动提取 Cookie
- 🤖 自动删除旧 Token
- 🤖 自动创建新 Token
- ✅ 完成！（约 2 分钟）

### 方式二：人机协作（备用）

```bash
python3 login_complete.py
```

如果自动化偶尔失败，使用此方式（需要手动点击验证）。

### 日常使用（Cookie 有效期内）

```bash
python3 renew_token.py
```

自动删除旧 Token 并创建新的，无需任何手动操作。

### 查看状态

```bash
python3 check_status.py
```

### 运行测试

```bash
python3 test_all.py
```

## 自动化设置

```bash
crontab -e

# 每天凌晨2点自动运行
0 2 * * * cd /path/to/MinerU-Token && python3 renew_token.py >> renew.log 2>&1
```

## 文件说明

- `login_complete.py` - 人机协作登录（每14天用一次）
- `renew_token.py` - 自动续期（随时可用）
- `check_status.py` - 状态检查
- `test_all.py` - 完整测试套件
- `cookies.json` - Cookie 存储（14天有效）
- `token_*.txt` - Token 记录

## 工作原理

### API 认证

```python
headers = {
    'authorization': f'Bearer {uaa_token}'
}
```

### Token 管理策略

```python
# 1. 删除所有旧 Token
DELETE /api/v4/tokens/{id}

# 2. 创建新 Token
POST /api/v4/tokens
Body: {"token_name": "token-20260125000000"}
```

### Token 命名

- 格式：`token-年月日时分秒`
- 例如：`token-20260125002900`
- 过期：创建后 14 天

## 维护周期

- **Cookie 有效期**：14 天
- **Token 有效期**：14 天
- **建议**：每 13 天运行一次 `login_complete.py`

## 下次使用

当看到提示：

```
❌ Cookie 即将过期，请重新登录
```

运行：
```bash
python3 login_complete.py
```

手动点一下验证按钮即可（5秒）。

## 成功案例

```
✅ 当前有 1 个 Token:
  - token-20260125002900
    过期: 2026-02-08T00:29:00+08:00
```

## 技术细节

- 使用 Playwright 模拟真实用户行为
- 超真实的打字速度（随机延迟、偶尔停顿）
- 贝塞尔曲线鼠标轨迹
- 反自动化检测（隐藏 webdriver 特征）
- Authorization Bearer 认证方式
- 智能 Token 管理（自动删除旧的）

## 版本

当前版本：**v1.1.0** - 智能管理版本

查看完整文档：
- `README_GITHUB.md` - GitHub 风格文档
- `DOCUMENTATION.md` - 详细操作手册
- `SECURITY.md` - 安全指南
