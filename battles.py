from others import*
from classes.enemy import*
from turns import*
import random, math, json

def header(side, turns, enemyParty = None):
    if side == "a":
        clear()
        draw()
        print("ALLIES TURN! " + showPressTurns(turns))
        enemyParty.display()
        draw()
    elif side == "e":
        clear()
        draw()
        print("ENEMIES TURN! " + showPressTurns(turns))
        draw()

def skillInfo(skillID):
    with open("json/skills.json", "r") as f:
        skills = json.load(f)
    
    return skills.get(skillID, None)

def skillMod(caster, skill, dmg, target, turns, used = None):
    addedHalfTurn = False
    if skill["type"] == "physical":
        if random.random() < caster.tempStats["critChance"]/100:
            dmg *= 1.5  
            print(">> Critical Hit!")
            if not addedHalfTurn:
                addTurn(turns, used)
                addedHalfTurn = True

    if skill["element"] in target.weak:
        dmg *= 2
        print(">> WEAK!!!")
        if not addedHalfTurn:
            addTurn(turns, used)
            addedHalfTurn = True

    elif skill["element"] in target.resist:
        dmg = math.ceil(dmg * 0.5)
        print(">> RESIST!!!")
    elif skill["element"] in target.block:
        dmg = 0
        useTurn(turns)
        print(">> BLOCK!!!")
    elif skill["element"] in target.absorb:
        target.hp = min(target.hp + dmg, target.maxHP)
        dmg = 0
        useTurn(turns)
        print(">> ABSORB!!!") 
    return dmg

def skillDmg(skillID, caster, turns, target, consumeTurn = False):
    if consumeTurn:
        usedTurn = useTurn(turns)

    skill = skillInfo(skillID)
    if skill["type"] == "physical":
        baseDMG = math.ceil((1+(caster.tempStats["skillP"]/100)) * skill.get("base_dmg", 1))
        dmg = skillMod(caster, skill, baseDMG, target, turns, used = usedTurn)
        target.take_physical_damage(dmg)
        return dmg
    
    elif skill["type"] == "magic":
        baseDMG = math.ceil((1+(caster.tempStats["skillM"]/100)) * skill.get("base_dmg", 1))
        dmg = skillMod(caster, skill, baseDMG, target, turns, used = usedTurn)
        target.take_magic_damage(dmg)
        return dmg
    
    elif skill["type"] == "heal": 
        heal = math.ceil((1+(caster.tempStats["skillM"]/100)) * skill.get("base_heal", 1))
        target.hp = min(target.hp + heal, target.maxHP)
        return heal
    
    elif skill["type"] == "buff" or skill["type"] == "debuff":
        if skill["element"] == "def":
            buffStage = target.buff_def
            buffType = "def"
            target.modify_stat("defP", buffStage, buffType)
            target.modify_stat("defM", buffStage, buffType)
            target.modify_stat("defA", buffStage, buffType)

        elif skill["element"] == "agi": #update this
            buffStage = target.buff_agi
            target.modify_stat("dodgeChance", buffStage, "eva")
            target.modify_stat("critChance", buffStage, "hit")
            
        elif skill["element"] == "atk":
            buffStage = target.buff_atk
            buffType = "atk"
            target.modify_stat("atk", buffStage, buffType)
            target.modify_stat("skillP", buffStage, buffType)
            target.modify_stat("skillM", buffStage, buffType)

def result(party, exp, addMoney):
    global fight, play
    party.update_party(money = addMoney) #add money
    for member in party.members:
        member.exp += exp
        member.update_stats()
        while member.exp >= member.expRequired: #update this
            member.lvl += 1
            member.exp -= member.expRequired
            member.expRequired = (50 * (member.lvl ** 2)) * (0.9 + (math.log10(member.lvl)/10))
            member.level_up()

def hit(dodgeChance):
    baseChance = 1
    chance = max(0.0, min(baseChance -  dodgeChance, 1.0)) 
    
    hitRoll = random.random() 
    if hitRoll <= chance:
        return True

