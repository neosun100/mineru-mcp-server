"""Token 生命周期管理。

负责：
  - 加载 all_tokens.json
  - 解析 expired_at 字段判断 Token 是否过期 / 即将过期
  - 调度 batch_login.py 自动续期（headless）
  - 在多账号间做加权负载均衡，避免单账号配额耗尽
  - 提供运行时反馈（"哪个账号配额满了" / "哪个 Token 快过期"）

向后兼容：
  - 不破坏 mineru_async.py 现有 _get_random_token() 接口
  - 旧调用方仍可直接 random.choice，新调用方用 TokenManager 拿到更智能的选择
"""
from __future__ import annotations

import datetime as _dt
import json
import logging
import random
import subprocess
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ───────────────────────────────────────────────────────────────────
# 数据结构
# ───────────────────────────────────────────────────────────────────


@dataclass
class TokenEntry:
    """单个账号的 Token 信息（来自 all_tokens.json 的一条）。"""

    email: str
    name: str
    token: str
    token_name: str
    expired_at: str  # ISO 格式 like "2026-02-07T17:33:52Z"

    # 运行时统计（不持久化）
    usage_count: int = 0       # 本次进程中被使用次数
    last_error: Optional[str] = None  # 上次失败的错误码
    quota_exhausted: bool = False     # 是否已知配额耗尽（today）

    @property
    def expires_at_dt(self) -> _dt.datetime:
        """expired_at 解析为 UTC datetime。"""
        s = self.expired_at.replace("Z", "+00:00")
        return _dt.datetime.fromisoformat(s)

    @property
    def days_until_expiry(self) -> int:
        """剩余有效天数（向下取整）。负值表示已过期。"""
        now = _dt.datetime.now(_dt.timezone.utc)
        delta = self.expires_at_dt - now
        return delta.days

    @property
    def is_expired(self) -> bool:
        return self.days_until_expiry < 0

    @property
    def is_expiring_soon(self, threshold_days: int = 3) -> bool:
        return 0 <= self.days_until_expiry <= threshold_days

    @property
    def status_label(self) -> str:
        """供 UI 展示的状态标签。"""
        d = self.days_until_expiry
        if d < 0:
            return "❌ 已过期"
        if d <= 1:
            return f"⚠️ {d} 天（紧急）"
        if d <= 7:
            return f"⚠️ {d} 天"
        return f"✅ {d} 天"


# ───────────────────────────────────────────────────────────────────
# TokenManager
# ───────────────────────────────────────────────────────────────────


