import json
from helpers import draw, clear, type_text
class NPC:
    def __init__(self, id, data):
        self.id = id
        self.name = data.get("name", "???")
        self.altName = data.get("alt-name", self.name)
        self.type = data.get("type", "NPC")
        self.data = data
    
    def appear(self, myParty):
        for key, value in self.data.items():
            if key.startswith("event") and isinstance(value, dict):
                condition = value.get("appear_condition", {})
                required_moon = condition.get("moon", 0)
                required_day = condition.get("days", 0)
                
                # Check moon and day condition
                moon_day_met = False
                if myParty.moons > required_moon:
                    moon_day_met = True
                elif myParty.moons == required_moon and myParty.days >= required_day:
                    moon_day_met = True
                
                if not moon_day_met:
                    continue
                
                # Check if previous event is completed
                if "event_prev" in condition:
                    prev_event = condition["event_prev"]
                    state = myParty.npcs.get(self.id, {})
                    # Check if previous event was encountered (encounter count increased past it)
                    prev_index = int(prev_event.replace("event", "")) - 1
                    if state.get("encounter", 0) <= prev_index:
                        continue
                
                # Check if required member is in party
                if "require_member" in condition:
                    required_member = condition["require_member"]
                    has_member = any(m.id == required_member for m in myParty.members)
                    if not has_member:
                        continue
                
                # If all conditions pass, NPC should appear
                return True
    
        return False

    def requirements_check(self, requirements, myParty):
        for req in requirements:
            if isinstance(req, list) and len(req) == 2: #[member_id, rank_id]
                member_id, expected_rank = req
                member = next((m for m in myParty.members if m.id == member_id), None)
                if not member or f"r{member.rank:03}" != expected_rank:
                    return False
                
            elif isinstance(req, str):
                if req.startswith("k"):
                    if req not in myParty.key_item:
                        return False
                else:
                    return False
            else:
                return True
        return True
                
    def talk(self, myParty):
        state = myParty.npcs.setdefault(self.id, {
            "encounter" : 0,
            "refusal" : False,
            "name" : False
        })
        
        displayName = self.altName if state["encounter"] == 0 else self.name
        encounterID = state["encounter"]

        event_count = 0
        for key in self.data.keys():
            if key.startswith("event"):
                event_count += 1

        for i in range(encounterID, event_count):
            event_key = f"event{i+1:03}"
            encounter = self.data.get(event_key)

            if not encounter:
                continue

            condition = encounter.get("appear_condition", {})
            required_moon = condition.get("moon", 0)
            required_day = condition.get("days", 0)

            moon_day_met = False
            if myParty.moons > required_moon:
                moon_day_met = True
            elif myParty.moons == required_moon and myParty.days >= required_day:
                moon_day_met = True
            
            if not moon_day_met:
                continue

            # Check previous event requirement
            if "event_prev" in condition:
                prev_event = condition["event_prev"]
                prev_index = int(prev_event.replace("event", "")) - 1
                if state.get("encounter", 0) <= prev_index:
                    continue
            
            # Check required member
            if "require_member" in condition:
                required_member = condition["require_member"]
                has_member = any(m.id == required_member for m in myParty.members)
                if not has_member:
                    continue
            
            # Check other requirements
            if not self.requirements_check(encounter.get("requirement", []), myParty):
                if "alt_dialogue" in encounter:
                    print(f"{displayName}:")
                    for line in encounter["alt_dialogue"]:
                        type_text(f">> {line}")
                        input()
                return

            print(f"{displayName}:") #dialogue or sub-dialogue from refusal
            if state["refusal"] and "refusal" in encounter["choices"]:
                refusalBLOCK = encounter["choices"]["refusal"]
                for line in refusalBLOCK.get("dialogue"):
                    type_text(f">> {line}")
                    input()
                choices = refusalBLOCK.get("choices")
            
            else:
                if state["encounter"] > i:
                    for line in encounter.get("chat", []):
                        type_text(f">> {line}")
                        input()
                        
                else:
                    for line in encounter.get("dialogue", []): 
                        type_text(f">> {line}")
                        input()
                choices = encounter.get("choices", {})

            if "choices" in encounter: #choices
                mode = choices.get("mode", "answer")
                optionsDICT = choices.get("options", {})
                print()
                while True:
                    print("You:")
                    draw()
                    options = list(optionsDICT.keys()) 
                    for i, choice in enumerate(options, 1):
                        print(f"{i}. {choice}")
                    
                    if mode == "questions":
                        print("0. Nevermind.")

                    draw()
                    select = input(">> ")
                    while not select.isdigit():
                        select = input(">> ")
                    if mode == "questions" and select == "0":
                        break
                    
                    if select.isdigit():
                        selected = int(select) - 1
                        if 0 <= selected <= len(options):
                            clear()
                            playersCHOICE = options[selected]
                            response = optionsDICT[playersCHOICE]
                            print(f"{self.name}: ")
                            if isinstance(response, str):
                                if response == "SHOW_INVENTORY" and isinstance(self, Merchant):
                                    clear()
                                    items = encounter.get("inventoryItem", [])
                                    self.show_inventory(items, myParty, "consumables")
                                elif response == "SHOW_WEAPONS" and isinstance(self, Merchant):
                                    clear()
                                    items = encounter.get("inventoryWeapon", [])
                                    extra_items = encounter.get("inventorySidearm", [])
                                    self.show_inventory(items, myParty, "weapons", extra_items, "sidearm")
                                elif response == "SHOW_SPELLS" and isinstance(self, Merchant):
                                    clear()
                                    items = encounter.get("inventorySpell", [])
                                    self.show_inventory(items, myParty, "skills")
                                else:
                                    input(f">> {response}")
                            elif isinstance(response, list):
                                for line in response:
                                    if isinstance(line, str) and line.startswith("JOIN_PARTY:") and myParty:
                                        path = line.replace("JOIN_PARTY:", "").strip()
                                        myParty.join(path)
                                        print(f">> {self.altName} has joined your party!")
                                        input(">> ")
                                        state["refusal"] = False
                                        self.name = self.altName #update name
                                    elif isinstance(line, str) and line.startswith("RANK_UP:"):
                                        member_id = line.replace("RANK_UP:", "").strip()
                                        for member in myParty.members:
                                            if member.id == member_id:
                                                print()
                                                print(f"{member.name.upper()}'s ability expanded!!")
                                                draw()
                                                print(f"{self.name}: ")
                                                member.rank_up()
                                    elif line == "REFUSAL":
                                        state["refusal"] = True
                                    else:
                                        type_text(f">> {line}")
                                        input()

                            if mode != "questions":
                                break
                            clear()
            print()
            if "statements" in encounter:
                print(f"{displayName}:") #statement
                for line in encounter["statements"]: 
                    type_text(f">> {line}")
                    input()

            if not state["refusal"] and state["encounter"] <= i:
                state["encounter"] += 1
            break