def enemyAction(enemy, enemyParty, party, turns):
    global fight, play, mainMenu
    while True:
        header("e", turns)
        aliveMembers = [member for member in party.members if member.hp > 0]
        skillID, target = enemy.behavior(enemyParty, aliveMembers)
        if skillID == "None":
            if hit(target.tempStats["dodgeChance"]/100):
                enemyDmg = math.ceil(enemy.attack(target)) 
                target.hp -= enemyDmg
                useTurn(turns)
                enemy.update_durations() #update duration of the buff only after act is done
                print(f">> The {enemy.name} attacked {target.name} for {enemyDmg} damage!")
            else:
                useTurn(turns)
                useTurn(turns)
                enemy.update_durations()
                print(f">> The {enemy.name} missed the attack on {target.name}!")
            
            if target.hp <= 0:
                if target == party.members[0]:
                    return "defeated"

                else:
                    print(target.name + " has been defeated!")
                    input(">> ")
                    break
        else:
            if skillInfo(skillID)["type"] == "heal":
                heal = skillDmg(skillID, enemy, turns, target, consumeTurn = True)
                enemy.update_durations() #update duration of the buff only after act is done
                print(f">> The {enemy.name} used {skillInfo(skillID)["name"]} on {target.name}!")
                print(f">> {target.name} is healed by {heal}!")

            elif skillInfo(skillID)["type"] == "buff":
                skill = skillInfo(skillID)
                buffType = skill["element"] #atk/def/agi
                currentStage = getattr(target, f"buff_{buffType}")
                if currentStage < 2:
                    setattr(target, f"buff_{buffType}", currentStage + skill["buff_stage"])

                skillDmg(skillID, enemy, turns, target, consumeTurn = True)
                target.buffDurations[buffType] = 3
                enemy.update_durations() #update duration of the buff only after act is done
                print(f">> The {enemy.name} used {skill["name"]} on {target.name}!")
                print(f">> {target.name}'s {buffType.upper()} is being buffed by {enemy.name}!")

            elif skillInfo(skillID)["type"] == "debuff":
                skill = skillInfo(skillID)
                debuffType = skill["element"] #atk/def/agi
                currentStage = getattr(target, f"buff_{debuffType}")
                if currentStage > -2:
                    setattr(target, f"buff_{debuffType}", currentStage + skill["debuff_stage"])

                skillDmg(skillID, enemy, turns, target, consumeTurn = True)
                target.buffDurations[debuffType] = 3
                enemy.update_durations() #update duration of the buff only after act is done
                print(f">> The {enemy.name} used {skill["name"]} on {target.name}!")
                print(f">> {target.name}'s {debuffType.upper()} is being debuffed by {enemy.name}!")

            else:
                if skillInfo(skillID)["target"] == "all" or skillInfo(skillID)["target"] == "multiple":
                    print(f">> The {enemy.name} used {skillInfo(skillID)["name"]}!")
                    first = True
                    miss = False
                    if skillInfo(skillID)["target"] == "all":
                        for t in target:
                            if hit(t.tempStats["dodgeChance"]/100):
                                dmg = max(skillDmg(skillID, enemy, turns, t, consumeTurn = first), 1)
                                print(f">> The {enemy.name} attacked {t.name} for {dmg} damage!")
                                first = False
                            else:
                                miss = True
                                print(f">> The {enemy.name} missed the attack on {t.name}!")

                            if t.hp <= 0:
                                if t == party.members[0]:
                                    return "defeated"
                                else:
                                    print(f">> {t.name} has been defeated!") 
                        enemy.update_durations() #update duration of the buff only after act is done

                    elif skillInfo(skillID)["target"] == "multiple":
                        for _ in range(skillInfo(skillID)["hits"]):
                            t = random.choice(target)
                            if hit(t.tempStats["dodgeChance"]/100):
                                dmg = max(skillDmg(skillID, enemy, turns, t, consumeTurn = first), 1)
                                print(f">> The {enemy.name} attacked the {t.name} for {dmg} damage!")
                                first = False
                            else:
                                miss = True
                                print(f">> The {enemy.name} missed the attack on {t.name}!")

                            if t.hp <= 0:
                                if t == party.members[0]:
                                    return "defeated"
                                else:
                                    print(f">> {t.name} has been defeated!") 
                        enemy.update_durations()   

                    if miss:
                        useTurn(turns)
                        useTurn(turns)
                    input(">> ")

                else:
                    if hit(target.tempStats["dodgeChance"]/100):
                        print(f">> The {enemy.name} used {skillInfo(skillID)["name"]}!")
                        dmg = max(skillDmg(skillID, enemy, turns, target, consumeTurn = True), 1)
                        enemy.update_durations() #update duration of the buff only after act is done
                        print(f">> The {enemy.name} attacked {target.name} for {dmg} damage!")
                    else:
                        useTurn(turns)
                        useTurn(turns)
                        enemy.update_durations()
                        print(f">> The {enemy.name} missed the attack on {target.name}!")

                    if target.hp <= 0:
                        if target == party.members[0]:
                            return "defeated"

                        else:
                            print(f">> {target.name} has been defeated!")
                            input(">> ")
                            break
        
        break
        
