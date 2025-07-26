from saver import save, load, update
from others import  clear, draw
import json, math

class PartyMember:
    def __init__(self, name = "Hero", id = "h001", lvl = 1, exp = 0, hp = 20, mp = 10, vit = 1, mind = 1, 
                 st = 1, dex = 1, mag = 1, arc = 1, agi = 1, weapon = None, side = None, **kwags):
        self.name = name
        self.id = id
        self.lvl = lvl
        self.exp = exp
        self.expRequired = (50 * (self.lvl ** 2)) * (0.9 + (math.log10(self.lvl)/10))
        self.hp = hp
        self.maxHP = kwags.get("maxHP", hp)
        self.mp = mp
        self.maxMP = kwags.get("maxMP", mp)
        self.weak = kwags.get("weak", []) 
        self.resist = kwags.get("resist", [])
        self.block = kwags.get("block", [])
        self.absorb = kwags.get("absorb", [])
        self.vit = vit
        self.mind = mind
        self.st = st
        self.dex = dex
        self.mag = mag
        self.arc = arc
        self.agi = agi
        self.skills = kwags.get("skill", [])
        if not self.skills:
            self.default_skills()

        self.buff_atk = 0
        self.buff_def = 0
        self.buff_agi = 0
        self.buffDurations = {
            "atk" : 0,
            "def" : 0,
            "agi" : 0
        }

        self.weaponData = {}
        self.sideData = {}
        self.weaponID, self.weapon = self.resolve_item(weapon, lambda wid: self.get_item(wid, "weapons.json", "weaponData"))
        self.sideID, self.side = self.resolve_item(side, lambda sid: self.get_item(sid, "sidearm.json", "sideData"))
        self.baseATK = self.weapon["baseATK"] if self.weapon else 1
        if isinstance(self.side, dict):
            self.sideSkills = self.side.get("effect", {}).get("skill", [])
        else:
            self.sideSkills = None

        self.stats = {}
        self.update_stats()
        self.baseStats = self.stats.copy()
        self.tempStats = self.baseStats.copy()

        self.statProgression = kwags.get("statProgression", {})
        self.rank = kwags.get("rank", 0)

    def rank_up(self):
        with open("json/ranks.json") as f:
            rewards_data = json.load(f)

        self.rank += 1
        rank = f"r{self.rank:03}"
        rewards = rewards_data.get(self.id).get(rank)

        if rewards:
            new_skills = rewards.get("skills", [])
            print(new_skills)
            self.skills.extend(skill for skill in new_skills if skill not in self.skills)

    def resolve_item(self, item, get_func):
        if isinstance(item, dict):
            itemDATA = item
            itemID = item.get("id", None)
        else:
            itemID = item
            itemDATA = get_func(itemID)
        return itemID, itemDATA
        
    def get_item(self, itemID, p, targetAttr):
        if not itemID:
            return None
        
        path = "json/items/" + p
        with open(path) as f:
            setattr(self, targetAttr, json.load(f))
        return getattr(self, targetAttr).get(itemID, None)

    def level_up(self):
        tallyHP = 2
        tallyMP = 1
        self.maxHP += tallyHP
        self.maxMP += tallyMP
        clear()
        draw()
        print(f">> {self.name} leveled up to level {self.lvl}!")
        gains = self.statProgression.get(str(self.lvl), {})
        vit = self.vit + gains.get("vit", 0)
        mind = self.mind + gains.get("mind", 0)

        if "vit" in gains:
            bonus = math.ceil(math.sqrt(vit + self.lvl)*1.5)
            self.maxHP +=  bonus
            tallyHP += bonus

        if "mind" in gains:
            bonus = math.ceil(math.sqrt(mind + self.lvl)*1.2)
            self.maxMP +=  bonus
            tallyMP += bonus

        print(f">> HP: {self.maxHP - tallyHP} -> {self.maxHP}")
        print(f">> MP: {self.maxMP - tallyMP} -> {self.maxMP}")

        for stat, value in gains.items():
            if hasattr(self, stat):
                setattr(self, stat, getattr(self, stat) + value)
                print(f">> {stat.upper()}: {getattr(self, stat) - value} -> {getattr(self, stat)}")

        self.update_stats()
        self.get_skills()
        input(">> ")
       
        if self.id == "h001":
            clear()
            draw()
            print("Please choose a stat to increase:")
            print(f"1. Vitality | {self.vit} -> {self.vit + 1}")
            print(f"2. Mind | {self.mind} -> {self.mind + 1}")
            print(f"3. Strength | {self.st} -> {self.st + 1}")
            print(f"4. Dexterity | {self.dex} -> {self.dex + 1}")
            print(f"5. Magic | {self.mag} -> {self.mag + 1}")
            print(f"6. Arcane | {self.arc} -> {self.arc + 1}")
            print(f"7. Agility | {self.agi} -> {self.agi + 1}")
            draw()
            stat = input(">> ")
            if stat == "1":
                self.vit += 1
                bonus = math.ceil(math.sqrt(self.vit + self.lvl)*1.5)
                self.maxHP += bonus
                print(">> Vitality increased!")
                print(f">> Hp is increased by {bonus}!")
            elif stat == "2":
                self.mind += 1
                bonus = math.ceil(math.sqrt(self.mind + self.lvl)*1.2)
                self.maxMP += bonus
                print(">> Mind increased!")
                print(f">> Mp is increased by {bonus}!")
            elif stat == "3":
                self.st += 1
                print(">> Strength increased!")
            elif stat == "4":
                self.dex += 1
                print(">> Dexterity increased!")
            elif stat == "5":
                self.mag += 1
                print(">> Magic increased!")
            elif stat == "6":
                self.arc += 1
                print(">> Arcane increased!")
            elif stat == "7": #update this 
                self.agi += 1
                print(">> Agility increased!")

            self.get_skills()
            self.update_stats()  # Update stats after leveling up
            input(">> ")

    def reset_stat(self):
        self.tempStats = self.baseStats.copy()

    def modify_stat(self, statName, stage, type):
        multipliers = {
            2 :  {"atk": 1.4, "def": 0.7, "hit": 1.2, "eva": 0.85},
            1 :  {"atk": 1.2, "def": 0.8, "hit": 1.1, "eva": 0.9},
            0 :  {"atk": 1,   "def": 1,   "hit": 1,   "eva": 1},
            -1 : {"atk": 0.8, "def": 1.2, "hit": 0.9, "eva": 1.1},
            -2 : {"atk": 0.7, "def": 1.4, "hit": 0.8, "eva": 1.2},
        }
        stage = max(-2, min(stage ,2)) # -2 to 2
        baseValue = self.baseStats.get(statName, 0)
        multiplier = multipliers[stage][type]
        self.tempStats[statName] = math.ceil(baseValue * multiplier)
    
    def update_durations(self):
        for stat in ["atk", "def", "agi"]:
            if self.buffDurations[stat] > 0:
                self.buffDurations[stat] -= 1
                if self.buffDurations[stat] == 0:
                    setattr(self, f"buff_{stat}", 0)
        
        # refresh existing buffs
        self.tempStats = self.baseStats.copy()
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

    def update_stats(self):
        # This to solve Load issue
        self.maxHP = self.maxHP or self.hp
        self.maxMP = self.maxMP or self.mp
        # This will update the stats every time the party member is created or updated
        stats = update(self.__dict__)  # Pass the current attributes to update function
        self.stats = stats["stats"]

    def default_skills(self):
        with open("json/skilltree.json", "r") as f:
            skillTree = json.load(f)

        if self.id in skillTree:
            tree = skillTree.get(self.id, {})
            for lvl in range(1, self.lvl+1):
                skills = tree.get(str(lvl), [])
                for skill in skills:
                    if skill not in self.skills:
                        self.skills.append(skill)

    def get_skills(self):
        with open("json/skilltree.json", "r") as f:
            skillTree = json.load(f)

        tree = skillTree.get(self.id, {})
        newSkills = tree.get(str(self.lvl), [])
        for skillID in newSkills:
            if skillID not in self.skills:
                self.skills.append(skillID)

                with open("json/skills.json", "r") as f:
                    skills = json.load(f)
                
                    skill = skills.get(skillID, None)
                draw()
                print(f">> {self.name} learned {skill["name"]}!")

    def take_physical_damage(self, base_dmg):
        dmg = math.ceil(base_dmg * (1 - (self.stats["defP"]/100)))
        reduced = max(dmg, 1)
        self.hp = max(self.hp - reduced, 0)
        return reduced

    def take_magic_damage(self, base_dmg):
        dmg = math.ceil(base_dmg * (1 - (self.stats["defP"]/100)))
        reduced = max(dmg, 1)
        self.hp = max(self.hp - reduced, 0)
        return reduced
    
    def to_dict(self):
        return {
            "name": self.name,
            "id": self.id,
            "lvl": self.lvl,
            "exp": self.exp,
            "hp": self.hp,
            "mp": self.mp,
            "maxHP": self.maxHP,
            "maxMP": self.maxMP,
            "atk": self.baseATK,
            "vit": self.vit,
            "mind": self.mind,
            "st": self.st,
            "dex": self.dex,
            "mag": self.mag,
            "arc": self.arc,
            "agi": self.agi,
            "weapon": self.weaponID,
            "side" : self.sideID,
            "skills": self.skills,
            "statProgression": self.statProgression,
            "rank": self.rank,
        }

