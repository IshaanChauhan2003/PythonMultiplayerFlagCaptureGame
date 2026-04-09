import requests
import websocket
import json
import threading
import time

class GameClient:
    def __init__(self, walls=None):
        self.base_url = "http://localhost:8000/api"
        self.ws_url = "ws://localhost:8000/ws/game"
        self.ws = None
        self.game_state = None
        self.team = None
        self.running = False
        self.last_dash = 0
        self.last_ability = 0
        self.last_interact = 0
        self.walls = walls or []
        self.player_radius = 20  # Half of sprite size for collision
    
    def create_room(self):
        # Send wall data to backend
        wall_data = [{'x': w['x'], 'y': w['y'], 'width': w['width'], 'height': w['height']} 
                     for w in self.walls]
        response = requests.post(f"{self.base_url}/create_room/", 
                                json={'walls': wall_data})
        return response.json()
    
    def join_room(self, room_id, passcode):
        response = requests.post(
            f"{self.base_url}/join_room/",
            json={'room_id': room_id, 'passcode': passcode}
        )
        return response.status_code == 200
    
    def connect_websocket(self, room_id):
        self.running = True
        ws_thread = threading.Thread(target=self._ws_connect, args=(room_id,))
        ws_thread.daemon = True
        ws_thread.start()
        
        time.sleep(1)
    
    def _ws_connect(self, room_id):
        self.ws = websocket.WebSocketApp(
            f"{self.ws_url}/{room_id}/",
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )
        self.ws.run_forever()
    
    def _on_message(self, ws, message):
        data = json.loads(message)
        
        if data['type'] == 'connection':
            self.team = data['team']
            print(f"Connected as {self.team} team")
        elif data['type'] == 'game_state':
            self.game_state = data['state']
    
    def _on_error(self, ws, error):
        print(f"WebSocket error: {error}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        print("WebSocket closed")
        self.running = False
    
    def check_wall_collision(self, new_x, new_y):
        """Check if the new position would collide with any walls"""
        for wall in self.walls:
            # Check if player circle intersects with wall rectangle
            closest_x = max(wall['rect'].left, min(new_x, wall['rect'].right))
            closest_y = max(wall['rect'].top, min(new_y, wall['rect'].bottom))
            
            distance_x = new_x - closest_x
            distance_y = new_y - closest_y
            distance_squared = distance_x**2 + distance_y**2
            
            if distance_squared < self.player_radius**2:
                return True
        return False
    
    def send_move(self, direction):
        if self.ws and self.running:
            # Client-side collision prediction (optional, server should also validate)
            self.ws.send(json.dumps({
                'type': 'move',
                'direction': direction
            }))
    
    def send_dash(self):
        current_time = time.time()
        if self.ws and self.running and (current_time - self.last_dash) > 0.5:
            self.last_dash = current_time
            self.ws.send(json.dumps({'type': 'dash'}))
    
    def send_ability(self):
        current_time = time.time()
        if self.ws and self.running and (current_time - self.last_ability) > 0.5:
            self.last_ability = current_time
            self.ws.send(json.dumps({'type': 'ability'}))
    
    def send_pickup(self):
        current_time = time.time()
        if self.ws and self.running and (current_time - self.last_interact) > 0.3:
            self.last_interact = current_time
            self.ws.send(json.dumps({'type': 'pickup'}))
    
    def send_drop(self):
        current_time = time.time()
        if self.ws and self.running and (current_time - self.last_interact) > 0.3:
            self.last_interact = current_time
            self.ws.send(json.dumps({'type': 'drop'}))
    
    def disconnect(self):
        self.running = False
        if self.ws:
            self.ws.close()
