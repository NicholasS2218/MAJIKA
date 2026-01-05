import pyxel
import math
from classes.party import Party
from battle_ui import BattleUI
from tower_ui import TowerUI
from talk_ui import TalkUI

class MajikaGame:
    def __init__(self):
        pyxel.init(256, 192, title="MAJIKA", quit_key=pyxel.KEY_NONE)

        # Key bindings
        self.keys = {
            'up': pyxel.KEY_UP,
            'down': pyxel.KEY_DOWN,
            'left': pyxel.KEY_LEFT,
            'right': pyxel.KEY_RIGHT,
            'confirm': pyxel.KEY_RETURN,
            'confirm_alt': pyxel.KEY_SPACE,
            'back': pyxel.KEY_ESCAPE,
            'delete': pyxel.KEY_BACKSPACE,
            'shift': pyxel.KEY_SHIFT,
        }
        
        # Game states
        self.state = "MAIN_MENU"
        self.prev_state = None
        
        # Menu selection
        self.menu_index = 0
        self.submenu_index = 0
        
        # Name input
        self.player_name = ""
        
        # Game data
        self.myParty = None
        self.selected_member = None
        self.message = ""
        self.message_timer = 0
        
        # Input cooldown
        self.input_cooldown = 0

        # Dialogue system
        # self.current_npc = None
        # self.dialogue_lines = []
        # self.dialogue_index = 0
        # self.dialogue_choices = []
        # self.dialogue_mode = "dialogue"  # "dialogue", "choices", "done"
        # self.current_encounter = None
        # self.choice_mode = "answer"
        # self.text_reveal_index = 0 
        # self.text_reveal_speed = 1 # higher = faster 
        # self.current_event_index = 0
        
        # Tower system
        # self.tower = None
        # self.current_floor = None
        # self.door_choices = []

        # Initialize UI modules
        self.battle_ui = BattleUI(self)
        self.tower_ui = TowerUI(self)
        self.talk_ui = TalkUI(self)

        pyxel.run(self.update, self.draw)
    
    def update(self):
        if self.input_cooldown > 0:
            self.input_cooldown -= 1
        
        if self.message_timer > 0:
            self.message_timer -= 1
        
        if self.state == "MAIN_MENU":
            self.update_main_menu()
        elif self.state == "NAME_INPUT":
            self.update_name_input()
        elif self.state == "GAME_MENU":
            self.update_game_menu()
        elif self.state == "STATS":
            self.update_stats()
        elif self.state == "EQUIPMENT":
            self.update_equipment()
        elif self.state == "EQUIPMENT_SELECT":
            self.update_equipment_select()
        elif self.state == "EQUIPMENT_LIST":
            self.update_equipment_list()
        elif self.state == "INVENTORY":
            self.update_inventory()
        elif self.state == "INVENTORY_USE":
            self.update_inventory_use()
        elif self.state == "TALK":
            self.talk_ui.update_talk()
        elif self.state == "DIALOGUE":
            self.talk_ui.update_dialogue()
        elif self.state == "TOWER_INTRO":
            self.tower_ui.update_tower_intro()
        elif self.state == "TOWER_FLOOR":
            self.tower_ui.update_tower_floor()
        elif self.state == "TOWER_RESULT":
            self.tower_ui.update_tower_result()
        elif self.state == "BATTLE":
            self.battle_ui.update_battle()
        elif self.state == "BATTLE_TARGET":
            self.battle_ui.update_battle_target()
        elif self.state == "BATTLE_SKILL":
            self.battle_ui.update_battle_skill()
        elif self.state == "BATTLE_VICTORY":
            self.battle_ui.update_battle_victory()
        elif self.state == "BATTLE_DEFEAT":
            self.battle_ui.update_battle_defeat()
    
    def update_main_menu(self):
        if self.input_cooldown > 0:
            return
        
        menu_items = ["New Game", "Load Game", "Manual", "Exit"]
        
        if pyxel.btnp(self.keys['up']):
            self.menu_index = (self.menu_index - 1) % len(menu_items)
            self.input_cooldown = 10
        elif pyxel.btnp(self.keys['down']):
            self.menu_index = (self.menu_index + 1) % len(menu_items)
            self.input_cooldown = 10
        elif pyxel.btnp(self.keys['confirm']) or pyxel.btnp(self.keys['confirm_alt']):
            if self.menu_index == 0:  # New Game
                self.player_name = ""
                self.state = "NAME_INPUT"
            elif self.menu_index == 1:  # Load Game
                self.myParty = Party()
                if self.myParty.load_party():
                    self.state = "GAME_MENU"
                    self.menu_index = 0
                else:
                    self.show_message("No save file found!")
            elif self.menu_index == 2:  # Manual
                self.state = "MANUAL"
                self.prev_state = "MAIN_MENU"
            elif self.menu_index == 3:  # Exit
                pyxel.quit()
            self.input_cooldown = 10
    
    def update_name_input(self):
        # Handle text input
        for key in range(pyxel.KEY_A, pyxel.KEY_Z + 1):
            if pyxel.btnp(key):
                if len(self.player_name) < 12:
                    char = chr(ord('A') + (key - pyxel.KEY_A))
                    # Check if shift is held for uppercase
                    if not (pyxel.btn(self.keys['shift'])):
                        char = char.lower()
                    self.player_name += char
        
        # Handle space
        if (pyxel.btnp(self.keys['confirm']) or pyxel.btnp(self.keys['confirm_alt'])) and len(self.player_name) < 12 and len(self.player_name) > 0:
            self.player_name += " "
        
        # Handle backspace
        if pyxel.btnp(self.keys['delete']) and len(self.player_name) > 0:
            self.player_name = self.player_name[:-1]
        
        # Handle enter - start game
        if pyxel.btnp(self.keys['confirm']) or pyxel.btnp(self.keys['confirm_alt']):
            if len(self.player_name) > 0:
                self.myParty = Party()
                self.myParty.join("json/playable/Player.json", name=self.player_name)
                self.state = "GAME_MENU"
                self.menu_index = 0
        
        # Handle ESC - back to main menu
        if pyxel.btnp(self.keys['back']):
            self.state = "MAIN_MENU"
    
    def update_game_menu(self):
        if self.input_cooldown > 0:
            return
        
        menu_items = ["Stats", "Equipment", "Inventory", "Talk", "Explore Tower", "Save & Exit"]
        
        if pyxel.btnp(self.keys['up']):
            self.menu_index = (self.menu_index - 1) % len(menu_items)
            self.input_cooldown = 10
        elif pyxel.btnp(self.keys['down']):
            self.menu_index = (self.menu_index + 1) % len(menu_items)
            self.input_cooldown = 10
        elif pyxel.btnp(self.keys['confirm']) or pyxel.btnp(self.keys['confirm_alt']):
            if self.menu_index == 0:  # Stats
                self.state = "STATS"
                self.submenu_index = 0
            elif self.menu_index == 1:  # Equipment
                self.state = "EQUIPMENT"
                self.submenu_index = 0
            elif self.menu_index == 2:  # Inventory
                self.available_items, self.item_effects = self.myParty.display_items() #refresh
                self.state = "INVENTORY"
                self.submenu_index = 0
            elif self.menu_index == 3:  # Talk
                self.talk_ui.load_npcs_for_talk()
            elif self.menu_index == 4:  # Explore Tower
                self.tower_ui.start_tower(self.myParty)
            elif self.menu_index == 5:  # Save & Exit
                self.myParty.save_party()
                self.state = "MAIN_MENU"
                self.menu_index = 0
            self.input_cooldown = 10
    
    def update_stats(self):
        if self.input_cooldown > 0:
            return
        
        if pyxel.btnp(self.keys['back']) or pyxel.btnp(self.keys['delete']):
            self.state = "GAME_MENU"
            self.selected_member = None
            self.input_cooldown = 10
            return
        
        if self.selected_member is None:
            # Selecting a party member
            if pyxel.btnp(self.keys['up']):
                self.submenu_index = (self.submenu_index - 1) % len(self.myParty.members)
                self.input_cooldown = 10
            elif pyxel.btnp(self.keys['down']):
                self.submenu_index = (self.submenu_index + 1) % len(self.myParty.members)
                self.input_cooldown = 10
            elif pyxel.btnp(self.keys['confirm']) or pyxel.btnp(self.keys['confirm_alt']):
                self.selected_member = self.myParty.members[self.submenu_index]
                self.input_cooldown = 10
        else:
            # Viewing member stats
            if pyxel.btnp(self.keys['back']) or pyxel.btnp(self.keys['delete']):
                self.selected_member = None
                self.input_cooldown = 10
    
    def update_equipment(self):
        if self.input_cooldown > 0:
            return
        
        if pyxel.btnp(self.keys['back']) or pyxel.btnp(self.keys['delete']):
            self.state = "GAME_MENU"
            self.selected_member = None
            self.input_cooldown = 10
            return
        
        menu_size = len(self.myParty.members) + 1

        if pyxel.btnp(self.keys['up']):
            self.submenu_index = (self.submenu_index - 1) % menu_size
            self.input_cooldown = 10
        elif pyxel.btnp(self.keys['down']):
            self.submenu_index = (self.submenu_index + 1) % menu_size
            self.input_cooldown = 10
        elif pyxel.btnp(self.keys['confirm']) or pyxel.btnp(self.keys['confirm_alt']):
            if self.submenu_index == len(self.myParty.members):
                self.state = "GAME_MENU"
            else:
                self.selected_member = self.myParty.members[self.submenu_index]
                self.state = "EQUIPMENT_SELECT"
                self.submenu_index = 0
            self.input_cooldown = 10
        
    
    def update_equipment_select(self):
        if self.input_cooldown > 0:
            return
        
        menu_size = 3

        if pyxel.btnp(self.keys['back']):
            self.state = "EQUIPMENT"
            self.selected_member = None
            self.input_cooldown = 10
            return
        
        if pyxel.btnp(self.keys['up']):
            self.submenu_index = (self.submenu_index - 1) % menu_size
            self.input_cooldown = 10
        elif pyxel.btnp(self.keys['down']):
            self.submenu_index = (self.submenu_index + 1) % menu_size
            self.input_cooldown = 10
        elif pyxel.btnp(self.keys['confirm']) or pyxel.btnp(self.keys['confirm_alt']):
            if self.submenu_index == 2:
                self.state = "EQUIPMENT"
                self.selected_member = None
                self.submenu_index = 0
            else:
                self.selected_equip_type = "weapon" if self.submenu_index == 0 else "side"
                self.available_equips = self.myParty.display_equip(self.selected_member.name, type=self.selected_equip_type)
                if self.available_equips:
                    self.state = "EQUIPMENT_LIST"
                    self.submenu_index = 0
                else:
                    self.show_message("No equipment available!")
            self.input_cooldown = 10
    
    def update_equipment_list(self):
        if self.input_cooldown > 0:
            return
        
        menu_size = len(self.available_equips) + 1
        
        if pyxel.btnp(self.keys['back']):
            self.state = "EQUIPMENT_SELECT"
            self.submenu_index = 0
            self.input_cooldown = 10
            return
        
        if pyxel.btnp(self.keys['up']):
            self.submenu_index = (self.submenu_index - 1) % menu_size
            self.input_cooldown = 10
        elif pyxel.btnp(self.keys['down']):
            self.submenu_index = (self.submenu_index + 1) % menu_size
            self.input_cooldown = 10
        elif pyxel.btnp(self.keys['confirm']) or pyxel.btnp(self.keys['confirm_alt']):
            if self.submenu_index == len(self.available_equips):
                self.state = "EQUIPMENT_SELECT"
                self.submenu_index = 0
            else:  
                selected_equip = self.available_equips[self.submenu_index]
                self.myParty.eqp_equip(selected_equip, self.selected_member.name, type=self.selected_equip_type)
                self.show_message("Equipment changed!")
                self.state = "EQUIPMENT"
                self.selected_member = None
            self.input_cooldown = 10
    
    def update_inventory(self):
        if self.input_cooldown > 0:
            return

        if pyxel.btnp(self.keys['back']) or pyxel.btnp(self.keys['delete']):
            self.state = "GAME_MENU"
            self.input_cooldown = 10
            return
        
        # refresh available items
        if not hasattr(self, 'available_items'):
            self.available_items, self.item_effects = self.myParty.display_items()

        menu_size = len(self.available_items) + 1
        
        if pyxel.btnp(self.keys['up']):
            self.submenu_index = (self.submenu_index - 1) % menu_size
            self.input_cooldown = 10
        elif pyxel.btnp(self.keys['down']):
            self.submenu_index = (self.submenu_index + 1) % menu_size
            self.input_cooldown = 10
        elif pyxel.btnp(self.keys['confirm']) or pyxel.btnp(self.keys['confirm_alt']):
            if self.submenu_index == len(self.available_items):  # Back selected
                self.state = "GAME_MENU"
                del self.available_items
                del self.item_effects
            elif self.available_items:
                self.state = "INVENTORY_USE"
                self.menu_index = 0

            self.input_cooldown = 10

    def update_inventory_use(self):
        if self.input_cooldown > 0:
            return
        
        menu_size = len(self.myParty.members) + 1 
        
        if pyxel.btnp(self.keys['back']):
            self.state = "INVENTORY"
            self.input_cooldown = 10
            return
        
        if pyxel.btnp(self.keys['up']):
            self.menu_index = (self.menu_index - 1) % menu_size
            self.input_cooldown = 10
        elif pyxel.btnp(self.keys['down']):
            self.menu_index = (self.menu_index + 1) % menu_size
            self.input_cooldown = 10
        elif pyxel.btnp(self.keys['confirm']) or pyxel.btnp(self.keys['confirm_alt']):
            if self.menu_index == len(self.myParty.members):
                self.state = "INVENTORY"
            else:
                selected_item = self.available_items[self.submenu_index]
                target_member = self.myParty.members[self.menu_index]

                message = self.myParty.use_item(selected_item, target_member.name)
                if message:
                    self.show_message(message)

                #refresh after use
                self.available_items, self.item_effects = self.myParty.display_items()

                if not self.available_items:
                    self.state = "GAME_MENU"
                    self.submenu_index = 0
                else:
                    self.state = "INVENTORY"
                    self.submenu_index = min(self.submenu_index, len(self.available_items) - 1)
            self.input_cooldown = 10

    def update_tower_intro(self):
        if self.input_cooldown > 0:
            return
        
        if pyxel.btnp(self.keys['confirm']) or pyxel.btnp(self.keys['confirm_alt']):
            self.state = "TOWER_FLOOR"
            self.current_floor = self.tower.floors[self.tower.current]
            self.door_choices = list(self.current_floor.doors.keys())
            self.submenu_index = 0
            self.input_cooldown = 10
        
        if pyxel.btnp(self.keys['back']):
            self.tower = None
            self.state = "GAME_MENU"
            self.input_cooldown = 10

    def update_tower_floor(self):
        if self.input_cooldown > 0:
            return
        
        if pyxel.btnp(self.keys['back']):
            self.tower = None
            self.state = "GAME_MENU"
            self.input_cooldown = 10
            return
        
        if pyxel.btnp(self.keys['up']):
            self.submenu_index = (self.submenu_index - 1) % len(self.door_choices)
            self.input_cooldown = 10
        elif pyxel.btnp(self.keys['down']):
            self.submenu_index = (self.submenu_index + 1) % len(self.door_choices)
            self.input_cooldown = 10
        elif pyxel.btnp(self.keys['confirm']) or pyxel.btnp(self.keys['confirm_alt']):
            selected_door = self.door_choices[self.submenu_index]
            door_func = self.current_floor.doors[selected_door]
            room_type = door_func.__name__.replace("floor_", "")
            
            if room_type == "battle":
                self.show_message("Battle! (Not yet implemented)")
                result = "victory"
            elif room_type == "heal":
                self.show_message("Rest room - Party healed!")
                result = "healed"
                for member in self.myParty.members:
                    member.hp = min(member.maxHP, member.hp + math.ceil(member.maxHP*0.2))
                    member.mp = min(member.maxMP, member.mp + math.ceil(member.maxMP*0.2))
            elif room_type == "treasure":
                self.show_message("Treasure found!")
                result = "treasure"
            
            self.tower.current += 1
            
            if self.tower.current <= self.tower.total:
                self.current_floor = self.tower.floors[self.tower.current]
                self.door_choices = list(self.current_floor.doors.keys())
                self.submenu_index = 0
            else:
                self.state = "TOWER_RESULT"
                self.submenu_index = 0
            
            self.input_cooldown = 10

    def update_tower_result(self):
        if self.input_cooldown > 0:
            return
        
        if pyxel.btnp(self.keys['confirm']) or pyxel.btnp(self.keys['confirm_alt']):
            self.tower = None
            self.state = "GAME_MENU"
            self.input_cooldown = 10

    def show_message(self, msg):
        self.message = msg
        self.message_timer = 120  # Show for 2 seconds at 60fps
    
    def draw(self):
        pyxel.cls(0)
        
        if self.state == "MAIN_MENU":
            self.draw_main_menu()
        elif self.state == "NAME_INPUT":
            self.draw_name_input()
        elif self.state == "GAME_MENU":
            self.draw_game_menu()
        elif self.state == "STATS":
            self.draw_stats()
        elif self.state == "EQUIPMENT":
            self.draw_equipment()
        elif self.state == "EQUIPMENT_SELECT":
            self.draw_equipment_select()
        elif self.state == "EQUIPMENT_LIST":
            self.draw_equipment_list()
        elif self.state == "INVENTORY":
            self.draw_inventory()
        elif self.state == "INVENTORY_USE":
            self.draw_inventory_use()
        elif self.state == "MANUAL":
            self.draw_manual()
        elif self.state == "TALK":
            self.talk_ui.draw_talk()
        elif self.state == "DIALOGUE":
            self.talk_ui.draw_dialogue()
        elif self.state == "TOWER_INTRO":
            self.tower_ui.draw_tower_intro()
        elif self.state == "TOWER_FLOOR":
            self.tower_ui.draw_tower_floor()
        elif self.state == "TOWER_RESULT":
            self.tower_ui.draw_tower_result()
        elif self.state == "BATTLE":
            self.battle_ui.draw_battle()
        elif self.state == "BATTLE_TARGET":
            self.battle_ui.draw_battle_target()
        elif self.state == "BATTLE_SKILL":
            self.battle_ui.draw_battle_skill()
        elif self.state == "BATTLE_VICTORY":
            self.battle_ui.draw_battle_victory()
        elif self.state == "BATTLE_DEFEAT":
            self.battle_ui.draw_battle_defeat()
        
        # Draw message if active
        if self.message_timer > 0:
            pyxel.rect(20, 170, 216, 15, 1)
            pyxel.rectb(20, 170, 216, 15, 7)
            pyxel.text(25, 175, self.message, 7)
    
    def draw_main_menu(self):
        # Title
        pyxel.text(90, 30, "M A J I K A", pyxel.frame_count % 16)
        pyxel.text(70, 50, "A Roguelite Adventure", 7)
        
        # Menu items
        menu_items = ["New Game", "Load Game", "Manual", "Exit"]
        y = 80
        for i, item in enumerate(menu_items):
            color = 11 if i == self.menu_index else 7
            prefix = "> " if i == self.menu_index else "  "
            pyxel.text(90, y, prefix + item, color)
            y += 15
        
        # Controls hint
        pyxel.text(50, 170, "Up/Down: Navigate | Enter: Select", 5)
    
    def draw_name_input(self):
        # Title
        pyxel.text(70, 40, "Enter your name:", 7)
        
        # Input box
        pyxel.rect(60, 70, 136, 20, 1)
        pyxel.rectb(60, 70, 136, 20, 7)
        
        # Display name with cursor
        display_name = self.player_name
        if pyxel.frame_count % 30 < 15:  # Blinking cursor
            display_name += "_"
        
        pyxel.text(65, 78, display_name, 11)
        
        # Instructions
        pyxel.text(50, 110, "Type your name (max 12 chars)", 7)
        pyxel.text(55, 120, "Hold SHIFT for uppercase", 7)
        pyxel.text(65, 140, "Press ENTER to start", 10)
        pyxel.text(70, 150, "Press ESC to go back", 5)
    
    def draw_game_menu(self):
        if not self.myParty:
            return
        
        # Header
        pyxel.rect(0, 0, 256, 20, 1)
        pyxel.rectb(0, 0, 256, 20, 7)
        pyxel.text(5, 5, f"Day: {self.myParty.days}", 7)
        pyxel.text(5, 12, f"Gold: {self.myParty.money}G", 10)
        
        # Party members preview
        x = 100
        for member in self.myParty.members:
            pyxel.text(x, 5, member.name[:8], 11)
            hp_percent = member.hp / member.maxHP
            bar_width = 40
            pyxel.rect(x, 12, bar_width, 4, 2)
            pyxel.rect(x, 12, int(bar_width * hp_percent), 4, 8)
            x += 50
        
        # Menu
        pyxel.text(90, 30, "What to do?", 7)
        menu_items = ["Stats", "Equipment", "Inventory", "Talk", "Explore Tower", "Save & Exit"]
        y = 50
        for i, item in enumerate(menu_items):
            color = 11 if i == self.menu_index else 7
            prefix = "> " if i == self.menu_index else "  "
            pyxel.text(80, y, prefix + item, color)
            y += 12
        
        # Controls
        pyxel.text(50, 175, "Up/Down + Enter | ESC: Back", 5)
    
    def draw_stats(self):
        if not self.myParty:
            return
        
        pyxel.text(100, 5, "STATS", 11)
        
        if self.selected_member is None:
            pyxel.text(70, 25, "Select Party Member:", 7)
            y = 45
            for i, member in enumerate(self.myParty.members):
                color = 11 if i == self.submenu_index else 7
                prefix = "> " if i == self.submenu_index else "  "
                pyxel.text(70, y, f"{prefix}{member.name}", color)
                y += 12
        else:
            me = self.selected_member
            pyxel.text(10, 25, f"{me.name} Lv.{me.stats['lvl']}", 7)
            pyxel.text(10, 33, f"EXP: {math.ceil(me.stats['exp'])}/{math.ceil(me.stats['expRequired'])}", 7)
            
            y = 45
            pyxel.text(10, y, "HP:", 8)
            pyxel.text(35, y, f"{me.stats['hp']}/{me.stats['maxHP']}", 7)
            y += 10
            
            pyxel.text(10, y, "MP:", 12)
            pyxel.text(35, y, f"{me.stats['mp']}/{me.stats['maxMP']}", 7)
            y += 12
            
            pyxel.text(10, y, f"ATK: {math.ceil(me.stats['atk'])}", 7)
            y += 8
            pyxel.text(10, y, f"P.ATK: {math.ceil(me.stats['skillP'])}", 7)
            y += 8
            pyxel.text(10, y, f"M.ATK: {math.ceil(me.stats['skillM'])}", 7)
            y += 8
            pyxel.text(10, y, f"A.ATK: {math.ceil(me.stats['skillA'])}", 7)
            y += 8
            
            pyxel.text(10, y, f"P.DEF: {math.ceil(me.stats['defP'])}", 7)
            y += 8
            pyxel.text(10, y, f"M.DEF: {math.ceil(me.stats['defM'])}", 7)
            y += 8
            pyxel.text(10, y, f"A.DEF: {math.ceil(me.stats['defA'])}", 7)
            
            y = 45
            pyxel.text(140, y, "SKILLS:", 11)
            y += 10
            for skill in me.skills[:10]:
                try:
                    skillName = skill.get("name", "")
                    pyxel.text(140, y, skillName[:12], 7)
                    y += 8
                except:
                    pass
        
        pyxel.text(80, 175, "ESC: Back", 5)

    def draw_equipment(self):
        pyxel.text(85, 5, "EQUIPMENT", 11)
        
        pyxel.text(70, 25, "Select Party Member:", 7)
        y = 45
        for i, member in enumerate(self.myParty.members):
            color = 11 if i == self.submenu_index else 7
            prefix = "> " if i == self.submenu_index else "  "
            pyxel.text(60, y, f"{prefix}{member.name}", color)
            y += 12
        
        color = 11 if self.submenu_index == len(self.myParty.members) else 7
        prefix = "> " if self.submenu_index == len(self.myParty.members) else "  "
        pyxel.text(60, y, prefix + "Back", color)
    
    def draw_equipment_select(self):
        pyxel.text(85, 5, "EQUIPMENT", 11)
        
        if self.selected_member:
            me = self.selected_member
            pyxel.text(10, 25, f"{me.name}'s Equipment:", 7)
            y = 40
            pyxel.text(10, y, f"Weapon: {me.weapon['name']}", 7)
            y += 10
            if me.side:
                pyxel.text(10, y, f"Sidearm: {me.side['name']}", 7)
            else:
                pyxel.text(10, y, "Sidearm: None", 7)
            
            y = 70
            pyxel.text(70, y, "Change Equipment:", 11)
            y += 15
            
            items = ["Main Weapon", "Sidearm", "Back"]
            for i, item in enumerate(items):
                color = 11 if i == self.submenu_index else 7
                prefix = "> " if i == self.submenu_index else "  "
                pyxel.text(70, y, prefix + item, color)
                y += 12

    def draw_equipment_list(self):
        import json
        
        pyxel.text(70, 5, "SELECT EQUIPMENT", 11)
        
        file = "weapons.json" if self.selected_equip_type == "weapon" else "sidearm.json"
        path = "json/items/" + file
        
        try:
            with open(path) as f:
                itemData = json.load(f)
            
            y = 25
            visible_start = max(0, self.submenu_index - 5)
            visible_end = min(len(self.available_equips) + 1, visible_start + 12)
            
            for i in range(visible_start, visible_end):
                if i < len(self.available_equips):
                    itemID = self.available_equips[i]
                    data = itemData.get(itemID)
                    if data:
                        color = 11 if i == self.submenu_index else 7
                        prefix = "> " if i == self.submenu_index else "  "
                        name = data['name'][:20]
                        pyxel.text(10, y, f"{prefix}{name}", color)
                else:
                    color = 11 if i == self.submenu_index else 7
                    prefix = "> " if i == self.submenu_index else "  "
                    pyxel.text(10, y, prefix + "Back", color)
                y += 10
        except:
            pyxel.text(10, 25, "Error loading equipment", 8)
        
        pyxel.text(80, 175, "ESC: Back", 5)
    
    def draw_inventory(self):
        import json
        
        pyxel.text(85, 5, "INVENTORY", 11)
        
        if not hasattr(self, 'available_items'):
            pyxel.text(70, 50, "Loading...", 7)
            return
        
        if not self.available_items:
            # Show only Back when no items
            color = 11 if self.submenu_index == 0 else 7
            pyxel.text(70, 50, "No items available", 7)
            pyxel.text(70, 70, "> Back", color)
            return
        
        try:
            with open("json/items/consumables.json") as f:
                itemData = json.load(f)
            
            y = 25
            visible_start = max(0, self.submenu_index - 5)
            visible_end = min(len(self.available_items)+1, visible_start + 12)
            
            for i in range(visible_start, visible_end):
                if i < len(self.available_items):
                    itemID = self.available_items[i]
                    data = itemData.get(itemID)
                    qty = self.myParty.inventory[itemID]["quantity"]
                    if data:
                        color = 11 if i == self.submenu_index else 7
                        prefix = "> " if i == self.submenu_index else "  "
                        name = data['name'][:15]
                        pyxel.text(10, y, f"{prefix}{name} x{qty}", color)
                    
                else:
                    # Show Back option at the end
                    color = 11 if i == self.submenu_index else 7
                    prefix = "> " if i == self.submenu_index else "  "
                    pyxel.text(10, y, prefix + "Back", color)

                y += 10

        except:
            pyxel.text(10, 25, "Error loading items", 8)
        
        pyxel.text(60, 175, "Select item | ESC: Back", 5)

    def draw_inventory_use(self):
        pyxel.text(85, 5, "USE ON WHO?", 11)
        
        if not hasattr(self, 'item_effects') or not self.item_effects:
            pyxel.text(70, 50, "Error: No item selected", 8)
            return

        effect = self.item_effects[self.submenu_index]
        
        y = 30
        for i, member in enumerate(self.myParty.members):
            color = 11 if i == self.menu_index else 7
            prefix = "> " if i == self.menu_index else "  "
            
            if "hp" in effect:
                info = f"{member.name} HP:{member.hp}/{member.maxHP}"
            elif "mp" in effect:
                info = f"{member.name} MP:{member.mp}/{member.maxMP}"
            else:
                info = member.name
            
            pyxel.text(60, y, prefix + info, color)
            y += 12
        
        color = 11 if self.menu_index == len(self.myParty.members) else 7
        prefix = "> " if self.menu_index == len(self.myParty.members) else "  "
        pyxel.text(60, y, prefix + "Back", color)

    def draw_manual(self):
        pyxel.text(95, 5, "MANUAL", 11)
        
        y = 25
        rules = [
            "This is a turn-based",
            "roguelite game.",
            "",
            "Stats affect the following:",
            "- VIT/MIND: HP/MP",
            "- ST/DEX: Physical attacks & Physical defense",
            "- MAG/ARC: Elemental attacks & Elemental defense",
            "- AGI: Crit/Evasion",
            "",
            "Have fun!",
        ]
        
        for line in rules:
            pyxel.text(40, y, line, 7)
            y += 10
        
        pyxel.text(60, 175, "ESC: Back", 5)
        
        if pyxel.btnp(self.keys['back']):
            self.state = self.prev_state
            self.input_cooldown = 10

MajikaGame()