import random, math, json
from battles import battle
from helpers import clear, draw

class Floor:
    def __init__(self, num, doors):
        self.num = num
        self.doors = doors

class Tower:
    def __init__(self, myParty, total = 6):
        self.myParty = myParty
        self.current = 1
        self.total = total
        self.floors = {}
        self.generate_floors()         

    def generate_floors(self):
        print("Entering the Tower...")
        for i in range(1, self.total + 1):
            if i == self.total:
                door = 1
            else:
                door = random.choices([2, 3], weights=[80, 20])[0]
        
            if door == 1:
                labels = ["Go Forward"]
            elif door == 2:
                labels = ["Go Left", "Go Right"]
            else:
                labels = ["Go Left", "Go Forward", "Go Right"]

            floorType = [self.floor_battle]
            for _ in range(door - 1):
                floorType.append(random.choice([self.floor_heal, self.floor_treasure, self.floor_battle]))

            random.shuffle(floorType)
            doors = dict(zip(labels, floorType))
            self.floors[i] = Floor(i, doors)

    def floor_battle(self, party, state = None):
        areaID = "a" + str(min(party.moons, 3)).zfill(3)
        result = battle(party, areaID, state)
        if result == "defeated":
            return result
        else:
            return "victory"
    
    def floor_heal(self, party):
        print(">> The room seems safe enough for the party to rest for a while.")
        print(">> Do you want to rest? (Y/N)")
        draw()
        ambushRate = 20
        while True:
            answer = input(">> ").upper()
            if answer == "Y":
                print()
                input("...")
                if random.randint(1, 100) <= ambushRate:
                    input(">> AMBUSHED!!!")
                    return self.floor_battle(party, state = "a")
                
                for member in party.members:
                    member.hp = min(member.maxHP, member.hp + math.ceil(member.maxHP*0.2))
                    member.mp = min(member.maxMP, member.mp + math.ceil(member.maxMP*0.2))
                ambushRate += 30

                input("The party rested for a while.")
                print("Seems like you can rest for a while longer.")
                print(">> Do you want to rest? (Y/N)")
                draw()
            elif answer == "N":
                break
        return "healed"
    
    def floor_treasure(self, party): #update this later with the moons
        print(">> You found a treasure room!")
        input(">> The party decided to search the room!")

        print()
        input("...")
        loot = random.choices(["money", "item", "nothing", "fight"], weights=[37, 37, 16, 10], k = 1)[0]
        if loot == "money":
            amount = random.randint(2, 5) * 50
            party.update_party(money = amount)
            print(f">> You found {amount} gold!")
        elif loot == "item":
            with open("json/items/consumables.json") as f:
                items = json.load(f)
            r1 = [key for key, item in items.items() if item.get("rarity") == 1]
            r2 = [key for key, item in items.items() if item.get("rarity") == 2]
            rarity = random.choices([1, 2], weights = [80, 20], k = 1)[0]
            if rarity == 1 and r1:
                itemID = random.choice(r1)
            elif rarity == 2 and r2:
                itemID = random.choice(r2)

            item = items[itemID]
            party.update_party(newItem = itemID)
            print(f">> You found {item['name']}!")
        elif loot == "nothing":
            print(f">> Seems like there's nothing worth left.")
        else:
            input(">> AMBUSHED!!!")
            return self.floor_battle(party, state = "a")
        input(">> ")
        return "treasure"
    
    def enter_floor(self):
        while self.current <= self.total:
            floor = self.floors[self.current]
            if self.current == 1:
                input(f">> Current Floor: {self.current}")
                result = self.floor_battle(self.myParty)
                if result == "defeated":
                    return result
            clear()
            print("Choose which way to proceed: ")
            for i, (label, func) in enumerate(floor.doors.items(), 1):
                roomName = func.__name__.replace("floor_", "").upper()
                print(f"{i}. {label} | {roomName}")
            draw()
            
            while True:
                choice = input(">> ")
                if choice.isdigit():
                    door_action = list(floor.doors.values())[int(choice) - 1]
                    break
            
            print()
            result = door_action(self.myParty)
            self.current += 1
            if result == "defeated":
                return result

            clear()
            print(f">> Traversing...")
            input(f">> Current Floor: {self.current}")
            draw()
            
            if self.current > self.total:
                #Add merchant here
                clear()
                print("You have reached the top!")
                print("And there lies the final battle of this trial..")
                result = battle(self.myParty, "ab001")
                if result == "defeated":
                    return result
                else:
                    print("Congratulations on Finishing the Demo!!")
                    print("You can keep playing for now with a higher difficulty!")  