import json
from helpers import draw, clear, type_text
class NPC:
    def __init__(self, id, data):
        self.id = id
        self.name = data.get("name", "???")
        # self.altName = data.get("alt-name", self.name)
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
  
    def get_dialogue_data(self, myParty):
        state = myParty.npcs.setdefault(self.id, {
            "encounter": 0,
            "refusal": False,
            "name": False
        })
        
        displayName = self.name
        event_count = sum(1 for key in self.data.keys() if key.startswith("event"))
        
        for i in range(event_count):
            event_key = f"event{i+1:03}"
            encounter = self.data.get(event_key)

            if state.get(f"{event_key}_done") and encounter.get("occurance") == 1:
                continue
            
            if not encounter:
                continue
            
            # Check conditions
            condition = encounter.get("appear_condition", {})
            required_moon = condition.get("moon", 0)
            required_day = condition.get("days", 0)
            
            moon_day_met = (myParty.moons > required_moon or 
                        (myParty.moons == required_moon and myParty.days >= required_day))
            
            if not moon_day_met:
                continue
            
            # Get dialogue text
            if state["refusal"] and "refusal" in encounter.get("choices", {}):
                refusalBLOCK = encounter["choices"]["refusal"]
                dialogue_text = refusalBLOCK.get("dialogue", [])
            elif state["encounter"] > i:
                dialogue_text = encounter.get("chat", [])
                if not dialogue_text:
                    dialogue_text = encounter.get("dialogue", [])
            else:
                dialogue_text = encounter.get("dialogue", [])
            
            if not dialogue_text:
                continue
            
            lines = [(displayName, line) for line in dialogue_text]
            
            # Get choices if available
            choices = None
            choice_mode = "answer"
            if "choices" in encounter:
                if state["encounter"] <= i or state.get("refusal", False):
                    if state["refusal"] and "refusal" in encounter["choices"]:
                        choices_data = encounter["choices"]["refusal"].get("choices", {})
                    else:
                        choices_data = encounter.get("choices", {})

                elif encounter.get("chat") and encounter["choices"].get("mode") == "questions":
                    choices_data = encounter.get("choices", {})
                    
                choice_mode = choices_data.get("mode", "answer")
                options = choices_data.get("options", {})
                choices = list(options.keys())

                if choice_mode == "questions":
                    choices.append("Nevermind")
            
            return {
                "speaker": displayName,
                "lines": lines,
                "choices": choices,
                "choice_mode": choice_mode,
                "encounter": encounter,
                "event_index": i,
                "is_new": state["encounter"] == i
            }
        
        # No valid event found
        return {
            "speaker": displayName,
            "lines": [(displayName, "...")],
            "choices": None,
            "choice_mode": "answer",
            "encounter": None,
            "event_index": -1,
            "is_new": False
        }

    def process_choice(self, choice_text, myParty):
        # Handle "Nevermind" for questions mode
        if choice_text == "Nevermind":
            return [], False, True  # End dialogue
        
        dialogue_data = self.get_dialogue_data(myParty)
        encounter = dialogue_data["encounter"]
        
        if not encounter or not dialogue_data["choices"]:
            return [], False, True
        
        state = myParty.npcs.get(self.id, {})
        
        # Get options from the right place (refusal or normal)
        if state.get("refusal") and "refusal" in encounter.get("choices", {}):
            options = encounter["choices"]["refusal"].get("choices", {}).get("options", {})
        else:
            options = encounter.get("choices", {}).get("options", {})
        
        response = options.get(choice_text)
        is_questions_mode = dialogue_data["choice_mode"] == "questions"
        
        # Handle Merchant special responses
        if isinstance(self, Merchant) and isinstance(response, str):
            if response == "SHOW_INVENTORY":
                items = encounter.get("inventoryItem", [])
                return [("MERCHANT_SHOP", "consumables", items)], False, False
            elif response == "SHOW_WEAPONS":
                items = encounter.get("inventoryWeapon", [])
                extra_items = encounter.get("inventorySidearm", [])
                return [("MERCHANT_SHOP", "weapons", items, extra_items)], False, False
            elif response == "SHOW_SPELLS":
                items = encounter.get("inventorySpell", [])
                return [("MERCHANT_SHOP", "skills", items)], False, False
        
        if isinstance(response, str):
            return [(self.name, response)], is_questions_mode, False
        
        elif isinstance(response, list):
            result_lines = []
            should_end = False
            
            for line in response:
                if isinstance(line, str):
                    if line.startswith("JOIN_PARTY:"):
                        path = line.replace("JOIN_PARTY:", "").strip()
                        if not path.startswith("json/"):
                            path = "json/" + path
                        myParty.join(path)
                        result_lines.append((self.name, f"{self.name} has joined your party!"))
                        state["refusal"] = False
                        
                    elif line.startswith("UPDATE_NAME:"):
                        new_name = line.replace("UPDATE_NAME:", "").strip()
                        self.name = new_name
                        
                    elif line.startswith("RANK_UP:"):
                        member_id = line.replace("RANK_UP:", "").strip()
                        for member in myParty.members:
                            if member.id == member_id:
                                result_lines.append((self.name, f"{member.name.upper()}'s ability expanded!!"))
                                member.rank_up()
                                
                    elif line == "REFUSAL":
                        state["refusal"] = True
                    
                    
                    elif line == "END":
                        should_end = True

                    else:
                        result_lines.append((self.name, line))

            keep_choices = is_questions_mode and not should_end
            return result_lines, keep_choices, should_end
       
        return [], False, True
    
    def mark_event_complete(self, myParty, event_index):
        state = myParty.npcs.get(self.id, {})
        event_key = f"event{event_index+1:03}"
        
        if self.data.get(event_key, {}).get("occurance") == 1:
            state[f"{event_key}_done"] = True

        if state.get("encounter", 0) <= event_index and not state.get("refusal", False):
            state["encounter"] = event_index + 1

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