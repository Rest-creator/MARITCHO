"""Guardrail against drift between the two hand-maintained skill/keyword
taxonomies: backend `shared_kernel.embeddings._CONCEPT_CLUSTERS` (used for
semantic job search/matching) and frontend `core/format/trades.ts`
`SKILL_GROUPS` (used for the worker skill picker and client-side search).

There is no single shared source of truth for these two lists (see
SOFTWARE-ENGINEER/Integrations_and_Auth dev-log and the WEB-012/CORE-008
PR review that raised this), so this test is the mechanism that catches
drift: every frontend keyword for a trade must be recognized by that
trade's backend concept cluster(s), or search/matching will silently
disagree between the worker skill picker and the backend matcher.
"""

from __future__ import annotations

import re
from pathlib import Path

from app.shared_kernel.embeddings import _CONCEPT_CLUSTERS, _TRADE_TO_CLUSTER
from app.shared_kernel.enums import TradeEnum

FRONTEND_TRADES_FILE = (
    Path(__file__).resolve().parents[2]
    / "frontend"
    / "src"
    / "core"
    / "format"
    / "trades.ts"
)

_SKILL_BLOCK_RE = re.compile(
    r'trade:\s*"(?P<trade>[A-Z_]+)".*?keywords:\s*\[(?P<keywords>[^\]]*)\]',
    re.DOTALL,
)
_KEYWORD_RE = re.compile(r'"([^"]+)"')


def _frontend_keywords_by_trade() -> dict[str, set[str]]:
    text = FRONTEND_TRADES_FILE.read_text(encoding="utf-8")
    by_trade: dict[str, set[str]] = {}
    for match in _SKILL_BLOCK_RE.finditer(text):
        trade = match.group("trade")
        keywords = {kw.lower() for kw in _KEYWORD_RE.findall(match.group("keywords"))}
        by_trade.setdefault(trade, set()).update(keywords)
    return by_trade


def _backend_keywords_for_trade(trade: TradeEnum) -> set[str]:
    cluster_ids = _TRADE_TO_CLUSTER.get(trade, ())
    keywords: set[str] = set()
    for cluster_id in cluster_ids:
        keywords.update(kw.lower() for kw in _CONCEPT_CLUSTERS[cluster_id])
    return keywords


def test_frontend_skill_file_exists() -> None:
    assert FRONTEND_TRADES_FILE.is_file(), (
        f"Expected frontend taxonomy at {FRONTEND_TRADES_FILE}; "
        "update this test's path if trades.ts moved."
    )


def test_frontend_keywords_recognized_by_backend_clusters() -> None:
    """Every frontend skill keyword for a backend-mapped trade must appear in
    that trade's backend concept cluster(s), or a worker who types/searches
    it will match on the frontend but not the backend (or vice versa).
    """
    frontend_by_trade = _frontend_keywords_by_trade()
    assert frontend_by_trade, "Failed to parse any skills out of trades.ts"

    missing: dict[str, set[str]] = {}
    for trade_name, frontend_keywords in frontend_by_trade.items():
        try:
            trade = TradeEnum(trade_name)
        except ValueError:
            continue  # not a backend trade (e.g. future-only skill group)
        backend_keywords = _backend_keywords_for_trade(trade)
        unmatched = {
            kw
            for kw in frontend_keywords
            if kw not in backend_keywords
            and not any(kw in bkw or bkw in kw for bkw in backend_keywords)
        }
        if unmatched:
            missing[trade_name] = unmatched

    assert not missing, (
        "Frontend skill keywords with no match in the backend's concept "
        "clusters for the same trade (add them to _CONCEPT_CLUSTERS in "
        f"app/shared_kernel/embeddings.py): {missing}"
    )
