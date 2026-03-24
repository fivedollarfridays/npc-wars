"""Cosmetic item catalog and reward constants.

Pure data — no DB access. See cosmetic_db.py for persistence.
"""

from __future__ import annotations

COSMETIC_CATALOG: dict[str, dict] = {
    # ── Color Palettes ──────────────────────────────────────────────
    "crimson": {"name": "Crimson", "type": "color_palette", "rarity": "common", "price": 100, "color": "#cc0000"},
    "neon": {"name": "Neon Green", "type": "color_palette", "rarity": "common", "price": 100, "color": "#00ff66"},
    "ghost": {"name": "Ghost White", "type": "color_palette", "rarity": "rare", "price": 300, "color": "#e8e8ff"},
    "ocean": {"name": "Ocean Blue", "type": "color_palette", "rarity": "common", "price": 100, "color": "#0066cc"},
    "toxic": {"name": "Toxic", "type": "color_palette", "rarity": "rare", "price": 300, "color": "#66ff00"},
    # ── Glow Effects ────────────────────────────────────────────────
    "fire_aura": {"name": "Fire Aura", "type": "glow_effect", "rarity": "rare", "price": 300, "color": "#ff4400"},
    "ice_shimmer": {"name": "Ice Shimmer", "type": "glow_effect", "rarity": "rare", "price": 300, "color": "#44ccff"},
    "shadow": {"name": "Shadow", "type": "glow_effect", "rarity": "epic", "price": 800, "color": "#220033"},
    "electric": {"name": "Electric", "type": "glow_effect", "rarity": "epic", "price": 800, "color": "#ffff00"},
    # ── Weapon Skins ────────────────────────────────────────────────
    "golden_blade": {"name": "Golden Blade", "type": "weapon_skin", "rarity": "epic", "price": 800, "color": "#ffd700"},
    "crystal_edge": {"name": "Crystal Edge", "type": "weapon_skin", "rarity": "rare", "price": 300, "color": "#88ddff"},
    "blood_edge": {"name": "Blood Edge", "type": "weapon_skin", "rarity": "rare", "price": 300, "color": "#880000"},
    "void": {"name": "Void", "type": "weapon_skin", "rarity": "legendary", "price": 2000, "color": "#110022"},
    # ── Death Effects ───────────────────────────────────────────────
    "shatter_gold": {"name": "Shatter Gold", "type": "death_effect", "rarity": "epic", "price": 800, "color": "#ffd700"},
    "fade_black": {"name": "Fade to Black", "type": "death_effect", "rarity": "common", "price": 100, "color": "#111111"},
    "sparkle": {"name": "Sparkle", "type": "death_effect", "rarity": "rare", "price": 300, "color": "#ffffff"},
    "void_death": {"name": "Void Collapse", "type": "death_effect", "rarity": "legendary", "price": 2000, "color": "#110022"},
    # ── Trail Effects ───────────────────────────────────────────────
    "spark_trail": {"name": "Spark Trail", "type": "trail_effect", "rarity": "rare", "price": 300, "color": "#ffaa00"},
    "smoke": {"name": "Smoke", "type": "trail_effect", "rarity": "common", "price": 100, "color": "#666666"},
    "frost": {"name": "Frost", "type": "trail_effect", "rarity": "epic", "price": 800, "color": "#aaddff"},
    "flame": {"name": "Flame", "type": "trail_effect", "rarity": "legendary", "price": 2000, "color": "#ff2200"},
}

MATCH_COIN_REWARD = 10
WIN_COIN_BONUS = 25
