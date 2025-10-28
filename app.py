from flask import Flask, render_template, request, jsonify, session
import sqlite3
import random

app = Flask(__name__)
app.secret_key = "secret-key"

def get_db_connection():
    conn = sqlite3.connect('game.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('game.html')

@app.before_request
def ensure_player():
    # Always have a base Traveler session, but do NOT start the game
    if 'player' not in session:
        session['player'] = 'Traveler'
    if 'health' not in session:
        session['health'] = 100
    if 'current_room' not in session:
        session['current_room'] = 1
    # Default: game has not started yet
    if 'gameStarted' not in session:
        session['gameStarted'] = False

# ---------- INITIALIZE WORLD ----------
@app.route("/init", methods=["POST"])
def init_game():
    conn = get_db_connection()
    conn.executescript("""
    DROP TABLE IF EXISTS rooms;
    DROP TABLE IF EXISTS inventory;
    DROP TABLE IF EXISTS dungeon_state;

    CREATE TABLE rooms (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        north INTEGER,
        south INTEGER,
        east INTEGER,
        west INTEGER,
        item TEXT,
        enemy TEXT,
        enemy_health INTEGER
    );

    CREATE TABLE inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT NOT NULL
    );

    CREATE TABLE dungeon_state (
        id INTEGER PRIMARY KEY,
        total_enemies INTEGER,
        enemies_spawned INTEGER,
        enemies_killed INTEGER
    );

    -- set total enemies to 20 (adjust if you want)
    INSERT INTO dungeon_state (id, total_enemies, enemies_spawned, enemies_killed)
    VALUES (1, 20, 0, 0);

    INSERT INTO rooms (id, name, description, north, south, east, west, item, enemy, enemy_health) VALUES
    (1, 'Ancient Gate',
     'The cracked stone gate looms before you, half buried under vines. Faint runes glow as you step closer.',
     NULL, 3, 2, NULL, NULL, NULL, NULL),
    (2, 'Hallway',
     'A narrow hallway with flickering torches. The air smells of dust and oil.',
     NULL, 4, NULL, 1, NULL, NULL, NULL),
    (3, 'Guard Room',
     'A dusty room with broken armor pieces scattered around. A shattered banner still clings to the wall.',
     1, 5, 4, NULL, NULL, NULL, NULL),
    (4, 'Armory',
     'Rusty weapons line the walls, and a cracked chest lies open on the floor.',
     2, 6, NULL, 3, NULL, NULL, NULL),
    (5, 'Forgotten Shrine',
     'A circular chamber covered in moss. A broken altar stands at its center, glowing faintly with ancient energy.',
     3, NULL, 6, NULL, NULL, NULL, NULL),
    (6, 'Crystal Cavern',
     'The tunnel opens into a glittering cavern. The air hums with magic from giant crystal shards.',
     4, NULL, NULL, 5, NULL, NULL, NULL);
    """)
    conn.commit()
    conn.close()
    session['gameStarted'] = False
    return jsonify({"message": "✅ Dungeon reset. Traveler awaits a new adventure!"})

@app.route('/start_game', methods=['POST'])
def start_game():
    """Triggered only by Start Game button."""
    session['gameStarted'] = True
    return jsonify({"message": "Game started!"})

@app.route('/get_game_state', methods=['GET'])
def get_game_state():
    """Return whether the game is in progress."""
    return jsonify({
        "gameStarted": bool(session.get('gameStarted', False)),
        "health": session.get('health', 100),
        "current_room": session.get('current_room', 1)
    })

# ---------- STATUS ----------
@app.route('/status', methods=['GET'])
def get_status():
    conn = get_db_connection()
    current_room_id = session.get('current_room', 1)
    room = conn.execute("SELECT name FROM rooms WHERE id=?", (current_room_id,)).fetchone()
    room_name = room['name'] if room else "Unknown"

    # inventory
    rows = conn.execute("""
        SELECT LOWER(item_name) AS item_name, COUNT(*) AS count
        FROM inventory
        GROUP BY LOWER(item_name)
    """).fetchall()

    # enemy counts
    dungeon = conn.execute("SELECT total_enemies, enemies_killed FROM dungeon_state WHERE id = 1").fetchone()
    total = dungeon['total_enemies'] if dungeon else 0
    killed = dungeon['enemies_killed'] if dungeon else 0
    remaining = max(0, total - killed)

    conn.close()

    inventory_counts = {r['item_name']: r['count'] for r in rows}
    return jsonify({
        "traveler": "Traveler",
        "health": session.get('health', 100),
        "room": room_name,
        "inventory_counts": inventory_counts,
        "remaining_enemies": remaining,
        "total_enemies": total
    })

# ---------- MOVE ----------
@app.route('/move', methods=['POST'])
def move():
    data = request.get_json() or {}
    direction = data.get('direction')

    if direction not in ('north', 'south', 'east', 'west'):
        return jsonify({"description": "Invalid direction."}), 400

    conn = get_db_connection()
    current_room_id = session.get('current_room', 1)
    current_room = conn.execute("SELECT * FROM rooms WHERE id = ?", (current_room_id,)).fetchone()

    if not current_room:
        conn.close()
        return jsonify({"description": "You seem to be lost."}), 400

    next_room_id = current_room[direction] if direction in current_room.keys() else None
    if not next_room_id:
        conn.close()
        return jsonify({"description": "You can’t go that way!"})

    session['current_room'] = next_room_id
    new_room = conn.execute("SELECT * FROM rooms WHERE id = ?", (next_room_id,)).fetchone()
    description = new_room['description']

    # --- enemy spawn logic ---
    dungeon = conn.execute("SELECT * FROM dungeon_state WHERE id = 1").fetchone()
    if not new_room['enemy'] and dungeon['enemies_spawned'] < dungeon['total_enemies'] and random.random() < 0.4:
        enemies = [("Goblin", 25), ("Skeleton", 40), ("Orc", 50), ("Zombie", 35), ("Dark Mage", 60)]
        enemy, hp = random.choice(enemies)
        conn.execute("UPDATE rooms SET enemy=?, enemy_health=? WHERE id=?", (enemy, hp, new_room['id']))
        conn.execute("UPDATE dungeon_state SET enemies_spawned = enemies_spawned + 1 WHERE id = 1")
        conn.commit()
        new_room = conn.execute("SELECT * FROM rooms WHERE id=?", (next_room_id,)).fetchone()

    # --- random item spawn ---
    if not new_room['item'] and random.random() < 0.3:
        loot = random.choice(["Potion", "Sword Fragment", "Shield Fragment"])
        conn.execute("UPDATE rooms SET item=? WHERE id=?", (loot, new_room['id']))
        conn.commit()
        new_room = conn.execute("SELECT * FROM rooms WHERE id=?", (next_room_id,)).fetchone()

    if new_room['item']:
        description += f" 💼 You found a {new_room['item']}! Type 'pickup' to collect it."
    if new_room['enemy']:
        description += f" ⚔️ A wild {new_room['enemy']} appears! Type 'Fight' to engage."

    conn.close()
    return jsonify({"description": description})


# ---------- PICKUP ----------
@app.route('/pickup', methods=['POST'])
def pickup_item():
    current_room_id = session.get('current_room', 1)
    conn = get_db_connection()
    room = conn.execute("SELECT * FROM rooms WHERE id = ?", (current_room_id,)).fetchone()

    if not room or not room['item']:
        conn.close()
        return jsonify({"message": "There’s nothing to pick up here."})

    item_name = room['item']
    item_lower = item_name.lower()

    # Count how many of that item the Traveler already holds
    count_query = "SELECT COUNT(*) FROM inventory WHERE LOWER(item_name)=?"
    existing_count = conn.execute(count_query, (item_lower,)).fetchone()[0]

    # Enforce max 3 for limited items
    limited_items = ["potion", "sword fragment", "shield fragment"]
    if item_lower in limited_items and existing_count >= 3:
        conn.close()
        return jsonify({"message": f"Traveler can’t carry more than 3 {item_name}s!"})

    # Normal pickup
    conn.execute("INSERT INTO inventory (item_name) VALUES (?)", (item_name,))
    conn.execute("UPDATE rooms SET item=NULL WHERE id=?", (room['id'],))
    conn.commit()
    conn.close()
    return jsonify({"message": f"Traveler picked up the {item_name}!"})

# ---------- FIGHT ----------
@app.route('/fight', methods=['POST'])
def fight():
    conn = get_db_connection()
    current_room_id = session.get('current_room', 1)
    room = conn.execute("SELECT * FROM rooms WHERE id=?", (current_room_id,)).fetchone()

    if not room or not room['enemy']:
        conn.close()
        return jsonify({"message": "There’s no enemy here."})

    # --- Base rolls ---
    player_attack = random.randint(8, 20)
    enemy_attack = random.randint(5, 15)

    # --- Count fragments and apply bonuses ---
    sword_count = conn.execute(
        "SELECT COUNT(*) FROM inventory WHERE LOWER(item_name)='sword fragment'"
    ).fetchone()[0]
    shield_count = conn.execute(
        "SELECT COUNT(*) FROM inventory WHERE LOWER(item_name)='shield fragment'"
    ).fetchone()[0]

    sword_count = min(sword_count, 3)
    shield_count = min(shield_count, 3)

    if sword_count:
        player_attack = int(player_attack * (1 + 0.25 * sword_count))
    if shield_count:
        enemy_attack = int(enemy_attack * (1 - 0.15 * shield_count))

    # --- Do combat ---
    new_enemy_hp = room['enemy_health'] - player_attack
    msg = [f"Traveler attacks the {room['enemy']} for {player_attack} damage!"]

    if new_enemy_hp <= 0:
        conn.execute("UPDATE rooms SET enemy=NULL, enemy_health=NULL WHERE id=?", (room['id'],))
        conn.execute("UPDATE dungeon_state SET enemies_killed = enemies_killed + 1 WHERE id = 1")
        msg.append(f"The {room['enemy']} is defeated! 🗡️")

        dungeon = conn.execute("SELECT * FROM dungeon_state WHERE id = 1").fetchone()
        if dungeon['enemies_killed'] >= dungeon['total_enemies']:
            msg.append("✨ The dungeon has been cleansed! All enemies are defeated! ✨")
            msg.append("🏆 Traveler Wins!")
    else:
        conn.execute("UPDATE rooms SET enemy_health=? WHERE id=?", (new_enemy_hp, room['id']))
        msg.append(f"The {room['enemy']} has {new_enemy_hp} HP left.")
        # Apply enemy counter-attack
        session['health'] = max(0, session['health'] - enemy_attack)
        msg.append(f"The {room['enemy']} strikes back for {enemy_attack} damage! ❤️ Health: {session['health']}")
        if session['health'] <= 0:
            msg.append("💀 Traveler has fallen... Game Over.")

    # --- 25 % chance for fragments to break ---
    broken = []
    sword_frags = conn.execute("SELECT id FROM inventory WHERE LOWER(item_name)='sword fragment'").fetchall()
    shield_frags = conn.execute("SELECT id FROM inventory WHERE LOWER(item_name)='shield fragment'").fetchall()
    if sword_frags and random.random() < 0.25:
        conn.execute("DELETE FROM inventory WHERE id=?", (sword_frags[0]['id'],))
        broken.append("Sword Fragment")
    if shield_frags and random.random() < 0.25:
        conn.execute("DELETE FROM inventory WHERE id=?", (shield_frags[0]['id'],))
        broken.append("Shield Fragment")
    if broken:
        msg.append(f"⚡ One of your {' and '.join(broken)} broke during the fight!")

    conn.commit()
    conn.close()
    return jsonify({"message": " ".join(msg)})

# ---------- HEAL ----------
@app.route('/heal', methods=['POST'])
def heal():
    conn = get_db_connection()
    potion = conn.execute("SELECT id FROM inventory WHERE LOWER(item_name)='potion'").fetchone()
    if not potion:
        conn.close()
        return jsonify({"message": "Traveler has no potions!"})

    conn.execute("DELETE FROM inventory WHERE id=?", (potion['id'],))
    conn.commit()
    conn.close()

    # Restore health (max 100)
    session['health'] = min(100, session['health'] + 30)
    return jsonify({"message": f"Traveler drinks a potion and restores health to ❤️ {session['health']} HP!"})

# ---------- RESTART ----------
@app.route('/restart', methods=['POST'])
def restart_game():
    session['current_room'] = 1
    session['health'] = 100
    session['gameStarted'] = False  # ✅ mark game inactive

    conn = get_db_connection()
    conn.execute("DELETE FROM inventory;")
    conn.execute("UPDATE rooms SET item=NULL, enemy=NULL, enemy_health=NULL;")
    dungeon = conn.execute("SELECT id FROM dungeon_state WHERE id = 1").fetchone()
    if dungeon:
        conn.execute("UPDATE dungeon_state SET enemies_spawned = 0, enemies_killed = 0 WHERE id = 1")
    conn.commit()
    conn.close()

    return jsonify({"message": "Traveler returns to the dungeon entrance. The evil has returned anew!"})

if __name__ == "__main__":
    app.run(debug=True)