// ---------- COUNTDOWN TIMER ----------
const GAME_DURATION = 10 * 60 * 1000; // 10 minutes in ms
let timerInterval = null;
let timeRemaining = GAME_DURATION;
let timerRunning = false;
let gameStarted = false;

window.addEventListener("load", async () => {
  // Ask backend whether a game is running
  const res = await fetch("/get_game_state");
  const data = await res.json();

  if (data.gameStarted) {
    // Resume game in progress
    document.getElementById("objective").style.display = "none";
    document.querySelectorAll("#controls button").forEach(btn => {
      btn.disabled = btn.id === "start-btn"; // disable only Start
    });
    gameStarted = true;
    startTimer();  // resume timer if needed
    updateStatus();
  } else {
    // Game NOT started yet
    document.getElementById("objective").style.display = "block";
    document.querySelectorAll("#controls button").forEach(btn => {
      btn.disabled = btn.id !== "start-btn"; // only Start is clickable
    });
    gameStarted = false;
    clearInterval(timerInterval);
    timerRunning = false;
    timeRemaining = GAME_DURATION;
    document.getElementById("timer").innerText = "⏱️ Time: 10:00";
  }
});

function formatTime(ms) {
  const totalSec = Math.max(0, Math.floor(ms / 1000));
  const min = String(Math.floor(totalSec / 60)).padStart(2, "0");
  const sec = String(totalSec % 60).padStart(2, "0");
  return `${min}:${sec}`;
}

// ---------- DISABLE EVERYTHING ON GAME END ----------
function disableAllExceptRestart() {
  document.querySelectorAll("#controls button").forEach(btn => {
    btn.disabled = btn.textContent !== "Restart Game";
  });
  clearInterval(timerInterval);
  timerRunning = false;
  gameStarted = false;
}

function updateTimer() {
  // if timer isn't running, do nothing
  if (!timerRunning) return;

  timeRemaining -= 1000;

  // Clamp to 0
  if (timeRemaining <= 0) {
    timeRemaining = 0;
    timerRunning = false;
    clearInterval(timerInterval);
    document.getElementById("timer").innerText = "⏱️ Time: 00:00";
    document.getElementById("output").innerText =
      "⏰ Time’s up! The dungeon collapses around Traveler!";
    disableAllExceptRestart(); // ⛔ disable controls except restart
    return;
  }

  // turn red when under a minute
  const timerDisplay = document.getElementById("timer");
  if (timeRemaining <= 60 * 1000) {
    timerDisplay.classList.add("low-time");
  } else {
    timerDisplay.classList.remove("low-time");
  }

  timerDisplay.innerText = `⏱️ Time: ${formatTime(timeRemaining)}`;
}

function startTimer() {
  clearInterval(timerInterval);
  timeRemaining = GAME_DURATION;
  timerRunning = true;
  document.getElementById("timer").innerText = `⏱️ Time: ${formatTime(timeRemaining)}`;
  timerInterval = setInterval(updateTimer, 1000);
}

function disableControls() {
  const buttons = document.querySelectorAll("#controls button");
  buttons.forEach(btn => (btn.disabled = true));
}

async function updateStatus() {
  const res = await fetch('/status');
  const data = await res.json();

  document.getElementById('health').innerText = `❤️ Health: ${data.health}`;
  document.getElementById('room').innerText = `🚪 Room: ${data.room}`;
  const counts = data.inventory_counts || {};
  if (Object.keys(counts).length === 0) {
    document.getElementById('inventory-status').innerText = '💼 Inventory: (empty)';
  } else {
    const parts = Object.entries(counts).map(([item, count]) =>
      count > 1 ? `${item} ×${count}` : item
    );
    document.getElementById('inventory-status').innerText =
      '💼 Inventory: ' + parts.join(' | ');
  }

  // 🧮 update enemy counter
  document.getElementById("enemy-counter").innerText =
    `🧟‍♂️ Enemies Remaining: ${data.remaining_enemies} / ${data.total_enemies}`;
}

async function move(direction) {
  const response = await fetch('/move', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ direction })
  });
  const data = await response.json();
  document.getElementById('output').innerText = data.description;
  updateStatus();
}

async function pickup() {
  const response = await fetch('/pickup', { method: 'POST' });
  const data = await response.json();
  document.getElementById('output').innerText = data.message;
  updateStatus();
}

async function takeDamage() {
  const response = await fetch('/damage', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ amount: 20 })
  });
  const data = await response.json();
  document.getElementById('output').innerText = data.message;
  updateStatus();
}

// ---------- START GAME ----------
async function startGame() {
  if (gameStarted) return;
  gameStarted = true;

  await fetch("/start_game", { method: "POST" }); // backend flips flag

  // Hide objective, enable all controls except Start
  document.getElementById("objective").style.display = "none";
  document.querySelectorAll("#controls button").forEach(btn => {
    btn.disabled = btn.id === "start-btn";
  });

  document.getElementById("output").innerText =
    "The dungeon stirs... Traveler begins their quest!";
  startTimer();
  updateStatus();
}

// ---------- RESTART GAME ----------
async function restartGame() {
  const confirmRestart = confirm("Are you sure you want to restart the game?\nAll progress will be lost?");
  if (!confirmRestart) return;

  const response = await fetch('/restart', { method: 'POST' });
  const data = await response.json();

  document.getElementById('output').innerText = data.message;

  // Reset UI to show objective again
  document.getElementById("objective").style.display = "block";
  document.getElementById("enemy-counter").innerText = "🧟‍♂️ Enemies Remaining: 20 / 20";
  document.getElementById("timer").innerText = "⏱️ Time: 10:00";
  document.getElementById("health").innerText = "❤️ Health: 100";
  document.getElementById("room").innerText = "🚪 Room:";
  document.getElementById("inventory-status").innerText = "💼 Inventory: (empty)";
  document.querySelectorAll("#controls button").forEach(btn => {
    btn.disabled = btn.id !== "start-btn";
  });

  clearInterval(timerInterval);
  timerRunning = false;
  timeRemaining = GAME_DURATION;
  gameStarted = false;
}

// ---------- FIGHT LOGIC ADJUSTMENT ----------
async function fight() {
  const response = await fetch('/fight', { method: 'POST' });
  const data = await response.json();
  document.getElementById('output').innerText = data.message;
  updateStatus();

  if (
    data.message.includes("Traveler Wins!") ||
    data.message.includes("Game Over") ||
    data.message.includes("fallen") ||
    data.message.includes("Time’s up")
  ) {
    disableAllExceptRestart();
  }
}

async function heal() {
  const response = await fetch('/heal', { method: 'POST' });
  const data = await response.json();
  document.getElementById('output').innerText = data.message;
  updateStatus(); // refresh HP + inventory display
}


