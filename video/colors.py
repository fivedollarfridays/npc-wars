"""Shared color constants and helpers for NPC Wars video rendering."""

HP_HIGH = (50, 200, 50)    # green  -- hp >= 60
HP_MID = (220, 180, 0)     # yellow -- hp 30-59
HP_LOW = (200, 40, 40)     # red    -- hp < 30


def hp_color(hp: int) -> tuple[int, int, int]:
    """Return HP bar fill color based on HP value."""
    if hp >= 60:
        return HP_HIGH
    if hp >= 30:
        return HP_MID
    return HP_LOW
