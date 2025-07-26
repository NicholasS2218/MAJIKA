import math
from battles import skillInfo
from others import clear, draw
from classes.party import Party
from classes.tower import Tower
from classes.npc import*

run = True
mainMenu = True
play = False
rules = False
fight = False

while run:
    while mainMenu:
        clear()
        print("Welcome to MAJIKA!")
        print("1. New Game")
        print("2. Load Game")
        print("3. Manual")
        print("0. Exit")
        draw()

        if rules:
            print()
            print("Game rules:")
            input("1. This is a simple turn-based roguelite game.")
            input("2. Player's Stats have different purposes:")
            input(">> Vitality (VIT) and Mind (MIND) is for HP and MP")
            input(">> Strength (ST) and Dexterity (DEX) is for physical attacks")
            input(">> Magic (MAG) and Arcane (ARC) is for magic attacks.")
            input(">> Agility (AGI) is for Crit/Evasion.")
            print("3. Have fun! :) ")

            rules = False
            choice = ""
            draw()
            input(">> ")
        else:
            choice = input(">> ")

        if choice == "1":
            clear()
            myParty = Party()
            playerName = input("Enter your name: ")
            myParty.join("json/playable/Player.json", name = playerName)
            mainMenu = False
            play = True

        elif choice == "2":
            myParty = Party()
            if myParty.load_party():
                clear()
                mainMenu = False
                play = True

        elif choice == "3":
            rules = True

        elif choice == "0":
            print("Exiting the game.")
            quit()
    
    while play:
        clear()
        print(f"Day(s): {myParty.days} | Gold: {myParty.money}G | What do you want to do?")
        draw()
        print("1. Stats")
        print("2. Equipment")
        print("3. Inventory")
        print("4. Talk")
        print("5. Explore the Tower")
        print("0. Exit")
        draw()
        dest = input(">> ")

        if dest == "1":
            clear()
            print("Party Stats:")
            draw()
            i = 1
            for member in myParty.members:
                print(str(i) + ". "+ member.name)
                i += 1
            print("0. Back")
            draw()
            memberInput = input(">> ")
            for i in range(len(myParty.members)):
                if memberInput == str(i+1):
                    clear()
                    me = myParty.members[i]
                    print(f"Name: {me.name} | lvl: {me.stats["lvl"]}")
                    print(f"To next lvl: {math.ceil(me.stats["exp"])}/{(math.ceil(me.stats["expRequired"]))}")
                    draw()
                    print("STATS:")
                    print(f"HP: {me.stats["hp"]}/{me.stats["maxHP"]}")
                    print(f"MP: {me.stats["mp"]}/{me.stats["maxMP"]}")
                    print(f"ATK: {math.ceil(me.stats["atk"])}")
                    print(f"SKILLP: {math.ceil(me.stats["skillP"])}")
                    print(f"SKILLM: {math.ceil(me.stats["skillM"])}")
                    print(f"PHYS_DEF: {math.ceil(me.stats["defP"])}")
                    print(f"MAG_DEF: {math.ceil(me.stats["defM"])}")
                    print(f"ARC_DEF: {math.ceil(me.stats["defA"])}")
                    draw()
                    print("SKILLS:")
                    for skill in me.skills:
                        skillName = skillInfo(skill)["name"]
                        print(skillName)
                    draw()
                    input(">> ")
                    break
            if memberInput == "0":
                clear()
                continue

        elif dest == "2":
            clear()
            print("Whose Equipment?")
            draw()
            i = 1
            for member in myParty.members:
                print(str(i) + ". "+ member.name)
                i += 1
            print("0. Back")
            draw()
            memberInput = input(">> ")
            for i in range(len(myParty.members)):
                if memberInput == str(i+1):
                    clear()
                    me = myParty.members[i]
                    print(f"Name: {me.name}")
                    print(f"Weapon: {me.weapon['name']} | ATK: {me.weapon['baseATK']}")
                    if me.side:
                        print(f"Sidearm: {me.side['name']} | TYPE: {me.side['element'].upper()}")
                    else:
                        print(f"Sidearm: None")
                    #print(f"Armor: {me.armor["name"]} | DEF: {me.armor["def"]}")
                    #print(f"Accessory: {me.accessory["name"]} | DEF: {me.accessory["def"]}")
                    draw()
                    print("1. Change Equipment")
                    print("0. Back")
                    draw()

                    choice = input(">> ")
                    if choice == "1":
                        print()
                        print("Which Equipment?")
                        draw()
                        print("1. Main Weapon")
                        print("2. Sidearm")
                        print("0. Back")
                        draw()
                        while True:
                            choice = input(">> ")
                            if choice in ("1", "2"):
                                clear()
                                t = "side" if choice == "2" else "weapon" 
                                weapons = myParty.display_equip(me.name, type = t)
                                draw()
                                if weapons:
                                    while True:
                                        choice = input(">> ")
                                        if choice.isdigit():
                                            choiceINT = int(choice)
                                            if 0 < choiceINT <= len(weapons):
                                                clear()
                                                myParty.eqp_equip(weapons[choiceINT - 1], me.name, type = t)
                                                break
                                        elif choice == "0":
                                            break
                            elif choice == "0":
                                break  
                    elif choice == "0":
                        break
                    
        elif dest == "3":
            clear()
            print("Party's Inventory:")
            draw()
            print("1. Consumables")
            if myParty.key_item:
                print("2. Key Items")
            print("0. Back")
            draw()
            while True:
                choice = input(">> ")
                if choice == "1":
                    clear()
                    print("Party's Items:")
                    draw()
                    items, itemsEffect = myParty.display_items()
                    while True:
                        draw()
                        choice = input(">> " )
                        if choice.isdigit():
                            choiceINT = int(choice)
                            if 0 < choiceINT <= len(items):
                                itemID = items[choiceINT - 1]
                                effect = itemsEffect[choiceINT - 1]
                                clear()
                                print(f"On who?")
                                for i, member in enumerate(myParty.members, 1):
                                    if "hp" in effect:
                                        print(f"{i}. {member.name} | HP: {member.hp}/{member.maxHP}")
                                    elif "mp" in effect:
                                        print(f"{i}. {member.name} | MP: {member.mp}/{member.maxMP}")
                                print("0. Back")
                                draw()
                                while True:
                                    memberInput = input(">> ") 
                                    if memberInput.isdigit():
                                        for i in range(len(myParty.members)):
                                            if memberInput == str(i+1):
                                                draw()
                                                member = myParty.members[i]
                                                myParty.use_item(itemID, member.name)
                                        break
                                    elif memberInput == "0":
                                        break   
                                break
                            elif choice == "0":
                                break

                elif choice == "2" and myParty.key_item:
                    clear()
                    print("Party's Key Items:")
                    draw()
                    while True:
                        myParty.display_keys()
                        print("0. Back")
                        draw()
                        back = input(">> ")
                        if back == "0":
                            break
                break

        elif dest == "4": #NPCs go here, blacksmith, item shop, etc
            npcs = load_npcs("json/npcs.json")
            npcsITEMS = list(npcs.items())
            clear()
            appearedNPC = []
            i = 1
            for id, data in npcsITEMS:
                if data.appear(myParty.days):
                    appearedNPC.append((id, data))
            
            if not appearedNPC:
                input(">> ...")
                input(">> No one is here...")
            else:
                print("Talk to who?")
                for _, data in appearedNPC:
                    state = myParty.npcs.setdefault(data.id, {
                        "encounter" : 0,
                        "refusal" : False,
                        "name" : False
                    })
                    
                    displayName = data.altName if state["encounter"] == 0 else data.name
                    print(f"{i}. {displayName}")
                    i += 1
                print("0. Back")
                draw()
                while True:
                    talk = input(">> ")
                    if talk.isdigit():
                        if 1 <= int(talk) <= len(appearedNPC): 
                            selectedID, selectedNPC = appearedNPC[int(talk) - 1]
                            print()
                            selectedNPC.talk(myParty)
                            break
                        elif talk == "0":
                            break

        elif dest == "5":
            print("Enter the Tower? (Y/N)")
            select = input(">> ").upper()
            if select == "Y":
                while True:
                    clear()
                    tower = Tower(myParty)
                    result = tower.enter_floor()
                    if result == "defeated":
                        print(">> You have been defeated!")
                        print(">> You decided to retreat!")
                        input(">> ")
                        for member in myParty.members:
                            member.hp = member.maxHP
                            member.mp = member.maxMP
                        myParty.update_party(days = 1)
                        myParty.save_party()
                    else:
                        for member in myParty.members:
                            member.hp = member.maxHP
                            member.mp = member.maxMP
                        myParty.update_party(days = 1, moons = 1)
                        myParty.save_party()
                    break
            else:
                break

        elif dest == "0":
            play = False
            mainMenu = True
            myParty.save_party()
            print("Game saved successfully!")
            input(">> ")