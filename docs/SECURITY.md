# ⚠️ 安全警告

## 🔒 敏感文件

以下文件包含敏感信息，**绝对不要提交到 Git**：

### 1. cookies.json
- 包含登录凭据
- 有效期 14 天
- 可用于访问你的账户

### 2. token_*.txt
- 包含 API Token
- 有效期 14 天
- 可用于调用 MinerU API

### 3. *.log
- 可能包含敏感信息
- 包含运行日志

## ✅ 已采取的保护措施

### .gitignore 配置

```gitignore
# ⚠️ 敏感信息 - 绝对不要提交！
cookies.json
token_*.txt
*.log
*_cookie*.json
*_token*.txt
*_session*.json
```

### 文件权限建议

```bash
# 设置敏感文件为只读（仅所有者）
chmod 600 cookies.json
chmod 600 token_*.txt
```

## ⚠️ 使用注意事项

### 1. 不要分享

- ❌ 不要将 cookies.json 发送给任何人
- ❌ 不要将 token_*.txt 上传到任何地方
- ❌ 不要在公开场合展示这些文件内容

### 2. 定期检查

```bash
# 检查 Git 状态
git status

# 确保敏感文件未被追踪
git ls-files | grep -E '(cookies|token_)'
# 如果有输出，立即执行：
git rm --cached <文件名>
```

### 3. 如果不小心提交了

```bash
# 立即从 Git 历史中删除
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch cookies.json token_*.txt" \
  --prune-empty --tag-name-filter cat -- --all

# 强制推送
git push origin --force --all
git push origin --force --tags
```

## 🛡️ 最佳实践

### 1. 使用环境变量

如果需要在脚本中使用凭据：

```python
import os
email = os.getenv('MINERU_EMAIL')
password = os.getenv('MINERU_PASSWORD')
```

### 2. 加密存储

对于生产环境，考虑加密存储：

```bash
# 使用 GPG 加密
gpg -c cookies.json
# 生成 cookies.json.gpg

# 解密使用
gpg -d cookies.json.gpg > cookies.json
```

### 3. 定期轮换

- 每 14 天自动过期
- 建议每 13 天主动更新
- 不要长期使用同一个 Token

## 📋 安全检查清单

在推送到 Git 之前，请确认：

- [ ] cookies.json 不在 Git 中
- [ ] token_*.txt 不在 Git 中
- [ ] *.log 不在 Git 中
- [ ] .gitignore 已正确配置
- [ ] 文档中没有真实的 Token 值
- [ ] 代码中没有硬编码的凭据

## 🚨 如果泄露了怎么办

1. **立即删除泄露的 Token**
   ```bash
   # 在 MinerU 网站上删除
   # 或使用 API 删除
   ```

2. **重新登录获取新的 Cookie**
   ```bash
   python3 login_complete.py
   ```

3. **创建新的 Token**
   ```bash
   python3 renew_token.py
   ```

4. **检查 Git 历史**
   ```bash
   git log --all --full-history -- cookies.json
   ```

---

**⚠️ 记住：安全第一！永远不要将敏感信息提交到版本控制系统！**
