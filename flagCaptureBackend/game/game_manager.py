import time
import math

class GameManager:
    def __init__(self):
        self.rooms = {}
    
    def create_room(self, room_id, passcode, walls=None):
        self.rooms[room_id] = {
            'passcode': passcode,
            'players': {},
            'game_state': self.init_game_state(),
            'started': False,
            'walls': walls or []
        }
    
    def validate_room(self, room_id, passcode):
        room = self.rooms.get(room_id)
        if room and room['passcode'] == passcode:
            return True
        return False
    
    def init_game_state(self):
        return {
            'players': {
                'blue': {
                    'x': 100, 'y': 300, 'direction': 'right',
                    'carrying_flag': None, 'alive': True,
                    'respawn_time': 0, 'dash_cooldown': 0,
                    'slow_unlocked': False, 'slow_cooldown': 0
                },
                'red': {
                    'x': 700, 'y': 300, 'direction': 'left',
                    'carrying_flag': None, 'alive': True,
                    'respawn_time': 0, 'dash_cooldown': 0,
                    'slow_unlocked': False, 'slow_cooldown': 0
                }
            },
            'flags': {
                'blue': [
                    {'x': 80, 'y': 200, 'status': 'base'},
                    {'x': 80, 'y': 300, 'status': 'base'},
                    {'x': 80, 'y': 400, 'status': 'base'}
                ],
                'red': [
                    {'x': 720, 'y': 200, 'status': 'base'},
                    {'x': 720, 'y': 300, 'status': 'base'},
                    {'x': 720, 'y': 400, 'status': 'base'}
                ]
            },
            'scores': {'blue': 0, 'red': 0},
            'potholes': [
                {'x': 300, 'y': 250}, {'x': 350, 'y': 300},
                {'x': 450, 'y': 350}, {'x': 500, 'y': 250}
            ],
            'game_time': 180,
            'start_time': time.time(),
            'winner': None
        }
    
    def add_player(self, room_id, player_id):
        room = self.rooms.get(room_id)
        if not room:
            return None
        
        if len(room['players']) >= 2:
            return None
        
        team = 'blue' if len(room['players']) == 0 else 'red'
        room['players'][player_id] = team
        
        if len(room['players']) == 2:
            room['started'] = True
            room['game_state']['start_time'] = time.time()
        
        return team
    
    def remove_player(self, room_id, player_id):
        room = self.rooms.get(room_id)
        if room and player_id in room['players']:
            del room['players'][player_id]
    
    def get_game_state(self, room_id):
        room = self.rooms.get(room_id)
        return room['game_state'] if room else None
    
    def update_player_position(self, room_id, team, x, y, direction):
        state = self.get_game_state(room_id)
        if state and team in state['players']:
            state['players'][team]['x'] = x
            state['players'][team]['y'] = y
            state['players'][team]['direction'] = direction
    
    def check_wall_collision(self, room_id, x, y, player_radius=20):
        """Check if position collides with any walls"""
        room = self.rooms.get(room_id)
        if not room:
            return False
        
        for wall in room['walls']:
            # Check if player circle intersects with wall rectangle
            wall_left = wall['x'] - wall['width'] / 2
            wall_right = wall['x'] + wall['width'] / 2
            wall_top = wall['y'] - wall['height'] / 2
            wall_bottom = wall['y'] + wall['height'] / 2
            
            closest_x = max(wall_left, min(x, wall_right))
            closest_y = max(wall_top, min(y, wall_bottom))
            
            distance_x = x - closest_x
            distance_y = y - closest_y
            distance_squared = distance_x**2 + distance_y**2
            
            if distance_squared < player_radius**2:
                return True
        return False

game_manager = GameManager()
