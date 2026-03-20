"""Tests for XP calculation engine."""

from __future__ import annotations

from engine.xp import XpBreakdown, calculate_match_xp, _placement_xp, _bonus_xp


# --- Helpers ---

def _minimal_match(
    players: list[dict] | None = None,
    eliminations: list[dict] | None = None,
    winner: str = "A",
    duration_rounds: int = 10,
    stats: dict | None = None,
    rounds: list[dict] | None = None,
) -> dict:
    """Build a minimal match result dict for testing."""
    if players is None:
        players = [
            {"emoji": "A", "name": "BotA"},
            {"emoji": "B", "name": "BotB"},
            {"emoji": "C", "name": "BotC"},
        ]
    if eliminations is None:
        eliminations = [
            {"emoji": "C", "round": 5, "killed_by": "A", "cause": "combat"},
            {"emoji": "B", "round": 8, "killed_by": "A", "cause": "combat"},
        ]
    if stats is None:
        stats = {
            "A": {"kills": 2, "rounds_survived": 10},
            "B": {"kills": 0, "rounds_survived": 8},
            "C": {"kills": 0, "rounds_survived": 5},
        }
    return {
        "players": players,
        "eliminations": eliminations,
        "winner": winner,
        "duration_rounds": duration_rounds,
        "stats": stats,
        "rounds": rounds or [],
    }


# --- XpBreakdown dataclass ---

class TestXpBreakdown:
    def test_dataclass_fields(self) -> None:
        xp = XpBreakdown(base=10, kills=30, survival=20, placement=50, bonuses=0)
        assert xp.base == 10
        assert xp.kills == 30
        assert xp.survival == 20
        assert xp.placement == 50
        assert xp.bonuses == 0

    def test_total_property(self) -> None:
        xp = XpBreakdown(base=10, kills=30, survival=20, placement=50, bonuses=25)
        assert xp.total == 135


# --- _placement_xp helper ---

class TestPlacementXp:
    def test_first_place(self) -> None:
        assert _placement_xp(1) == 50

    def test_second_place(self) -> None:
        assert _placement_xp(2) == 25

    def test_third_place(self) -> None:
        assert _placement_xp(3) == 15

    def test_fourth_place(self) -> None:
        assert _placement_xp(4) == 0

    def test_large_placement(self) -> None:
        assert _placement_xp(10) == 0


# --- _bonus_xp helper ---

class TestBonusXp:
    def test_first_blood(self) -> None:
        assert _bonus_xp(is_first_blood=True, killed_leader=False) == 20

    def test_leader_bounty(self) -> None:
        assert _bonus_xp(is_first_blood=False, killed_leader=True) == 25

    def test_both_bonuses(self) -> None:
        assert _bonus_xp(is_first_blood=True, killed_leader=True) == 45

    def test_no_bonuses(self) -> None:
        assert _bonus_xp(is_first_blood=False, killed_leader=False) == 0


# --- calculate_match_xp ---

