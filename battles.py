from helpers import*
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

def check_survival_passive(character):
    for skill in getattr(character, 'skills', []):
        if not isinstance(skill, dict):
            continue
        
        # Check if it's a survival passive
        if (skill.get("type") == "survival" and 
            skill.get("skill_trigger") == "LETHAL_DMG"):
            
            skill_id = skill["id"]
            
            # Check if skill has uses remaining
            if character.passive_uses.get(skill_id, 0) > 0:
                character.passive_uses[skill_id] -= 1
                character.hp = 1  # Survive with 1 HP
                print(f"\n[PASSIVE] {skill['name']} activated!")
                print(f">> {character.name} survives with 1 HP!")
                input(">> ")
                return True
    
    return False

def set_team_passive(members):
    passive_skills = {}
    for member in members:
        for skill_ID in member.skills:
            skill_data = skillInfo(skill_ID)
            if skill_data.get("skill_type")  == "team_passive":
                passive_skills[skill_ID] =  skill_data.get("skill_trigger")
    return passive_skills
    
def get_passive_skills(passive_skills, skill_trigger): #passive_skills = {'ps001': ['CRIT', 'WEAK']} 
    filtered_passive_skills = []
    for skill_ID, skill_triggers in passive_skills.items():
        if skill_trigger in skill_triggers:
            filtered_passive_skills.append(skill_ID)
        
    return filtered_passive_skills

def trigger_passive_by_mod_info(party, caster, target, mod_info):
    skillIDs = get_passive_skills(party.passive_skills, mod_info)
    for skillID in skillIDs:
        passive_skill = skillInfo(skillID)
        if passive_skill["type"] in ("magic", "physical"):
            if random.random() <= passive_skill["base_chance"]/100:
                skill_modifier = caster.tempStats["skillP"] if passive_skill["type"] == "physical" else caster.tempStats["skillM"]
                passive_dmg = math.ceil((1+(skill_modifier/100)) * passive_skill.get("base_dmg", 1))
                if passive_skill["type"] == "magic":
                    dmg = target.take_magic_damage(passive_dmg)
                elif passive_skill["type"] == "arcane":
                    dmg = target.take_arcane_damage(passive_dmg)
                elif passive_skill["type"] == "physical":
                    dmg = target.take_physical_damage(passive_dmg)
                print(f"[PASSIVE] {passive_skill['name']} has been triggered!")
                print(f"Deal additional {dmg}dmg to the enemy.")

def skillInfo(skillID):
    with open("json/skills.json", "r") as f:
        skills = json.load(f)
    
    return skills.get(skillID, None)

def skillMod(party, caster, skill, dmg, target, turns, used = None):
    addedHalfTurn = False
    mod_info = None
    dmg_type = None

    if skill["type"] == "physical":
        dmg_type = skill.get("element", "strike")

        if dmg_type == "stab": #Crit Bonus
            crit_chance = caster.tempStats["critChance"] * 1.5

        else:
            crit_chance = caster.tempStats["critChance"]

        if random.random() < crit_chance/100:
            dmg *= 1.5  
            mod_info = "CRIT"

            if not addedHalfTurn:
                addTurn(turns, used)
                addedHalfTurn = True

    if skill["element"] in target.weak:
        dmg *= 2
        mod_info = "WEAK"

        if not addedHalfTurn:
            addTurn(turns, used)
            addedHalfTurn = True

    elif skill["element"] in target.resist:
        dmg = math.ceil(dmg * 0.5)
        mod_info = "RESIST"

    elif skill["element"] in target.block:
        dmg = 0
        useTurn(turns)
        mod_info = "BLOCK"

    elif skill["element"] in target.absorb:
        target.hp = min(target.hp + dmg, target.maxHP)
        dmg = 0
        useTurn(turns)
        mod_info = "ABSORB"

    return dmg, mod_info, dmg_type if skill["type"] == "physical" else None

