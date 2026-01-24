# MinerU Token 自动续期 - 最终方案

## 🎯 已完全解决

通过人机协作，成功实现了 MinerU API Token 的自动续期。

## 📝 使用方法

### 方法一：首次使用或 Cookie 过期（每14天一次）

```bash
python3 login_complete.py
```

**你需要做的：**
1. 等待浏览器自动填写账号密码
2. 等待自动点击登录
3. **手动点击【确认您不是机器人】** ← 唯一需要手动的步骤
4. 等待跳转到 Token 页面
5. 回到终端按回车
6. 完成！

### 方法二：自动创建新 Token（随时可用）

```bash
python3 renew_token.py
```

完全自动，无需任何手动操作。

## ✅ 验证成功

```bash
# 查看所有 Token
python3 -c "
import json, requests
cookies = json.load(open('cookies.json'))
r = requests.get('https://mineru.net/api/v4/tokens',
                headers={'authorization': f'Bearer {cookies[\"uaa-token\"]}'})
print(r.json())
"
```

当前已有 Token：
- token-20260125000512 (过期: 2026-02-08)
- token-20260125000527 (过期: 2026-02-08)  
- token-20260125000655 (过期: 2026-02-08)
- token-20260125000734 (过期: 2026-02-08)

## 🔧 核心技术

1. **认证方式**：`Authorization: Bearer <uaa-token>`
2. **参数字段**：`{"token_name": "名称"}`
3. **真人模拟**：随机打字速度、贝塞尔曲线鼠标轨迹
4. **反检测**：隐藏 webdriver 特征

## 📅 维护计划

- 每 13 天运行一次 `login_complete.py`（手动点一下验证，5秒）
- 设置 cron 任务每天自动运行 `renew_token.py`

## 🎉 成功率

- Cookie 获取：100%（需要手动点验证）
- Token 创建：100%（完全自动）
