# API v4 完整参数参考

> v4.0.0 全面升级后，MCP 工具支持的所有官方参数。
> 与 [MinerU 官方文档](https://mineru.net/apiManage/docs) 保持一致。

## 1. `process_document` — 精准 API 单文件处理

### 输入参数（11 个）

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `file_path` | string | **必填** | 本地路径或 URL |
| `model_version` | string | `vlm` | 模型：`pipeline` / `vlm` / `MinerU-HTML` |
| `enable_formula` | bool | `true` | 公式识别（仅 pipeline / vlm） |
| `enable_table` | bool | `true` | 表格识别（仅 pipeline / vlm） |
| `is_ocr` | bool | `false` | OCR；图片自动开启 |
| `language` | string | `ch` | 文档语言（见下方语言取值表） |
| `page_ranges` | string | — | 页码范围，例 `"1-50"` 或 `"2,4-6,10-20"` |
| `extra_formats` | array | — | 额外导出格式：`["docx", "html", "latex"]` |
| `data_id` | string | — | 业务标识（≤128 字符） |
| `no_cache` | bool | `false` | 跳过 URL 缓存（仅 URL 模式） |
| `output_dir` | string | 文件同目录 | 输出目录 |

### 限制
- 文件大小 ≤ 200 MB
- 文件页数 ≤ 200 页（超页会自动 `auto_split` 拆 180 页/片处理后合并）

### 自动行为
- URL 输入：**优先服务端直传**（不下载），失败兜底走下载-上传
- 图片格式（png/jpg/jpeg）：自动开 OCR
- HTML 格式：自动切 `MinerU-HTML` 模型
- Office（doc/docx/ppt/pptx/xls/xlsx）：自动切 `pipeline` 模型（VLM 对 Office 易卡 pending）

---

## 2. `process_directory` — 精准 API 批量处理

### 输入参数（10 个）

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `directory` | string | **必填** | 目录路径 |
| `file_pattern` | string | `*.pdf` | glob 过滤 |
| `recursive` | bool | `false` | （暂未实现） |
| `max_workers` | number | 3 | 并发上限 |
| `model_version` / `enable_formula` / `enable_table` / `is_ocr` / `language` / `extra_formats` | — | — | 同 `process_document` |

### 自动行为
- 入口扫描所有文件，对超页超大 PDF 自动 `auto_split`
- 处理完成后自动合并 chunks → 完整 .md + 统一图片目录

---

## 3. `process_document_lite` — Agent 轻量 API

### 输入参数（6 个）

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `file_path` | string | **必填** | 本地路径或 URL |
| `language` | string | `ch` | 文档语言 |
| `page_range` | string | — | 仅支持 `"1-10"` 或 `"5"`（**不支持逗号** ） |
| `enable_table` / `is_ocr` / `enable_formula` | bool | true/false/true | 同上，仅 PDF 生效 |

### 限制
- 文件大小 ≤ 10 MB
- 页数 ≤ 20 页
- 不支持 HTML
- 文件类型：PDF / 图片 / Doc(x) / PPT(x) / Excel
- IP 限频（每 IP 每分钟有上限）

### 适用场景
- 小文档（票据 / 单页扫描 / 短论文）
- 主账号每日 1000 页配额耗尽时的兜底
- AI Agent 工作流（无登录态）

---

## 4. `query_task_status` — 异步查询任务

### 输入参数（2 个）

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `task_id` | string | **必填** | 任务 ID |
| `lite` | bool | `false` | 是否查询 Agent 轻量 API 任务 |

### 返回
精准 API：`{state, full_zip_url, err_msg, extract_progress: {extracted_pages, total_pages, start_time}}`
轻量 API：`{state, markdown_url, err_msg, err_code}`

---

## 5. `renew_tokens` — 触发 Token 续期

### 输入参数（2 个）

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `force` | bool | `false` | 强制全部续期；否则仅过期或 ≤3 天才续 |
| `headless` | bool | `true` | 无 UI 模式 |

### 行为
- 调用 `src/batch_login.py`，自动登录所有账号刷新 Token
- 完成后内存中 TokenManager 自动 `reload()`

---

## 6. `get_token_status` — Token 状态报告

### 返回结构

```json
{
  "total": 6,
  "expired": 0,
  "expiring_soon": 6,
  "needs_renewal": true,
  "tokens": [
    {
      "email": "...",
      "name": "...",
      "token_name": "token-20260213...",
      "expired_at": "2026-05-19T...",
      "days_remaining": 3,
      "status": "⚠️ 3 天",
      "usage_count": 12,
      "quota_exhausted": false
    }
  ]
}
```

---

## 错误处理

所有工具失败时返回 `{"status": "failed", "error_code": "...", "error_message": "..."}`，
其中 `error_code` 与官方一致。常见错误码：

| 错误码 | 类别 | 说明 | 处理建议 |
|---|---|---|---|
| `A0211` | AUTH | Token 过期 | 自动续期（已集成） |
| `-60005` | PERMANENT | 文件 > 200MB | 用 `split_large_pdf` 拆分 |
| `-60006` | PERMANENT | 页数 > 200 | 用 `auto_split.prepare_files()` 拆分 |
| `-60018` | QUOTA | 当日配额耗尽 | 明日再试 / 切轻量 API |
| `-10001` / `-60007` / `-60009` | RETRYABLE | 服务瞬时异常 | 已自动重试 1-3 次 |
| `-30001` | PERMANENT | 轻量 API 超 10MB | 改用 `process_document` |
| `-30003` | PERMANENT | 轻量 API 超 20 页 | 改用 `process_document` |

完整错误码表见 `src/api_errors.py`。

---

## Language 参数取值

### 单语言包

| 值 | 包含语言 | 备注 |
|---|---|---|
| `ch` | 中 / 英 / 繁中 | **默认** |
| `ch_server` | 中 / 英 / 繁中 / 日 | 繁体 / 手写为主 |
| `en` | 英 | 纯英 |
| `japan` | 中 / 英 / 繁中 / 日 | 日文为主 |
| `korean` | 韩 / 英 | 韩文 |
| `chinese_cht` | 中 / 英 / 繁中 / 日 | 繁中为主 |
| `ta` / `te` / `ka` / `el` / `th` | — | 泰米尔 / 泰卢固 / 卡纳达 / 希腊 / 泰 |

### 语言族包

| 值 | 主要语种 |
|---|---|
| `latin` | 法 / 德 / 西 / 葡 / 意 / 荷 / 瑞典等 40+ 拉丁语种 |
| `arabic` | 阿拉伯 / 波斯 / 维吾尔 / 乌尔都 / 普什图 / 库尔德 / 信德等 |
| `cyrillic` | 俄 / 白俄 / 乌克兰 / 蒙 / 哈 / 塔等 30+ 西里尔语种 |
| `east_slavic` | 俄 / 白俄 / 乌 |
| `devanagari` | 印地 / 马拉地 / 尼泊尔 / 梵 / 哈里亚纳等 |

完整列表见 [官方文档](https://mineru.net/apiManage/docs#language-取值参考)。
