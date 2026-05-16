"""TokenManager 集成测试 — 用临时 token 文件，不调真实续期。"""
import json
from datetime import datetime, timedelta, timezone

import pytest

import token_manager as TM


pytestmark = pytest.mark.integration


def _make_tokens_file(tmp_path, entries):
    """根据 [(email, days_remaining), ...] 生成一个 all_tokens.json。"""
    data = {}
    now = datetime.now(timezone.utc)
    for i, (email, days) in enumerate(entries):
        exp = now + timedelta(days=days)
        data[email] = {
            "name": f"账号{i+1}",
            "token": f"fake-token-{i+1}",
            "token_name": f"token-{exp.strftime('%Y%m%d%H%M%S')}",
            "expired_at": exp.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    p = tmp_path / "all_tokens.json"
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return p


@pytest.fixture
def fresh_manager(tmp_path):
    """每个测试用一个干净的 TokenManager 实例（避开单例污染）。"""
    # 单例重置
    TM.TokenManager._instance = None

    def _build(entries):
        f = _make_tokens_file(tmp_path, entries)
        return TM.TokenManager(tokens_file=f)

    yield _build

    TM.TokenManager._instance = None


def test_load_basic(fresh_manager):
    mgr = fresh_manager([("a@x.com", 30), ("b@x.com", 60)])
    tokens = mgr.all_tokens()
    assert len(tokens) == 2
    assert tokens[0].email == "a@x.com"
    # timedelta 向下取整可能少 1，允许一定误差
    assert tokens[0].days_until_expiry in (29, 30)
    assert not tokens[0].is_expired


def test_classify_expired(fresh_manager):
    mgr = fresh_manager([
        ("expired@x.com", -5),
        ("ok@x.com", 30),
        ("urgent@x.com", 1),
    ])
    assert mgr.has_expired() is True
    assert mgr.has_expiring_soon() is True
    assert len(mgr.valid_tokens()) == 2  # expired 排除


def test_status_report_fields(fresh_manager):
    mgr = fresh_manager([("a@x.com", 30)])
    report = mgr.status_report()
    assert len(report) == 1
    r = report[0]
    assert set(r.keys()) >= {"email", "name", "token_name", "expired_at",
                              "days_remaining", "status", "usage_count",
                              "quota_exhausted"}
    assert r["days_remaining"] in (29, 30)
    assert "✅" in r["status"]


def test_pick_least_used(fresh_manager):
    mgr = fresh_manager([("a@x.com", 30), ("b@x.com", 30), ("c@x.com", 30)])
    # 第一次 pick 任何一个
    first = mgr.pick(strategy="least_used")
    assert first is not None
    # 多次 pick 应该轮转，最终大致均匀
    for _ in range(5):
        mgr.pick(strategy="least_used")
    counts = [t.usage_count for t in mgr.all_tokens()]
    # 6 次 pick 在 3 个账号间，最大值不应超过最小值 + 2
    assert max(counts) - min(counts) <= 2


def test_pick_returns_none_when_all_expired(fresh_manager):
    mgr = fresh_manager([("a@x.com", -5)])
    assert mgr.pick() is None


def test_mark_quota_exhausted(fresh_manager):
    mgr = fresh_manager([("a@x.com", 30), ("b@x.com", 30)])
    a_token = mgr.all_tokens()[0].token
    mgr.mark_quota_exhausted(a_token)
    assert mgr.all_tokens()[0].quota_exhausted is True
    valid = mgr.valid_tokens()
    assert len(valid) == 1
    assert valid[0].email == "b@x.com"


def test_pick_skips_quota_exhausted(fresh_manager):
    mgr = fresh_manager([("a@x.com", 30), ("b@x.com", 30)])
    mgr.mark_quota_exhausted(mgr.all_tokens()[0].token)
    for _ in range(3):
        chosen = mgr.pick()
        assert chosen.email == "b@x.com"


def test_renew_if_needed_no_op_when_all_valid(fresh_manager):
    mgr = fresh_manager([("a@x.com", 30)])
    ok, msg = mgr.renew_if_needed(threshold_days=3)
    assert ok is True
    assert "无需" in msg or "valid" in msg.lower() or "全部" in msg


def test_status_label_categories(fresh_manager):
    mgr = fresh_manager([
        ("expired@x.com", -1),
        ("urgent@x.com", 1),
        ("warn@x.com", 5),
        ("ok@x.com", 60),
    ])
    labels = {t.email: t.status_label for t in mgr.all_tokens()}
    assert "❌" in labels["expired@x.com"]
    assert "⚠️" in labels["urgent@x.com"]
    assert "⚠️" in labels["warn@x.com"]
    assert "✅" in labels["ok@x.com"]
