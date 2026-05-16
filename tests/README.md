# 测试运行手册

四层测试体系，所有依赖必须通过 **`uv pip install -r requirements-dev.txt`** 安装。

## 测试分类

| 目录 | marker | 性质 | 运行成本 |
|---|---|---|---|
| `tests/unit/` | `unit` | 无依赖、毫秒级、纯算法 | <1s |
| `tests/integration/` | `integration` | 不调真网，用 tmp_path / 临时 token 文件 | <2s |
| `tests/regression/` | `regression` | 防止已修 bug 复发，含真实产物校验 | <2s |
| `tests/e2e/` | `e2e` | 调真实 MinerU 服务，需有效 Token + 网络 | ~30s |

## 默认运行（推荐）

```bash
.venv/bin/python3 -m pytest
# → 跑 unit + integration + regression（共 82），e2e 自动 skip
```

## 跑指定层

```bash
# 只跑某一类
.venv/bin/python3 -m pytest -m unit
.venv/bin/python3 -m pytest -m integration
.venv/bin/python3 -m pytest -m regression
.venv/bin/python3 -m pytest -m e2e            # 默认即生效，自动启用 e2e

# 多个组合
.venv/bin/python3 -m pytest -m "unit or regression"
.venv/bin/python3 -m pytest -m "not e2e"      # 与默认行为等价
```

## 跑 e2e（真调 API）

```bash
# 方式 1：环境变量
RUN_E2E=1 .venv/bin/python3 -m pytest

# 方式 2：marker
.venv/bin/python3 -m pytest -m e2e

# 跑全部含 e2e
RUN_E2E=1 .venv/bin/python3 -m pytest
```

E2E 测试在以下情况会自动 skip：
- `all_tokens.json` 不存在或全部过期
- `~/Downloads/sample_pdfs/PDF-A..pdf` 不存在
- 默认运行（即没设 `RUN_E2E=1` 也没用 `-m e2e`）

## 添加新测试

| 类型 | 放哪 | 模板 |
|---|---|---|
| 纯算法函数 | `tests/unit/test_xxx.py` | `pytestmark = pytest.mark.unit` |
| 多模块联动、用 tmp 资源 | `tests/integration/test_xxx.py` | `pytestmark = pytest.mark.integration` |
| 防 bug 复发 | `tests/regression/test_xxx.py` | `pytestmark = pytest.mark.regression` |
| 真调 API | `tests/e2e/test_xxx.py` | `pytestmark = pytest.mark.e2e` |

测试可用的共享 fixture（来自 `tests/conftest.py`）：

| Fixture | 作用 |
|---|---|
| `project_root` | 项目根目录的 `Path` |
| `sample_pdfs_dir` | `~/Downloads/sample_pdfs/`（不存在时返回 `None`） |
| `make_pdf` | `make_pdf(name, n_pages)` 在 tmp_path 造一个 N 页空白 PDF |

## 当前测试统计

| 分类 | 通过数 | 速度 |
|---|---|---|
| unit | 30 | 0.4s |
| integration | 31 | 0.4s |
| regression | 21 | 0.6s |
| e2e | 2 | ~30s |
| **合计 (RUN_E2E=1)** | **84** | ~30s |

## CI 推荐配置

```yaml
- name: 单元 + 集成 + 回归（必须全过）
  run: .venv/bin/python3 -m pytest

- name: E2E（每日定时跑 / 主分支才跑）
  if: github.ref == 'refs/heads/main' || github.event_name == 'schedule'
  env:
    RUN_E2E: 1
  run: .venv/bin/python3 -m pytest -m e2e
```
