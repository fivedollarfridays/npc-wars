"""NPC Wars Bot -- Cognify (vibes DSL example)"""

BOT_NAME = "Cognify"
BOT_EMOJI = "\U0001f9e0"
BOT_GLYPH = "◈"
BOT_BIO = "rests until it doesn't"
BOT_AUTHOR = "kevin"
BOT_POWER = 15
BOT_SPEED = 20
BOT_ARMOR = 20
BOT_MIND = 45


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

    # P4: Rest briefly when low energy
    if me.energy < 20:
        return me.rest()

    # P5: Chase closest — don't idle, plague punishes passivity
    closest = enemies.closest()
    if closest:
        if me.dist_to(closest) <= 5:
            return me.move_toward(closest)

    # P6: Always move toward someone
    if closest:
        return me.move_toward(closest)

    return me.move_toward_center()
