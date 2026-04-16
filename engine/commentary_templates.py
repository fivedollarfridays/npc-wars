"""Commentary templates for Kill Switch play-by-play and color commentary.

Templates use {placeholders} for runtime substitution:
  {attacker}, {victim}, {bot}, {direction}, {trait}, {rival},
  {streak}, {variant}, {weapon}, {armor}, {tactical}
"""

from __future__ import annotations

__all__ = ["PLAY_BY_PLAY", "COLOR_COMMENTARY", "TONE_MODIFIERS"]

# --- Play-by-play templates keyed by event/action type ---

PLAY_BY_PLAY: dict[str, list[str]] = {
    "kill": [
        "{attacker} eliminates {victim}!",
        "{victim} goes down — {attacker} claims the kill.",
        "{attacker} lands the finishing blow on {victim}.",
        "That's it for {victim} — taken out by {attacker}.",
        "{attacker} just erased {victim} from the battlefield.",
    ],
    "storm_kill": [
        "The storm claims {victim}!",
        "{victim} caught outside the safe zone — eliminated by storm damage.",
        "The storm closes in and {victim} doesn't make it.",
    ],
    "move": [
        "{bot} repositions {direction}.",
        "{bot} moves {direction}, reading the field.",
        "{bot} advances {direction}.",
        "{bot} shifts {direction}.",
    ],
    "defend": [
        "{bot} digs in and defends.",
        "{bot} raises their guard.",
        "{bot} turtles up — playing it safe.",
        "{bot} braces for impact.",
    ],
    "trap": [
        "{bot} lays a trap.",
        "{bot} sets a trap — watch your step.",
        "{bot} plants a surprise for the unwary.",
        "{bot} rigs the ground nearby.",
    ],
    "attack": [
        "{bot} attacks {direction}!",
        "{bot} strikes {direction}!",
        "{bot} goes in swinging {direction}.",
        "{bot} lunges {direction} with an attack.",
    ],
    "ranged_attack": [
        "{bot} fires a ranged shot {direction}!",
        "{bot} lets loose from range {direction}.",
        "{bot} takes aim and fires {direction}.",
    ],
    "dash": [
        "{bot} dashes {direction}!",
        "{bot} bursts forward with a dash {direction}.",
    ],
    "ability": [
        "{bot} activates {tactical}!",
        "{bot} uses {tactical} — bold move.",
        "{bot} triggers {tactical}.",
    ],
    "watcher_spawn": [
        "The Watcher has entered the battlefield.",
        "A dark presence — the Watcher appears.",
        "The Watcher materializes. Everyone is on edge.",
    ],
    "watcher_kill": [
        "The Watcher claims a victim!",
        "The Watcher strikes — another one falls.",
        "Nobody is safe when the Watcher hunts.",
    ],
    "watcher_sync": [
        "The Watcher syncs with the arena.",
        "A pulse wave ripples through the field — Watcher sync.",
    ],
    "near_death": [
        "{bot} is barely alive — hanging on by a thread!",
        "{bot} at critical HP! One more hit and it's over.",
        "{bot} is on death's door.",
    ],
    "chain_bump": [
        "Bodies collide — chain bump!",
        "A chain reaction sends bots flying!",
    ],
    "kill_streak": [
        "{attacker} is on a kill streak!",
        "{attacker} can't be stopped — streak continues!",
        "The streak grows — {attacker} is on fire!",
    ],
    "rest": [
        "{bot} takes a breather.",
        "{bot} rests and recovers.",
    ],
}

# --- Color commentary templates keyed by context ---

COLOR_COMMENTARY: dict[str, list[str]] = {
    "trait_aggro": [
        "Classic {variant} play — all offense, no apologies.",
        "That {trait} instinct is showing — pure aggression.",
        "{bot} living up to the {variant} reputation.",
    ],
    "trait_defensive": [
        "{bot} is patient — the {variant} way.",
        "Textbook {trait} play. Wait for the opening, then strike.",
        "You don't rush a {variant}. They'll outlast you.",
    ],
    "trait_mobile": [
        "{bot} is everywhere and nowhere — that {trait} speed.",
        "Can't hit what you can't catch. {variant} at work.",
    ],
    "trait_trap": [
        "The battlefield is {bot}'s web now.",
        "{variant} turning the arena into a minefield.",
    ],
    "rivalry_kill": [
        "That's personal — {attacker} has history with {victim}.",
        "{attacker} makes it {streak} in a row against {victim}.",
        "The rivalry continues — {attacker} over {victim} once again.",
    ],
    "rivalry_streak": [
        "{bot} owns this matchup — {streak} straight wins.",
        "Total domination in this head-to-head. {streak} wins running.",
    ],
    "rivalry_upset": [
        "{bot} breaks the streak! Upset alert!",
        "Against all odds, {bot} takes down the rival.",
    ],
    "equipment_weapon": [
        "That {weapon} is doing work.",
        "{bot}'s {weapon} is the difference maker.",
    ],
    "equipment_armor": [
        "Good thing {bot} brought the {armor} — absorbing hits.",
        "That {armor} is earning its keep.",
    ],
    "equipment_tactical": [
        "{tactical} changes the dynamic entirely.",
        "Smart use of {tactical} from {bot}.",
    ],
    "watcher_event": [
        "The Watcher doesn't pick sides — it picks victims.",
        "Nobody expected the Watcher to intervene here.",
        "The Watcher adds chaos to an already tense situation.",
    ],
    "momentum": [
        "{bot} is building momentum — this could get ugly.",
        "The snowball is rolling. {variant} at full steam.",
    ],
    "closer": [
        "And that's the match. {bot} takes the win.",
        "It's over! {bot} stands alone as the victor.",
        "Decisive victory for {bot}.",
    ],
}

# Tone modifiers: prefix/suffix by drama tier
TONE_MODIFIERS: dict[str, dict[str, str]] = {
    "calm": {"prefix": "", "suffix": ""},
    "heating": {"prefix": "", "suffix": ""},
    "intense": {"prefix": "Things are heating up — ", "suffix": ""},
    "hype": {"prefix": "", "suffix": " What a moment!"},
    "chaos": {"prefix": "ABSOLUTE CHAOS — ", "suffix": "!!!"},
}
