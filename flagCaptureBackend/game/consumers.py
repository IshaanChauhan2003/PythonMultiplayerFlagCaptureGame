import json
import asyncio
import time
import math
from channels.generic.websocket import AsyncWebsocketConsumer
from .game_manager import game_manager

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'game_{self.room_id}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        self.team = game_manager.add_player(self.room_id, self.channel_name)
        
        if self.team:
            await self.send(text_data=json.dumps({
                'type': 'connection',
                'team': self.team
            }))
            
            if len(game_manager.rooms[self.room_id]['players']) == 2:
                asyncio.create_task(self.game_loop())
    
    async def disconnect(self, close_code):
        game_manager.remove_player(self.room_id, self.channel_name)
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get('type')
        
        if msg_type == 'move':
            self.handle_move(data)
        elif msg_type == 'dash':
            self.handle_dash(data)
        elif msg_type == 'ability':
            self.handle_ability(data)
        elif msg_type == 'pickup':
            self.handle_pickup(data)
        elif msg_type == 'drop':
            self.handle_drop(data)
    
    def handle_move(self, data):
        state = game_manager.get_game_state(self.room_id)
        if not state:
            return
        
        player = state['players'][self.team]
        if not player['alive']:
            return
        
        direction = data.get('direction')
        speed = 5
        
        # Calculate new position
        new_x = player['x']
        new_y = player['y']
        
        if direction == 'up':
            new_y -= speed
        elif direction == 'down':
            new_y += speed
        elif direction == 'left':
            new_x -= speed
        elif direction == 'right':
            new_x += speed
        
        # Check wall collision before moving
        if not game_manager.check_wall_collision(self.room_id, new_x, new_y):
            player['x'] = new_x
            player['y'] = new_y
            player['direction'] = direction
            
            # Keep within bounds
            player['x'] = max(0, min(800, player['x']))
            player['y'] = max(0, min(600, player['y']))
            
            self.check_pothole_collision(player)
    
    def handle_dash(self, data):
        state = game_manager.get_game_state(self.room_id)
        if not state:
            return
        
        player = state['players'][self.team]
        if not player['alive'] or player['dash_cooldown'] > 0:
            return
        
        direction = player['direction']
        dash_distance = 50
        
        # Calculate new position
        new_x = player['x']
        new_y = player['y']
        
        if direction == 'up':
            new_y -= dash_distance
        elif direction == 'down':
            new_y += dash_distance
        elif direction == 'left':
            new_x -= dash_distance
        elif direction == 'right':
            new_x += dash_distance
        
        # Check wall collision before dashing
        if not game_manager.check_wall_collision(self.room_id, new_x, new_y):
            player['x'] = new_x
            player['y'] = new_y
            
            # Keep within bounds
            player['x'] = max(0, min(800, player['x']))
            player['y'] = max(0, min(600, player['y']))
            player['dash_cooldown'] = 2.0
            
            self.check_pothole_collision(player)
        else:
            # Dash failed due to wall, still apply cooldown
            player['dash_cooldown'] = 2.0
    
    def handle_ability(self, data):
        state = game_manager.get_game_state(self.room_id)
        if not state:
            return
        
        player = state['players'][self.team]
        if not player['alive'] or not player['slow_unlocked']:
            return
        
        player['slow_unlocked'] = False
        player['slow_cooldown'] = 5.0
        
        enemy_team = 'red' if self.team == 'blue' else 'blue'
        state['players'][enemy_team]['slowed'] = True
    
    def handle_pickup(self, data):
        state = game_manager.get_game_state(self.room_id)
        if not state:
            return
        
        player = state['players'][self.team]
        if not player['alive'] or player['carrying_flag'] is not None:
            return
        
        enemy_team = 'red' if self.team == 'blue' else 'blue'
        
        # Try to pick up enemy flag (for capturing)
        for flag in state['flags'][enemy_team]:
            if flag['status'] in ['base', 'captured'] and self.distance(player, flag) < 30:
                player['carrying_flag'] = {'team': enemy_team, 'flag': flag}
                flag['status'] = 'carried'
                flag['carrier'] = self.team
                return
        
        # Try to recapture own flag from enemy base or enemy player
        for flag in state['flags'][self.team]:
            if flag['status'] == 'captured' and self.distance(player, flag) < 30:
                # Own flag is in enemy base, recapture it
                player['carrying_flag'] = {'team': self.team, 'flag': flag}
                flag['status'] = 'carried'
                flag['carrier'] = self.team
                # Decrease enemy score since they lost the flag
                state['scores'][enemy_team] = max(0, state['scores'][enemy_team] - 1)
                return
        
        # Try to recapture from enemy player (if adjacent)
        enemy_player = state['players'][enemy_team]
        if enemy_player['alive'] and enemy_player.get('carrying_flag'):
            if self.distance(player, enemy_player) < 40:  # Adjacent range
                carried_flag_data = enemy_player['carrying_flag']
                # Check if enemy is carrying our flag
                if carried_flag_data['team'] == self.team:
                    # Recapture our flag
                    player['carrying_flag'] = carried_flag_data
                    carried_flag_data['flag']['carrier'] = self.team
                    enemy_player['carrying_flag'] = None
                    return
    
    def handle_drop(self, data):
        state = game_manager.get_game_state(self.room_id)
        if not state:
            return
        
        player = state['players'][self.team]
        if not player['alive'] or player['carrying_flag'] is None:
            return
        
        flag_data = player['carrying_flag']
        flag = flag_data['flag']
        flag_team = flag_data['team']
        
        # Check if in own base to store
        if self.team == 'blue' and player['x'] < 150:
            if flag_team == 'red':
                # Storing enemy flag
                self.store_flag(state, player)
            else:
                # Returning own flag to base
                self.return_flag_to_base(state, player, flag)
        elif self.team == 'red' and player['x'] > 650:
            if flag_team == 'blue':
                # Storing enemy flag
                self.store_flag(state, player)
            else:
                # Returning own flag to base
                self.return_flag_to_base(state, player, flag)
        else:
            # Drop flag at current location
            flag['x'] = player['x']
            flag['y'] = player['y']
            flag['status'] = 'dropped'
            player['carrying_flag'] = None
    
    def return_flag_to_base(self, state, player, flag):
        """Return own flag back to base"""
        # Find original position or first available slot
        my_flags = state['flags'][self.team]
        base_positions = {
            'blue': [(80, 200), (80, 300), (80, 400)],
            'red': [(720, 200), (720, 300), (720, 400)]
        }
        
        # Find the flag's original index
        flag_index = my_flags.index(flag)
        original_pos = base_positions[self.team][flag_index]
        
        flag['x'] = original_pos[0]
        flag['y'] = original_pos[1]
        flag['status'] = 'base'
        player['carrying_flag'] = None
    
    def store_flag(self, state, player):
        flag_data = player['carrying_flag']
        captured_flag = flag_data['flag']
        captured_flag['status'] = 'captured'
        
        # Move the captured flag to the player's base next to their own flags
        my_flags = state['flags'][self.team]
        
        # Find the next available position next to own flags
        if self.team == 'blue':
            # Blue base is on the left, stack captured flags to the right of own flags
            base_x = 120  # Right of blue flags
            base_y_positions = [200, 300, 400]
            captured_count = sum(1 for f in state['flags']['red'] if f['status'] == 'captured')
            captured_flag['x'] = base_x
            captured_flag['y'] = base_y_positions[min(captured_count, 2)]
        else:
            # Red base is on the right, stack captured flags to the left of own flags
            base_x = 680  # Left of red flags
            base_y_positions = [200, 300, 400]
            captured_count = sum(1 for f in state['flags']['blue'] if f['status'] == 'captured')
            captured_flag['x'] = base_x
            captured_flag['y'] = base_y_positions[min(captured_count, 2)]
        
        player['carrying_flag'] = None
        state['scores'][self.team] += 1
        player['slow_unlocked'] = True
    
    def check_pothole_collision(self, player):
        state = game_manager.get_game_state(self.room_id)
        for pothole in state['potholes']:
            if self.distance(player, pothole) < 25:
                player['alive'] = False
                player['respawn_time'] = 4.0
                if player['carrying_flag']:
                    flag_data = player['carrying_flag']
                    flag = flag_data['flag']
                    flag_team = flag_data['team']
                    
                    # Return flag to its last valid location
                    if flag_team == self.team:
                        # Own flag returns to base
                        my_flags = state['flags'][self.team]
                        flag_index = my_flags.index(flag)
                        base_positions = {
                            'blue': [(80, 200), (80, 300), (80, 400)],
                            'red': [(720, 200), (720, 300), (720, 400)]
                        }
                        original_pos = base_positions[self.team][flag_index]
                        flag['x'] = original_pos[0]
                        flag['y'] = original_pos[1]
                        flag['status'] = 'base'
                    else:
                        # Enemy flag returns to enemy base if not yet captured
                        enemy_team = 'red' if self.team == 'blue' else 'blue'
                        enemy_flags = state['flags'][enemy_team]
                        flag_index = enemy_flags.index(flag)
                        base_positions = {
                            'blue': [(80, 200), (80, 300), (80, 400)],
                            'red': [(720, 200), (720, 300), (720, 400)]
                        }
                        original_pos = base_positions[enemy_team][flag_index]
                        flag['x'] = original_pos[0]
                        flag['y'] = original_pos[1]
                        flag['status'] = 'base'
                    
                    player['carrying_flag'] = None
    
    def distance(self, obj1, obj2):
        return math.sqrt((obj1['x'] - obj2['x'])**2 + (obj1['y'] - obj2['y'])**2)
    
    async def game_loop(self):
        while True:
            await asyncio.sleep(0.05)
            
            state = game_manager.get_game_state(self.room_id)
            if not state:
                break
            
            current_time = time.time()
            elapsed = current_time - state['start_time']
            state['game_time'] = max(0, 180 - elapsed)
            
            for team in ['blue', 'red']:
                player = state['players'][team]
                
                if not player['alive']:
                    player['respawn_time'] -= 0.05
                    if player['respawn_time'] <= 0:
                        player['alive'] = True
                        player['x'] = 100 if team == 'blue' else 700
                        player['y'] = 300
                
                if player['dash_cooldown'] > 0:
                    player['dash_cooldown'] -= 0.05
                
                if player.get('slowed'):
                    player['slow_cooldown'] -= 0.05
                    if player['slow_cooldown'] <= 0:
                        player['slowed'] = False
            
            self.check_win_condition(state)
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'game_update',
                    'state': state
                }
            )
    
    def check_win_condition(self, state):
        if state['winner']:
            return
        
        blue_score = state['scores']['blue']
        red_score = state['scores']['red']
        blue_flags = sum(1 for f in state['flags']['blue'] if f['status'] == 'base')
        red_flags = sum(1 for f in state['flags']['red'] if f['status'] == 'base')
        
        if blue_score >= 3 and blue_flags >= 1:
            state['winner'] = 'blue'
        elif red_score >= 3 and red_flags >= 1:
            state['winner'] = 'red'
        elif state['game_time'] <= 0:
            if blue_score > red_score and blue_flags >= 1:
                state['winner'] = 'blue'
            elif red_score > blue_score and red_flags >= 1:
                state['winner'] = 'red'
    
    async def game_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'game_state',
            'state': event['state']
        }))
