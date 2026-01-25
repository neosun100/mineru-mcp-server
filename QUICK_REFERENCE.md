# 🚀 快速参考

## 常用命令

```bash
# 首次使用或 Cookie 过期（每14天）
python3 login_complete.py

# 自动创建新 Token（随时）
python3 renew_token.py

# 查看 Token 状态
python3 check_status.py
```

## 文件说明

| 文件 | 用途 | 重要性 |
|------|------|--------|
| `login_complete.py` | 登录脚本 | ⭐⭐⭐ |
| `renew_token.py` | 续期脚本 | ⭐⭐⭐ |
| `check_status.py` | 状态检查 | ⭐⭐ |
| `cookies.json` | Cookie 存储 | 🔒 敏感 |
| `token_*.txt` | Token 记录 | 🔒 敏感 |

## 维护周期

- 🔄 **每 14 天**：运行 `login_complete.py`（5秒）
- 🤖 **每天自动**：Cron 运行 `renew_token.py`

## 故障速查

| 问题 | 解决方案 |
|------|---------|
| Cookie 过期 | `python3 login_complete.py` |
| Token 创建失败 | 检查 Cookie 是否过期 |
| 验证码无法通过 | 确保点击复选框，等待3-5秒 |
| 浏览器无法启动 | `python3 -m playwright install chromium` |

## 技术要点

```python
# API 认证
headers = {'authorization': f'Bearer {uaa_token}'}

# 创建 Token
json = {"token_name": "token-20260125000000"}
```

## 成功标志

```
✅ 当前有 5 个 Token
✅ Cookie 已保存
✅ Token 续期成功
```

---

**💡 提示**：将此文件保存为书签，方便快速查阅！
