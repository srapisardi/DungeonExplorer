# 🏰 Dungeon Explorer – Full Project Summary

**Project Type:** Text-Based Dungeon Adventure Game  
**Tech Stack:** Flask (Python), SQLite, HTML, CSS, JavaScript  
**Player:** Generic "Traveler"  
**Goal:** Defeat all 20 enemies before time runs out while managing health, inventory, and time.

---

## 🧩 Overview

Dungeon Explorer is a web-based text adventure built using Flask, SQLite, and JavaScript. The player navigates through interconnected rooms, battles enemies, collects items, and must defeat all 20 enemies before the timer expires. The game combines persistent session data with asynchronous Fetch API calls for smooth, reload-free interactivity.

The project demonstrates full-stack development and integrates concepts from CS50 topics such as algorithms, data structures, SQL, and web programming.

---

## ⚙️ Features

- **Dungeon Rooms:** Six interconnected rooms, each with unique descriptions.
- **Enemies:** Randomly spawn (40% chance) until total count is reached; last few guaranteed.
- **Combat System:** Randomized attack/defense; enemy HP decreases until defeat.
- **Sword & Shield Fragments:**  
  - Sword: +25% damage per fragment (max 3)  
  - Shield: −15% damage taken per fragment (max 3)  
  - 25% break chance each fight
- **Potions:** Heal 30 HP, max 3 in inventory.
- **Timer:** 10-minute countdown; loss when it reaches 0.
- **Enemy Counter:** Displays remaining enemies (20 → 0).
- **Persistence:** Flask sessions maintain progress through refresh.
- **Start/Restart Flow:** Game begins only when “Start Game” clicked; restarts reset world.
- **Victory & End States:** “Traveler Wins!” or “Game Over” messages; disables all buttons except Restart.

---

## 🧱 Backend (`app.py`)

### Main Components

| Route | Purpose |
|--------|----------|
| `/` | Renders main interface (`game.html`). |
| `/init` | Initializes database and resets all game state. |
| `/start_game` | Sets session flag to start the game manually. |
| `/get_game_state` | Checks if a game is active to control objective screen. |
| `/move` | Handles directional navigation, enemy and item spawning. |
| `/pickup` | Adds room items to inventory, enforces 3-item limit. |
| `/fight` | Executes combat logic and fragment bonuses. |
| `/heal` | Uses potion to restore HP (max 100). |
| `/status` | Returns health, room name, inventory, and enemy counter. |
| `/restart` | Clears all data and resets to objective screen. |

### Database Tables

- **rooms:** ID, name, description, exits, item, enemy, enemy_health  
- **inventory:** Stores items picked up in current run  
- **dungeon_state:** Tracks total enemies, spawned, and killed counts

### Session Variables

| Variable | Description |
|-----------|-------------|
| `player` | Traveler |
| `health` | Current HP |
| `current_room` | Player’s room ID |
| `gameStarted` | Boolean flag |
| `start_time` | Optional timer anchor |

---

## 💻 Frontend

### HTML (`templates/game.html`)

- Displays objective intro and Start button on load.
- Status bar shows Health, Room, Inventory.
- Top bar shows Timer (right) and Enemy Counter (left).
- Controls include: Move, Pickup, Heal, Fight, Restart.

### CSS (`static/style.css`)

- Dark “terminal RPG” aesthetic (black background, neon text).  
- `#top-bar` fixed; red glow (`.low-time`) when <1 minute.  
- Buttons fade and disable post-game.

### JavaScript (`static/script.js`)

- Manages timer, game state, and interactions via Fetch API.  
- Prevents auto-start (only starts on Start button click).  
- Handles `updateStatus()`, `startTimer()`, `move()`, `pickup()`, `fight()`, `heal()`, `restartGame()`.

#### Important Functions

| Function | Purpose |
|-----------|----------|
| `startGame()` | Hides objective, starts timer, enables controls. |
| `updateStatus()` | Updates health, inventory, enemy counter. |
| `move(direction)` | Sends `/move` to Flask, updates text. |
| `fight()` | Sends `/fight`, shows results, disables on end. |
| `restartGame()` | Confirms restart, resets UI and backend. |
| `startTimer()` | Handles countdown; stops game at 0. |

---

## 🎮 Gameplay Loop

1. **Page Load** → Objective screen visible; only Start active.  
2. **Start Game** → Timer starts; controls enabled.  
3. **Explore Rooms** → Move around; find enemies/items.  
4. **Combat** → Attack enemies; manage fragments and HP.  
5. **Healing** → Use potions strategically.  
6. **Win/Lose Conditions** →  
   - All enemies killed → “🏆 Traveler Wins!”  
   - HP 0 or timer = 0 → “💀 Game Over.”  
7. **Restart** → Resets dungeon; returns to objective screen.

---

## 🕰️ Timer Details

- Default: 10 minutes (`10 * 60 * 1000` ms)  
- Turns red under 1 minute (`.low-time`).  
- Freezes on victory, defeat, or timeout.  
- Only Restart enabled after end.

---

## 🧠 Design Decisions

- **Start/Restart System:** Chosen to make flow intentional.  
- **Session + DB Hybrid:** Session handles transient data; DB persists dungeon world.  
- **Fragment Mechanics:** Adds simple progression with clear risk-reward loop.  
- **Guaranteed Final Enemy:** Prevents soft-lock due to RNG.  
- **Persistent State:** Maintains immersion even through refresh.

---

## 🧩 CS50 Relevance

Draws on concepts from multiple CS50 weeks:

- **Week 3–5:** Algorithms, data structures (capped inventory, combat calc).  
- **Week 6:** Python + Flask logic.  
- **Week 7:** SQL schema for persistent data.  
- **Week 8:** HTML/CSS/JS interface.  
- **Week 9:** Flask routing and session handling.  
- **Week 10:** Polishing, deployment, and documentation.

---

## 🚀 Future Improvements

- Graphical dungeon map or 2D sprite system.  
- Boss fights / difficulty levels.  
- Save and resume multiple dungeon runs.  
- Sound effects and animations.  
- Port to Unity (C#) or Godot (GDScript) for graphical gameplay.  

---

## 🏁 Summary

Dungeon Explorer evolved from a simple text-based concept into a full-stack web game with persistent sessions, item and combat systems, and structured game flow.  
It merges backend logic, database persistence, and responsive frontend design, forming a strong foundation for future graphical or multiplayer versions.

---
