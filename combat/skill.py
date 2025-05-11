import time
import random

class SkillEffect:
    def apply(self, user, targets):
        pass

class AreaDamageEffect(SkillEffect):
    def __init__(self, radius=100, damage=20):
        self.radius = radius
        self.damage = damage

    def apply(self, user, targets):
        for t in targets:
            if abs(user.x - t.x) <= self.radius and t.alive:
                t.health -= self.damage
                if t.health <= 0:
                    t.alive = False

class BuffAttackSpeedEffect(SkillEffect):
    def __init__(self, buff_amount=0.5, duration=5):
        self.buff_amount = buff_amount
        self.duration = duration

    def apply(self, user, targets):
        for ally in targets:
            if not hasattr(ally, "original_cooldown"):
                ally.original_cooldown = ally.attack.cooldown
            ally.attack.cooldown = max(0.1, ally.attack.cooldown - self.buff_amount)
            ally.buff_end_time = time.time() + self.duration

class GroupHealEffect(SkillEffect):
    def __init__(self, heal_amount=15):
        self.heal_amount = heal_amount

    def apply(self, user, targets):
        for t in targets:
            if t.alive and t.health < t.max_health:
                t.health += self.heal_amount
                if t.health > t.max_health:
                    t.health = t.max_health

class Skill:
    def __init__(self, name, skill_cooldown, effect: SkillEffect, skill_chance=1.0, cast_duration=0.3):
        self.name = name
        self.skill_cooldown = skill_cooldown
        self.effect = effect
        self.skill_chance = skill_chance
        self.cast_duration = cast_duration
        self.last_used_time = 0

    def can_use_skill(self):
        cooldown_ready = time.time() - self.last_used_time >= self.skill_cooldown
        chance_roll = random.random() < self.skill_chance
        return cooldown_ready and chance_roll

    def use(self, user, targets):
        if self.can_use_skill():
            self.effect.apply(user, targets)
            self.last_used_time = time.time()