def action(party, member, enemyParty, turns):
    global fight, play
    if member.hp <= 0:
        print(member.name + " is unconscious!")
        return 
    
    if not enemyParty.is_defeated():
        while True:
            header("a", turns, enemyParty)
            buffs = " ".join([
                formatBuff("atk", member.buff_atk),
                formatBuff("def", member.buff_def),
                formatBuff("agi", member.buff_agi)
            ])
            print(f">> {member.name} | HP: {member.hp}/{member.maxHP} | MP: {member.mp}/{member.maxMP} | {buffs}")
            print(f"1. Attack | {member.weapon.get("element").upper()}")
            print("2. Use Sidearm")
            print("3. Skills")
            print("4. Items")
            print("5. Pass")
            draw()
            act = input(">> ")

            if act == "1": 
                header("a", turns, enemyParty)
                print("Select a Target (0. Back):")
                while True:
                    target = input(">> ")
                    if target.isdigit():
                        if target == "0":
                            break
                        else:
                            enemy = enemyParty.enemyMembers[int(target) - 1]
                            
                        if hit(enemy.tempStats["dodgeChance"]/100):
                            usedTurn = useTurn(turns)
                            weaponATK = member.tempStats.get("atk", 1)
                            weapon = member.weapon
                            finalDMG = skillMod(member, weapon, weaponATK, enemy, turns, used = usedTurn)
                            dmg = max(enemy.take_physical_damage(finalDMG), 1)
                            member.mp += 2
                            if member.mp >= member.maxMP:
                                member.mp = member.maxMP

                            member.update_durations() #update duration of the buff only after act is done
                            print(f">> {member.name} attacked the {enemy.name} for {dmg} damage!")
                        
                            if not enemy.is_alive():
                                enemy.is_dead()
                                enemyParty.update()
                            input(">> ")
                        else:
                            useTurn(turns)
                            useTurn(turns)
                            member.update_durations()
                            print(f">> {member.name} missed the attack on {enemy.name}!")
                            input(">> ")
                        break
                break

            elif act == "2":
                header("a", turns, enemyParty)
                print("Sidearm Skills:")
                if member.side:
                    for i, skillID in enumerate(member.sideSkills, start=1):
                        sideDATA = skillInfo(skillID)
                        skillName = sideDATA["name"]
                        skillDesc = sideDATA["desc"]
                        skillCost = sideDATA["mp_cost"]
                        print(f"{i}. {skillName} | {skillDesc} | COST: {skillCost}MP")
                    print("0. Back")
                    draw()
                    while True:
                        selectSkill = input(">> ")
                        if selectSkill.isdigit():
                            selectINT = int(selectSkill)
                            if selectSkill == "0":
                                clear()
                                break

                            elif 1 <= selectINT <= len(member.skills):
                                header("a", turns, enemyParty)
                                skillID = member.sideSkills[selectINT- 1] 
                                if member.mp < skillInfo(skillID)["mp_cost"]:
                                    print("Not enough MP!")
                                    input(">> ")
                                    continue
                                
                                print("Select a Target (0. Back):")
                                while True:
                                    target = input(">> ")
                                    if target.isdigit():
                                        if target == "0":
                                            break
                                        else:
                                            enemy = enemyParty.enemyMembers[int(target) - 1]
                                            member.mp = max(0, member.mp - skillInfo(skillID)["mp_cost"])
                                            if hit(enemy.tempStats["dodgeChance"]/100):
                                                print(f">> {member.name} used {skillInfo(skillID)["name"]}!")
                                                dmg = max(skillDmg(skillID, member, turns, enemy, consumeTurn = True), 1)
                                                member.update_durations() #update duration of the buff only after act is done
                                                print(f">> {member.name} attacked the {enemy.name} for {dmg} damage!")
                                            
                                                if not enemy.is_alive():
                                                    enemy.is_dead()
                                                    enemyParty.update()
                                            
                                            else:
                                                useTurn(turns)
                                                useTurn(turns)
                                                member.update_durations()
                                                print(f">> {member.name} missed the attack on {enemy.name}!")
                                            input(">> ")
                                            break
                                break
                else:
                    print("No sidearm equipped.")
                    print("0. Back")
                    draw()
                    back = input(">> ")
                    if back == "0":
                        break
                break

            elif act == "3": 
                header("a", turns, enemyParty)
                print("Skills:")
                for i, skill in enumerate(member.skills, start=1):
                    skillName = skillInfo(skill)["name"]
                    skillDesc = skillInfo(skill)["desc"]
                    skillCost = skillInfo(skill)["mp_cost"]
                    print(f"{i}. {skillName} | {skillDesc} | COST: {skillCost}MP")
                print("0. Back")
                draw()
                while True:
                    selectSkill = input(">> ")
                    if selectSkill.isdigit():
                        selectINT = int(selectSkill)
                        if selectSkill == "0":
                            clear()
                            break

                        elif 1 <= selectINT <= len(member.skills):
                            header("a", turns, enemyParty)
                            skillID = member.skills[selectINT- 1] 
                            if member.mp < skillInfo(skillID)["mp_cost"]:
                                print("Not enough MP!")
                                input(">> ")
                                continue
                            
                            if skillInfo(skillID)["type"] == "heal":
                                print("To who?")
                                for i, ally in enumerate(party.members, start=1):
                                    print(f"{i}. {ally.name} | HP: {ally.hp}/{ally.maxHP}")
                                print("0. Back")
                                draw()
                                while True:
                                    selected = input(">> ")
                                    if selected.isdigit():
                                        selectedINT = int(selected)
                                        if selectedINT == 0:
                                            clear()
                                            break
                                        
                                        ally = party.members[selectedINT - 1]
                                        heal = skillDmg(skillID, member, turns, ally, consumeTurn = True)
                                        member.mp = max(0, member.mp - skillInfo(skillID)["mp_cost"])
                                        member.update_durations() #update duration of the buff only after act is done
                                        print(f">> {member.name} used {skillInfo(skillID)["name"]} on {ally.name}!")
                                        print(f">> {ally.name} is healed by {heal}!")
                                        input(">> ")
                                        break
                            
                            elif skillInfo(skillID)["type"] == "buff":
                                print("To who?")
                                for i, ally in enumerate(party.members, start=1):
                                    buffs = " ".join([
                                        formatBuff("atk", ally.buff_atk),
                                        formatBuff("def", ally.buff_def),
                                        formatBuff("agi", ally.buff_agi)
                                    ])
                                    print(f"{i}. {ally.name} | {buffs}")
                                print("0. Back")
                                draw()
                                while True:
                                    selected = input(">> ")
                                    if selected.isdigit():
                                        selectedINT = int(selected)
                                        if selectedINT == 0:
                                            clear()
                                            break
                                        
                                        ally = party.members[selectedINT - 1]                                        
                                        skill = skillInfo(skillID)
                                        buffType = skill["element"] #atk/def/agi
                                        currentStage = getattr(ally, f"buff_{buffType}")
                                        if currentStage < 2:
                                            setattr(ally, f"buff_{buffType}", currentStage + skill["buff_stage"])

                                        skillDmg(skillID, member, turns, ally, consumeTurn = True)
                                        member.mp = max(0, member.mp - skillInfo(skillID)["mp_cost"])
                                        ally.buffDurations[buffType] = 3
                                        member.update_durations() #update duration of the buff only after act is done
                                        print(f">> {member.name} used {skill["name"]} on {ally.name}!")
                                        print(f">> {ally.name}'s {buffType.upper()} is being buffed by {member.name}!")
                                        input(">>")
                                        break

                            elif skillInfo(skillID)["type"] == "debuff": #update enemy to support debuff
                                print("Select a Target (0. Back):")
                                while True:
                                    selected = input(">> ")
                                    if selected.isdigit():
                                        selectedINT = int(selected)
                                        if selectedINT == 0:
                                            clear()
                                            break
                                        
                                        enemy = enemyParty.enemyMembers[selectedINT - 1]
                                        skill = skillInfo(skillID)
                                        debuffType = skill["element"] #atk/def/agi
                                        currentStage = getattr(enemy, f"buff_{debuffType}")
                                        if currentStage > -2:
                                            setattr(enemy, f"buff_{debuffType}", currentStage - skill["debuff_stage"])

                                        skillDmg(skillID, member, turns, enemy, consumeTurn = True)
                                        member.mp = max(0, member.mp - skillInfo(skillID)["mp_cost"])
                                        enemy.buffDurations[debuffType] = 3
                                        member.update_durations() #update duration of the buff only after act is done
                                        print(f">> {member.name} used {skillInfo(skillID)["name"]}!")
                                        print(f">> {enemy.name}'s {debuffType.upper()} is being debuffed by {member.name}!")
                                        input(">> ")
                                        break

                            else:
                                if skillInfo(skillID)["target"] == "all" or skillInfo(skillID)["target"] == "multiple":
                                    print("Are you sure? (Y/N)")
                                    confirm = input(">> ").upper()

                                    if confirm == "Y":
                                        print(f">> {member.name} used {skillInfo(skillID)["name"]}!")
                                        member.mp = max(0, member.mp - skillInfo(skillID)["mp_cost"])
                                        first = True
                                        miss = False
                                        if skillInfo(skillID)["target"] == "all":
                                            for enemy in enemyParty.enemyMembers:
                                                if hit(enemy.tempStats["dodgeChance"]/100):
                                                    dmg = max(skillDmg(skillID, member, turns, enemy, consumeTurn = first), 1)
                                                    print(f">> {member.name} attacked the {enemy.name} for {dmg} damage!")
                                                
                                                    if not enemy.is_alive():
                                                        enemy.is_dead()
                                                        enemyParty.update()
                                                    draw()
                                                    first = False
                                                else:
                                                    miss = True
                                                    print(f">> {member.name} missed the attack on {enemy.name}!")
                                        else:
                                            for _ in range(skillInfo(skillID)["hits"]):
                                                enemy = random.choice(enemyParty.enemyMembers)
                                                if hit(enemy.tempStats["dodgeChance"]/100):
                                                    dmg = max(skillDmg(skillID, member, turns, enemy, consumeTurn = first), 1)
                                                    print(f">> {member.name} attacked the {enemy.name} for {dmg} damage!")
                                                
                                                    if not enemy.is_alive():
                                                        enemy.is_dead()
                                                        enemyParty.update()
                                                    draw()
                                                    first = False
                                                else:
                                                    miss = True
                                                    print(f">> {member.name} missed the attack on {enemy.name}!")
                                        if miss:
                                            useTurn(turns)
                                            useTurn(turns)
                                        member.update_durations()   
                                        input(">> ")
                                    else:
                                        clear()
                                        continue
                                    
                                else:
                                    print("Select a Target (0. Back):")
                                    while True:
                                        selected = input(">> ")
                                        if selected.isdigit():
                                            selectedINT = int(selected)
                                            if selectedINT == 0:
                                                clear()
                                                break
                                            
                                            enemy = enemyParty.enemyMembers[selectedINT - 1]
                                            member.mp = max(0, member.mp - skillInfo(skillID)["mp_cost"])
                                            if hit(enemy.tempStats["dodgeChance"]/100):
                                                print(f">> {member.name} used {skillInfo(skillID)["name"]}!")
                                                dmg = max(skillDmg(skillID, member, turns, enemy, consumeTurn = True), 1)
                                                member.update_durations() #update duration of the buff only after act is done
                                                print(f">> {member.name} attacked the {enemy.name} for {dmg} damage!")

                                                if not enemy.is_alive():
                                                    enemy.is_dead()
                                                    enemyParty.update()
                                        
                                            else:
                                                useTurn(turns)
                                                useTurn(turns)
                                                member.update_durations()
                                                print(f">> {member.name} missed the attack on {enemy.name}!")
                                            input(">> ")
                                            break
                            break
                break

            elif act == "4":
                clear()
                header("a", turns, enemyParty)
                print("Use what item?")
                items, itemsEffect = party.display_items()
                draw()
                while True:
                    choice = input(">> " )
                    if choice.isdigit():
                        choiceINT = int(choice)
                        if 0 < choiceINT <= len(items):
                            itemID = items[choiceINT - 1]
                            effect = itemsEffect[choiceINT - 1]
                            clear()
                            header("a", turns, enemyParty)
                            print(f"On who?")
                            for i, member in enumerate(party.members, 1):
                                if "hp" in effect:
                                    print(f"{i}. {member.name} | HP: {member.hp}/{member.maxHP}")
                                elif "mp" in effect:
                                    print(f"{i}. {member.name} | MP: {member.mp}/{member.maxMP}")
                            print("0. Back")
                            draw()
                            while True:
                                memberInput = input(">> ") 
                                if memberInput == "0":
                                    clear()
                                    break
                                
                                for i in range(len(party.members)):
                                    if memberInput == str(i+1):
                                        clear()
                                        member = party.members[i]
                                        party.use_item(itemID, member.name)
                                
                                        useTurn(turns)
                                        break
                        break

            elif act == "5":
                passTurn(turns)
                member.update_durations()
                break
    else:
        fight = False
        play = True
        
