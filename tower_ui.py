import pyxel
import math
from classes.tower import Tower

class TowerUI:
    def __init__(self, game):
        self.game = game
        self.tower = None
        self.current_floor = None
        self.door_choices = []
    
    def start_tower(self, myParty):
        self.tower = Tower(myParty, total=6)
        self.game.state = "TOWER_INTRO"
    
    def advance_floor(self):
        self.tower.current += 1
        
        if self.tower.current <= self.tower.total:
            self.current_floor = self.tower.floors[self.tower.current]
            self.door_choices = list(self.current_floor.doors.keys())
            self.game.submenu_index = 0
            self.game.state = "TOWER_FLOOR"
        else:
            self.game.state = "TOWER_RESULT"
            self.game.submenu_index = 0
    
    def update_tower_intro(self):
        if self.game.input_cooldown > 0:
            return
        
        if pyxel.btnp(self.game.keys['confirm']) or pyxel.btnp(self.game.keys['confirm_alt']):
            self.game.state = "TOWER_FLOOR"
            self.current_floor = self.tower.floors[self.tower.current]
            self.door_choices = list(self.current_floor.doors.keys())
            self.game.submenu_index = 0
            self.game.input_cooldown = 10
        
        if pyxel.btnp(self.game.keys['back']):
            self.tower = None
            self.game.state = "GAME_MENU"
            self.game.input_cooldown = 10
    
    def update_tower_floor(self):
        if self.game.input_cooldown > 0:
            return
        
        if pyxel.btnp(self.game.keys['back']):
            self.tower = None
            self.game.state = "GAME_MENU"
            self.game.input_cooldown = 10
            return
        
        if pyxel.btnp(self.game.keys['up']):
            self.game.submenu_index = (self.game.submenu_index - 1) % len(self.door_choices)
            self.game.input_cooldown = 10
        elif pyxel.btnp(self.game.keys['down']):
            self.game.submenu_index = (self.game.submenu_index + 1) % len(self.door_choices)
            self.game.input_cooldown = 10
        elif pyxel.btnp(self.game.keys['confirm']) or pyxel.btnp(self.game.keys['confirm_alt']):
            selected_door = self.door_choices[self.game.submenu_index]
            door_func = self.current_floor.doors[selected_door]
            room_type = door_func.__name__.replace("floor_", "")
            
            if room_type == "battle":
                self.game.battle_ui.start_battle(self.game.myParty)
                return
            elif room_type == "heal":
                self.game.show_message("Rest room - Party healed!")
                for member in self.game.myParty.members:
                    member.hp = min(member.maxHP, member.hp + math.ceil(member.maxHP*0.2))
                    member.mp = min(member.maxMP, member.mp + math.ceil(member.maxMP*0.2))
            elif room_type == "treasure":
                self.game.show_message("Treasure found!")
            
            self.advance_floor()
            self.game.input_cooldown = 10
    
    def update_tower_result(self):
        if self.game.input_cooldown > 0:
            return
        
        if pyxel.btnp(self.game.keys['confirm']) or pyxel.btnp(self.game.keys['confirm_alt']):
            self.tower = None
            self.game.state = "GAME_MENU"
            self.game.input_cooldown = 10
    
    def draw_tower_intro(self):
        pyxel.text(80, 40, "ENTERING THE TOWER", 11)
        
        if self.tower:
            pyxel.text(60, 70, "You are about to enter the tower.", 7)
            pyxel.text(50, 85, f"Total Floors: {self.tower.total}", 7)
            pyxel.text(50, 100, "Defeat all enemies to proceed!", 8)
            
            pyxel.text(70, 130, "Press ENTER to begin", 10)
            pyxel.text(70, 145, "Press ESC to go back", 5)
    
    def draw_tower_floor(self):
        if not self.tower or not self.current_floor:
            return
        
        pyxel.text(75, 10, f"FLOOR {self.tower.current}/{self.tower.total}", 11)
        pyxel.text(70, 35, "Choose your path:", 7)
        
        y = 60
        for i, door_label in enumerate(self.door_choices):
            door_func = self.current_floor.doors[door_label]
            room_type = door_func.__name__.replace("floor_", "").upper()
            
            color = 11 if i == self.game.submenu_index else 7
            prefix = "> " if i == self.game.submenu_index else "  "
            
            pyxel.text(60, y, f"{prefix}{door_label}", color)
            pyxel.text(130, y, f"[{room_type}]", 5)
            y += 15
        
        y = 130
        pyxel.text(10, y, "Party Status:", 7)
        y += 10
        for member in self.game.myParty.members[:3]:
            hp_percent = member.hp / member.maxHP
            bar_color = 8
            
            pyxel.text(10, y, member.name[:8], 7)
            bar_width = 60
            pyxel.rect(70, y, bar_width, 6, 2)
            pyxel.rect(70, y, int(bar_width * hp_percent), 6, bar_color)
            pyxel.text(135, y, f"{member.hp}/{member.maxHP}", 7)
            y += 10
        
        pyxel.text(50, 178, "Select | ESC: Abandon Tower", 5)
    
    def draw_tower_result(self):
        pyxel.text(60, 50, "TOWER COMPLETED!", 11)
        pyxel.text(50, 80, "Congratulations on reaching", 7)
        pyxel.text(65, 95, "the top of the tower!", 7)
        pyxel.text(60, 125, "Press ENTER to continue", 10)