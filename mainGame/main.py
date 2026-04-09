import pygame
import sys
import json
import threading
import math
from game_client import GameClient

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Capture The Flag")

# Load and scale sprites with smooth scaling
SPRITE_SIZE = (64, 64)  # Adjust this size as needed

def load_sprite(path, size):
    """Load and smoothly scale sprite to maintain quality"""
    img = pygame.image.load(path).convert_alpha()
    return pygame.transform.smoothscale(img, size)

blue_sprites = {
    'idle': load_sprite('assets/spr/blue_idle.png', SPRITE_SIZE),
    'horizontal': load_sprite('assets/spr/blue_horizontal.png', SPRITE_SIZE),
    'vertical_front': load_sprite('assets/spr/blue_vertical_front.png', SPRITE_SIZE),
    'vertical_back': load_sprite('assets/spr/blue_vertical_back.png', SPRITE_SIZE)
}

red_sprites = {
    'idle': load_sprite('assets/spr/red_Idle.png', SPRITE_SIZE),
    'horizontal': load_sprite('assets/spr/red_horizontal.png', SPRITE_SIZE),
    'vertical_front': load_sprite('assets/spr/red_vertical_front.png', SPRITE_SIZE),
    'vertical_back': load_sprite('assets/spr/red_vertical_back.png', SPRITE_SIZE)
}

# Load map configuration
def load_map(filename='map_config.txt'):
    """Load map layout from config file"""
    walls = []
    potholes = []
    
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
            
        tile_width = SCREEN_WIDTH // 32  # 32 columns
        tile_height = SCREEN_HEIGHT // len(lines)
        
        for row, line in enumerate(lines):
            for col, char in enumerate(line.strip()):
                x = col * tile_width + tile_width // 2
                y = row * tile_height + tile_height // 2
                
                if char == 'W':
                    walls.append({
                        'x': x,
                        'y': y,
                        'width': tile_width,
                        'height': tile_height,
                        'rect': pygame.Rect(x - tile_width//2, y - tile_height//2, tile_width, tile_height)
                    })
                elif char == 'P':
                    potholes.append({
                        'x': x,
                        'y': y,
                        'radius': min(tile_width, tile_height) // 3
                    })
    except FileNotFoundError:
        print("Map config not found, using empty map")
    
    return walls, potholes

map_walls, map_potholes = load_map()

client = GameClient(walls=map_walls)

# Colors
BG_COLOR = (25, 25, 40)
BUTTON_COLOR = (60, 60, 100)
BUTTON_HOVER = (80, 80, 140)
TEXT_COLOR = (255, 255, 255)
ACCENT_BLUE = (0, 150, 255)
ACCENT_RED = (255, 50, 80)
INPUT_BG = (40, 40, 60)
INPUT_ACTIVE = (50, 50, 80)

class Button:
    def __init__(self, x, y, width, height, text, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover = False
    
    def draw(self, screen, font):
        color = BUTTON_HOVER if self.hover else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, TEXT_COLOR, self.rect, 2, border_radius=10)
        
        text_surf = font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
    
    def check_hover(self, pos):
        self.hover = self.rect.collidepoint(pos)
        return self.hover
    
    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

class InputBox:
    def __init__(self, x, y, width, height, label):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.text = ''
        self.active = False
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                return True
            elif len(self.text) < 20:
                self.text += event.unicode
        return False
    
    def draw(self, screen, font, small_font):
        color = INPUT_ACTIVE if self.active else INPUT_BG
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, TEXT_COLOR if self.active else (100, 100, 120), 
                        self.rect, 2, border_radius=5)
        
        label_surf = small_font.render(self.label, True, (180, 180, 200))
        screen.blit(label_surf, (self.rect.x, self.rect.y - 25))
        
        text_surf = font.render(self.text, True, TEXT_COLOR)
        screen.blit(text_surf, (self.rect.x + 10, self.rect.y + 10))