class TestCalculateMatchXp:
    def test_returns_dict_per_bot(self) -> None:
        match = _minimal_match()
        result = calculate_match_xp(match)
        assert set(result.keys()) == {"A", "B", "C"}

    def test_all_values_are_xp_breakdowns(self) -> None:
        match = _minimal_match()
        result = calculate_match_xp(match)
        for v in result.values():
            assert isinstance(v, XpBreakdown)

    def test_base_xp_always_10(self) -> None:
        match = _minimal_match()
        result = calculate_match_xp(match)
        for v in result.values():
            assert v.base == 10

    def test_kill_xp(self) -> None:
        match = _minimal_match()
        result = calculate_match_xp(match)
        assert result["A"].kills == 30  # 2 kills * 15
        assert result["B"].kills == 0
        assert result["C"].kills == 0

    def test_survival_xp(self) -> None:
        match = _minimal_match()
        result = calculate_match_xp(match)
        assert result["A"].survival == 20  # 10 rounds * 2
        assert result["B"].survival == 16  # 8 rounds * 2
        assert result["C"].survival == 10  # 5 rounds * 2

    def test_placement_xp_winner(self) -> None:
        match = _minimal_match()
        result = calculate_match_xp(match)
        assert result["A"].placement == 50  # winner = 1st

    def test_placement_by_elimination_order(self) -> None:
        """Last eliminated = higher placement."""
        match = _minimal_match()
        result = calculate_match_xp(match)
        # B eliminated round 8 (2nd), C eliminated round 5 (3rd)
        assert result["B"].placement == 25
        assert result["C"].placement == 15

    def test_zero_kills(self) -> None:
        match = _minimal_match(
            stats={
                "A": {"kills": 0, "rounds_survived": 10},
                "B": {"kills": 0, "rounds_survived": 5},
                "C": {"kills": 0, "rounds_survived": 3},
            },
            eliminations=[
                {"emoji": "C", "round": 3, "killed_by": "storm", "cause": "storm"},
                {"emoji": "B", "round": 5, "killed_by": "storm", "cause": "storm"},
            ],
        )
        result = calculate_match_xp(match)
        assert result["A"].kills == 0
        assert result["B"].kills == 0

    def test_zero_rounds(self) -> None:
        match = _minimal_match(
            duration_rounds=0,
            stats={
                "A": {"kills": 0, "rounds_survived": 0},
                "B": {"kills": 0, "rounds_survived": 0},
                "C": {"kills": 0, "rounds_survived": 0},
            },
        )
        result = calculate_match_xp(match)
        for v in result.values():
            assert v.survival == 0

    def test_first_blood_bonus(self) -> None:
        """The bot who gets the first kill of the match gets first blood XP."""
        match = _minimal_match(
            eliminations=[
                {"emoji": "C", "round": 5, "killed_by": "B", "cause": "combat"},
                {"emoji": "B", "round": 8, "killed_by": "A", "cause": "combat"},
            ],
            stats={
                "A": {"kills": 1, "rounds_survived": 10},
                "B": {"kills": 1, "rounds_survived": 8},
                "C": {"kills": 0, "rounds_survived": 5},
            },
        )
        result = calculate_match_xp(match)
        # B got first blood (first combat kill at round 5)
        assert result["B"].bonuses >= 20

    def test_storm_kill_not_first_blood(self) -> None:
        """Storm kills don't count as first blood."""
        match = _minimal_match(
            eliminations=[
                {"emoji": "C", "round": 3, "killed_by": "storm", "cause": "storm"},
                {"emoji": "B", "round": 8, "killed_by": "A", "cause": "combat"},
            ],
            stats={
                "A": {"kills": 1, "rounds_survived": 10},
                "B": {"kills": 0, "rounds_survived": 8},
                "C": {"kills": 0, "rounds_survived": 3},
            },
        )
        result = calculate_match_xp(match)
        # A got first blood (first combat kill), not storm
        assert result["A"].bonuses >= 20

    def test_leader_bounty(self) -> None:
        """Killing the momentum leader awards leader bounty XP."""
        match = _minimal_match(
            eliminations=[
                {"emoji": "C", "round": 5, "killed_by": "A", "cause": "combat"},
                {"emoji": "B", "round": 8, "killed_by": "A", "cause": "combat"},
            ],
            stats={
                "A": {"kills": 2, "rounds_survived": 10, "momentum_tier": 3},
                "B": {"kills": 0, "rounds_survived": 8, "momentum_tier": 0},
                "C": {"kills": 0, "rounds_survived": 5, "momentum_tier": 0},
            },
            rounds=[
                {
                    "round": 5,
                    "events": [
                        {"type": "leader_bounty", "killer": "A", "victim": "C", "bonus": 20},
                    ],
                },
            ],
        )
        result = calculate_match_xp(match)
        # A killed leader (has leader_bounty event)
        assert result["A"].bonuses >= 25

    def test_total_xp_sum(self) -> None:
        match = _minimal_match()
        result = calculate_match_xp(match)
        for v in result.values():
            assert v.total == v.base + v.kills + v.survival + v.placement + v.bonuses

    def test_no_winner_match(self) -> None:
        """When winner is 'none', placement is by elimination order only."""
        match = _minimal_match(
            winner="none",
            eliminations=[
                {"emoji": "C", "round": 5, "killed_by": "storm", "cause": "storm"},
                {"emoji": "B", "round": 8, "killed_by": "storm", "cause": "storm"},
                {"emoji": "A", "round": 8, "killed_by": "storm", "cause": "storm"},
            ],
        )
        result = calculate_match_xp(match)
        # A and B tied at round 8 = rank 1, C at round 5 = rank 3
        # (competition ranking: two 1sts → skip 2nd)
        assert result["A"].placement == 50  # tied 1st
        assert result["B"].placement == 50  # tied 1st
        assert result["C"].placement == 15  # 3rd (competition ranking skips 2nd)

    def test_tie_elimination_same_round(self) -> None:
        """Bots eliminated in the same round share the higher placement."""
        match = _minimal_match(
            eliminations=[
                {"emoji": "C", "round": 5, "killed_by": "storm", "cause": "storm"},
                {"emoji": "B", "round": 5, "killed_by": "storm", "cause": "storm"},
            ],
        )
        result = calculate_match_xp(match)
        # B and C both eliminated round 5 — both get 2nd place XP
        assert result["B"].placement == result["C"].placement
