import math, random, json
from helpers import*

class Enemy:
    def __init__(self, enemy_data):
        self.id = enemy_data["id"]
        self.name = enemy_data["name"]
        self.maxHP = enemy_data["hp"]
        self.hp = enemy_data["hp"]
        self.atk = enemy_data["atk"]
        self.turns = enemy_data.get("turns", 1)
        self.defP = enemy_data["defP"]
        self.defM = enemy_data["defM"]
        self.weak = enemy_data.get("weak", [])
        self.resist = enemy_data.get("resist", [])
        self.block = enemy_data.get("block", [])
        self.absorb = enemy_data.get("absorb", [])

        self.skills = []
        self.skillsID = enemy_data.get("skills", [])
        self.load_skills()

        self.passive_uses = {}
        self.initialize_passive_uses()

        self.exp = enemy_data["exp"]
        self.money = enemy_data["money"]
        self.key_item = enemy_data.get("key_item", [])
        self.areaIDs = enemy_data.get("areaIDs", [])

        self.buff_atk = 0
        self.buff_def = 0
        self.buff_agi = 0
        self.buffDurations = {
            "atk" : 0,
            "def" : 0,
            "agi" : 0
        }

        self.stats = {
            "atk": self.atk,
            "skillP" : math.sqrt((self.atk*2/3)) + 12,
            "skillM" : math.sqrt((self.atk*2/3)) + 15,
            "defP": self.defP,
            "defM": self.defM,
            "weak": self.weak,
            "resist": self.resist,
            "block": self.block,
            "absorb": self.absorb,
            "dodgeChance": 10,
            "critChance": 10,
        }
        self.tempStats = self.stats.copy()

        self.status_effects = {
            "bleed": {"active": False, "duration": 0, "target_maxHP": 0},
            "frenzy": {},
            "mute": {},
            "disarm": {}
        }

    def scale(self, days):
        for key in self.stats:
            if isinstance(self.stats[key], (int, float)):
                self.stats[key] *= (1 + (days*0.04))

        self.tempStats = self.stats.copy()


    def load_skills(self):
        with open("json/skills.json", "r") as f:
            skillsJSON = json.load(f)

        for skillID in self.skillsID:
            if skillID in skillsJSON:
                skillData = skillsJSON[skillID]
                skillData = skillData.copy()  # Create a copy of the skill data
                skillData["id"] = skillID  # Add the ID to the skill data
                self.skills.append(skillData)  # Append the skill data to the skills list
    
    def initialize_passive_uses(self):
        for skill in self.skills:
            if skill.get("type") == "survival":
                uses = skill.get("uses_per_battle", 1)
                self.passive_uses[skill["id"]] = uses

    def reset_passive_uses(self):
        self.initialize_passive_uses()

    def reset_stat(self):
        self.tempStats = self.stats.copy()

    def modify_stat(self, statName, stage, type):
        multipliers = {
            2 :  {"atk": 1.4, "def": 0.7, "hit": 1.2, "eva": 0.85},
            1 :  {"atk": 1.2, "def": 0.8, "hit": 1.1, "eva": 0.9},
            0 :  {"atk": 1,   "def": 1,   "hit": 1,   "eva": 1},
            -1 : {"atk": 0.8, "def": 1.2, "hit": 0.9, "eva": 1.1},
            -2 : {"atk": 0.7, "def": 1.4, "hit": 0.8, "eva": 1.2},
        }
        stage = max(-2, min(stage ,2)) # -2 to 2
        baseValue = self.stats.get(statName, 0)
        multiplier = multipliers[stage][type]
        self.tempStats[statName] = math.ceil(baseValue * multiplier)
    
    def update_durations(self):
        for stat in ["atk", "def", "agi"]:
            if self.buffDurations[stat] > 0:
                self.buffDurations[stat] -= 1
                if self.buffDurations[stat] == 0:
                    setattr(self, f"buff_{stat}", 0)

        # refresh existing buffs
        self.tempStats = self.stats.copy()
        if self.buff_atk != 0:
            self.modify_stat("atk", self.buff_atk, "atk")
            self.modify_stat("skillP", self.buff_atk, "atk")
            self.modify_stat("skillM", self.buff_atk, "atk")

        if self.buff_def != 0:
            self.modify_stat("defP", self.buff_def, "def")
            self.modify_stat("defM", self.buff_def, "def")
            self.modify_stat("defA", self.buff_def, "def")

        if self.buff_agi != 0:
            self.modify_stat("critChance", self.buff_agi, "hit")
            self.modify_stat("dodgeChance", self.buff_agi, "eva")

    def is_alive(self):
        return self.hp > 0
    
    def is_dead(self):
        if self.hp <= 0:
            print(f">> {self.name} is defeated!")

    def take_physical_damage(self, base_dmg, dmg_type="None"):
        if dmg_type == "strike":
            defPEN = 0.5 
            dmg = math.ceil(base_dmg * (1 - (self.stats["defP"]/100 * defPEN )))
        else:
            dmg = math.ceil(base_dmg * (1 - (self.stats["defP"]/100)))

        reduced = max(dmg, 1)
        self.hp = max(self.hp - reduced, 0)
        return reduced

    def take_magic_damage(self, base_dmg):
        dmg = math.ceil(base_dmg * (1 - (self.stats["defM"]/100)))
        reduced = max(dmg, 1)
        self.hp = max(self.hp - reduced, 0)
        return reduced
    
    def take_arcane_damage(self, base_dmg):
        dmg = math.ceil(base_dmg * (1 - (self.stats["defA"]/100)))
        reduced = max(dmg, 1)
        self.hp = max(self.hp - reduced, 0)
        return reduced
    
    def apply_bleed(self):
        self.status_effects["bleed"] = {
            "active": True,
            "duration": 3
        }

    def process_status_effects(self):
        bleed = self.status_effects["bleed"]
        if bleed["active"]:
            bleed_dmg = math.ceil(self.maxHP * 0.05)
            self.hp = max(self.hp - bleed_dmg, 0)
            bleed["duration"] -= 1
            
            print(f">> {self.name} takes {bleed_dmg} bleed damage!")
            
            if bleed["duration"] <= 0:
                bleed["active"] = False
                print(f">> {self.name}'s bleed has ended.")
            else:
                print(f">> Bleed duration: {bleed['duration']} turns remaining.")
            
            return bleed_dmg
        return 0

    def attack(self, target):
        if self.is_alive():
            damage = max(self.atk * (1 - (target.stats["defP"]/100)), 1)
            return damage
        return 0
    
    def get_available_skills(self):
        available = []
        hp_percent = (self.hp / self.maxHP) * 100
        
        for skill in self.skills:
            # Check if skill has phase requirement
            min_phase = skill.get("min_hp_percent", 0)  # Minimum HP% to unlock
            max_phase = skill.get("max_hp_percent", 100)  # Maximum HP% to use
            
            if min_phase <= hp_percent <= max_phase:
                available.append(skill)
        
        return available if available else self.skills 
    
    def behavior(self, enemyParty, targetParty):
        available_skills = self.get_available_skills()

        dmgSkills = [skill for skill in available_skills if skill["type"] in ("physical", "magic")]
        buffSkills = [skill for skill in available_skills if skill["type"] == "buff"]
        healSkills = [skill for skill in available_skills if skill["type"] == "heal"]
        debuffSkills = [skill for skill in available_skills if skill["type"] == "debuff"]

        total = 0
        if dmgSkills: total += 1
        if buffSkills: total += 1
        if debuffSkills: total += 1

        if total == 0:
            skill = "None"
            target = random.choice(targetParty)
            return skill, target
        
        else:
            chance = 0.3 / total
        
        lowestHP = [e for e in enemyParty.enemyMembers if e.is_alive() and e.hp < e.maxHP * 0.4] # 40% HP threshold
        if lowestHP and healSkills: 
            skill = random.choice(healSkills)
            target = min(lowestHP, key=lambda e: e.hp) #compare e.hp to find the lowest HP, may cause issue if multiple targets have the same name
            return skill["id"], target # Heal the target if they are below 40% HP
        
        if buffSkills and random.random() < chance: # 10% chance to buff
            skill = random.choice(buffSkills)
            target = random.choice(enemyParty) # Maybe update this to target the leader 
            return skill["id"], target
        
        elif debuffSkills and random.random() < chance:
            skill = random.choice(debuffSkills)
            target = random.choice(targetParty) 
            return skill["id"], target
        
        elif dmgSkills and random.random() < chance:
            skill = random.choice(dmgSkills)
            if skill["target"] == "all" or skill["target"] == "multiple":
                target = targetParty
            else:
                target = random.choice(targetParty)
            return skill["id"], target
        
        else: # Default behavior: attack a random target
            skill = "None"
            target = random.choice(targetParty)
            return skill, target