def main_menu():
    font = pygame.font.Font(None, 48)
    medium_font = pygame.font.Font(None, 32)
    small_font = pygame.font.Font(None, 24)
    
    create_btn = Button(250, 300, 300, 60, "Create Room", ACCENT_BLUE)
    join_btn = Button(250, 380, 300, 60, "Join Room", ACCENT_RED)
    
    clock = pygame.time.Clock()
    
    while True:
        mouse_pos = pygame.mouse.get_pos()
        create_btn.check_hover(mouse_pos)
        join_btn.check_hover(mouse_pos)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if create_btn.is_clicked(mouse_pos):
                    return 'create'
                elif join_btn.is_clicked(mouse_pos):
                    return 'join'
        
        screen.fill(BG_COLOR)
        
        title = font.render("CAPTURE THE FLAG", True, TEXT_COLOR)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 80))
        
        subtitle = small_font.render("1v1 Top-Down Arena", True, (150, 150, 170))
        screen.blit(subtitle, (SCREEN_WIDTH//2 - subtitle.get_width()//2, 140))
        
        pygame.draw.line(screen, ACCENT_BLUE, (200, 180), (400, 180), 2)
        pygame.draw.line(screen, ACCENT_RED, (400, 180), (600, 180), 2)
        
        create_btn.draw(screen, medium_font)
        join_btn.draw(screen, medium_font)
        
        controls = [
            "Controls: WASD - Move | E - Dash | Q - Ability",
            "Left Click - Pickup Flag | Right Click - Drop Flag",
            "Objective: Capture 3 enemy flags while keeping 1 of yours"
        ]
        for i, text in enumerate(controls):
            control_surf = small_font.render(text, True, (120, 120, 140))
            screen.blit(control_surf, (SCREEN_WIDTH//2 - control_surf.get_width()//2, 470 + i*25))
        
        pygame.display.flip()
        clock.tick(60)

def game_loop():
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)
    
    # Track player facing directions
    player_directions = {
        'blue': {'facing': 'right', 'last_move': 'idle'},
        'red': {'facing': 'right', 'last_move': 'idle'}
    }
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                client.disconnect()
                pygame.quit()
                sys.exit()
        
        keys = pygame.key.get_pressed()
        
        if keys[pygame.K_w]:
            client.send_move('up')
        elif keys[pygame.K_s]:
            client.send_move('down')
        elif keys[pygame.K_a]:
            client.send_move('left')
        elif keys[pygame.K_d]:
            client.send_move('right')
        
        if keys[pygame.K_e]:
            client.send_dash()
        
        if keys[pygame.K_q]:
            client.send_ability()
        
        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[0]:  # Left click - pickup
            client.send_pickup()
        if mouse_buttons[2]:  # Right click - drop
            client.send_drop()
        
        screen.fill((50, 50, 50))
        
        if client.game_state:
            draw_game(screen, client.game_state, client.team, font, player_directions)
        
        pygame.display.flip()
        clock.tick(60)

def draw_transparent_rect(surface, color, rect, alpha=180):
    """Draw a semi-transparent rectangle with blur effect simulation"""
    s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(s, (*color, alpha), s.get_rect(), border_radius=10)
    surface.blit(s, rect.topleft)

def draw_ability_circle(screen, x, y, radius, letter, cooldown, is_ready, is_active, font):
    """Draw ability indicator circle with cooldown/status"""
    # Background circle
    if is_active:
        bg_color = (100, 255, 100, 200)  # Green when active
    elif is_ready:
        bg_color = (80, 80, 120, 200)  # Normal when ready
    else:
        bg_color = (40, 40, 60, 200)  # Dark when locked
    
    s = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
    pygame.draw.circle(s, bg_color, (radius, radius), radius)
    pygame.draw.circle(s, (255, 255, 255, 150), (radius, radius), radius, 3)
    screen.blit(s, (x - radius, y - radius))
    
    # Cooldown arc
    if cooldown > 0:
        draw_cooldown_arc(screen, x, y, radius - 5, cooldown, letter == 'E' and 2.0 or 5.0)
    
    # Text
    if cooldown > 0 and cooldown < (2.0 if letter == 'E' else 5.0):
        text = font.render(f"{cooldown:.2f}", True, (255, 255, 100))
    elif not is_ready and letter == 'Q':
        text = font.render(letter, True, (100, 100, 100))  # Grey when locked
    else:
        text = font.render(letter, True, (255, 255, 255))
    
    text_rect = text.get_rect(center=(x, y))
    screen.blit(text, text_rect)

def draw_cooldown_arc(screen, x, y, radius, current, max_time):
    """Draw cooldown progress arc"""
    progress = 1 - (current / max_time)
    angle = int(360 * progress)
    
    points = [(x, y)]
    for i in range(angle + 1):
        rad = math.radians(i - 90)
        px = x + radius * math.cos(rad)
        py = y + radius * math.sin(rad)
        points.append((px, py))
    
    if len(points) > 2:
        s = pygame.Surface((radius*2 + 10, radius*2 + 10), pygame.SRCALPHA)
        offset_points = [(p[0] - x + radius + 5, p[1] - y + radius + 5) for p in points]
        pygame.draw.polygon(s, (100, 200, 255, 100), offset_points)
        screen.blit(s, (x - radius - 5, y - radius - 5))

def draw_flag_slots(screen, x, y, flags, team_color, is_enemy=False):
    """Draw flag storage slots"""
    slot_size = 30
    spacing = 10
    
    for i in range(3):
        slot_x = x + i * (slot_size + spacing)
        
        # Determine flag status
        if i < len(flags):
            flag = flags[i]
            if is_enemy:
                # For enemy flags, show if captured by us
                is_filled = flag['status'] == 'captured'
            else:
                # For our flags, show if still in base
                is_filled = flag['status'] == 'base'
        else:
            is_filled = False
        
        # Draw slot
        if is_filled:
            color = (100, 255, 100, 200)  # Green when filled
        else:
            color = (60, 60, 60, 200)  # Grey when empty
        
        s = pygame.Surface((slot_size, slot_size), pygame.SRCALPHA)
        pygame.draw.rect(s, color, s.get_rect(), border_radius=5)
        pygame.draw.rect(s, (255, 255, 255, 150), s.get_rect(), 2, border_radius=5)
        screen.blit(s, (slot_x, y))
        
        # Draw flag icon if filled
        if is_filled:
            pygame.draw.circle(screen, team_color, (slot_x + slot_size//2, y + slot_size//2), 8)

def draw_player_ui(screen, x, y, team, player, flags, my_flags, is_my_team, font, small_font):
    """Draw player UI panel"""
    panel_width = 220
    panel_height = 140
    
    # Semi-transparent background
    draw_transparent_rect(screen, (20, 20, 30), pygame.Rect(x, y, panel_width, panel_height), 180)
    
    team_color = ACCENT_BLUE if team == 'blue' else ACCENT_RED
    
    # Team name
    team_text = font.render(team.upper(), True, team_color)
    screen.blit(team_text, (x + 10, y + 10))
    
    # Status
    status = "ALIVE" if player['alive'] else f"RESPAWN: {int(player['respawn_time'])}s"
    status_color = (100, 255, 100) if player['alive'] else (255, 100, 100)
    status_text = small_font.render(status, True, status_color)
    screen.blit(status_text, (x + 10, y + 35))
    
    # Flag slots label
    label_text = small_font.render("My Flags:" if is_my_team else "Captured:", True, (180, 180, 200))
    screen.blit(label_text, (x + 10, y + 60))
    
    # Flag slots
    draw_flag_slots(screen, x + 10, y + 85, my_flags if is_my_team else flags, team_color, not is_my_team)
    
    # Abilities (only show for my team)
    if is_my_team:
        # Dash ability (E)
        dash_cd = max(0, player.get('dash_cooldown', 0))
        draw_ability_circle(screen, x + 170, y + 50, 25, 'E', dash_cd, True, False, font)
        
        # Slow ability (Q)
        slow_unlocked = player.get('slow_unlocked', False)
        slow_cd = max(0, player.get('slow_cooldown', 0))
        is_slowing = slow_cd > 0 and slow_unlocked == False
        draw_ability_circle(screen, x + 170, y + 100, 25, 'Q', slow_cd if is_slowing else 0, 
                          slow_unlocked, is_slowing, font)

def get_player_sprite(team, player_data, sprites, direction_data):
    """Get the appropriate sprite for a player based on their movement"""
    # Determine which sprite to use based on last position change
    prev_x = direction_data.get('prev_x', player_data['x'])
    prev_y = direction_data.get('prev_y', player_data['y'])
    
    current_x = player_data['x']
    current_y = player_data['y']
    
    # Update stored position
    direction_data['prev_x'] = current_x
    direction_data['prev_y'] = current_y
    
    # Determine movement and sprite
    dx = current_x - prev_x
    dy = current_y - prev_y
    
    flip = False
    
    if abs(dx) > abs(dy):  # Horizontal movement
        if dx != 0:
            direction_data['facing'] = 'left' if dx < 0 else 'right'
            direction_data['last_move'] = 'horizontal'
        sprite = sprites['horizontal']
        flip = direction_data['facing'] == 'left'
    elif dy > 0.1:  # Moving down
        sprite = sprites['vertical_front']
        direction_data['last_move'] = 'down'
    elif dy < -0.1:  # Moving up
        sprite = sprites['vertical_back']
        direction_data['last_move'] = 'up'
    else:  # Idle
        if direction_data['last_move'] == 'horizontal':
            sprite = sprites['horizontal']
            flip = direction_data['facing'] == 'left'
        elif direction_data['last_move'] == 'down':
            sprite = sprites['vertical_front']
        elif direction_data['last_move'] == 'up':
            sprite = sprites['vertical_back']
        else:
            sprite = sprites['idle']
            flip = direction_data['facing'] == 'left'
    
    return sprite, flip

def draw_game(screen, state, my_team, font, player_directions):
    import math
    
    players = state['players']
    flags = state['flags']
    potholes = state['potholes']
    scores = state['scores']
    game_time = state.get('game_time', 180)
    
    small_font = pygame.font.Font(None, 20)
    medium_font = pygame.font.Font(None, 24)
    
    # Draw walls from map config
    for wall in map_walls:
        pygame.draw.rect(screen, (60, 60, 80), wall['rect'])
        pygame.draw.rect(screen, (100, 100, 120), wall['rect'], 2)
    
    # Draw potholes from map config
    for pothole in map_potholes:
        pygame.draw.circle(screen, (20, 20, 20), (int(pothole['x']), int(pothole['y'])), pothole['radius'])
        pygame.draw.circle(screen, (100, 50, 50), (int(pothole['x']), int(pothole['y'])), pothole['radius'], 2)
    
    # Draw potholes from server (if any)
    for pothole in potholes:
        pygame.draw.circle(screen, (20, 20, 20), (int(pothole['x']), int(pothole['y'])), 20)
        pygame.draw.circle(screen, (100, 50, 50), (int(pothole['x']), int(pothole['y'])), 20, 2)
    
    # Draw flags
    for flag in flags['blue']:
        if flag['status'] not in ['carried']:
            pygame.draw.circle(screen, (0, 100, 255), (int(flag['x']), int(flag['y'])), 10)
            pygame.draw.circle(screen, (100, 150, 255), (int(flag['x']), int(flag['y'])), 10, 2)
            # Add a border if captured
            if flag['status'] == 'captured':
                pygame.draw.circle(screen, (255, 215, 0), (int(flag['x']), int(flag['y'])), 13, 2)
            # Add a pulsing effect if dropped
            elif flag['status'] == 'dropped':
                pygame.draw.circle(screen, (255, 255, 100), (int(flag['x']), int(flag['y'])), 15, 2)
    
    for flag in flags['red']:
        if flag['status'] not in ['carried']:
            pygame.draw.circle(screen, (255, 50, 50), (int(flag['x']), int(flag['y'])), 10)
            pygame.draw.circle(screen, (255, 100, 100), (int(flag['x']), int(flag['y'])), 10, 2)
            # Add a border if captured
            if flag['status'] == 'captured':
                pygame.draw.circle(screen, (255, 215, 0), (int(flag['x']), int(flag['y'])), 13, 2)
            # Add a pulsing effect if dropped
            elif flag['status'] == 'dropped':
                pygame.draw.circle(screen, (255, 255, 100), (int(flag['x']), int(flag['y'])), 15, 2)
    
    # Draw players with sprites
    blue_player = players['blue']
    if blue_player['alive']:
        sprite, flip = get_player_sprite('blue', blue_player, blue_sprites, player_directions['blue'])
        sprite_rect = sprite.get_rect(center=(int(blue_player['x']), int(blue_player['y'])))
        
        if flip:
            sprite = pygame.transform.flip(sprite, True, False)
        
        screen.blit(sprite, sprite_rect)
        
        # Draw carried flag above player
        if blue_player.get('carrying_flag'):
            flag_team = blue_player['carrying_flag']['team']
            flag_color = (255, 50, 50) if flag_team == 'red' else (0, 100, 255)
            pygame.draw.circle(screen, flag_color, 
                             (int(blue_player['x']), int(blue_player['y']) - 25), 8)
    
    red_player = players['red']
    if red_player['alive']:
        sprite, flip = get_player_sprite('red', red_player, red_sprites, player_directions['red'])
        sprite_rect = sprite.get_rect(center=(int(red_player['x']), int(red_player['y'])))
        
        if flip:
            sprite = pygame.transform.flip(sprite, True, False)
        
        screen.blit(sprite, sprite_rect)
        
        # Draw carried flag above player
        if red_player.get('carrying_flag'):
            flag_team = red_player['carrying_flag']['team']
            flag_color = (255, 50, 50) if flag_team == 'red' else (0, 100, 255)
            pygame.draw.circle(screen, flag_color, 
                             (int(red_player['x']), int(red_player['y']) - 25), 8)
    
    # Timer at top center
    timer_width = 200
    timer_height = 60
    timer_x = SCREEN_WIDTH//2 - timer_width//2
    timer_y = 10
    draw_transparent_rect(screen, (20, 20, 30), pygame.Rect(timer_x, timer_y, timer_width, timer_height), 200)
    
    minutes = int(game_time) // 60
    seconds = int(game_time) % 60
    time_text = font.render(f"{minutes:02d}:{seconds:02d}", True, (255, 255, 255))
    time_rect = time_text.get_rect(center=(SCREEN_WIDTH//2, timer_y + 30))
    screen.blit(time_text, time_rect)
    
    # Blue player UI (bottom left)
    if my_team == 'blue':
        draw_player_ui(screen, 10, SCREEN_HEIGHT - 150, 'blue', blue_player, 
                      flags['red'], flags['blue'], True, medium_font, small_font)
        # Red player UI (top right) - minimal
        draw_player_ui(screen, SCREEN_WIDTH - 230, 10, 'red', red_player, 
                      flags['blue'], flags['red'], False, medium_font, small_font)
    else:
        draw_player_ui(screen, 10, SCREEN_HEIGHT - 150, 'red', red_player, 
                      flags['blue'], flags['red'], True, medium_font, small_font)
        # Blue player UI (top right) - minimal
        draw_player_ui(screen, SCREEN_WIDTH - 230, 10, 'blue', blue_player, 
                      flags['red'], flags['blue'], False, medium_font, small_font)
    
    # Winner announcement
    if state.get('winner'):
        winner_bg = pygame.Rect(SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT//2 - 50, 400, 100)
        draw_transparent_rect(screen, (20, 20, 30), winner_bg, 230)
        
        winner_color = ACCENT_BLUE if state['winner'] == 'blue' else ACCENT_RED
        winner_text = font.render(f"{state['winner'].upper()} WINS!", True, winner_color)
        winner_rect = winner_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        screen.blit(winner_text, winner_rect)

def create_room_screen():
    font = pygame.font.Font(None, 36)
    medium_font = pygame.font.Font(None, 28)
    small_font = pygame.font.Font(None, 22)
    clock = pygame.time.Clock()
    
    room_info = client.create_room()
    room_id = room_info['room_id']
    passcode = room_info['passcode']
    
    start_btn = Button(300, 450, 200, 50, "Start Game", ACCENT_BLUE)
    
    while True:
        mouse_pos = pygame.mouse.get_pos()
        start_btn.check_hover(mouse_pos)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_btn.is_clicked(mouse_pos):
                    client.connect_websocket(room_id)
                    return
        
        screen.fill(BG_COLOR)
        
        title = font.render("Room Created!", True, ACCENT_BLUE)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100))
        
        info_texts = [
            ("Share these with Player 2:", (180, 180, 200)),
            (f"Room ID: {room_id}", TEXT_COLOR),
            (f"Passcode: {passcode}", TEXT_COLOR),
        ]
        
        y_pos = 200
        for text, color in info_texts:
            if "Room ID" in text or "Passcode" in text:
                surf = medium_font.render(text, True, color)
                pygame.draw.rect(screen, INPUT_BG, 
                               (SCREEN_WIDTH//2 - 150, y_pos - 10, 300, 50), border_radius=5)
                pygame.draw.rect(screen, ACCENT_BLUE, 
                               (SCREEN_WIDTH//2 - 150, y_pos - 10, 300, 50), 2, border_radius=5)
            else:
                surf = small_font.render(text, True, color)
            screen.blit(surf, (SCREEN_WIDTH//2 - surf.get_width()//2, y_pos))
            y_pos += 70 if "Room ID" in text or "Passcode" in text else 40
        
        waiting = small_font.render("Waiting for Player 2 to join...", True, (150, 150, 170))
        screen.blit(waiting, (SCREEN_WIDTH//2 - waiting.get_width()//2, 380))
        
        start_btn.draw(screen, medium_font)
        
        pygame.display.flip()
        clock.tick(60)

def join_room_screen():
    font = pygame.font.Font(None, 36)
    medium_font = pygame.font.Font(None, 28)
    small_font = pygame.font.Font(None, 22)
    clock = pygame.time.Clock()
    
    room_id_input = InputBox(250, 220, 300, 45, "Room ID")
    passcode_input = InputBox(250, 310, 300, 45, "Passcode")
    join_btn = Button(300, 400, 200, 50, "Join Game", ACCENT_RED)
    back_btn = Button(300, 470, 200, 50, "Back", BUTTON_COLOR)
    
    error_msg = ""
    
    while True:
        mouse_pos = pygame.mouse.get_pos()
        join_btn.check_hover(mouse_pos)
        back_btn.check_hover(mouse_pos)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            room_id_input.handle_event(event)
            passcode_input.handle_event(event)
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if join_btn.is_clicked(mouse_pos):
                    if room_id_input.text and passcode_input.text:
                        if client.join_room(room_id_input.text, passcode_input.text):
                            client.connect_websocket(room_id_input.text)
                            return
                        else:
                            error_msg = "Invalid Room ID or Passcode!"
                    else:
                        error_msg = "Please fill in all fields!"
                elif back_btn.is_clicked(mouse_pos):
                    return main()
        
        screen.fill(BG_COLOR)
        
        title = font.render("Join Room", True, ACCENT_RED)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100))
        
        room_id_input.draw(screen, medium_font, small_font)
        passcode_input.draw(screen, medium_font, small_font)
        join_btn.draw(screen, medium_font)
        back_btn.draw(screen, medium_font)
        
        if error_msg:
            error_surf = small_font.render(error_msg, True, ACCENT_RED)
            screen.blit(error_surf, (SCREEN_WIDTH//2 - error_surf.get_width()//2, 540))
        
        pygame.display.flip()
        clock.tick(60)

def main():
    choice = main_menu()
    
    if choice == 'create':
        create_room_screen()
    elif choice == 'join':
        join_room_screen()
    
    game_loop()

if __name__ == '__main__':
    main()
