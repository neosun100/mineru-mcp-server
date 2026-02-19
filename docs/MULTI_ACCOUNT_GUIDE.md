# 多账号使用指南

## 🔒 安全说明

**重要**：账号密码不再硬编码在代码中，而是保存在配置文件中。

## 📝 配置步骤

### 1. 创建配置文件

```bash
cp accounts.yaml.example accounts.yaml
```

### 2. 编辑配置文件

```bash
vi accounts.yaml
```

填入你的账号信息：

```yaml
accounts:
  - name: "主账号"
    email: "your_email@example.com"
    password: "your_password"
    
  - name: "备用账号"
    email: "another@example.com"
    password: "another_password"
```

### 3. 设置文件权限

```bash
chmod 600 accounts.yaml
```

## 🚀 使用方式

### 单账号

如果只有一个账号，直接运行：

```bash
python3 login_complete.py
```

### 多账号

如果有多个账号，运行时会提示选择：

```bash
python3 login_complete.py

请选择账号:
  1. 主账号 (user1@example.com)
  2. 备用账号 (another@example.com)

输入序号: 1
```

## 📁 文件管理

### 每个账号的文件

- `cookies.json` - 当前使用账号的 Cookie
- `token_*.txt` - 创建的 Token

### 多账号管理建议

为每个账号创建独立目录：

```bash
mkdir -p accounts/account1 accounts/account2

# 账号1
cd accounts/account1
cp ../../accounts.yaml .
python3 ../../login_complete.py

# 账号2
cd accounts/account2
cp ../../accounts.yaml .
python3 ../../login_complete.py
```

## 🔒 安全检查

```bash
# 确保配置文件不会被提交
git status | grep accounts.yaml
# 应该没有输出

# 检查文件权限
ls -l accounts.yaml
# 应该是 -rw------- (600)
```

## ⚠️ 注意事项

1. **不要提交 accounts.yaml 到 Git**
2. **设置文件权限为 600**
3. **定期更换密码**
4. **不要分享配置文件**

---

**✅ 现在账号密码安全了！**