class Merchant(NPC):
    def __init__(self, id, data):
        super().__init__(id, data)
    
    def show_inventory(self, items, myParty, t, extra_items = [], p = None):
        if not items:
            type_text(">> ...There is no item left.")
            input()
            return

        print(f"{self.name}'s Shop")
        draw()
        self.display_items(items, myParty, t, extra_items, p)
        draw()

    def display_items(self, items, myParty, t, extra_items = [], p = None):
        itemData = {}

        if t == "skills":
            path = f"json/skills.json"
            
        else:
            path = f"json/items/" + t + ".json"

        with open(path) as f:
            itemData.update(json.load(f))

        if p:
            path = f"json/items/" + p + ".json"
            with open(path) as f:
                itemData.update(json.load(f))

        priceList = []
        indexed_items = []

        # Section 1: Weapons
        print("-- Weapons --")
        for itemID in items:
            data = itemData.get(itemID)
            if not data:
                continue
            index = len(priceList) + 1
            print(f"{index}. {data['name']} | {data['description']} | PRICE: {data['buy']}G")
            priceList.append(data["buy"])
            indexed_items.append((itemID, t))  # Save itemID with its type

        # Section 2: Sidearms
        if extra_items:
            print("\n-- Sidearms --")
            for itemID in extra_items:
                data = itemData.get(itemID)
                if not data:
                    continue
                index = len(priceList) + 1
                print(f"{index}. {data['name']} | {data['description']} | PRICE: {data['buy']}G")
                priceList.append(data["buy"])
                indexed_items.append((itemID, p))  # Save itemID with its type

        if indexed_items:
            print("0. Back")
        draw()

        while True:
            choice = input(">> " )
            if choice.isdigit():
                choiceINT = int(choice)
                if 1 <= choiceINT <= len(indexed_items):
                    (itemID, item_type) = indexed_items[choiceINT - 1]
                    price = priceList[choiceINT - 1]
                    self.buy_items(itemID, price, myParty, item_type)
                    break
                elif choiceINT == 0:
                    break
        
    def buy_items(self, itemID, price, myParty, t):
        print()
        print(f"{self.name}:")
        if myParty.money < price:
            print(">> ..I'm sorry, but, you don't have enough for that.")
            input(">> ")
            return
        if t == "consumables":
            myParty.update_party(money = -price, newItem = itemID)
        elif t == "weapons":
            myParty.update_party(money = -price, newWeapon = itemID)
        elif t == "sidearm":
            myParty.update_party(money = -price, newWeapon = itemID, weaponType = "side")
        elif t == "skills":
            myParty.update_party(money = -price, newSkill = itemID)
        print(">> Thanks for the patronage!!")
        input(">> ")

def load_npcs(file):
    with open(file, "r") as f:
        data = json.load(f)
    
    npcs = {}
    for npcID , npcDATA in data.items():
        if npcDATA.get("type") == "Merchant":
            npcs[npcID] = Merchant(npcID, npcDATA)
        else:
            npcs[npcID] = NPC(npcID, npcDATA)
    return npcs