import pyxel
from classes.npc import load_npcs

class TalkUI:
    def __init__(self, game):
        self.game = game
        self.current_npc = None
        self.dialogue_lines = []
        self.dialogue_index = 0
        self.dialogue_choices = []
        self.dialogue_mode = "dialogue"
        self.current_encounter = None
        self.choice_mode = "answer"
        self.text_reveal_index = 0
        self.text_reveal_speed = 1
        self.current_event_index = 0
        self.available_npcs = []
    
    def load_npcs_for_talk(self):
        npcs = load_npcs("json/npcs.json")
        self.available_npcs = [(id, npc) for id, npc in npcs.items() if npc.appear(self.game.myParty)]
        
        if self.available_npcs:
            self.game.state = "TALK"
            self.game.submenu_index = 0
        else:
            self.game.show_message("No one is here...")
    
    def start_dialogue(self, npc):
        self.current_npc = npc
        dialogue_data = npc.get_dialogue_data(self.game.myParty)
        
        self.dialogue_lines = dialogue_data["lines"]
        self.dialogue_choices = dialogue_data["choices"]
        self.choice_mode = dialogue_data["choice_mode"]
        self.current_encounter = dialogue_data["encounter"]
        self.current_event_index = dialogue_data["event_index"]
        
        self.dialogue_index = 0
        self.dialogue_mode = "dialogue"
        self.text_reveal_index = 0
        self.game.state = "DIALOGUE"
    
    def update_talk(self):
        if self.game.input_cooldown > 0:
            return
        
        if pyxel.btnp(self.game.keys['back']):
            self.game.state = "GAME_MENU"
            self.game.input_cooldown = 10
            return
        
        total_options = len(self.available_npcs) + 1
        
        if pyxel.btnp(self.game.keys['up']):
            self.game.submenu_index = (self.game.submenu_index - 1) % total_options
            self.game.input_cooldown = 10
        elif pyxel.btnp(self.game.keys['down']):
            self.game.submenu_index = (self.game.submenu_index + 1) % total_options
            self.game.input_cooldown = 10
        elif pyxel.btnp(self.game.keys['confirm']) or pyxel.btnp(self.game.keys['confirm_alt']):
            if self.game.submenu_index == len(self.available_npcs):
                self.game.state = "GAME_MENU"
            else:
                _, npc = self.available_npcs[self.game.submenu_index]
                self.start_dialogue(npc)
            self.game.input_cooldown = 10
    
    def update_dialogue(self):
        if self.game.input_cooldown > 0:
            return
        
        if self.dialogue_mode == "dialogue":
            if self.dialogue_index < len(self.dialogue_lines):
                _, text = self.dialogue_lines[self.dialogue_index]
                if self.text_reveal_index < len(text):
                    self.text_reveal_index += self.text_reveal_speed
            
            if pyxel.btnp(self.game.keys['confirm']) or pyxel.btnp(self.game.keys['confirm_alt']):
                _, text = self.dialogue_lines[self.dialogue_index]
                
                if self.text_reveal_index < len(text):
                    self.text_reveal_index = len(text)
                else:
                    self.dialogue_index += 1
                    self.text_reveal_index = 0
                    
                    if self.dialogue_index >= len(self.dialogue_lines):
                        if self.dialogue_choices:
                            self.dialogue_mode = "choices"
                            self.game.submenu_index = 0
                        else:
                            self.current_npc.mark_event_complete(self.game.myParty, self.current_event_index)
                            self.game.state = "TALK"
                            self.current_npc = None
                
                self.game.input_cooldown = 10
        
        elif self.dialogue_mode == "choices":
            if pyxel.btnp(self.game.keys['up']):
                self.game.submenu_index = (self.game.submenu_index - 1) % len(self.dialogue_choices)
                self.game.input_cooldown = 10
            elif pyxel.btnp(self.game.keys['down']):
                self.game.submenu_index = (self.game.submenu_index + 1) % len(self.dialogue_choices)
                self.game.input_cooldown = 10
            elif pyxel.btnp(self.game.keys['confirm']) or pyxel.btnp(self.game.keys['confirm_alt']):
                selected_choice = self.dialogue_choices[self.game.submenu_index]
                response_lines, keep_choices, should_end = self.current_npc.process_choice(
                    selected_choice, self.game.myParty
                )
                
                if response_lines:
                    self.dialogue_lines = response_lines
                    self.dialogue_index = 0
                    self.text_reveal_index = 0
                    self.dialogue_mode = "dialogue"
                    
                    if not keep_choices:
                        self.dialogue_choices = []
                
                elif should_end:
                    if self.current_encounter and "statements" in self.current_encounter:
                        statement_lines = [
                            (self.current_npc.name, line)
                            for line in self.current_encounter["statements"]
                        ]
                        self.dialogue_lines = statement_lines
                        self.dialogue_index = 0
                        self.text_reveal_index = 0
                        self.dialogue_mode = "dialogue"
                        self.dialogue_choices = []
                    else:
                        self.current_npc.mark_event_complete(self.game.myParty, self.current_event_index)
                        self.game.state = "TALK"
                        self.current_npc = None
                
                self.game.input_cooldown = 10
        
        if pyxel.btnp(self.game.keys['back']):
            if self.dialogue_mode == "choices" and self.choice_mode == "questions":
                self.current_npc.mark_event_complete(self.game.myParty, self.current_event_index)
            
            self.game.state = "TALK"
            self.current_npc = None
            self.game.input_cooldown = 10
    
    def draw_talk(self):
        pyxel.text(95, 5, "TALK", 11)
        pyxel.text(80, 25, "Talk to who?", 7)
        
        y = 45
        for i, (_, npc) in enumerate(self.available_npcs):
            color = 11 if i == self.game.submenu_index else 7
            prefix = "> " if i == self.game.submenu_index else "  "
            pyxel.text(70, y, f"{prefix}{npc.name}", color)
            y += 12
        
        color = 11 if self.game.submenu_index == len(self.available_npcs) else 7
        prefix = "> " if self.game.submenu_index == len(self.available_npcs) else "  "
        pyxel.text(70, y, f"{prefix}Back", color)
        
        pyxel.text(50, 175, "Select | ESC: Back", 5)
    
    def draw_dialogue(self):
        pyxel.cls(0)
        
        if self.dialogue_mode == "dialogue":
            pyxel.rect(10, 120, 236, 65, 1)
            pyxel.rectb(10, 120, 236, 65, 7)
            
            if self.dialogue_index < len(self.dialogue_lines):
                speaker, text = self.dialogue_lines[self.dialogue_index]
                pyxel.text(15, 125, f"{speaker}:", 11)
                revealed_text = text[:int(self.text_reveal_index)]
                words = revealed_text.split()
                lines = []
                current_line = ""
                
                for word in words:
                    test_line = current_line + (" " if current_line else "") + word
                    if len(test_line) <= 38:
                        current_line = test_line
                    else:
                        if current_line:
                            lines.append(current_line)
                        current_line = word
                
                if current_line:
                    lines.append(current_line)
                
                y = 135
                for line in lines[:3]:
                    pyxel.text(15, y, line, 7)
                    y += 10
            
            if self.dialogue_index < len(self.dialogue_lines):
                _, text = self.dialogue_lines[self.dialogue_index]
                if self.text_reveal_index >= len(text) and pyxel.frame_count % 30 < 15:
                    pyxel.text(230, 175, "v", 10)
            
            pyxel.text(40, 188, "SPACE: Continue/Skip | ESC: Exit", 5)
        
        elif self.dialogue_mode == "choices":
            pyxel.rect(10, 60, 236, 120, 1)
            pyxel.rectb(10, 60, 236, 120, 7)
            pyxel.text(90, 68, "Your response:", 11)
            
            y = 85
            for i, choice in enumerate(self.dialogue_choices):
                color = 11 if i == self.game.submenu_index else 7
                prefix = "> " if i == self.game.submenu_index else "  "
                
                if len(choice) > 36:
                    pyxel.text(15, y, prefix + choice[:36], color)
                    y += 8
                    pyxel.text(20, y, choice[36:72], color)
                else:
                    pyxel.text(15, y, prefix + choice, color)
                
                y += 12
            
            pyxel.text(50, 188, "UP/DOWN: Select | ENTER: Confirm", 5)