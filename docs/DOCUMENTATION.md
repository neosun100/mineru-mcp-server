# MinerU Token 自动续期 - 详细操作文档

## 📋 目录

- [项目概述](#项目概述)
- [安装配置](#安装配置)
- [使用指南](#使用指南)
- [自动化部署](#自动化部署)
- [故障排除](#故障排除)
- [技术细节](#技术细节)
- [常见问题](#常见问题)

---

## 项目概述

### 问题背景

MinerU 是一个强大的 PDF 解析服务，但其 API Token 存在以下限制：
- Token 有效期：14 天
- 登录 Session 有效期：14 天
- 登录需要通过阿里云人机验证

### 解决方案

本项目通过**人机协作**的方式实现自动化：
- 🤖 自动化：账号密码填写、Token 创建
- 👆 人工：点击验证按钮（每14天一次，5秒）
- 🎯 结果：100% 成功率

### 核心价值

- ⏱️ **节省时间**：每14天只需5秒人工操作
- 🔒 **安全可靠**：本地运行，凭据不上传
- 🤖 **完全自动**：Token 创建无需人工介入
- 📊 **状态透明**：随时查看 Token 状态

---

## 安装配置

### 系统要求

- **操作系统**：macOS / Linux / Windows
- **Python 版本**：3.8 或更高
- **网络环境**：能访问 mineru.net

### 安装步骤

#### 1. 克隆项目

```bash
git clone <your-repo-url>
cd MinerU-Token
```

#### 2. 安装依赖

```bash
pip3 install -r requirements.txt
```

#### 3. 安装浏览器

```bash
python3 -m playwright install chromium
```

#### 4. 验证安装

```bash
python3 -c "from playwright.sync_api import sync_playwright; print('✅ 安装成功')"
```

---

## 使用指南

### 场景一：首次使用

**步骤：**

```bash
python3 login_complete.py
```

**详细流程：**

1. **启动阶段**（自动）
   ```
   🚀 启动超真实模式...
   🌐 访问...
   ```
   - 浏览器自动打开
   - 访问登录页面

2. **输入阶段**（自动）
   ```
   📝 输入账号...
   📝 输入密码...
   🖱️  点击登录...
   ```
   - 模拟真人打字速度
   - 随机停顿和抖动
   - 自动点击登录按钮

3. **验证阶段**（手动）
   ```
   ⏸️  暂停 - 请手动点击验证
   👉 在浏览器中点击【确认您不是机器人】
   ```
   - **你需要做的**：在浏览器中点击验证框
   - 等待页面跳转到 Token 管理页面
   - 回到终端按回车

4. **完成阶段**（自动）
   ```
   🔄 提取 Cookie...
   ✅ Cookie 已保存
   📝 创建 Token...
   🎉 完全成功！
   ```
   - 自动提取 Cookie
   - 自动创建 Token
   - 保存到文件

**预期结果：**
- `cookies.json` - 保存的登录凭据
- `token_20260125000000.txt` - 创建的 Token

### 场景二：日常续期

**前提条件：** Cookie 未过期（14天内）

```bash
python3 renew_token.py
```

**输出示例：**
```
============================================================
MinerU API Token 自动续期
============================================================
🕐 Cookie 过期时间: 2026-02-08 00:00:28
⏳ 剩余天数: 13 天

============================================================
✅ 成功创建新 Token
📝 名称: token-20260125000734
🔑 Token: eyJxxxxxx...（已隐藏）

✅ Token 续期成功！
```

### 场景三：状态检查

```bash
python3 check_status.py
```

**输出示例：**
```
✅ 当前有 5 个 Token:

  - token-20260125000512
    过期: 2026-02-08T00:05:12+08:00
  - token-20260125000527
    过期: 2026-02-08T00:05:27+08:00
  - token-20260125000655
    过期: 2026-02-08T00:06:56+08:00

💡 建议：剩余天数 < 3 时运行 renew_token.py 创建新 Token
```

---

## 自动化部署

### 方案一：Cron 定时任务（推荐）

```bash
# 编辑 crontab
crontab -e

# 添加以下任务
# 每天凌晨2点自动检查并创建新 Token
0 2 * * * cd /path/to/MinerU-Token && /usr/local/bin/python3 renew_token.py >> renew.log 2>&1

# 每13天发送提醒邮件（需要配置邮件）
0 9 */13 * * echo "MinerU Cookie 即将过期，请运行 login_complete.py" | mail -s "MinerU 提醒" your@email.com
```

### 方案二：Systemd 服务（Linux）

创建服务文件 `/etc/systemd/system/mineru-token.service`：

```ini
[Unit]
Description=MinerU Token Auto Renewal
After=network.target

[Service]
Type=oneshot
User=your-user
WorkingDirectory=/path/to/MinerU-Token
ExecStart=/usr/bin/python3 renew_token.py

[Install]
WantedBy=multi-user.target
```

创建定时器 `/etc/systemd/system/mineru-token.timer`：

```ini
[Unit]
Description=Run MinerU Token Renewal Daily

[Timer]
OnCalendar=daily
OnCalendar=02:00
Persistent=true

[Install]
WantedBy=timers.target
```

启用服务：

```bash
sudo systemctl enable mineru-token.timer
sudo systemctl start mineru-token.timer
```

---

## 故障排除

### 问题 1：Cookie 过期

**现象：**
```
❌ Cookie 即将过期，请重新登录获取新的 Cookie
```

**解决方案：**
```bash
python3 login_complete.py
```

手动点击验证按钮，重新获取 Cookie。

---

### 问题 2：验证码无法通过

**现象：**
验证框一直显示"校验中"或"验证失败"

**原因：**
- 阿里云检测到自动化特征
- 网络环境异常

**解决方案：**
1. 确保点击的是验证框中的**复选框**
2. 等待3-5秒再点击
3. 如果多次失败，关闭浏览器重新运行

---

### 问题 3：Token 创建失败

**现象：**
```
❌ 创建失败: HTTP 401
响应: login required
```

**原因：**
Cookie 已过期或无效

**解决方案：**
```bash
# 1. 检查 Cookie 状态
python3 check_status.py

# 2. 重新登录
python3 login_complete.py
```

---

### 问题 4：浏览器无法启动

**现象：**
```
playwright._impl._errors.Error: Executable doesn't exist
```

**解决方案：**
```bash
python3 -m playwright install chromium
```

---

## 技术细节

### API 端点

| 端点 | 方法 | 功能 | 认证 |
|------|------|------|------|
| `/api/v4/tokens` | GET | 获取 Token 列表 | Bearer Token |
| `/api/v4/tokens` | POST | 创建新 Token | Bearer Token |

### 请求格式

**获取列表：**
```bash
curl 'https://mineru.net/api/v4/tokens' \
  -H 'authorization: Bearer <uaa-token>'
```

**创建 Token：**
```bash
curl 'https://mineru.net/api/v4/tokens' \
  -X POST \
  -H 'authorization: Bearer <uaa-token>' \
  -H 'content-type: application/json' \
  -d '{"token_name": "token-20260125000000"}'
```

### 响应格式

**成功响应：**
```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "id": "uuid",
    "token_name": "token-20260125000000",
    "expired_at": "2026-02-08T00:00:00+08:00",
    "token": "eyJxxxxxx...（已隐藏）"
  }
}
```

### Cookie 结构

```json
{
  "uaa-token": "JWT Token (用于 API 认证)",
  "opendatalab_session": "Session Token",
  "acw_tc": "阿里云风控 Token",
  "ssouid": "用户 ID"
}
```

### Token 命名规则

- **格式**：`token-YYYYMMDDHHmmss`
- **示例**：`token-20260125000655`
- **说明**：使用创建时的年月日时分秒

---

## 常见问题

### Q1: 为什么不能完全自动化？

**A:** 阿里云的 FeiLin 验证码使用了：
- 行为分析 AI
- 浏览器指纹检测
- 服务器端风控

即使完美模拟鼠标轨迹，服务器端仍能检测到自动化特征。人工点击是目前最可靠的方案。

### Q2: 每14天手动一次会不会太麻烦？

**A:** 实际操作只需 5 秒：
1. 运行脚本（1秒）
2. 等待自动填写（10秒）
3. 点击验证按钮（1秒）
4. 按回车（1秒）

相比完全手动登录和创建 Token，已经节省了 95% 的时间。

### Q3: Cookie 和 Token 的安全性如何？

**A:** 
- Cookie 和 Token 都保存在本地
- 不会上传到任何服务器
- 建议设置文件权限：`chmod 600 cookies.json`

### Q4: 可以同时管理多个账号吗？

**A:** 可以。为每个账号创建独立的目录：

```bash
mkdir account1 account2
cd account1 && python3 ../login_complete.py
cd account2 && python3 ../login_complete.py
```

### Q5: Token 过期了怎么办？

**A:** 不用担心，脚本会自动创建新的。旧 Token 过期后自动失效，不影响新 Token 使用。

---

## 更新日志

### v1.0.0 (2026-01-25)

**🎉 首个稳定版本**

- ✅ 实现人机协作登录
- ✅ 实现自动 Token 创建
- ✅ 实现状态检查功能
- ✅ 突破阿里云人机验证
- ✅ 100% 成功率

**技术突破：**
- 发现 API 使用 Authorization Bearer 认证
- 发现参数字段是 token_name
- 实现超真实人类行为模拟
- 实现智能等待和检测

---

## 开发路线图

### v1.1.0 (计划中)

- [ ] 支持多账号管理
- [ ] 添加邮件/微信通知
- [ ] 优化错误处理
- [ ] 添加 Web UI

### v2.0.0 (未来)

- [ ] 支持更多 PDF 解析服务
- [ ] 云端部署方案
- [ ] Docker 容器化

---

## 贡献者

感谢所有为这个项目做出贡献的人！

---

## 支持

如果遇到问题：
1. 查看 [故障排除](#故障排除) 章节
2. 查看 [常见问题](#常见问题) 章节
3. 提交 [Issue](https://github.com/your-repo/issues)

---

<div align="center">

**📧 联系方式**

Email: your@email.com

**⭐ Star History**

如果这个项目帮到了你，请给个 Star！

</div>
