"""Helpers DSL for NPC Wars bot authors.

Re-exports Me, Enemies, and Storm from their respective modules.
No engine imports allowed — sandbox-safe.

Usage::

    from npcwars.helpers import Me, Enemies, Storm

    def decide(state):
        me = Me(state)
        enemies = Enemies(state)
        storm = Storm(state)
        ...
"""

from npcwars._enemies import Enemies
from npcwars._me import Me
from npcwars._storm import Storm

__all__ = ["Enemies", "Me", "Storm"]
