import json, math
path = "json/saveData.json"

def update(member):
    name = member.get("name", "Hero")
    lvl = member.get("lvl", 1)
    exp = member.get("exp", 0)
    expRequired = member.get("expRequired", ((50 * (lvl ** 2)) * (0.9 + (math.log10(lvl)/10))))
    
    hp = member.get("hp", 20)
    maxHP = member.get("maxHP", 20)
    mp = member.get("mp", 10)
    maxMP = member.get("maxMP", 10)

    vit = member.get("vit", 1)
    mind = member.get("mind", 1)
    st = member.get("st", 1)
    dex = member.get("dex", 1)
    mag = member.get("mag", 1)
    arc = member.get("arc", 1)
    agi = member.get("agi", 1)

    atk = member.get("baseATK", 1) * (1 + (((lvl + st + dex) / (2 + math.log10(lvl)))/100)) #1.5 - 50
    skillP = math.sqrt((lvl*2/3) + ((st + dex)/1.5)) + 10 # 11.4% - 21.54%
    skillM = math.sqrt((lvl*2/3) + mag) + 10 # 10.8% - 28.11%
    defP = (lvl + math.ceil(math.sqrt(vit))) / 3
    defM = (lvl + math.ceil(math.sqrt(mind))) / 3
    defA = (lvl + math.ceil(math.sqrt(arc))) / 3
    critChance = 20 + math.ceil(math.sqrt(agi) * 2)  # 22%–40%
    dodgeChance = 10 + math.ceil(math.sqrt(agi) / 0.7) # 12%–25%

    member["stats"] = {
        "name": name,
        "lvl": lvl,
        "exp": exp,
        "expRequired": expRequired,
        "hp": hp,
        "maxHP": maxHP,
        "mp": mp,
        "maxMP": maxMP,
        "atk": atk,
        "skills": member.get("skills", []),
        "skillP": skillP,
        "skillM": skillM,
        "defP": defP,
        "defM": defM,
        "defA": defA,
        "critChance": critChance,
        "dodgeChance": dodgeChance,
    }

    return member


def save(party, money, weapons, sides, inventory, key_item, days, moons, npcs):
    for member in party:
        if "stats" in member:
            member.pop("stats", None)  # Remove stats from member before saving

    data = {
        "party": party,
        "money": money,
        "weapons": weapons,
        "sides": sides,
        "inventory": inventory,
        "key_item" : key_item,
        "days": days,
        "moons": moons,
        "npcs" : npcs
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

def load():
    try:
        with open(path, "r") as f:
            data = json.load(f)
        
        party = data.get("party", [])
        money = data.get("money", 0)
        weapons = data.get("weapons", {})
        sides = data.get("sides", {})
        inventory = data.get("inventory", {})
        key_item = data.get("key_item", [])
        days = data.get("days", 1)
        moons = data.get("moons", 1)
        npcs = data.get("npcs", {})

        for member in party:
            update(member)

        print("Game loaded successfully!")
        return party, money, weapons, sides, inventory, key_item, days, moons, npcs
        
    except FileNotFoundError:
        print("No save file found.")
        input(">> ")
        return None
    except json.JSONDecodeError:
        print("Save file is corrupted.")
        input(">> ")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        input(">> ")
        return None