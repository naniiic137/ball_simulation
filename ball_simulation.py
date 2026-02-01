import pygame
import random
import math
import time

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700
PANEL_HEIGHT = 150
GAME_HEIGHT = SCREEN_HEIGHT - PANEL_HEIGHT

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (50, 50, 50)
RED = (255, 100, 100)
BLUE = (100, 100, 255)
GREEN = (100, 255, 100)
LIGHT_BLUE = (173, 216, 230)
BLUE_ACTIVE = (30, 144, 255)

FPS = 60

class Ball:
    def __init__(self, x, y, radius, color, value, is_boss=False, update_func=None):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.value = value  # Health for Boss, Power for Minions
        self.is_boss = is_boss
        self.update_func = update_func
        self.level = 1
        
        # Random velocity
        speed = 2 if is_boss else 5
        angle = random.uniform(0, 2 * math.pi)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        
        self.mass = radius * radius # Mass proportional to area

    def move(self, max_x, max_y):
        self.x += self.vx
        self.y += self.vy

        # Wall Collisions (Left/Right)
        if self.x - self.radius < 0:
            self.x = self.radius
            self.vx *= -1
        elif self.x + self.radius > max_x:
            self.x = max_x - self.radius
            self.vx *= -1

        # Wall Collisions (Top/Bottom of Game Area)
        if self.y - self.radius < 0:
            self.y = self.radius
            self.vy *= -1
        elif self.y + self.radius > max_y:
            self.y = max_y - self.radius
            self.vy *= -1

    def draw(self, surface, font):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, BLACK, (int(self.x), int(self.y)), self.radius, 2)
        
        # Draw value text (Health or Power)
        val_str = str(self.value)
        if len(val_str) > 10:
            try:
                val_str = f"{self.value:.2e}"
            except:
                pass

        text_surf = font.render(val_str, True, BLACK)
        text_rect = text_surf.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(text_surf, text_rect)

