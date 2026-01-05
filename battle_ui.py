import pyxel
import random
from classes.enemy import loadEnemies, EnemyParty
from turns import initPressTurns, useTurn, passTurn, showPressTurns
from battles import skillInfo, skillDmg, skillMod, hit

class BattleUI:
    def __init__(self, game):
        self.game = game
        self.enemy_party = None
        self.battle_turns = []
        self.battle_phase = "player"
        self.selected_target = None
        self.selected_skill = None
        self.battle_log = []
        self.battle_log_timer = 0
        self.current_member_index = 0
    
    def start_battle(self, myParty):
        areaID = "a" + str(min(myParty.moons, 3)).zfill(3)
        mobs = loadEnemies(areaID)
        
        if myParty.members[0].lvl == 1:
            selectedMobs = [mobs[0]]
        else:
            mobsCount = random.choices([1, 2, 3], weights=[60, 30, 10])[0]
            selectedMobs = random.choices(mobs, k=mobsCount)
        
        self.enemy_party = EnemyParty(selectedMobs)
        for enemy in self.enemy_party.get_alive_members():
            enemy.scale(myParty.days)
        
        self.battle_turns = initPressTurns(len(myParty.members))
        self.battle_phase = "player"
        self.current_member_index = 0
        self.game.state = "BATTLE"
        self.game.submenu_index = 0
        self.add_battle_log("Battle started!")
    
    def add_battle_log(self, message):
        self.battle_log.append(message)
        if len(self.battle_log) > 3:
            self.battle_log.pop(0)
        self.battle_log_timer = 120
    
    def get_current_member(self):
        alive = [m for m in self.game.myParty.members if m.hp > 0]
        if self.current_member_index >= len(alive):
            self.current_member_index = 0
        return alive[self.current_member_index] if alive else None
    
    def update_battle(self):
        if self.game.input_cooldown > 0:
            return
        
        if self.enemy_party.is_defeated():
            self.game.state = "BATTLE_VICTORY"
            return
        
        alive_members = [m for m in self.game.myParty.members if m.hp > 0]
        if not alive_members:
            self.game.state = "BATTLE_DEFEAT"
            return
        
        if self.battle_phase == "player":
            if not any(t in ['full', 'half'] for t in self.battle_turns):
                self.battle_phase = "enemy"
                enemy_turn_count = sum(e.turns for e in self.enemy_party.get_alive_members())
                self.battle_turns = initPressTurns(enemy_turn_count)
                self.add_battle_log("Enemy turn!")
                self.game.input_cooldown = 30
                return
            
            if pyxel.btnp(self.game.keys['up']):
                self.game.submenu_index = (self.game.submenu_index - 1) % 4
                self.game.input_cooldown = 10
            elif pyxel.btnp(self.game.keys['down']):
                self.game.submenu_index = (self.game.submenu_index + 1) % 4
                self.game.input_cooldown = 10
            elif pyxel.btnp(self.game.keys['confirm']) or pyxel.btnp(self.game.keys['confirm_alt']):
                if self.game.submenu_index == 0:
                    self.game.state = "BATTLE_TARGET"
                    self.selected_skill = None
                elif self.game.submenu_index == 1:
                    self.game.state = "BATTLE_SKILL"
                elif self.game.submenu_index == 2:
                    self.game.show_message("Items - Not yet implemented")
                elif self.game.submenu_index == 3:
                    passTurn(self.battle_turns)
                    member = self.get_current_member()
                    if member:
                        member.update_durations()
                    self.add_battle_log(f"{member.name if member else 'Player'} passed turn")
                    self.advance_turn()
                self.game.input_cooldown = 10
        
        elif self.battle_phase == "enemy":
            if not any(t in ['full', 'half'] for t in self.battle_turns):
                self.battle_phase = "player"
                self.battle_turns = initPressTurns(len(self.game.myParty.members))
                self.current_member_index = 0
                self.add_battle_log("Your turn!")
                self.game.input_cooldown = 30
                return
            
            if self.game.input_cooldown == 0:
                self.execute_enemy_turn()
                self.game.input_cooldown = 60
    
    def advance_turn(self):
        """Move to next party member's turn"""
        alive = [m for m in self.game.myParty.members if m.hp > 0]
        self.current_member_index = (self.current_member_index + 1) % len(alive) if alive else 0
    
    def execute_enemy_turn(self):
        enemy = random.choice(self.enemy_party.get_alive_members())
        alive_members = [m for m in self.game.myParty.members if m.hp > 0]
        target = random.choice(alive_members)
        
        skillID, target = enemy.behavior(self.enemy_party, alive_members)
        
        if skillID == "None":
            if hit(target.tempStats["dodgeChance"]/100):
                import math
                enemyDmg = math.ceil(enemy.attack(target))
                target.hp -= enemyDmg
                useTurn(self.battle_turns)
                enemy.update_durations()
                self.add_battle_log(f"{enemy.name} attacks {target.name} for {enemyDmg} dmg!")
            else:
                useTurn(self.battle_turns)
                useTurn(self.battle_turns)
                enemy.update_durations()
                self.add_battle_log(f"{enemy.name} missed!")
        else:
            skill = skillInfo(skillID)
            if skill["type"] == "heal":
                heal = skillDmg(self.enemy_party, skillID, enemy, self.battle_turns, target, consumeTurn=True)
                enemy.update_durations()
                self.add_battle_log(f"{enemy.name} heals {target.name} for {heal}!")
            else:
                if hit(target.tempStats["dodgeChance"]/100):
                    dmg, mod_info = skillDmg(self.enemy_party, skillID, enemy, self.battle_turns, target, consumeTurn=True)
                    enemy.update_durations()
                    msg = f"{enemy.name} uses {skill['name']}! "
                    if mod_info:
                        msg += f"{mod_info}! "
                    if mod_info not in ("ABSORB", "BLOCK"):
                        msg += f"{dmg} dmg to {target.name}!"
                    self.add_battle_log(msg)
                else:
                    useTurn(self.battle_turns)
                    useTurn(self.battle_turns)
                    enemy.update_durations()
                    self.add_battle_log(f"{enemy.name} missed!")
        
        if target.hp <= 0:
            self.add_battle_log(f"{target.name} defeated!")
    
    def update_battle_target(self):
        if self.game.input_cooldown > 0:
            return
        
        alive_enemies = self.enemy_party.get_alive_members()
        
        if pyxel.btnp(self.game.keys['up']):
            self.game.submenu_index = (self.game.submenu_index - 1) % len(alive_enemies)
            self.game.input_cooldown = 10
        elif pyxel.btnp(self.game.keys['down']):
            self.game.submenu_index = (self.game.submenu_index + 1) % len(alive_enemies)
            self.game.input_cooldown = 10
        elif pyxel.btnp(self.game.keys['confirm']) or pyxel.btnp(self.game.keys['confirm_alt']):
            target = alive_enemies[self.game.submenu_index]
            
            if self.selected_skill:
                self.execute_skill(target)
            else:
                self.execute_attack(target)
            
            self.game.state = "BATTLE"
            self.game.submenu_index = 0
            self.game.input_cooldown = 10
        elif pyxel.btnp(self.game.keys['back']):
            self.game.state = "BATTLE"
            self.game.submenu_index = 0
            self.game.input_cooldown = 10
    
    def execute_attack(self, target):
        member = self.get_current_member()
        if not member:
            return
        
        if hit(target.tempStats["dodgeChance"]/100):
            usedTurn = useTurn(self.battle_turns)
            weaponATK = member.tempStats.get("atk", 1)
            weapon = member.weapon
            dmg_type = weapon.get("element", "slash")
            finalDMG, mod_info, _ = skillMod(self.game.myParty, member, weapon, weaponATK, target, self.battle_turns, used=usedTurn)
            dmg = max(target.take_physical_damage(finalDMG, dmg_type), 1)
            
            import math
            member.mp += math.ceil(member.maxMP * 0.02)
            if member.mp >= member.maxMP:
                member.mp = member.maxMP
            
            member.update_durations()
            
            msg = f"{member.name} attacks {target.name}! "
            if mod_info:
                msg += f"{mod_info}! "
            msg += f"{dmg} dmg!"
            self.add_battle_log(msg)
            
            if not target.is_alive():
                target.is_dead()
                self.enemy_party.update()
                self.add_battle_log(f"{target.name} defeated!")
        else:
            useTurn(self.battle_turns)
            useTurn(self.battle_turns)
            member.update_durations()
            self.add_battle_log(f"{member.name} missed!")
        
        self.advance_turn()
    
    def execute_skill(self, target):
        member = self.get_current_member()
        if not member or not self.selected_skill:
            return
        
        skill = skillInfo(self.selected_skill)
        if member.mp < skill.get("mp_cost", 0):
            self.add_battle_log("Not enough MP!")
            return
        
        if hit(target.tempStats["dodgeChance"]/100):
            dmg, mod_info = skillDmg(self.game.myParty, self.selected_skill, member, self.battle_turns, target, consumeTurn=True)
            member.mp = max(0, member.mp - skill["mp_cost"])
            member.update_durations()
            
            msg = f"{member.name} uses {skill['name']}! "
            if mod_info:
                msg += f"{mod_info}! "
            if mod_info not in ("ABSORB", "BLOCK"):
                msg += f"{dmg} dmg!"
            self.add_battle_log(msg)
            
            if not target.is_alive():
                target.is_dead()
                self.enemy_party.update()
                self.add_battle_log(f"{target.name} defeated!")
        else:
            useTurn(self.battle_turns)
            useTurn(self.battle_turns)
            member.update_durations()
            self.add_battle_log(f"{member.name} missed!")
        
        self.selected_skill = None
        self.advance_turn()
    
    def update_battle_skill(self):
        if self.game.input_cooldown > 0:
            return
        
        member = self.get_current_member()
        if not member:
            return
        
        all_skills = (member.skills or []) + (member.sideSkills or [])
        
        if not all_skills:
            self.game.show_message("No skills available!")
            self.game.state = "BATTLE"
            return
        
        if pyxel.btnp(self.game.keys['up']):
            self.game.submenu_index = (self.game.submenu_index - 1) % len(all_skills)
            self.game.input_cooldown = 10
        elif pyxel.btnp(self.game.keys['down']):
            self.game.submenu_index = (self.game.submenu_index + 1) % len(all_skills)
            self.game.input_cooldown = 10
        elif pyxel.btnp(self.game.keys['confirm']) or pyxel.btnp(self.game.keys['confirm_alt']):
            self.selected_skill = all_skills[self.game.submenu_index]
            self.game.state = "BATTLE_TARGET"
            self.game.submenu_index = 0
            self.game.input_cooldown = 10
        elif pyxel.btnp(self.game.keys['back']):
            self.game.state = "BATTLE"
            self.game.submenu_index = 0
            self.game.input_cooldown = 10
    
    def update_battle_victory(self):
        if self.game.input_cooldown > 0:
            return
        
        if pyxel.btnp(self.game.keys['confirm']) or pyxel.btnp(self.game.keys['confirm_alt']):
            totalExp = self.enemy_party.exp
            totalMoney = self.enemy_party.money
            
            self.game.myParty.update_party(money=totalMoney)
            
            # Give EXP and handle level ups (from battles.py result function)
            import math
            for member in self.game.myParty.members:
                member.exp += totalExp
                member.update_stats()
                
                # Check for level ups
                while member.exp >= member.expRequired:
                    member.lvl += 1
                    member.exp -= member.expRequired
                    member.expRequired = (50 * (member.lvl ** 2)) * (0.9 + (math.log10(member.lvl)/10))
                    member.level_up()
            
            if hasattr(self.game, 'tower_ui') and self.game.tower_ui.tower:
                self.game.tower_ui.advance_floor()
            else:
                self.game.state = "GAME_MENU"
            
            self.enemy_party = None
            self.game.input_cooldown = 10
    
    def update_battle_defeat(self):
        if self.game.input_cooldown > 0:
            return
        
        if pyxel.btnp(self.game.keys['confirm']) or pyxel.btnp(self.game.keys['confirm_alt']):
            if hasattr(self.game, 'tower_ui'):
                self.game.tower_ui.tower = None
            self.enemy_party = None
            self.game.state = "GAME_MENU"
            self.game.input_cooldown = 10
    
    def draw_battle(self):
        pyxel.cls(0)
        
        # Top bar - Phase indicator and Press Turn icons
        pyxel.rect(0, 0, 256, 12, 1)
        
        if self.battle_phase == "player":
            pyxel.text(5, 4, "PLAYER PHASE", 11)
        else:
            pyxel.text(5, 4, "ENEMY PHASE", 8)
        
        # Draw Press Turn icons as circles
        turn_x = 160
        for turn in self.battle_turns:
            if turn == 'full':
                pyxel.circb(turn_x, 6, 3, 10)
                pyxel.circ(turn_x, 6, 2, 10)
            elif turn == 'half':
                pyxel.circb(turn_x, 6, 3, 10)
            turn_x += 10
        
        # Enemy display area
        pyxel.rect(2, 14, 252, 70, 1)
        pyxel.rectb(2, 14, 252, 70, 7)
        pyxel.text(110, 18, "ENEMIES", 8)
        
        y = 30
        for i, enemy in enumerate(self.enemy_party.get_alive_members()):
            hp_percent = enemy.hp / enemy.maxHP
            pyxel.text(10, y, f"{i+1}. {enemy.name[:14]}", 7)
            
            bar_width = 80
            pyxel.rect(110, y, bar_width, 6, 2)
            pyxel.rect(110, y, int(bar_width * hp_percent), 6, 8)
            pyxel.text(195, y, f"HP:{enemy.hp}/{enemy.maxHP}", 7)
            y += 14
        
        # Party display area (horizontal)
        pyxel.rect(2, 88, 252, 52, 1)
        pyxel.rectb(2, 88, 252, 52, 7)
        
        box_width = 82
        box_height = 24
        start_x = 4
        start_y = 90

        for idx, member in enumerate(self.game.myParty.members):
            if idx >= 6:  # Max 6 party members (3x2)
                break
            
            row = idx // 3
            col = idx % 3

            x = start_x + (col * box_width) + (col * 2) 
            y = start_y + (row * box_height) + (row * 2)

            pyxel.rect(x, y, box_width, box_height, 1)
            pyxel.rectb(x, y, box_width, box_height, 7) 

            color = 7 if member.hp > 0 else 5

            pyxel.text(x + 2, y + 2, member.name[:12], color)

            if member.hp > 0:
                # HP bar
                hp_percent = member.hp / member.maxHP
                bar_width = 35

                pyxel.text(x + 2, y + 10, "HP:", 7)
                pyxel.rect(x + 16, y + 10, bar_width, 5, 2)
                pyxel.rect(x + 16, y + 10, int(bar_width * hp_percent), 5, 8)
                pyxel.text(x + 53, y + 10, f"{member.hp}/{member.maxHP}", 7)
                
                # MP bar
                mp_percent = member.mp / member.maxMP

                pyxel.text(x + 2, y + 17, "MP:", 7)
                pyxel.rect(x + 16, y + 17, bar_width, 5, 2)
                pyxel.rect(x + 16, y + 17, int(bar_width * mp_percent), 5, 12)
                pyxel.text(x + 53, y + 17, f"{member.mp}/{member.maxMP}", 7)
            else:
                pyxel.text(x + 2, y + 12, "DEAD", 8)
        
        # Battle log
        pyxel.rect(2, 144, 160, 32, 1)
        pyxel.rectb(2, 144, 160, 32, 7)
        
        log_y = 147
        for log in self.battle_log[-2:]:
            pyxel.text(6, log_y, log[:30], 10)
            log_y += 8
        
        # Commands
        if self.battle_phase == "player":
            pyxel.rect(166, 144, 88, 32, 1)
            pyxel.rectb(166, 144, 88, 32, 7)
            
            actions = ["Attack", "Skills", "Items", "Pass"]
            for i, action in enumerate(actions):
                color = 11 if i == self.game.submenu_index else 7
                prefix = ">" if i == self.game.submenu_index else " "
                pyxel.text(170 + (i % 2) * 42, 147 + (i // 2) * 8, f"{prefix}{action[:6]}", color)
    
    def draw_battle_target(self):
        self.draw_battle()
        
        pyxel.rect(60, 40, 136, 80, 0)
        pyxel.rectb(60, 40, 136, 80, 11)
        pyxel.rectb(61, 41, 134, 78, 11)
        
        pyxel.text(110, 46, "SELECT TARGET", 11)
        
        y = 58
        for i, enemy in enumerate(self.enemy_party.get_alive_members()):
            color = 11 if i == self.game.submenu_index else 7
            prefix = ">" if i == self.game.submenu_index else " "
            
            pyxel.text(70, y, f"{prefix}{enemy.name[:12]}", color)
            pyxel.text(160, y, f"{enemy.hp}", color)
            y += 12
        
        pyxel.text(70, 106, "ESC: Back", 5)
    
    def draw_battle_skill(self):
        self.draw_battle()
        
        pyxel.rect(40, 30, 176, 110, 0)
        pyxel.rectb(40, 30, 176, 110, 11)
        pyxel.rectb(41, 31, 174, 108, 11)
        
        pyxel.text(105, 36, "SELECT SKILL", 11)
        
        member = self.get_current_member()
        if not member:
            return
        
        all_skills = (member.skills or []) + (member.sideSkills or [])
        
        y = 48
        visible_start = max(0, self.game.submenu_index - 4)
        visible_end = min(len(all_skills), visible_start + 8)
        
        for i in range(visible_start, visible_end):
            skill = skillInfo(all_skills[i])
            if skill:
                color = 11 if i == self.game.submenu_index else 7
                prefix = ">" if i == self.game.submenu_index else " "
                mp_cost = skill.get("mp_cost", 0)
                
                if member.mp < mp_cost:
                    color = 5
                
                pyxel.text(46, y, f"{prefix}{skill['name'][:18]}", color)
                pyxel.text(180, y, f"MP:{mp_cost}", color)
                y += 10
        
        pyxel.text(46, 128, "ESC: Back", 5)
        pyxel.text(130, 128, f"Current MP: {member.mp}", 10)
    
    def draw_battle_victory(self):
        pyxel.cls(0)
        
        pyxel.rect(40, 50, 176, 80, 1)
        pyxel.rectb(40, 50, 176, 80, 11)
        pyxel.rectb(41, 51, 174, 78, 11)
        
        pyxel.text(100, 60, "VICTORY!", 11)
        
        pyxel.text(70, 80, f"Experience: +{self.enemy_party.exp}", 10)
        pyxel.text(70, 92, f"Gold: +{self.enemy_party.money}G", 10)
        
        pyxel.text(65, 115, "Press ENTER to continue", 7)
    
    def draw_battle_defeat(self):
        pyxel.cls(0)
        
        pyxel.rect(40, 50, 176, 80, 1)
        pyxel.rectb(40, 50, 176, 80, 8)
        pyxel.rectb(41, 51, 174, 78, 8)
        
        pyxel.text(95, 60, "DEFEATED...", 8)
        
        pyxel.text(55, 80, "Your party has been defeated.", 7)
        pyxel.text(50, 92, "You have been sent back to town.", 7)
        
        pyxel.text(65, 115, "Press ENTER to continue", 7)