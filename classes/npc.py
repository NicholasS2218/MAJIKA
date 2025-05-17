import json
from others import draw, clear
class NPC:
    def __init__(self, id, data):
        self.id = id
        self.name = data.get("name", "???")
        self.altName = data.get("alt-name", "???")
        self.type = data.get("type", "NPC")
        self.data = data
    
    def appear(self, days):
        return self.data.get("appear", 0) <= days

    def talk(self, myParty):
        state = myParty.npcs.setdefault(self.id, {
            "encounter" : 0,
            "refusal" : False,
            "name" : False
        })
        
        displayName = self.altName if state["name"] else self.name
        nameUpdate = None
        encounterID = state["encounter"]
        maxMoons = myParty.moons if myParty else encounterID

        for i in range(encounterID, maxMoons + 1):
            key = f"moon{i:03}"
            encounter = self.data.get(key)

            if not encounter:
                continue

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
                    for i, key in enumerate(options, 1):
                        print(f"{i}. {key}")
                    
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
                                    self.show_inventory(items, myParty, "weapons")
                                elif response == "SHOW_SIDES" and isinstance(self, Merchant):
                                    clear()
                                    items = encounter.get("inventoryS", [])
                                    self.show_inventory(items, myParty, "sidearm")
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
                                    elif isinstance(line, str) and line.startswith("UPDATE_NAME:"):
                                        nameUpdate = line.replace("UPDATE_NAME:", "").strip() #for in game update
                                        state["name"] = True #for next time
                                    elif line == "REFUSAL":
                                        state["refusal"] = True
                                    else:
                                        input(f">> {line}")

                            if nameUpdate:
                                displayName = nameUpdate

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
    
    def show_inventory(self, items, myParty, t):
        if not items:
            print(f"{self.name}:")
            input(">> ... I have nothing to sell.")
            return

        print(f"{self.name}'s Shop")
        draw()
        self.display_items(items, myParty, t)
        draw()

    def display_items(self, items, myParty, t):
        path = f"json/items/" + t + ".json"
        with open(path) as f:
                itemData = json.load(f)

        priceList = []
        for i, itemID in enumerate(items, 1):
            data = itemData.get(itemID, None)
            print(f"{i}. {data['name']} | {data['description']} | PRICE: {data['buy']}G")
            priceList.append(data["buy"])
        if items:
            print("0. Back")
        draw()

        while True:
            choice = input(">> " )
            if choice.isdigit():
                choiceINT = int(choice)
                if 1 <= choiceINT <= len(items):
                    itemID = items[choiceINT - 1]
                    price = priceList[choiceINT - 1]
                    self.buy_items(itemID, price, myParty, t)
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