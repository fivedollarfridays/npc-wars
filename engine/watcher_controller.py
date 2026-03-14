"""Controller for The Cringe boss bot lifecycle within a match.

Owns the Watcher's spawn, brain, observation, and persistence lifecycle.
Keeps game.py clean by encapsulating all Watcher integration logic.
"""

from __future__ import annotations

import random
from typing import Any

from engine.combat import Bot, MAX_HP
from engine.watcher import WATCHER_ACTIONS, WatcherBot
from engine.watcher_brain import (
    HumanPerformance,
    SyncTracker,
    apply_accuracy_cap,
    get_accuracy_cap,
    select_counter_action,
    select_target,
)
from engine.watcher_memory import (
    CROSS_SESSION_RETENTION,
    SESSION_RETENTION,
    PatternTable,
    decay_memory,
    load_memory,
    save_memory,
)
from engine.watcher_observer import classify_contexts, observe_round
from engine.watcher_spawn import build_spawn_event, check_watcher_spawn, find_spawn_position
from engine.watcher_spectacle import (
    emit_sync_milestone_event,
    emit_watcher_kill_event,
    emit_watcher_spawn_event,
)
from engine.watcher_stats import WatcherStats, load_stats, save_stats

__all__ = ["WatcherController"]

_SYNC_MILESTONES = (50.0, 75.0, 90.0)


