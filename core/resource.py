import time

class ResourceManager:
    def __init__(self):
        self.energy = 100
        self.max_energy = 100
        self.regen_rate = 0.1
        self.upgrade_clicks = 0
        self.last_upgrade_display_time = 0

    def can_afford(self, cost):
        return self.energy >= cost

    def spend(self, amt):
        self.energy -= amt

    def regenerate(self):
        if self.energy < self.max_energy:
            self.energy += self.regen_rate
            if self.energy > self.max_energy:
                self.energy = self.max_energy

    def upgrade_energy(self):
        upgrade_cost = 20 + 10 * self.upgrade_clicks
        if self.upgrade_clicks < 5 and self.energy >= upgrade_cost:
            self.energy -= upgrade_cost
            self.max_energy += 10
            self.regen_rate += 0.01
            self.upgrade_clicks += 1
            self.last_upgrade_display_time = time.time()
