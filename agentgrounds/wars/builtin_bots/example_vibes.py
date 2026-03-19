"""NPC Wars Bot -- Cognify (vibes DSL example)"""

BOT_NAME = "Cognify"
BOT_EMOJI = "\U0001f9e0"
BOT_GLYPH = "◈"
BOT_BIO = "rests until it doesn't"
BOT_AUTHOR = "kevin"


def decide(state):
    from agentgrounds.wars.helpers import Me, Enemies, Storm

    me = Me(state)
    enemies = Enemies(state)
    storm = Storm(state)

    # P0: Storm escape
    if storm.danger:
        return me.flee_storm()

    adj = enemies.adjacent()
    killable = [e for e in adj if e["hp"] <= me.attack_power]

    # P1: Energy crisis
    if me.energy < 15 and not killable:
        return me.rest()

    # P2: Finish kills
    if killable:
        target = min(killable, key=lambda e: e["hp"])
        return me.attack(target)

    # P3: Defend or counter
    if adj:
        weakest = min(adj, key=lambda e: e["hp"])
        if me.hp <= 40 or len(adj) > 1:
            return me.defend()
        if weakest["hp"] <= 50:
            return me.attack(weakest)
        return me.defend()

    # P4: Rest when safe
    if me.energy < 30:
        return me.rest()

    # P5: Chase wounded
    if me.hp > 50 and me.energy >= 40:
        wounded = enemies.wounded(50)
        if wounded:
            target = min(wounded, key=lambda e: e["hp"])
            if me.dist_to(target) <= 4:
                return me.move_toward(target)

    # P6: Drift center
    return me.move_toward_center()