class WatcherController:
    """Orchestrates The Cringe's lifecycle during a single match.

    Handles spawn checks, action selection via the counter-action brain,
    pattern observation, kill tracking, and persistence.
    """

    def __init__(
        self,
        rng: random.Random,
        memory_path: str | None = None,
        stats_path: str | None = None,
    ) -> None:
        self._memory_path = memory_path
        self._stats_path = stats_path
        self.rng = rng
        self.watcher_bot: WatcherBot | None = None
        self.sync_tracker = SyncTracker()
        self._prev_sync: dict[str, float] = {}

        load_kw: dict[str, str] = {}
        if memory_path is not None:
            load_kw["path"] = memory_path
        self.pattern_table: PatternTable = load_memory(**load_kw)
        decay_memory(self.pattern_table, CROSS_SESSION_RETENTION)

        stats_kw: dict[str, str] = {}
        if stats_path is not None:
            stats_kw["path"] = stats_path
        self.stats: WatcherStats = load_stats(**stats_kw)

    # -- spawn ----------------------------------------------------------------

    def try_spawn(
        self,
        bots: list[Bot],
        round_num: int,
        grid_size: int,
        storm_border: int,
    ) -> list[dict[str, Any]]:
        """Check spawn conditions and spawn if triggered. Returns events."""
        if self.watcher_bot is not None:
            return []
        if not check_watcher_spawn(bots, round_num, watcher_present=False):
            return []

        occupied = {(b.x, b.y) for b in bots if b.alive}
        human_positions = [
            (b.x, b.y) for b in bots
            if b.alive and getattr(b, "human_adapter", None) is not None
        ]
        x, y = find_spawn_position(grid_size, storm_border, occupied, human_positions, self.rng)

        self.watcher_bot = WatcherBot(x=x, y=y)
        bots.append(self.watcher_bot)
        return [build_spawn_event(x, y), emit_watcher_spawn_event(x, y, sync=0.0)]

    # -- action selection -----------------------------------------------------

    def get_watcher_action(
        self,
        bots: list[Bot],
        round_num: int,
        grid_size: int,
        storm_border: int,
    ) -> tuple[str, ...] | None:
        """Get The Cringe's action for this round. Returns None if not spawned."""
        if self.watcher_bot is None or not self.watcher_bot.alive:
            return None

        human_emojis = [
            b.emoji for b in bots
            if b.alive and getattr(b, "human_adapter", None) is not None
        ]
        if not human_emojis:
            return ("rest",)

        target_id = select_target(self.sync_tracker, human_emojis)
        if target_id is None:
            return ("rest",)

        target_bot = next((b for b in bots if b.emoji == target_id and b.alive), None)
        if target_bot is None:
            return ("rest",)

        contexts = classify_contexts(
            target_id, [], bots, storm_border, grid_size, {},
        )
        if not contexts:
            contexts = ["__default__"]

        counter = select_counter_action(
            self.pattern_table, target_id,
            self.watcher_bot.x, self.watcher_bot.y,
            target_bot.x, target_bot.y,
            contexts, set(WATCHER_ACTIONS),
        )

        perf = HumanPerformance(
            hp_ratio=target_bot.hp / MAX_HP,
            kills=target_bot.kills,
            rounds_survived=target_bot.rounds_survived,
        )
        cap = get_accuracy_cap(perf)
        return apply_accuracy_cap(counter, cap, list(WATCHER_ACTIONS), self.rng)

    # -- round integration ----------------------------------------------------

    def post_round(
        self,
        bots: list[Bot],
        round_data: dict[str, Any],
        round_elims: list[dict[str, Any]],
        round_num: int,
        grid_size: int,
        storm_border: int,
    ) -> None:
        """Run all post-round watcher hooks: action override, observe, kills."""
        # Override watcher's placeholder action in the round record
        watcher_action = self.get_watcher_action(bots, round_num, grid_size, storm_border)
        if watcher_action is not None and self.watcher_bot is not None:
            actions_in_round = round_data.get("actions", {})
            actions_in_round[self.watcher_bot.emoji] = " ".join(watcher_action)

        human_emojis = [
            b.emoji for b in bots
            if b.alive and getattr(b, "human_adapter", None) is not None
        ]
        actions_dict = round_data.get("actions", {})
        self.observe(
            human_emojis, round_data.get("events", []),
            bots, storm_border, grid_size, actions_dict,
        )
        for elim in round_elims:
            self.record_kill(elim.get("killed_by", ""), elim["emoji"], human_emojis)

    # -- observation ----------------------------------------------------------

    def observe(
        self,
        human_emojis: list[str],
        round_events: list[dict[str, Any]],
        bots: list[Bot],
        storm_border: int,
        grid_size: int,
        actions: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Record human actions for pattern learning. Returns spectacle events."""
        observe_round(
            self.pattern_table, human_emojis, round_events,
            bots, storm_border, grid_size, actions,
        )

        events: list[dict[str, Any]] = []
        for emoji in human_emojis:
            sync = self.sync_tracker.get_sync(emoji)
            prev = self._prev_sync.get(emoji, 0.0)
            for milestone in _SYNC_MILESTONES:
                if prev < milestone <= sync:
                    events.append(emit_sync_milestone_event(sync))
            self._prev_sync[emoji] = sync
        return events

    # -- kill tracking --------------------------------------------------------

    def record_kill(
        self,
        killer_emoji: str,
        victim_emoji: str,
        human_emojis: list[str],
    ) -> list[dict[str, Any]]:
        """Track kills by/against The Cringe. Returns spectacle events."""
        if self.watcher_bot is None:
            return []
        events: list[dict[str, Any]] = []
        if killer_emoji == self.watcher_bot.emoji:
            victim_type = "human" if victim_emoji in human_emojis else "bot"
            self.stats.record_kill(victim_type)
            sync = (
                self.sync_tracker.get_sync(victim_emoji)
                if victim_emoji in human_emojis else 0.0
            )
            events.append(emit_watcher_kill_event(victim_emoji, sync))
        if victim_emoji == self.watcher_bot.emoji:
            self.stats.record_death()
        return events

    # -- finalize -------------------------------------------------------------

    def finalize(self, won: bool) -> None:
        """Save memory and stats after match ends."""
        self.stats.record_match(won=won)
        decay_memory(self.pattern_table, SESSION_RETENTION)
        save_kw: dict[str, str] = {}
        if self._memory_path is not None:
            save_kw["path"] = self._memory_path
        save_memory(self.pattern_table, **save_kw)
        stats_kw: dict[str, str] = {}
        if self._stats_path is not None:
            stats_kw["path"] = self._stats_path
        save_stats(self.stats, **stats_kw)