class TokenManager:
    """全局 Token 管理器。

    线程安全；同一进程多次实例化会共享底层 _tokens 列表。
    """

    _instance: Optional["TokenManager"] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, tokens_file: str | Path | None = None):
        if self._initialized:  # pragma: no cover - 单例
            return

        # tokens_file 默认在项目根目录（src 的上一级）
        if tokens_file is None:
            tokens_file = Path(__file__).resolve().parent.parent / "all_tokens.json"
        self.tokens_file = Path(tokens_file)
        self._tokens: List[TokenEntry] = []
        self._load()
        self._initialized = True

    # ────────────────────────────────────────────────────────────
    # 加载 / 保存
    # ────────────────────────────────────────────────────────────

    def _load(self) -> None:
        """从磁盘重新加载 Token。"""
        if not self.tokens_file.exists():
            logger.warning(f"Token 文件不存在: {self.tokens_file}")
            self._tokens = []
            return

        try:
            raw: Dict[str, Dict] = json.loads(self.tokens_file.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error(f"解析 {self.tokens_file} 失败: {e}")
            self._tokens = []
            return

        new_tokens: List[TokenEntry] = []
        for email, info in raw.items():
            try:
                new_tokens.append(TokenEntry(
                    email=email,
                    name=info.get("name", email),
                    token=info["token"],
                    token_name=info.get("token_name", ""),
                    expired_at=info.get("expired_at", ""),
                ))
            except KeyError as e:
                logger.warning(f"账号 {email} 缺字段 {e}，跳过")
        self._tokens = new_tokens
        logger.info(f"已加载 {len(self._tokens)} 个 Token")

    def reload(self) -> None:
        """对外暴露的重新加载接口（续期后调用）。"""
        with self._lock:
            self._load()

    # ────────────────────────────────────────────────────────────
    # 查询
    # ────────────────────────────────────────────────────────────

    def all_tokens(self) -> List[TokenEntry]:
        return list(self._tokens)

    def valid_tokens(self) -> List[TokenEntry]:
        """未过期、未标记配额耗尽的 Token。"""
        return [t for t in self._tokens if not t.is_expired and not t.quota_exhausted]

    def has_expired(self) -> bool:
        return any(t.is_expired for t in self._tokens)

    def has_expiring_soon(self, threshold_days: int = 3) -> bool:
        return any(0 <= t.days_until_expiry <= threshold_days for t in self._tokens)

    def status_report(self) -> List[Dict]:
        """供 MCP 工具返回的状态列表。"""
        return [
            {
                "email": t.email,
                "name": t.name,
                "token_name": t.token_name,
                "expired_at": t.expired_at,
                "days_remaining": t.days_until_expiry,
                "status": t.status_label,
                "usage_count": t.usage_count,
                "quota_exhausted": t.quota_exhausted,
            }
            for t in self._tokens
        ]

    # ────────────────────────────────────────────────────────────
    # 选择策略
    # ────────────────────────────────────────────────────────────

    def pick(self, strategy: str = "least_used") -> Optional[TokenEntry]:
        """选一个可用的 Token。

        strategy:
          - 'random'      随机
          - 'least_used'  本次进程中使用次数最少（默认）
          - 'longest_lived' 剩余有效期最长
        """
        candidates = self.valid_tokens()
        if not candidates:
            return None

        if strategy == "random":
            chosen = random.choice(candidates)
        elif strategy == "longest_lived":
            chosen = max(candidates, key=lambda t: t.days_until_expiry)
        else:  # least_used
            chosen = min(candidates, key=lambda t: t.usage_count)

        chosen.usage_count += 1
        return chosen

    def mark_quota_exhausted(self, token: str) -> None:
        """标记指定 Token 的账号已配额耗尽（当 -60018 / -60019 出现时）。"""
        for t in self._tokens:
            if t.token == token:
                t.quota_exhausted = True
                logger.warning(f"账号 {t.email} 已标记配额耗尽")
                return

    def mark_error(self, token: str, code: str) -> None:
        for t in self._tokens:
            if t.token == token:
                t.last_error = code
                return

    # ────────────────────────────────────────────────────────────
    # 自动续期
    # ────────────────────────────────────────────────────────────

    def renew_all(self, headless: bool = True, timeout: int = 600) -> Tuple[bool, str]:
        """触发批量登录续期。

        成功后会自动 reload 内存中的 token 列表。
        返回 (是否成功, 摘要)。
        """
        project_root = self.tokens_file.parent
        venv_python = project_root / ".venv" / "bin" / "python3"
        login_script = project_root / "src" / "batch_login.py"

        if not login_script.exists():
            return False, f"找不到 {login_script}"

        python_bin = str(venv_python) if venv_python.exists() else sys.executable
        cmd = [python_bin, str(login_script)]
        if not headless:
            cmd.append("--headed")

        logger.info(f"启动续期：{' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd,
                cwd=str(project_root),
                timeout=timeout,
                capture_output=True,
                text=True,
            )
        except subprocess.TimeoutExpired:
            return False, f"续期超时（>{timeout}s）"
        except Exception as e:
            return False, f"续期异常：{e}"

        success = result.returncode == 0
        # 不论成功失败都尝试 reload，因为可能续期了一部分
        self.reload()
        summary = (
            f"返回码 {result.returncode}\n"
            f"--- stdout (尾) ---\n{result.stdout[-2000:] if result.stdout else ''}\n"
            f"--- stderr (尾) ---\n{result.stderr[-2000:] if result.stderr else ''}"
        )
        return success, summary

    def renew_if_needed(self, threshold_days: int = 1) -> Tuple[bool, str]:
        """有任意 Token 过期 / 即将过期时触发续期，否则跳过。"""
        if not (self.has_expired() or self.has_expiring_soon(threshold_days)):
            return True, "全部 Token 有效，无需续期"
        logger.info("检测到 Token 过期或即将过期，自动触发续期…")
        return self.renew_all()


# ───────────────────────────────────────────────────────────────────
# 兼容旧接口
# ───────────────────────────────────────────────────────────────────


def get_default_manager() -> TokenManager:
    return TokenManager()