def skillDmg(party, skillID, caster, turns, target, consumeTurn = False):
    usedTurn = None
    if consumeTurn:
        usedTurn = useTurn(turns)

    skill = skillInfo(skillID)
    if skill["type"] == "physical":
        baseDMG = math.ceil((1+(caster.tempStats["skillP"]/100)) * skill.get("base_dmg", 1))
        dmg, mod_info, dmg_type = skillMod(party, caster,  skill, baseDMG, target, turns, used = usedTurn)
        final_dmg = target.take_physical_damage(dmg, dmg_type)
        return final_dmg, mod_info
    
    elif skill["type"] == "magic":
        baseDMG = math.ceil((1+(caster.tempStats["skillM"]/100)) * skill.get("base_dmg", 1))
        dmg, mod_info = skillMod(party, caster, skill, baseDMG, target, turns, used = usedTurn)
        final_dmg = target.take_magic_damage(dmg)
        return final_dmg, mod_info
    
    elif skill["type"] == "arcane":
        baseDMG = math.ceil((1+(caster.tempStats["skillA"]/100)) * skill.get("base_dmg", 1))
        dmg, mod_info = skillMod(party, caster, skill, baseDMG, target, turns, used = usedTurn)
        final_dmg = target.take_arcane_damage(dmg)
        return final_dmg, mod_info
    
    
    elif skill["type"] == "heal": 
        heal_M = math.ceil((1+(caster.tempStats["skillM"]/100)) * skill.get("base_heal", 1))
        heal_A = math.ceil((1+(caster.tempStats["skillA"]/100)) * skill.get("base_heal", 1))
        heal = max(heal_M, heal_A)
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
            target.modify_stat("skillA", buffStage, buffType)

def result(party, exp, addMoney, dropped_key = None):
    global fight, play
    if dropped_key:
        print("")
    party.update_party(money = addMoney, newKey = dropped_key) #add money
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
                input(f">> The {enemy.name} attacked {target.name} for {enemyDmg} damage!")
            else:
                useTurn(turns)
                useTurn(turns)
                enemy.update_durations()
                input(f">> The {enemy.name} missed the attack on {target.name}!")
            
            if target.hp <= 0:
                if target == party.members[0]:
                    return "defeated"

                else:
                    print(target.name + " has been defeated!")
                    input(">> ")
                    break
        else:
            if skillInfo(skillID)["type"] == "heal":
                heal = skillDmg(enemyParty, skillID, enemy, turns, target, consumeTurn = True)
                enemy.update_durations() #update duration of the buff only after act is done
                print(f">> The {enemy.name} used {skillInfo(skillID)['name']} on {target.name}!")
                input(f">> {target.name} is healed by {heal}!")

            elif skillInfo(skillID)["type"] == "buff":
                skill = skillInfo(skillID)
                buffType = skill["element"] #atk/def/agi
                currentStage = getattr(target, f"buff_{buffType}")
                if currentStage < 2:
                    setattr(target, f"buff_{buffType}", currentStage + skill["buff_stage"])

                skillDmg(enemyParty, skillID, enemy, turns, target, consumeTurn = True)
                target.buffDurations[buffType] = 3
                enemy.update_durations() #update duration of the buff only after act is done
                print(f">> The {enemy.name} used {skill['name']} on {target.name}!")
                input(f">> {target.name}'s {buffType.upper()} is being buffed by {enemy.name}!")

            elif skillInfo(skillID)["type"] == "debuff":
                skill = skillInfo(skillID)
                debuffType = skill["element"] #atk/def/agi
                currentStage = getattr(target, f"buff_{debuffType}")
                if currentStage > -2:
                    setattr(target, f"buff_{debuffType}", currentStage - skill["debuff_stage"])

                skillDmg(enemyParty, skillID, enemy, turns, target, consumeTurn = True)
                target.buffDurations[debuffType] = 3
                enemy.update_durations() #update duration of the buff only after act is done
                print(f">> The {enemy.name} used {skill['name']} on {target.name}!")
                input(f">> {target.name}'s {debuffType.upper()} is being debuffed by {enemy.name}!")

            else:
                if skillInfo(skillID)["target"] == "all" or skillInfo(skillID)["target"] == "multiple":
                    print(f">> The {enemy.name} used {skillInfo(skillID)['name']}!")
                    first = True
                    miss = False
                    if skillInfo(skillID)["target"] == "all":
                        for t in target:
                            if hit(t.tempStats["dodgeChance"]/100):
                                dmg, mod_info = skillDmg(enemyParty, skillID, enemy, turns, t, consumeTurn = first)
                                if mod_info is not None:
                                    print(f">> {mod_info}!!!")
                                if mod_info not in ("ABSORB", "BLOCK"):
                                    input(f">> The {enemy.name} attacked {t.name} for {dmg} damage!")

                                trigger_passive_by_mod_info(enemyParty, enemy, t, mod_info)
                                first = False
                            else:
                                miss = True
                                input(f">> The {enemy.name} missed the attack on {t.name}!")

                            if t.hp <= 0:
                                if t == party.members[0]:
                                    return "defeated"
                                else:
                                    input(f">> {t.name} has been defeated!") 
                        enemy.update_durations() #update duration of the buff only after act is done

                    elif skillInfo(skillID)["target"] == "multiple":
                        for _ in range(skillInfo(skillID)["hits"]):
                            t = random.choice(target)
                            if hit(t.tempStats["dodgeChance"]/100):
                                dmg, mod_info = skillDmg(enemyParty, skillID, enemy, turns, t, consumeTurn = first)
                                if mod_info is not None:
                                    print(f">> {mod_info}!!!")
                                if mod_info not in ("ABSORB", "BLOCK"):
                                    input(f">> The {enemy.name} attacked the {t.name} for {dmg} damage!")

                                trigger_passive_by_mod_info(enemyParty, enemy, t, mod_info)
                                first = False
                            else:
                                miss = True
                                input(f">> The {enemy.name} missed the attack on {t.name}!")

                            if t.hp <= 0:
                                if t == party.members[0]:
                                    return "defeated"
                                else:
                                    input(f">> {t.name} has been defeated!") 
                        enemy.update_durations()   

                    if miss:
                        useTurn(turns)
                        useTurn(turns)
                    input(">> ")

                else:
                    if hit(target.tempStats["dodgeChance"]/100):
                        print(f">> The {enemy.name} used {skillInfo(skillID)['name']}!")
                        dmg, mod_info = skillDmg(enemyParty, skillID, enemy, turns, target, consumeTurn = True)
                        enemy.update_durations() #update duration of the buff only after act is done
                        if mod_info is not None:
                                    print(f">> {mod_info}!!!")
                        if mod_info not in ("ABSORB", "BLOCK"):
                            print(f">> The {enemy.name} attacked {target.name} for {dmg} damage!")
                        trigger_passive_by_mod_info(enemyParty, enemy, target, mod_info)
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
        
