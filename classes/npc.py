import json
from others import draw, clear
class NPC:
    def __init__(self, id, data):
        self.id = id
        self.name = data.get("name", "???")
        self.altName = data.get("alt-name", self.name)
        self.type = data.get("type", "NPC")
        self.data = data
    
    def appear(self, days):
        return self.data.get("appear", 0) <= days

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
        
        moon_ID = "moon000"
        displayName = self.altName if state["encounter"] == 0 else self.name
        encounterID = state["encounter"]
        maxMoons = myParty.moons if myParty else encounterID

        for i in range(encounterID, maxMoons + 1):
            moon_ID = f"moon{i:03}"
            encounter = self.data.get(moon_ID)

            if not encounter:
                continue

            if not self.requirements_check(encounter.get("requirement", []), myParty):
                if "alt_dialogue" in encounter:
                    print(f"{displayName}:")
                    for line in encounter["alt_dialogue"]:
                        input(f">> {line}")
                return

            print(f"{displayName}:") #dialogue or sub-dialogue from refusal
            if state["refusal"] and "refusal" in encounter["choices"]:
                refusalBLOCK = encounter["choices"]["refusal"]
                for line in refusalBLOCK.get("dialogue"):
                    input(f">> {line}")
                choices = refusalBLOCK.get("choices")
            
            else:
                if encounterID == maxMoons:
                    for line in encounter["chat"]:
                        input(f">> {line}")
                        
                else:
                    for line in encounter["dialogue"]: 
                        input(f">> {line}")
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
                                    items = encounter.get("inventoryI", [])
                                    self.show_inventory(items, myParty, "consumables")
                                elif response == "SHOW_WEAPONS" and isinstance(self, Merchant):
                                    clear()
                                    items = encounter.get("inventoryW", [])
                                    extra_items = encounter.get("inventoryS", [])
                                    self.show_inventory(items, myParty, "weapons", extra_items, "sidearm")
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
                                        input(f">> {line}")

                            if mode != "questions":
                                break
                            clear()
            print()
            if "statements" in encounter:
                print(f"{displayName}:") #statement
                for line in encounter["statements"]: 
                    input(f">> {line}")

            if not state["refusal"] and encounterID < myParty.moons:
                state["encounter"] += 1
            break

class Merchant(NPC):
    def __init__(self, id, data):
        super().__init__(id, data)
    
    def show_inventory(self, items, myParty, t, extra_items = [], p = None):
        if not items:
            print(f"{self.name}:")
            input(">> ... I have nothing to sell.")
            return

        print(f"{self.name}'s Shop")
        draw()
        self.display_items(items, myParty, t, extra_items, p)
        draw()

    def display_items(self, items, myParty, t, extra_items = [], p = None):
        itemData = {}
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