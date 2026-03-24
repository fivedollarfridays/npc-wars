"""Tournament bracket engine for Kill Switch."""

from __future__ import annotations

import random
from typing import Any

__all__ = ["Tournament", "VALID_SIZES"]

VALID_SIZES = (8, 16, 32)


class Tournament:
    """Manages bracket state, seeding, match pairing, and advancement."""

    def __init__(self, name: str, size: int, seed: int | None = None) -> None:
        if size not in VALID_SIZES:
            raise ValueError(f"Size must be one of {VALID_SIZES}")
        self.name = name
        self.size = size
        self.seed = seed
        self.players: list[str] = []
        self.rounds: list[list[dict[str, Any]]] = []
        self.status: str = "open"
        self.winner: str | None = None

    def add_player(self, player_id: str) -> bool:
        """Add a player. Returns False if full, already joined, or not open."""
        if self.status != "open":
            return False
        if player_id in self.players:
            return False
        if len(self.players) >= self.size:
            return False
        self.players.append(player_id)
        return True

    def is_full(self) -> bool:
        """Check if tournament has reached capacity."""
        return len(self.players) >= self.size

    def seed_bracket(self) -> None:
        """Randomize seeding and generate round 1 groups."""
        if self.status != "open":
            return
        rng = random.Random(self.seed)
        shuffled = list(self.players)
        rng.shuffle(shuffled)
        groups = [shuffled[i : i + 4] for i in range(0, len(shuffled), 4)]
        round1 = [
            {"group": g, "results": None, "match_id": None, "advancing": []}
            for g in groups
        ]
        self.rounds = [round1]
        self.status = "running"

    def get_current_round(self) -> int:
        """0-indexed current round number."""
        return len(self.rounds) - 1

    def get_pending_matches(self) -> list[dict[str, Any]]:
        """Matches in the current round that haven't been played."""
        if not self.rounds:
            return []
        current = self.rounds[-1]
        return [m for m in current if m["results"] is None]

    def record_result(
        self, match_idx: int, results: dict[str, Any], match_id: int
    ) -> None:
        """Record match results. Top 2 from placements advance."""
        current = self.rounds[-1]
        match = current[match_idx]
        match["results"] = results
        match["match_id"] = match_id
        placements = results.get("placements", [])
        match["advancing"] = placements[:2] if len(placements) >= 2 else placements
        if all(m["results"] is not None for m in current):
            self._advance_round()

    def _advance_round(self) -> None:
        """Create next round from advancing players, or crown a winner."""
        current = self.rounds[-1]
        # If this was a single-match final, the winner takes the tournament
        if len(current) == 1 and current[0]["results"] is not None:
            self.winner = current[0]["results"].get("winner")
            self.status = "complete"
            return
        advancing: list[str] = []
        for m in current:
            advancing.extend(m["advancing"])
        if len(advancing) <= 4:
            final = [
                {"group": advancing, "results": None,
                 "match_id": None, "advancing": []}
            ]
            self.rounds.append(final)
        else:
            groups = [advancing[i : i + 4] for i in range(0, len(advancing), 4)]
            next_round = [
                {"group": g, "results": None, "match_id": None, "advancing": []}
                for g in groups
            ]
            self.rounds.append(next_round)

    def is_complete(self) -> bool:
        """Check if tournament has finished."""
        return self.status == "complete"

    def get_winner(self) -> str | None:
        """Return the tournament winner, or None if not complete."""
        return self.winner

    def to_dict(self) -> dict[str, Any]:
        """Serialize tournament state to a dictionary."""
        return {
            "name": self.name,
            "size": self.size,
            "seed": self.seed,
            "players": self.players,
            "rounds": self.rounds,
            "status": self.status,
            "winner": self.winner,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Tournament:
        """Deserialize tournament state from a dictionary."""
        t = cls(data["name"], data["size"], data.get("seed"))
        t.players = data["players"]
        t.rounds = data["rounds"]
        t.status = data["status"]
        t.winner = data.get("winner")
        return t
