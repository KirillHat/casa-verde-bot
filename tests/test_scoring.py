"""Tests for the lead-scoring rubric."""

from __future__ import annotations

import pytest

from app.services.scoring import LeadFacts, score_lead


class TestBuyScoring:
    def test_hot_buy_high_budget_cash_urgent(self) -> None:
        facts = LeadFacts(intent="buy", budget_max=2_500_000, timeline_months=2, financing="cash")
        label, value = score_lead(facts)
        assert label == "HOT"
        assert value >= 80

    def test_hot_buy_foreign_national(self) -> None:
        facts = LeadFacts(
            intent="buy", budget_max=1_500_000, timeline_months=2, financing="foreign_national"
        )
        label, _ = score_lead(facts)
        assert label == "HOT"

    def test_warm_buy_mid_budget_conventional(self) -> None:
        facts = LeadFacts(
            intent="buy", budget_max=900_000, timeline_months=4, financing="conventional"
        )
        label, _ = score_lead(facts)
        assert label == "WARM"

    def test_cold_buy_low_budget_no_financing(self) -> None:
        facts = LeadFacts(intent="buy", budget_max=400_000, timeline_months=24, financing=None)
        label, _ = score_lead(facts)
        assert label == "COLD"

    def test_cold_buy_no_budget(self) -> None:
        facts = LeadFacts(intent="buy", budget_max=0, timeline_months=12, financing=None)
        label, _ = score_lead(facts)
        assert label == "COLD"

    def test_foreign_national_premium_beats_conventional(self) -> None:
        a = LeadFacts(
            intent="buy", budget_max=1_500_000, timeline_months=3, financing="conventional"
        )
        b = LeadFacts(
            intent="buy", budget_max=1_500_000, timeline_months=3, financing="foreign_national"
        )
        _, va = score_lead(a)
        _, vb = score_lead(b)
        assert vb > va, "foreign_national should outscore conventional at the same budget/timeline"


class TestRentScoring:
    def test_hot_rent_premium_urgent(self) -> None:
        facts = LeadFacts(intent="rent", budget_max=6_000, timeline_months=1, financing="rental")
        label, _ = score_lead(facts)
        assert label == "HOT"

    def test_warm_rent_mid_short(self) -> None:
        facts = LeadFacts(intent="rent", budget_max=3_500, timeline_months=2, financing="rental")
        label, _ = score_lead(facts)
        assert label == "WARM"

    def test_cold_rent_low_budget_far_out(self) -> None:
        facts = LeadFacts(intent="rent", budget_max=1_500, timeline_months=6, financing="rental")
        label, _ = score_lead(facts)
        assert label == "COLD"

    def test_rent_inherent_lift(self) -> None:
        """Rentals get a +20 lift over equivalent buys (shorter sales cycle)."""
        rent = LeadFacts(intent="rent", budget_max=3_000, timeline_months=2, financing="rental")
        _, rent_value = score_lead(rent)
        # Same dollar amount as a "buy" intent yields essentially nothing
        buy = LeadFacts(intent="buy", budget_max=3_000, timeline_months=2, financing=None)
        _, buy_value = score_lead(buy)
        assert rent_value > buy_value


class TestThresholds:
    def test_threshold_overrides(self) -> None:
        facts = LeadFacts(intent="rent", budget_max=2_000, timeline_months=6, financing="rental")
        # Bump the bar so high that only an exceptional lead would qualify
        label, _ = score_lead(facts, hot_threshold=99, warm_threshold=99)
        assert label == "COLD"

    def test_unknown_intent_is_cold(self) -> None:
        facts = LeadFacts(
            intent="invest", budget_max=1_000_000, timeline_months=1, financing="cash"
        )
        label, value = score_lead(facts)
        assert label == "COLD"
        assert value == 0


@pytest.mark.parametrize(
    "facts,expected",
    [
        # buyer, $5M cash, 1 month → undeniably HOT
        (LeadFacts("buy", 5_000_000, 1, "cash"), "HOT"),
        # buyer, $1M conventional, 12 months → WARM
        (LeadFacts("buy", 1_000_000, 12, "conventional"), "WARM"),
        # renter, $4k, 2 months → WARM
        (LeadFacts("rent", 4_000, 2, "rental"), "WARM"),
        # renter, $5.5k, 1 month → HOT
        (LeadFacts("rent", 5_500, 1, "rental"), "HOT"),
    ],
)
def test_scoring_table(facts: LeadFacts, expected: str) -> None:
    label, _ = score_lead(facts)
    assert label == expected
