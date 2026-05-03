"""Lead scoring rules tuned for Westside LA real estate.

Kept as pure Python (not LLM-judged) because:
  * Deterministic — same input always yields the same score
  * Cheap — no API calls in the hot path
  * Tunable — agency owner can adjust thresholds without re-prompting Claude
  * Testable — unit tests cover every rule path
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ScoreLabel = Literal["HOT", "WARM", "COLD"]


@dataclass(frozen=True)
class LeadFacts:
    """Minimal set of facts the scoring rubric needs."""

    intent: str  # "buy" | "rent"
    budget_max: int  # USD total for "buy", USD/month for "rent"
    timeline_months: int
    financing: str | None  # cash | conventional | jumbo | foreign_national | rental | None


def score_lead(
    facts: LeadFacts,
    *,
    hot_threshold: int = 80,
    warm_threshold: int = 50,
) -> tuple[ScoreLabel, int]:
    """Return ``(label, raw_score)`` where label is HOT / WARM / COLD."""
    if facts.intent == "buy":
        score = _score_buy(facts)
    elif facts.intent == "rent":
        score = _score_rent(facts)
    else:
        score = 0

    if score >= hot_threshold:
        return "HOT", score
    if score >= warm_threshold:
        return "WARM", score
    return "COLD", score


def _score_buy(facts: LeadFacts) -> int:
    score = 0
    # Budget tiers (USD purchase price)
    if facts.budget_max >= 1_500_000:
        score += 40
    elif facts.budget_max >= 800_000:
        score += 25
    elif facts.budget_max > 0:
        score += 10
    # Financing — cash and foreign-national are Casa Verde's premium segment
    if facts.financing == "cash":
        score += 30
    elif facts.financing in ("jumbo", "foreign_national"):
        score += 25
    elif facts.financing == "conventional":
        score += 15
    # Timeline — sooner = hotter; "browsing 6+ months out" is still a real lead
    if facts.timeline_months <= 2:
        score += 30
    elif facts.timeline_months <= 6:
        score += 20
    elif facts.timeline_months > 0:
        score += 10
    return score


def _score_rent(facts: LeadFacts) -> int:
    score = 0
    # Budget tiers (USD/month)
    if facts.budget_max >= 5_000:
        score += 40
    elif facts.budget_max >= 3_000:
        score += 25
    elif facts.budget_max > 0:
        score += 10
    # Timeline — rentals close fast
    if facts.timeline_months <= 1:
        score += 35
    elif facts.timeline_months <= 3:
        score += 20
    else:
        score += 5
    # Rentals are inherently shorter cycle than purchases — small constant lift
    score += 20
    return score