class Button:
    def __init__(self, x, y, w, h, text, callback, color=GRAY, right_click_callback=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.right_click_callback = right_click_callback
        self.color = color
        self.hover_color = (min(color[0]+30, 255), min(color[1]+30, 255), min(color[2]+30, 255))

    def draw(self, surface, font):
        mouse_pos = pygame.mouse.get_pos()
        col = self.hover_color if self.rect.collidepoint(mouse_pos) else self.color
        
        pygame.draw.rect(surface, col, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)
        
        text_surf = font.render(self.text, True, BLACK)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                if event.button == 1:
                    self.callback()
                elif event.button == 3 and self.right_click_callback:
                    self.right_click_callback()

    def set_color(self, color):
        self.color = color
        self.hover_color = (min(color[0]+30, 255), min(color[1]+30, 255), min(color[2]+30, 255))

class InputBox:
    def __init__(self, x, y, w, h, text='', callback=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.base_w = w
        self.color_inactive = LIGHT_BLUE
        self.color_active = BLUE_ACTIVE
        self.color = self.color_inactive
        self.text = str(text)
        self.callback = callback
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            self.color = self.color_active if self.active else self.color_inactive
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                elif event.unicode.isprintable():
                    self.text += event.unicode
                if self.callback:
                    self.callback(self.text)

    def update_text(self, text):
        try:
            # Check if it's a number and large enough for scientific notation
            val = float(text)
            if abs(val) > 1e9:
                self.text = f"{val:.2e}"
            else:
                self.text = str(text)
        except OverflowError:
            # Handle numbers too big for float
            try:
                self.text = f"{text:.2e}"
            except:
                self.text = str(text)
        except:
            self.text = str(text)

    def update_dimensions(self, font):
        text_surf = font.render(self.text, True, BLACK)
        self.rect.w = max(self.base_w, text_surf.get_width() + 10)

    def draw(self, surface, font):
        text_surf = font.render(self.text, True, BLACK)
        pygame.draw.rect(surface, WHITE, self.rect)
        pygame.draw.rect(surface, self.color, self.rect, 2)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

class ScriptEditor:
    def __init__(self, width, height, font, on_save):
        # Center the editor
        w = int(width * 0.8)
        h = int(height * 0.8)
        x = (width - w) // 2
        y = (height - h) // 2
        self.rect = pygame.Rect(x, y, w, h)
        self.ui_font = font
        self.code_font = pygame.font.SysFont("Consolas", 20)
        self.lines = ["def power(level):", "    # Return an integer", "    return level + 1"]
        self.on_save = on_save
        self.active = False
        
        # Visuals
        self.bg_color = (40, 44, 52)
        self.text_color = (255, 255, 255)
        self.line_num_color = (100, 100, 100)
        self.cursor_visible = True
        self.last_blink = 0
        
        # Buttons relative to the editor rect
        self.save_btn = Button(x + w - 100, y + h - 50, 80, 40, "Save", self.save, color=GREEN)
        self.close_btn = Button(x + w - 200, y + h - 50, 80, 40, "Close", self.close, color=RED)
        self.error_msg = ""

    def resize(self, width, height):
        w = int(width * 0.8)
        h = int(height * 0.8)
        x = (width - w) // 2
        y = (height - h) // 2
        self.rect = pygame.Rect(x, y, w, h)
        self.save_btn.rect.topleft = (x + w - 100, y + h - 50)
        self.close_btn.rect.topleft = (x + w - 200, y + h - 50)

    def save(self):
        script = "\n".join(self.lines)
        success, msg = self.on_save(script)
        if success:
            self.active = False
            self.error_msg = ""
        else:
            self.error_msg = str(msg)

    def close(self):
        self.active = False
        self.error_msg = ""

    def handle_event(self, event):
        if not self.active: return
        
        self.save_btn.handle_event(event)
        self.close_btn.handle_event(event)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                if not self.lines: self.lines.append("")
                self.lines[-1] += "    "
            elif event.key == pygame.K_BACKSPACE:
                if self.lines:
                    if len(self.lines[-1]) > 0:
                        self.lines[-1] = self.lines[-1][:-1]
                    elif len(self.lines) > 1:
                        self.lines.pop()
            elif event.key == pygame.K_RETURN:
                self.lines.append("")
            elif event.unicode.isprintable():
                if not self.lines: self.lines.append("")
                self.lines[-1] += event.unicode

    def draw(self, surface):
        if not self.active: return
        
        # Dim background
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        
        # Editor Window
        pygame.draw.rect(surface, self.bg_color, self.rect)
        pygame.draw.rect(surface, WHITE, self.rect, 2)
        
        # Title
        title = self.ui_font.render("Python Script Editor - Define 'def power(level):'", True, WHITE)
        surface.blit(title, (self.rect.x + 20, self.rect.y + 10))

        # Code Lines
        line_h = self.code_font.get_height()
        y_off = 50
        
        # Cursor Blink
        if pygame.time.get_ticks() - self.last_blink > 500:
            self.cursor_visible = not self.cursor_visible
            self.last_blink = pygame.time.get_ticks()

        for i, line in enumerate(self.lines):
            if self.rect.y + y_off > self.rect.bottom - 60: break
            
            # Line Number
            num_surf = self.code_font.render(str(i + 1), True, self.line_num_color)
            surface.blit(num_surf, (self.rect.x + 10, self.rect.y + y_off))
            
            # Text
            txt_surf = self.code_font.render(line, True, self.text_color)
            surface.blit(txt_surf, (self.rect.x + 50, self.rect.y + y_off))
            
            # Cursor (End of last line)
            if i == len(self.lines) - 1 and self.cursor_visible:
                txt_w = txt_surf.get_width()
                cx = self.rect.x + 50 + txt_w
                cy = self.rect.y + y_off
                pygame.draw.line(surface, WHITE, (cx, cy), (cx, cy + line_h), 3)

            y_off += line_h
            
        # Error Message
        if self.error_msg:
            err = self.ui_font.render(f"Error: {self.error_msg}", True, RED)
            surface.blit(err, (self.rect.x + 20, self.rect.bottom - 80))

        # Buttons
        self.save_btn.draw(surface, self.ui_font)
        self.close_btn.draw(surface, self.ui_font)

class Game:
    def __init__(self):
        pygame.init()
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption("Ball Battle Simulation")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 16, bold=True)
        self.large_font = pygame.font.SysFont("Arial", 24, bold=True)

        self.balls = []
        self.running = True
        self.game_over = False
        
        # Control Panel State
        self.spawn_count = 3
        self.spawn_power = 3
        self.boss_health = 500
        self.minion_color = BLUE
        self.boss_color = RED
        self.palette = [RED, BLUE, GREEN, (255, 255, 0), (128, 0, 128), (255, 165, 0), (0, 255, 255), (255, 105, 180)]
        self.custom_script_func = None
        self.script_editor = ScriptEditor(self.width, self.height, self.font, self.save_script)

        self.create_ui()

    def create_ui(self):
        self.buttons = []
        self.input_boxes = []
        
        # Count Controls
        self.btn_count_minus = Button(0, 0, 30, 40, "-", lambda: self.adjust_count(-1))
        self.count_box = InputBox(0, 0, 50, 40, self.spawn_count, self.set_count_from_input)
        self.btn_count_plus = Button(0, 0, 30, 40, "+", lambda: self.adjust_count(1))
        
        # Power Controls (Function Input)
        self.btn_code = Button(0, 0, 50, 40, "Code", self.open_script_editor, color=BLUE)
        self.power_box = InputBox(0, 0, 80, 40, self.spawn_power, self.set_power_from_input)
        
        # Boss HP Controls
        self.btn_boss_minus = Button(0, 0, 30, 40, "-", lambda: self.adjust_boss_health(-50))
        self.boss_hp_box = InputBox(0, 0, 60, 40, self.boss_health, self.set_boss_health_from_input)
        self.btn_boss_plus = Button(0, 0, 30, 40, "+", lambda: self.adjust_boss_health(50))
        
        # Color Controls
        self.btn_minion_col = Button(0, 0, 80, 40, "Minion Col", self.cycle_minion_color, color=self.minion_color, right_click_callback=self.randomize_minion_color)
        self.btn_boss_col = Button(0, 0, 80, 40, "Boss Col", self.cycle_boss_color, color=self.boss_color, right_click_callback=self.randomize_boss_color)
        
        # Action Buttons
        self.btn_spawn_minions = Button(0, 0, 10, 50, "SPAWN MINIONS", self.spawn_minions, color=BLUE)
        self.btn_spawn_boss = Button(0, 0, 10, 50, "SPAWN BOSS", self.spawn_boss, color=RED)
        self.btn_reset = Button(0, 0, 10, 50, "RESET GAME", self.reset_game, color=DARK_GRAY)

        self.buttons = [
            self.btn_count_minus, self.btn_count_plus,
            self.btn_code,
            self.btn_boss_minus, self.btn_boss_plus,
            self.btn_minion_col, self.btn_boss_col,
            self.btn_spawn_minions, self.btn_spawn_boss, self.btn_reset
        ]
        self.input_boxes = [self.count_box, self.power_box, self.boss_hp_box]

    def update_layout(self):
        w = self.width
        game_h = self.height - PANEL_HEIGHT
        y_row1 = game_h + 35
        y_row2 = game_h + 90
        
        # Update dimensions of input boxes first
        for box in self.input_boxes:
            box.update_dimensions(self.font)
            
        # Calculate group widths based on current content
        g1_w = 30 + 5 + self.count_box.rect.w + 5 + 30
        g2_w = 50 + 10 + self.power_box.rect.w
        g3_w = 30 + 5 + self.boss_hp_box.rect.w + 5 + 30
        g4_w = 80 + 10 + 80
        
        total_w = g1_w + g2_w + g3_w + g4_w
        spacing = (w - total_w) / 5
        if spacing < 10: spacing = 10
        
        cur_x = spacing
        
        # Group 1: Count
        self.btn_count_minus.rect.topleft = (cur_x, y_row1)
        self.count_box.rect.topleft = (self.btn_count_minus.rect.right + 5, y_row1)
        self.btn_count_plus.rect.topleft = (self.count_box.rect.right + 5, y_row1)
        cur_x += g1_w + spacing
        
        # Group 2: Power
        self.btn_code.rect.topleft = (cur_x, y_row1)
        self.power_box.rect.topleft = (self.btn_code.rect.right + 10, y_row1)
        cur_x += g2_w + spacing
        
        # Group 3: Boss HP
        self.btn_boss_minus.rect.topleft = (cur_x, y_row1)
        self.boss_hp_box.rect.topleft = (self.btn_boss_minus.rect.right + 5, y_row1)
        self.btn_boss_plus.rect.topleft = (self.boss_hp_box.rect.right + 5, y_row1)
        cur_x += g3_w + spacing
        
        # Group 4: Colors
        self.btn_minion_col.rect.topleft = (cur_x, y_row1)
        self.btn_boss_col.rect.topleft = (self.btn_minion_col.rect.right + 10, y_row1)
        
        # Row 2: Actions
        btn_w = (w - 40) / 3
        self.btn_spawn_minions.rect = pygame.Rect(10, y_row2, btn_w, 50)
        self.btn_spawn_boss.rect = pygame.Rect(10 + btn_w + 10, y_row2, btn_w, 50)
        self.btn_reset.rect = pygame.Rect(10 + 2*btn_w + 20, y_row2, btn_w, 50)

    def adjust_count(self, amount):
        self.spawn_count = max(1, self.spawn_count + amount)
        self.count_box.update_text(self.spawn_count)

    def adjust_power(self, amount):
        try:
            val = int(self.spawn_power)
            self.spawn_power = max(1, val + amount)
            self.power_box.update_text(self.spawn_power)
        except:
            pass

    def adjust_boss_health(self, amount):
        self.boss_health = max(10, self.boss_health + amount)
        self.boss_hp_box.update_text(self.boss_health)

    def set_count_from_input(self, text):
        if text.isdigit() and text != "":
            self.spawn_count = int(text)
        else:
            self.spawn_count = 0

    def set_power_from_input(self, text):
        # If user types in box, disable custom script
        self.spawn_power = text
        self.custom_script_func = None

    def open_script_editor(self):
        self.script_editor.active = True

    def save_script(self, script_text):
        try:
            local_scope = {}
            # Allow math, random, time
            exec(script_text, {"math": math, "random": random, "time": time}, local_scope)
            if "power" in local_scope and callable(local_scope["power"]):
                self.custom_script_func = local_scope["power"]
                self.power_box.update_text("Custom Script")
                return True, "Saved!"
            else:
                return False, "Function 'power(level)' not found."
        except Exception as e:
            return False, str(e)

    def set_boss_health_from_input(self, text):
        if text == "":
            self.boss_health = 100
            return
        
        try:
            val = eval(text, {"__builtins__": None}, {"math": math})
            self.boss_health = int(val)
        except:
            pass

    def cycle_minion_color(self):
        if self.minion_color in self.palette:
            idx = self.palette.index(self.minion_color)
            self.minion_color = self.palette[(idx + 1) % len(self.palette)]
        else:
            self.minion_color = self.palette[0]
        self.btn_minion_col.set_color(self.minion_color)

    def cycle_boss_color(self):
        if self.boss_color in self.palette:
            idx = self.palette.index(self.boss_color)
            self.boss_color = self.palette[(idx + 1) % len(self.palette)]
        else:
            self.boss_color = self.palette[0]
        self.btn_boss_col.set_color(self.boss_color)

    def randomize_minion_color(self):
        self.minion_color = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
        self.btn_minion_col.set_color(self.minion_color)

    def randomize_boss_color(self):
        self.boss_color = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
        self.btn_boss_col.set_color(self.boss_color)

    def spawn_minions(self):
        if self.game_over: return
        game_h = self.height - PANEL_HEIGHT
        
        # Determine power configuration once
        initial_val = 1
        update_func = None
        
        if self.custom_script_func:
            update_func = self.custom_script_func
            try:
                initial_val = int(update_func(1))
            except:
                initial_val = 1
        else:
            try:
                allowed = {"random": random, "math": math, "time": time}
                val = eval(str(self.spawn_power), {"__builtins__": None}, allowed)
                if callable(val):
                    # This handles the old lambda logic if user types lambda in box
                    update_func = val
                    try:
                        initial_val = int(update_func(1))
                    except:
                        initial_val = 1
                else:
                    initial_val = int(val)
            except Exception as e:
                print(f"Error parsing power: {e}")
                initial_val = 1

        for i in range(self.spawn_count):
            # Spawn away from edges to prevent sticking
            x = random.randint(30, self.width - 30)
            y = random.randint(30, game_h - 30)
            
            # Small blue balls
            b = Ball(x, y, 15, self.minion_color, initial_val, is_boss=False, update_func=update_func)
            self.balls.append(b)

    def spawn_boss(self):
        if self.game_over: return
        # Remove existing bosses if you only want one, or keep them. Let's keep them.
        game_h = self.height - PANEL_HEIGHT
        x = self.width // 2
        y = game_h // 2
        # Big red ball
        b = Ball(x, y, 60, self.boss_color, self.boss_health, is_boss=True)
        self.balls.append(b)

    def reset_game(self):
        self.balls = []
        self.game_over = False

    def check_collisions(self):
        # Simple elastic collision logic
        for i in range(len(self.balls)):
            for j in range(i + 1, len(self.balls)):
                b1 = self.balls[i]
                b2 = self.balls[j]

                dx = b1.x - b2.x
                dy = b1.y - b2.y
                distance = math.hypot(dx, dy)

                if distance < b1.radius + b2.radius:
                    # 1. Resolve Overlap (prevent sticking)
                    overlap = (b1.radius + b2.radius - distance)
                    if distance == 0: distance = 0.1 # prevent div by zero
                    nx = dx / distance
                    ny = dy / distance
                    
                    # Move balls apart proportional to inverse mass (simplified: equal push)
                    move_dist = overlap / 2
                    b1.x += nx * move_dist
                    b1.y += ny * move_dist
                    b2.x -= nx * move_dist
                    b2.y -= ny * move_dist

                    # 2. Elastic Bounce Physics
                    # Tangent vector
                    tx = -ny
                    ty = nx

                    # Dot Product Tangent
                    dpTan1 = b1.vx * tx + b1.vy * ty
                    dpTan2 = b2.vx * tx + b2.vy * ty

                    # Dot Product Normal
                    dpNorm1 = b1.vx * nx + b1.vy * ny
                    dpNorm2 = b2.vx * nx + b2.vy * ny

                    # Conservation of momentum in 1D
                    m1 = b1.mass
                    m2 = b2.mass

                    p1 = (dpNorm1 * (m1 - m2) + 2 * m2 * dpNorm2) / (m1 + m2)
                    p2 = (dpNorm2 * (m2 - m1) + 2 * m1 * dpNorm1) / (m1 + m2)

                    # Update velocities
                    b1.vx = tx * dpTan1 + nx * p1
                    b1.vy = ty * dpTan1 + ny * p1
                    b2.vx = tx * dpTan2 + nx * p2
                    b2.vy = ty * dpTan2 + ny * p2

                    # 3. Game Logic (Damage)
                    self.handle_combat(b1, b2)

    def handle_combat(self, b1, b2):
        # If one is Boss and one is Minion
        boss = None
        minion = None

        if b1.is_boss and not b2.is_boss:
            boss = b1
            minion = b2
        elif b2.is_boss and not b1.is_boss:
            boss = b2
            minion = b1
        
        if boss and minion:
            boss.value -= minion.value
            
            # Level up minion logic
            minion.level += 1
            if minion.update_func:
                try:
                    minion.value = int(minion.update_func(minion.level))
                except Exception as e:
                    print(f"Script Error: {e}")
                    minion.value += 1
            else:
                minion.value += 1

            if boss.value <= 0:
                boss.value = 0

    def run(self):
        while self.running:
            try:
                # 1. Event Handling
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.VIDEORESIZE:
                        self.width = event.w
                        self.height = event.h
                        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                        self.script_editor.resize(self.width, self.height)
                        
                        # Clamp balls to new window size
                        game_h = self.height - PANEL_HEIGHT
                        for ball in self.balls:
                            if ball.x > self.width - ball.radius:
                                ball.x = self.width - ball.radius
                            if ball.y > game_h - ball.radius:
                                ball.y = game_h - ball.radius
                    
                    if self.script_editor.active:
                        self.script_editor.handle_event(event)
                        continue

                    for btn in self.buttons:
                        btn.handle_event(event)
                    
                    for box in self.input_boxes:
                        box.handle_event(event)

                # Update Layout every frame to handle resizing text boxes
                self.update_layout()

                # 2. Update
                game_h = self.height - PANEL_HEIGHT
                if not self.game_over:
                    for ball in self.balls:
                        ball.move(self.width, game_h)
                    
                    self.check_collisions()
                    
                    # Remove dead bosses and check for game over
                    had_bosses = any(b.is_boss for b in self.balls)
                    self.balls = [b for b in self.balls if not (b.is_boss and b.value <= 0)]
                    if had_bosses and not any(b.is_boss for b in self.balls):
                        self.game_over = True

                # 3. Draw
                self.screen.fill(WHITE)
                
                # Draw Game Area Background
                pygame.draw.rect(self.screen, (240, 240, 255), (0, 0, self.width, game_h))
                
                # Draw Balls
                for ball in self.balls:
                    ball.draw(self.screen, self.font)

                # Draw Control Panel Background
                pygame.draw.rect(self.screen, DARK_GRAY, (0, game_h, self.width, PANEL_HEIGHT))
                pygame.draw.line(self.screen, BLACK, (0, game_h), (self.width, game_h), 3)

                # Draw UI Labels
                # Count Label
                count_lbl = self.font.render("Count", True, WHITE)
                self.screen.blit(count_lbl, (self.count_box.rect.centerx - count_lbl.get_width()//2, game_h + 10))
                
                # Power Label
                power_lbl = self.font.render("Power (Function)", True, WHITE)
                self.screen.blit(power_lbl, (self.power_box.rect.centerx - power_lbl.get_width()//2, game_h + 10))

                # Boss HP Label
                boss_lbl = self.font.render("Boss HP", True, WHITE)
                self.screen.blit(boss_lbl, (self.boss_hp_box.rect.centerx - boss_lbl.get_width()//2, game_h + 10))

                # Draw Buttons
                for btn in self.buttons:
                    btn.draw(self.screen, self.font)
                
                # Draw Input Boxes
                for box in self.input_boxes:
                    box.draw(self.screen, self.font)
                
                # Draw Script Editor Overlay
                self.script_editor.draw(self.screen)

                # Draw Game Over Message
                if self.game_over:
                    msg = self.large_font.render("BOSS DEFEATED! SIMULATION STOPPED.", True, RED)
                    rect = msg.get_rect(center=(self.width//2, game_h//2))
                    pygame.draw.rect(self.screen, BLACK, rect.inflate(20, 20))
                    self.screen.blit(msg, rect)

                pygame.display.flip()
                self.clock.tick(FPS)
            except Exception as e:
                print(f"Game Loop Error: {e}")

        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()