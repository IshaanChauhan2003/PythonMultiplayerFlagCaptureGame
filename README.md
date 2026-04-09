# Capture The Flag - 1v1 Arena Game

A real-time multiplayer top-down capture the flag game with Django backend and Pygame frontend.

## Setup Instructions

### Backend Setup (Django)

1. Navigate to backend folder:
```bash
cd flagCaptureBackend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the server:
```bash
python manage.py runserver
```

The backend will run on `http://localhost:8000`

### Frontend Setup (Pygame)

1. Navigate to game folder:
```bash
cd mainGame
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the game:
```bash
python main.py
```

## How to Play

### Starting a Game

1. Player 1: Press `C` to create a room (note the Room ID and Passcode)
2. Player 2: Press `J` to join, enter the Room ID and Passcode

### Controls

- **WASD** - Move player
- **E** - Dash (2s cooldown)
- **Q** - Time Slow ability (unlocks after capturing enemy flag)
- **Left Click** - Interact/Capture flag

### Game Rules

- Capture 3 enemy flags while keeping at least 1 of your own to win
- Carry only 1 flag at a time
- Avoid potholes (black circles) - instant death with 4s respawn
- Store captured flags in your base to score
- Time limit: 180 seconds

### Visual Guide

- **Blue Box** = Blue player
- **Red Box** = Red player
- **Blue Circles** = Blue team flags
- **Red Circles** = Red team flags
- **Black Circles** = Potholes (death zones)

## Architecture

- **Backend**: Django + Channels (WebSockets)
- **Frontend**: Pygame
- **Communication**: REST API for room management, WebSocket for real-time game state