def battle(party, areaID, state = None):
    global fight, mainMenu

    fight = True
    mobs = loadEnemies(areaID) # Load enemies for the area
    if party.members[0].lvl == 1:
        selectedMobs = [mobs[0]]
    elif areaID.startswith("ab"):
        selectedMobs = random.choices(mobs, k=1)
    else:
        first = 80 - (((3 + party.days) % 4)*5) #80,75,70,65
        second = 20 + (((3 + party.days) % 4)*2) #20,22,24,26
        third = 100 - first - second #0, 3, 6, 9
        mobsCount = random.choices([1,2,3], weights=[first, second, third])[0]
        selectedMobs = random.choices(mobs, k = mobsCount)

    enemyParty = EnemyParty(selectedMobs)
    for enemy in enemyParty.get_alive_members():
        enemy.scale(party.days)

    draw()
    print("Enemies appeared!")
    print("Defeat the enemies!!")
    input(">> ")

    while fight:
        if state != "a": #if not ambushed, party can act first
            #ALLY TURN
            turns = initPressTurns(len(party.members))
            while any(t in ['full', 'half'] for t in turns): #update turns to 0 if enemy is defeat and turn is left
                for member in party.members:
                    if not any(t in ['full', 'half'] for t in turns):
                        break

                    enemyParty.update()
                    if enemyParty.is_defeated():
                        break
                    
                    header("a", turns, enemyParty)
                    action(party, member, enemyParty, turns)
                    draw()

                if enemyParty.is_defeated(): #check enemy party die everytime an action occur
                    totalExp = enemyParty.exp
                    totalMoney = enemyParty.money
                    clear()
                    print(f"REWARDS:")
                    print(f"EXP: {totalExp}")
                    print(f"MONEY: {totalMoney}")
                    draw()
                    input(">>")
                    result(party, totalExp, totalMoney)
                    fight = False
                    play = True
                    break

        enemyParty.update()
        if not enemyParty.is_defeated(): #check if die
            #ENEMY TURN
            enemyTurns = initPressTurns(sum(enemy.turns for enemy in enemyParty.get_alive_members()))
            
            while any(t in ['full', 'half'] for t in enemyTurns):
                for enemy in enemyParty.get_alive_members():
                    header("e", enemyTurns)
                    state = enemyAction(enemy, enemyParty, party, enemyTurns)
                    if state == "defeated":
                        fight = False
                        mainMenu = True
                        return "defeated"
                input(">> ")
            if state == "a":
                state = None