# Party class to handle all members
class Party:
    def __init__(self):
        self.members = []  # List of party members
        self.money = 0
        self.weapons = {}
        self.sides = {}
        self.equipment = {
            "weapon" : self.weapons,
            "side" : self.sides 
        }
        self.itemFiles = {
            "weapon": "weapons.json",
            "side" : "sidearm.json"
        }
        self.inventory = {
            "hp001" : {"quantity": 1},
        }
        self.key_item = []
        self.passive_skills = {}
        self.days = 1
        self.moons = 1
        self.npcs = {}
    
    def display_items(self):
        with open("json/items/consumables.json") as f:
            itemData = json.load(f)

        itemlist = []
        itemEffect = []
        for i, (itemID, item) in enumerate(self.inventory.items(), 1):
            if item["quantity"] > 0:
                data = itemData.get(itemID, None)
                print(f"{i}. {data["name"]} {item['quantity']}x | {data["description"]}")
                itemlist.append(itemID)
                itemEffect.append(data["effect"])
        
        if itemlist:
            print("0. Back")
            return itemlist, itemEffect
        else:
            print("No items available.")
            print("0. Back")
            return [], []
    
    def display_keys(self):
        with open("json/items/key.json") as f:
            key_data = json.load(f)

        for i, key_ID in enumerate(self.key_item, 1):
            key_info = key_data.get(key_ID, None)
            print(f"{i}. {key_info["name"]} | {key_info["description"]}")

    def use_item(self, itemID, user):
        member = self.get(user)
        item = self.inventory.get(itemID)
        if item and item["quantity"] > 0:
            with open("json/items/consumables.json") as f:
                itemData = json.load(f)
            data = itemData.get(itemID, None)
            if data:
                effect = data.get("effect", {})
                print(f">> {member.name} used {data["name"]}!")
                if "hp" in effect:
                    member.hp = min(member.maxHP, member.hp + effect["hp"])
                    input(f">> HP restored to {member.hp}.")
                if "mp" in effect:
                    member.mp = min(member.maxMP, member.mp + effect["mp"])
                    input(f">> MP restored to {member.mp}.")
                #add other effects here
                item["quantity"] -= 1

    def add_equip(self, itemID, user = None, type = "weapon"):
        storage = self.equipment[type]

        if itemID in storage:
            storage[itemID]["quantity"] += 1
        else:
            storage[itemID] = {"quantity": 1, "equipped": []}
            if user and user not in storage[itemID]["equipped"]:
                storage[itemID]["equipped"].append(user)
    
    def display_equip(self, user, type = "weapon"):
        member = self.get(user)
        storage = self.equipment[type]
        file = self.itemFiles[type]
        path = "json/items/" + file
        name = f"{type.capitalize()}arm" if type == "side" else f"{type.capitalize()}"
        print(f"Available {name}s for {user}:")
        with open(path) as f:
            itemData = json.load(f)

        itemList = []
        i = 1
        for itemID, item in storage.items():
            if item["quantity"] > 0 and member.name not in item["equipped"]:
                data = itemData.get(itemID, None)
                if data is not None:
                    equipped = (", ".join(item["equipped"]) if item["equipped"] else "None")
                    print(f"{i}. {data['name']} {item['quantity']}x | ATK: {data['baseATK']} | EQP: {equipped}")
                    itemList.append(itemID)
                    i += 1

        print("0. Back" if itemList else f"No {name} available.\n0. Back")
        return itemList

    def eqp_equip(self, itemID, user, type = "weapon"):
        member = self.get(user)
        storage = self.equipment[type]
        file = self.itemFiles[type]
        itemAttr = f"{type}Data"

        if itemID != getattr(member, f"{type}ID") and len(storage[itemID]["equipped"]) >= storage[itemID]["quantity"]:
            print(f">> Not enough {type} available.")
            input(">> ")
            return
        
        else:
            #unequip previous weapon
            prevID = getattr(member, f"{type}ID")
            if prevID:
                prev = storage.get(prevID)
                if prev and user in prev["equipped"]:
                    prev["equipped"].remove(user)
                    
            setattr(member, f"{type}ID", itemID)
            itemDATA = member.get_item(itemID, file, itemAttr)
            setattr(member, type, itemDATA)

            if type == "weapon":
                member.baseATK = itemDATA.get("baseATK", 1)
            elif type == "side":
                member.sideSkills = itemDATA.get("effect", {}).get("skill", [])

            if user not in storage[itemID]["equipped"]:
                storage[itemID]["equipped"].append(user)

            member.update_stats()
            print(f">> {user} equipped {itemDATA['name']}!")
            input(">> ")

    def join(self, memberFile, name = None):
        if isinstance(memberFile, PartyMember):
            self.members.append(memberFile)
            if memberFile.weapon:
                self.add_equip(memberFile.weaponID, memberFile.name)

        elif isinstance(memberFile, str) and memberFile.endswith('.json'):
            with open(memberFile, 'r') as f:
                data = json.load(f)
                if name:
                    data["name"] = name
                
                member = PartyMember(**data)
                self.members.append(member)
                if member.weapon:
                    self.add_equip(member.weaponID, member.name)

    def remove(self, name):
        self.members = [member for member in self.members if member.name != name]

    def get(self, name):
        for member in self.members:
            if member.name == name:
                return member
        return None

    def add_item(self, itemID, quantity):
        if itemID in self.inventory:
            self.inventory[itemID]["quantity"] += quantity
        else:
            self.inventory[itemID] = {"quantity": quantity}

    def add_key(self, newKey):
        if isinstance(newKey, list):
            for keyID in newKey:
                if keyID not in self.key_item:
                    self.key_item.append(keyID)
        else:
            if newKey not in self.key_item:
                self.key_item.append(newKey)

    def update_party(self, money = None, newKey = None, newItem = None, newWeapon = None, weaponType = None, qty = 1, days = None, moons = None):
        if money is not None:
            self.money += money

        if newItem is not None:
            self.add_item(newItem, qty)

        if newWeapon is not None:
            self.add_equip(newWeapon) if weaponType == None else self.add_equip(newWeapon, type = weaponType)

        if days is not None:
            self.days += days

        if moons is not None:
            self.moons += moons

        if newKey is not None:
            self.add_key(newKey)

    def save_party(self):
        # Convert members to dictionaries for saving
        party_data = [member.to_dict() for member in self.members]
        save(party_data, self.money, self.weapons, self.sides, self.inventory, self.key_item, self.days, self.moons, self.npcs)  # Call save function

    def load_party(self):
        # Load the game data
        game_data = load()
        if game_data:
            party_data, money, weapons, sides, inventory, key_item, days, moons, npcs = game_data
            self.members = [PartyMember(**member_data) for member_data in party_data]
            self.money = money
            self.weapons = weapons
            self.sides = sides
            self.inventory = inventory
            self.key_item = key_item
            self.days = days
            self.moons = moons
            self.npcs = npcs
            return True
        return False