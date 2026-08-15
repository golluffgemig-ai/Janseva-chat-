from flask import Flask, render_template_string, request, jsonify
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'bk_kar_real_game_key_2026'

def get_db():
    conn = sqlite3.connect('bk_kar.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    name TEXT,
                    mobile TEXT UNIQUE, 
                    password TEXT
                )''')
    conn.commit()
    conn.close()

init_db()

GAME_HTML = """
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>BK Kar Game 🏎️</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: sans-serif; touch-action: manipulation; }
        body { background-color: #0b131f; color: #ffffff; min-height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 10px; overflow: hidden; }

        /* Auth Screen Box */
        .auth-box { background: #132238; border: 2px solid #00e5ff; padding: 25px; border-radius: 12px; width: 100%; max-width: 340px; text-align: center; }
        .auth-box h1 { color: #00e5ff; margin-bottom: 15px; font-size: 26px; }
        .auth-box input { width: 100%; padding: 12px; margin: 8px 0; background: #1c2d42; border: 1px solid #00e5ff; color: #fff; border-radius: 6px; outline: none; }
        .auth-box button { width: 100%; padding: 12px; background: #00e5ff; border: none; color: #000; font-weight: bold; font-size: 16px; border-radius: 6px; cursor: pointer; margin-top: 10px; }
        .toggle-btn { margin-top: 12px; font-size: 13px; color: #88a0c0; cursor: pointer; text-decoration: underline; }

        /* Lobby Screen */
        #lobbyScreen { display: none; width: 100%; max-width: 360px; background: #132238; border: 2px solid #00e5ff; border-radius: 12px; padding: 20px; text-align: center; }
        .lobby-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
        .player-tag { background: #1c2d42; padding: 6px 12px; border-radius: 20px; color: #00e5ff; font-weight: bold; border: 1px solid #00e5ff; font-size: 14px; }
        
        .stage { background: #0b131f; height: 160px; border-radius: 10px; border: 1px dashed #00e5ff; display: flex; justify-content: center; align-items: center; gap: 20px; margin-bottom: 15px; }
        .avatar { font-size: 50px; color: #ffca28; }
        .vehicle-preview { font-size: 60px; color: #00e5ff; }

        .start-btn { background: #00e5ff; color: #000; font-size: 20px; font-weight: bold; padding: 12px; border: none; border-radius: 25px; cursor: pointer; width: 100%; box-shadow: 0 0 10px #00e5ff; }

        /* Settings Modal */
        #settingsModal { display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.85); justify-content: center; align-items: center; padding: 20px; z-index: 100; }
        .modal-box { background: #132238; border: 2px solid #00e5ff; padding: 20px; border-radius: 10px; width: 100%; max-width: 300px; }
        .setting-item { margin: 12px 0; text-align: left; }
        .setting-item label { display: block; margin-bottom: 5px; font-size: 13px; color: #88a0c0; }
        .setting-item select, .setting-item input { width: 100%; padding: 8px; background: #1c2d42; border: 1px solid #00e5ff; color: white; border-radius: 5px; }

        /* Game Screen Area */
        #gameArea { display: none; flex-direction: column; align-items: center; position: relative; }
        #gameCanvas { background: #222; border: 3px solid #00e5ff; border-radius: 8px; display: block; }
        
        /* Mobile Touch Controls */
        .game-controls { display: flex; justify-content: space-between; width: 320px; margin-top: 10px; }
        .ctrl-btn { background: #00e5ff; color: #000; border: none; padding: 15px 40px; font-size: 24px; font-weight: bold; border-radius: 10px; cursor: pointer; }

        /* Game Over Screen */
        #gameOverBox { display: none; position: absolute; top: 30%; background: rgba(19, 34, 56, 0.95); border: 2px solid #ff5252; padding: 20px; border-radius: 10px; text-align: center; width: 260px; }
        #gameOverBox h2 { color: #ff5252; margin-bottom: 10px; }
        #gameOverBox button { background: #00e5ff; border: none; padding: 10px 20px; font-weight: bold; border-radius: 5px; margin-top: 10px; cursor: pointer; }
    </style>
</head>
<body>

    <!-- 1. AUTH SCREEN -->
    <div class="auth-box" id="authBox">
        <h1>🏎️ BK KAR</h1>
        <div id="nameGroup">
            <input type="text" id="authName" placeholder="Full Name">
        </div>
        <input type="tel" id="authMobile" placeholder="Mobile Number">
        <input type="password" id="authPassword" placeholder="Strong Password">
        
        <button id="submitBtn" onclick="handleAuth()">Register & Play</button>
        
        <div class="toggle-btn" id="toggleText" onclick="switchAuthMode()">Pehle se account hai? Login Karein</div>
        <div class="toggle-btn" style="color: #ff5252; margin-top: 8px;" onclick="forgotPass()">Password Bhool Gaye?</div>
    </div>

    <!-- 2. GAME LOBBY -->
    <div id="lobbyScreen">
        <div class="lobby-header">
            <div class="player-tag"><i class="fa-solid fa-user"></i> <span id="pName">Player</span></div>
            <h2 style="color: #00e5ff;">BK KAR</h2>
            <i class="fa-solid fa-gear" style="font-size: 22px; color: #00e5ff; cursor: pointer;" onclick="toggleSettings(true)"></i>
        </div>

        <div class="stage">
            <div class="avatar"><i class="fa-solid fa-user-ninja"></i></div>
            <div class="vehicle-preview" id="vIcon"><i class="fa-solid fa-car"></i></div>
        </div>

        <button class="start-btn" onclick="startRacingGame()">RACE START 🏁</button>
    </div>

    <!-- 3. SETTINGS MODAL -->
    <div id="settingsModal">
        <div class="modal-box">
            <h3 style="color: #00e5ff; text-align: center; margin-bottom: 12px;">⚙️ Game Settings</h3>
            
            <div class="setting-item">
                <label>Vehicle Select:</label>
                <select id="vSelect" onchange="changeVehicle(this.value)">
                    <option value="car">Car 🏎️</option>
                    <option value="bike">Bike 🏍️</option>
                </select>
            </div>

            <div class="setting-item">
                <label>Sensitivity (Steering Speed):</label>
                <input type="range" id="sensInput" min="4" max="14" value="7" onchange="userSensitivity = parseInt(this.value)">
            </div>

            <button onclick="toggleSettings(false)" style="width: 100%; padding: 10px; background: #00e5ff; border: none; font-weight: bold; border-radius: 5px; margin-top: 10px; cursor: pointer;">Save & Close</button>
            <button onclick="location.reload()" style="width: 100%; padding: 8px; background: #ff5252; border: none; color: white; font-weight: bold; border-radius: 5px; margin-top: 8px; cursor: pointer;">Logout</button>
        </div>
    </div>

    <!-- 4. REAL GAME CANVAS AREA -->
    <div id="gameArea">
        <div style="font-size: 16px; margin-bottom: 5px; color: #00e5ff; font-weight: bold;">Score: <span id="scoreText">0</span></div>
        <canvas id="gameCanvas" width="320" height="420"></canvas>
        
        <!-- Touch Buttons -->
        <div class="game-controls">
            <button class="ctrl-btn" id="btnLeft">◀</button>
            <button class="ctrl-btn" id="btnRight">▶</button>
        </div>

        <!-- Game Over Modal -->
        <div id="gameOverBox">
            <h2>💥 CRASHED! 💥</h2>
            <p>Score: <span id="finalScore">0</span></p>
            <button onclick="restartRace()">Play Again 🔄</button>
            <button onclick="exitToLobby()" style="background:#ff5252; color:white; margin-left:5px;">Lobby 🏠</button>
        </div>
    </div>

    <script>
        let isLoginMode = false;
        let selectedVehicle = 'car';
        let userSensitivity = 7;
        
        // Auth Handling
        function switchAuthMode() {
            isLoginMode = !isLoginMode;
            document.getElementById('nameGroup').style.display = isLoginMode ? 'none' : 'block';
            document.getElementById('submitBtn').innerText = isLoginMode ? 'Login' : 'Register & Play';
            document.getElementById('toggleText').innerText = isLoginMode ? 'Naye user hain? Register Karein' : 'Pehle se account hai? Login Karein';
        }

        function handleAuth() {
            let name = document.getElementById('authName').value;
            let mobile = document.getElementById('authMobile').value;
            let password = document.getElementById('authPassword').value;

            if(!mobile || !password) { alert('Mobile Number aur Password bharein!'); return; }

            fetch('/auth', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ action: isLoginMode ? 'login' : 'register', name, mobile, password })
            })
            .then(res => res.json())
            .then(data => {
                if(data.status === 'ok') {
                    document.getElementById('authBox').style.display = 'none';
                    document.getElementById('lobbyScreen').style.display = 'block';
                    document.getElementById('pName').innerText = data.user.name || 'Racer';
                } else {
                    alert(data.message);
                }
            });
        }

        function forgotPass() {
            let mob = prompt("Apna Mobile Number Daalein:");
            if(mob) alert("Reset code aapke mobile par bhej diya gaya hai!");
        }

        function changeVehicle(type) {
            selectedVehicle = type;
            let icon = document.getElementById('vIcon');
            icon.innerHTML = (type === 'bike') ? '<i class="fa-solid fa-motorcycle"></i>' : '<i class="fa-solid fa-car"></i>';
        }

        function toggleSettings(show) {
            document.getElementById('settingsModal').style.display = show ? 'flex' : 'none';
        }

        // --- REAL GAME ENGINE LOGIC ---
        const canvas = document.getElementById("gameCanvas");
        const ctx = canvas.getContext("2d");

        let score = 0;
        let isGameOver = false;
        let roadY = 0;
        let gameLoopReq = null;

        let player = { x: 140, y: 330, w: 35, h: 55 };
        let enemies = [];
        let keys = { left: false, right: false };

        // Touch Control Listeners
        const btnL = document.getElementById("btnLeft");
        const btnR = document.getElementById("btnRight");

        btnL.addEventListener("touchstart", (e) => { e.preventDefault(); keys.left = true; });
        btnL.addEventListener("touchend", (e) => { e.preventDefault(); keys.left = false; });
        btnL.addEventListener("mousedown", () => keys.left = true);
        btnL.addEventListener("mouseup", () => keys.left = false);

        btnR.addEventListener("touchstart", (e) => { e.preventDefault(); keys.right = true; });
        btnR.addEventListener("touchend", (e) => { e.preventDefault(); keys.right = false; });
        btnR.addEventListener("mousedown", () => keys.right = true);
        btnR.addEventListener("mouseup", () => keys.right = false);

        // Key Controls (Keyboard)
        document.addEventListener("keydown", (e) => {
            if(e.key === "ArrowLeft" || e.key === "a") keys.left = true;
            if(e.key === "ArrowRight" || e.key === "d") keys.right = true;
        });
        document.addEventListener("keyup", (e) => {
            if(e.key === "ArrowLeft" || e.key === "a") keys.left = false;
            if(e.key === "ArrowRight" || e.key === "d") keys.right = false;
        });

        function startRacingGame() {
            document.getElementById('lobbyScreen').style.display = 'none';
            document.getElementById('gameArea').style.display = 'flex';
            restartRace();
        }

        function restartRace() {
            score = 0;
            isGameOver = false;
            player.x = 140;
            enemies = [];
            document.getElementById('gameOverBox').style.display = 'none';
            document.getElementById('scoreText').innerText = "0";
            if(gameLoopReq) cancelAnimationFrame(gameLoopReq);
            runGame();
        }

        function exitToLobby() {
            if(gameLoopReq) cancelAnimationFrame(gameLoopReq);
            document.getElementById('gameArea').style.display = 'none';
            document.getElementById('lobbyScreen').style.display = 'block';
        }

        function spawnEnemy() {
            const lanes = [30, 110, 190, 250];
            const rx = lanes[Math.floor(Math.random() * lanes.length)];
            enemies.push({ x: rx, y: -60, w: 35, h: 55, speed: 3.5 + Math.random() * 3 });
        }

        function updateGame() {
            if(isGameOver) return;

            // Move Road
            roadY += 6;
            if(roadY >= 40) roadY = 0;

            // Player Movement using Sensitivity
            if(keys.left && player.x > 20) player.x -= userSensitivity;
            if(keys.right && player.x < canvas.width - player.w - 20) player.x += userSensitivity;

            // Enemy Spawning
            if(Math.random() < 0.03) spawnEnemy();

            // Update Enemies
            for(let i = 0; i < enemies.length; i++) {
                enemies[i].y += enemies[i].speed;

                // Collision Detection
                if(player.x < enemies[i].x + enemies[i].w &&
                   player.x + player.w > enemies[i].x &&
                   player.y < enemies[i].y + enemies[i].h &&
                   player.y + player.h > enemies[i].y) {
                    
                    isGameOver = true;
                    document.getElementById('finalScore').innerText = score;
                    document.getElementById('gameOverBox').style.display = 'block';
                }

                // Passed Enemy Score Add
                if(enemies[i].y > canvas.height) {
                    enemies.splice(i, 1);
                    score += 10;
                    document.getElementById('scoreText').innerText = score;
                }
            }
        }

        function drawGame() {
            // Draw Road
            ctx.fillStyle = "#1e242b";
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            // Grass Borders
            ctx.fillStyle = "#2e7d32";
            ctx.fillRect(0, 0, 15, canvas.height);
            ctx.fillRect(canvas.width - 15, 0, 15, canvas.height);

            // Road Lines
            ctx.strokeStyle = "#ffffff";
            ctx.lineWidth = 3;
            ctx.setLineDash([20, 20]);
            ctx.lineDashOffset = -roadY;
            ctx.beginPath();
            ctx.moveTo(canvas.width / 2, 0);
            ctx.lineTo(canvas.width / 2, canvas.height);
            ctx.stroke();

            // Draw Player Vehicle
            ctx.fillStyle = (selectedVehicle === 'bike') ? "#ffca28" : "#00e5ff";
            ctx.fillRect(player.x, player.y, player.w, player.h);
            ctx.fillStyle = "#ffffff";
            ctx.fillRect(player.x + 5, player.y + 5, player.w - 10, 12); // Windshield

            // Draw Enemy Cars
            ctx.fillStyle = "#ff5252";
            enemies.forEach(e => {
                ctx.fillRect(e.x, e.y, e.w, e.h);
                ctx.fillStyle = "#000000";
                ctx.fillRect(e.x + 5, e.y + 35, e.w - 10, 10);
                ctx.fillStyle = "#ff5252";
            });
        }

        function runGame() {
            updateGame();
            drawGame();
            if(!isGameOver) {
                gameLoopReq = requestAnimationFrame(runGame);
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(GAME_HTML)

@app.route('/auth', methods=['POST'])
def auth():
    data = request.json
    conn = get_db()
    c = conn.cursor()
    
    if data['action'] == 'register':
        try:
            c.execute("INSERT INTO users (name, mobile, password) VALUES (?, ?, ?)", 
                      (data['name'], data['mobile'], data['password']))
            conn.commit()
            conn.close()
            return jsonify({'status': 'ok', 'user': {'name': data['name'], 'mobile': data['mobile']}})
        except:
            conn.close()
            return jsonify({'status': 'error', 'message': 'Mobile number pehle se registered hai!'})
            
    elif data['action'] == 'login':
        c.execute("SELECT name, mobile FROM users WHERE mobile=? AND password=?", 
                  (data['mobile'], data['password']))
        user = c.fetchone()
        conn.close()
        if user:
            return jsonify({'status': 'ok', 'user': {'name': user[0], 'mobile': user[1]}})
        else:
            return jsonify({'status': 'error', 'message': 'Galat Mobile Number ya Password!'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