class EnemyParty:
    def __init__(self, enemyList):
        self.enemyMembers = [Enemy(data) for data in enemyList]
        self.exp = sum(enemy.exp for enemy in self.enemyMembers)
        self.money = sum(enemy.money for enemy in self.enemyMembers)
        self.key_item = []
        self.key_item.extend(item for enemy in self.enemyMembers if enemy.key_item for item in enemy.key_item)
        self.passive_skills = {}

    def is_defeated(self):
        return all(not enemy.is_alive() for enemy in self.enemyMembers)
    
    def get_alive_members(self):
        return [enemy for enemy in self.enemyMembers if enemy.is_alive()]
    
    def update(self): #update the list when someone die
        self.enemyMembers = [enemy for enemy in self.enemyMembers if enemy.is_alive()]

    def display(self):
        for i, enemy in enumerate(self.enemyMembers):
            buffs = " ".join([
                formatBuff("atk", enemy.buff_atk),
                formatBuff("def", enemy.buff_def),
                formatBuff("agi", enemy.buff_agi)
            ])
            status = f"{enemy.name} | HP: {enemy.hp}/{enemy.maxHP} | {buffs}"
            print(f"{i+1}. {status}")

    def choose_random(self): #for random hits skill
        alive = self.get_alive_members()
        return random.choice(alive) if alive else None
    
def loadEnemies(areaID):
    with open("json/enemies.json", "r") as f:
        allEnemies = json.load(f)
    return [e for e in allEnemies if areaID in e.get("areaIDs", [])]