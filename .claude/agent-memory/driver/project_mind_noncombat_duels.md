---
name: mind-noncombat-duels
description: Mind stat has no offensive value in stats-only 1v1 melee duels; mage archetype is structurally weak there
metadata:
  type: project
---

In Kill Switch (npc-wars), the `mind` stat only buys `max_energy` and
`energy_regen` in `engine/stats.calculate_derived`. In a stats-only 1v1 melee
duel — where both bots share a simple chase-and-attack decide func that never
rests to bank energy or casts abilities — mind is effectively dead weight.

**Why:** Discovered during T73.6 versatility retune. The mage archetype
(15/20/20/45) could NOT be tuned into a 40-60% win band vs balanced by any
versatility-constant setting: at the chosen constants it loses 87-90% of duels.
Its combat profile (HP 66 / dmg 9-21) is strictly worse than balanced's
(102 / 28-48), and no HP/dmg/variance-cap value closes the gap.

**How to apply:** For any future balance task that measures archetypes via
stats-only duels, expect mind-heavy builds to look broken — that's the combat
model, not a stat-constant bug. Making mind matter in duels requires a combat
change (energy-gated abilities the policy actually uses), which is out of scope
for `engine/stats.py`-only retunes. The limitation is pinned by
`tests/test_versatility_balance.py::test_mage_documented_structural_weakness`.
