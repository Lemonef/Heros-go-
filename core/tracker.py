import os
import csv
import time
from collections import defaultdict

class Tracker:
    def __init__(self, csv_filename="game_data.csv"):
        self.csv_filename = csv_filename
        self.snapshot_data = []
        self.last_snapshot_time = time.time()

        self.enemies_defeated = 0
        self.hero_spawn_counter = defaultdict(int)
        self.ability_usage_counter = defaultdict(int)
        self.energy_spent = 0
        self.heroes_defeated = 0

        self.initialize_csv_if_needed()

    def initialize_csv_if_needed(self):
        if not os.path.exists(self.csv_filename):
            with open(self.csv_filename, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Timestamp", "TotalEnergyUsed", "EnemiesDefeated",
                    "HeroesDefeated", "MostSpawnedHero", "MostSpawnedCount",
                    "Attack_speed_Buff_Used", "AOE_Used", "GroupHeal_Used"
                ])

    def log_hero_defeated(self):
        self.heroes_defeated += 1

    def log_hero_spawn_count(self, hero_name):
        self.hero_spawn_counter[hero_name] += 1

    def log_ability_used(self, skill_name):
        self.ability_usage_counter[skill_name] += 1

    def log_enemy_defeated(self):
        self.enemies_defeated += 1

    def log_energy_spent(self, amount):
        self.energy_spent += amount

    def try_snapshot(self):
        now = time.time()
        if now - self.last_snapshot_time >= 5:
            most_spawned = max(self.hero_spawn_counter.items(), key=lambda x: x[1], default=("None", 0))
            archer_count = self.ability_usage_counter.get("Buff", 0)
            mage_count = self.ability_usage_counter.get("AOE", 0)
            healer_count = self.ability_usage_counter.get("Group Heal", 0)

            self.snapshot_data.append([
                now,
                self.energy_spent,
                self.enemies_defeated,
                self.heroes_defeated,
                most_spawned[0],
                most_spawned[1],
                archer_count,
                mage_count,
                healer_count
            ])
            self.heroes_defeated = 0
            self.enemies_defeated = 0
            self.hero_spawn_counter.clear()
            self.ability_usage_counter.clear()
            self.last_snapshot_time = now

    def append_new_rows(self):
        if not self.snapshot_data:
            return

        with open(self.csv_filename, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(self.snapshot_data)
        self.snapshot_data.clear()
