# 📁 项目结构

## 最终文件列表

```
MinerU-Token/
├── 📜 核心脚本（3个）
│   ├── login_complete.py      ⭐ 人机协作登录
│   ├── renew_token.py          ⭐ 自动续期
│   └── check_status.py         ⭐ 状态检查
│
├── 📚 完整文档（7个）
│   ├── README.md               主文档
│   ├── README_GITHUB.md        GitHub 风格
│   ├── DOCUMENTATION.md        详细手册
│   ├── FINAL_GUIDE.md          快速指南
│   ├── QUICK_REFERENCE.md      快速参考
│   ├── PROJECT_SUMMARY.md      项目总结
│   └── PROJECT_DELIVERY.md     交付清单
│
├── ⚙️ 配置文件（2个）
│   ├── requirements.txt        依赖清单
│   └── .gitignore              Git 忽略
│
├── 🔒 运行时文件（不提交）
│   ├── cookies.json            Cookie 存储
│   ├── token_*.txt             Token 记录
│   └── *.log                   运行日志
│
└── 📦 归档目录
    └── archive/                测试和开发文件
```

## 文件说明

### 核心脚本

#### 1. login_complete.py
**用途**：人机协作登录  
**使用频率**：每 14 天一次  
**功能**：
- 自动填写账号密码
- 等待手动验证
- 自动提取 Cookie
- 自动创建 Token

#### 2. renew_token.py
**用途**：自动续期  
**使用频率**：随时可用  
**功能**：
- 检查 Cookie 有效期
- 自动创建新 Token
- 保存到文件

#### 3. check_status.py
**用途**：状态检查  
**使用频率**：随时可用  
**功能**：
- 查看所有 Token
- 显示过期时间

### 文档文件

| 文档 | 用途 | 适用场景 |
|------|------|---------|
| `README.md` | 项目主文档 | 首次了解项目 |
| `README_GITHUB.md` | GitHub 风格 | 开源发布 |
| `DOCUMENTATION.md` | 详细手册 | 深入学习 |
| `FINAL_GUIDE.md` | 快速指南 | 快速上手 |
| `QUICK_REFERENCE.md` | 快速参考 | 日常查阅 |
| `PROJECT_SUMMARY.md` | 项目总结 | 了解背景 |
| `PROJECT_DELIVERY.md` | 交付清单 | 项目验收 |

## Git 版本

- **v1.0.0** - 首个稳定版本
- **v1.0.1** - 文档完善版
- **v1.0.2** - 生产就绪版本（当前）

## 使用建议

### 日常使用

只需要关注这 3 个文件：
- `login_complete.py`
- `renew_token.py`
- `check_status.py`

### 文档查阅

- 快速查阅：`QUICK_REFERENCE.md`
- 详细学习：`DOCUMENTATION.md`
- GitHub 展示：`README_GITHUB.md`

---

**💡 提示**：archive/ 目录包含开发过程中的测试文件，可以安全删除。