def action(party, member, target_party, turns):
    global fight, play
    if member.hp <= 0:
        print(member.name + " is unconscious!")
        return 
    
    if not target_party.is_defeated():
        while True:
            header("a", turns, target_party)
            buffs = " ".join([
                formatBuff("atk", member.buff_atk),
                formatBuff("def", member.buff_def),
                formatBuff("agi", member.buff_agi)
            ])
            print(f">> {member.name} | HP: {member.hp}/{member.maxHP} | MP: {member.mp}/{member.maxMP} | {buffs}")
            print(f"1. Attack | {member.weapon.get('element').upper()}")
            print("2. Skills")
            print("3. Items")
            print("4. Pass")
            draw()
            act = input(">> ")

            if act == "1": 
                header("a", turns, target_party)
                print("Select a Target (0. Back):")
                while True:
                    selected_target = input(">> ")
                    if selected_target.isdigit():
                        if selected_target == "0":
                            break
                        else:
                            target = target_party.enemyMembers[int(selected_target) - 1]
                            
                        if hit(target.tempStats["dodgeChance"]/100):
                            usedTurn = useTurn(turns)
                            weaponATK = member.tempStats.get("atk", 1)
                            weapon = member.weapon
                            dmg_type =  weapon.get("element", "slash")
                            finalDMG, mod_info, _ = skillMod(party, member, weapon, weaponATK, target, turns, used = usedTurn)
                            dmg = max(target.take_physical_damage(finalDMG, dmg_type), 1)

                            if dmg_type == "slash" and dmg > 0 and mod_info not in ("ABSORB", "BLOCK"):
                                target.apply_bleed()
                                print(f">> {target.name} is bleeding!")

                            member.mp += math.ceil(member.maxMP * 0.02)
                            if member.mp >= member.maxMP:
                                member.mp = member.maxMP

                            member.update_durations() #update duration of the buff only after act is done
                            if mod_info is not None:
                                print(f">> {mod_info}!!!") 
                            if mod_info not in ("ABSORB", "BLOCK"):
                                print(f">> {member.name} attacked the {target.name} for {dmg} damage!")

                            trigger_passive_by_mod_info(party, member, target, mod_info)
                        
                            if not target.is_alive():
                                target.is_dead()
                                target_party.update()
                            input(">> ")
                        else:
                            useTurn(turns)
                            useTurn(turns)
                            member.update_durations()
                            print(f">> {member.name} missed the attack on {target.name}!")
                            input(">> ")
                        break
      
            elif act == "2": 
                header("a", turns, target_party)
                print("Skills:")
                member.all_skills = (member.skills or []) + (member.sideSkills or [])
                for i, skill in enumerate(member.all_skills, start=1):
                    skillName = skillInfo(skill)["name"]
                    skillDesc = skillInfo(skill)["desc"]
                    skillCost = skillInfo(skill).get("mp_cost", "--")
                    print(f"{i}. {skillName} | {skillDesc} | MP COST: {skillCost}")
                print("0. Back")
                draw()
                while True:
                    selectSkill = input(">> ")
                    if selectSkill.isdigit():
                        selectINT = int(selectSkill)
                        if selectSkill == "0":
                            clear()
                            break

                        elif 1 <= selectINT <= len(member.all_skills):
                            header("a", turns, target_party)
                            skillID = member.all_skills[selectINT- 1] 
                            if member.mp < skillInfo(skillID)["mp_cost"]:
                                print("Not enough MP!")
                                input(">> ")
                                break
                            
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
                                        heal = skillDmg(party, skillID, member, turns, ally, consumeTurn = True)
                                        member.mp = max(0, member.mp - skillInfo(skillID)["mp_cost"])
                                        member.update_durations() #update duration of the buff only after act is done
                                        print(f">> {member.name} used {skillInfo(skillID)['name']} on {ally.name}!")
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

                                        skillDmg(party, skillID, member, turns, ally, consumeTurn = True)
                                        member.mp = max(0, member.mp - skillInfo(skillID)["mp_cost"])
                                        ally.buffDurations[buffType] = 3
                                        member.update_durations() #update duration of the buff only after act is done
                                        print(f">> {member.name} used {skill['name']} on {ally.name}!")
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
                                        
                                        target = target_party.enemyMembers[selectedINT - 1]
                                        skill = skillInfo(skillID)
                                        debuffType = skill["element"] #atk/def/agi
                                        currentStage = getattr(target, f"buff_{debuffType}")
                                        if currentStage > -2:
                                            setattr(target, f"buff_{debuffType}", currentStage - skill["debuff_stage"])

                                        skillDmg(party, skillID, member, turns, target, consumeTurn = True)
                                        member.mp = max(0, member.mp - skillInfo(skillID)["mp_cost"])
                                        target.buffDurations[debuffType] = 3
                                        member.update_durations() #update duration of the buff only after act is done
                                        print(f">> {member.name} used {skillInfo(skillID)['name']}!")
                                        print(f">> {target.name}'s {debuffType.upper()} is being debuffed by {member.name}!")
                                        input(">> ")
                                        break

                            else:
                                if skillInfo(skillID)["target"] == "all" or skillInfo(skillID)["target"] == "multiple":
                                    print("Are you sure? (Y/N)")
                                    confirm = input(">> ").upper()

                                    if confirm == "Y":
                                        print(f">> {member.name} used {skillInfo(skillID)['name']}!")
                                        member.mp = max(0, member.mp - skillInfo(skillID)["mp_cost"])
                                        first = True
                                        miss = False
                                        if skillInfo(skillID)["target"] == "all":
                                            for target in target_party.enemyMembers:
                                                if hit(target.tempStats["dodgeChance"]/100):
                                                    dmg, mod_info = skillDmg(party, skillID, member, turns, target, consumeTurn = first)
                                                    if mod_info is not None:
                                                        print(f">> {mod_info}!!!") 
                                                    if mod_info not in ("ABSORB", "BLOCK"):
                                                        print(f">> {member.name} attacked the {target.name} for {dmg} damage!")

                                                    trigger_passive_by_mod_info(party, member, target, mod_info)

                                                    if not target.is_alive():
                                                        target.is_dead()
                                                        target_party.update()
                                                    draw()
                                                    first = False
                                                else:
                                                    miss = True
                                                    print(f">> {member.name} missed the attack on {target.name}!")
                                        else:
                                            for _ in range(skillInfo(skillID)["hits"]):
                                                target = random.choice(target_party.enemyMembers)
                                                if hit(target.tempStats["dodgeChance"]/100):
                                                    dmg, mod_info = skillDmg(party, skillID, member, turns, target, consumeTurn = first)
                                                    if mod_info is not None:
                                                        print(f">> {mod_info}!!!")
                                                    if mod_info not in ("ABSORB", "BLOCK"):
                                                        print(f">> {member.name} attacked the {target.name} for {dmg} damage!")

                                                    trigger_passive_by_mod_info(party, member, target, mod_info)

                                                    if not target.is_alive():
                                                        target.is_dead()
                                                        target_party.update()
                                                    draw()
                                                    first = False
                                                else:
                                                    miss = True
                                                    print(f">> {member.name} missed the attack on {target.name}!")
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
                                            
                                            target = target_party.enemyMembers[selectedINT - 1]
                                            member.mp = max(0, member.mp - skillInfo(skillID)["mp_cost"])
                                            if hit(target.tempStats["dodgeChance"]/100):
                                                print(f">> {member.name} used {skillInfo(skillID)['name']}!")
                                                dmg, mod_info = skillDmg(party, skillID, member, turns, target, consumeTurn = True)
                                                member.update_durations() #update duration of the buff only after act is done
                                                if mod_info is not None:
                                                    print(f">> {mod_info}!!!") 
                                                if mod_info not in ("ABSORB", "BLOCK"):
                                                    print(f">> {member.name} attacked the {target.name} for {dmg} damage!")

                                                trigger_passive_by_mod_info(party, member, target, mod_info)

                                                if not target.is_alive():
                                                    target.is_dead()
                                                    target_party.update()
                                        
                                            else:
                                                useTurn(turns)
                                                useTurn(turns)
                                                member.update_durations()
                                                print(f">> {member.name} missed the attack on {target.name}!")
                                            input(">> ")
                                            break
                            break   

            elif act == "3":
                while True:
                    clear()
                    header("a", turns, target_party)
                    print("Use what item?")
                    items, itemsEffect = party.display_items()
                    draw()
                    choice = input(">> " ).strip()
                    if not choice or choice == "0":
                        break

                    elif choice.isdigit():
                        choiceINT = int(choice)
                        if 0 < choiceINT <= len(items):
                            itemID = items[choiceINT - 1]
                            effect = itemsEffect[choiceINT - 1]
                            clear()
                            header("a", turns, target_party)
                            print(f"On who?")
                            for i, member in enumerate(party.members, 1):
                                if "hp" in effect:
                                    print(f"{i}. {member.name} | HP: {member.hp}/{member.maxHP}")
                                elif "mp" in effect:
                                    print(f"{i}. {member.name} | MP: {member.mp}/{member.maxMP}")
                            print("0. Back")
                            draw()
                            while True:
                                memberInput = input(">> ").strip() 
                                if not memberInput or memberInput == "0":
                                    break
                                
                                if memberInput.isdigit():
                                    i = int(memberInput) - 1
                                    if 0 <= i < len(party.members):
                                        clear()
                                        member = party.members[i]
                                        party.use_item(itemID, member.name)
                                        useTurn(turns)
                                        return

            elif act == "4":
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
            party.passive_skills = set_team_passive(members = party.members) #Load party's passive skills
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
                    dropped_key = enemyParty.key_item or None
                    clear()
                    print(f"REWARDS:")
                    print(f"EXP: {totalExp}")
                    print(f"MONEY: {totalMoney}")
                    if dropped_key:
                        try:
                            with open("json/items/key.json") as f:
                                keyData = json.load(f)

                            print("KEY ITEMS:")
                            for keyID in dropped_key:
                                keyInfo = keyData.get(keyID)
                                print(f">> {keyInfo['name']}")
                        except FileNotFoundError:
                            print(f"KEY ITEMS: {dropped_key}")

                    draw()
                    input(">>")
                    result(party, totalExp, totalMoney, dropped_key)
                    fight = False
                    play = True
                    break

            if state == "a":
                state = None

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