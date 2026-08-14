from flask import Flask, render_template_string, request, jsonify, session, redirect
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'bk_kar_gaming_secret_key_2026'

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
                    password TEXT,
                    sensitivity INTEGER DEFAULT 50,
                    brightness INTEGER DEFAULT 100,
                    vehicle TEXT DEFAULT 'car'
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
    <title>BK Kar 🏎️</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; touch-action: manipulation; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { background: #080d14; color: white; overflow: hidden; height: 100vh; width: 100vw; display: flex; justify-content: center; align-items: center; }
        
        /* Brightness Overlay */
        #brightnessOverlay { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: black; opacity: 0; pointer-events: none; z-index: 9999; }

        /* Rotate Screen Warning for Portrait Mode */
        @media screen and (orientation: portrait) {
            #rotateNotice { display: flex !important; }
        }
        #rotateNotice { display: none; position: fixed; top:0; left:0; width:100%; height:100%; background: #080d14; z-index: 10000; flex-direction: column; justify-content: center; align-items: center; text-align: center; color: #00ffcc; padding: 20px; }

        /* Auth Box (Login/Signup) */
        .auth-container { background: rgba(17, 27, 33, 0.95); border: 2px solid #00ffcc; padding: 20px 30px; border-radius: 15px; width: 340px; text-align: center; box-shadow: 0 0 20px rgba(0,255,204,0.3); }
        .auth-container h2 { color: #00ffcc; margin-bottom: 15px; font-size: 24px; text-transform: uppercase; }
        .auth-container input { width: 100%; padding: 10px; margin: 8px 0; background: #1f2c34; border: 1px solid #00ffcc; color: white; border-radius: 8px; outline: none; }
        .auth-container button { width: 100%; padding: 12px; background: #00ffcc; border: none; color: #000; font-weight: bold; border-radius: 8px; cursor: pointer; margin-top: 10px; font-size: 16px; }
        .auth-toggle { font-size: 12px; color: #8696a0; margin-top: 12px; cursor: pointer; text-decoration: underline; }

        /* Game Lobby Screen */
        #lobbyScreen { display: none; width: 100vw; height: 100vh; background: linear-gradient(to bottom, #111e2e, #050a10); position: relative; flex-direction: column; justify-content: space-between; padding: 15px; }
        .lobby-header { display: flex; justify-content: space-between; align-items: center; }
        .player-info { background: rgba(0,0,0,0.6); padding: 8px 15px; border-radius: 20px; border: 1px solid #00ffcc; color: #00ffcc; font-weight: bold; }

        /* Lobby Display Area (Character & Vehicle) */
        .lobby-stage { flex: 1; display: flex; justify-content: center; align-items: center; position: relative; }
        .stage-platform { width: 320px; height: 120px; background: rgba(0,255,204,0.1); border-radius: 50%; border: 2px solid #00ffcc; position: absolute; bottom: 30px; transform: rotateX(60deg); box-shadow: 0 0 30px #00ffcc; }
        
        .lobby-entities { display: flex; align-items: flex-end; gap: 20px; z-index: 2; transition: all 0.3s ease; }
        .character-avatar { font-size: 70px; color: #ffbc00; text-shadow: 0 0 10px #ffbc00; }
        .vehicle-avatar { font-size: 85px; color: #00ffcc; text-shadow: 0 0 15px #00ffcc; transition: transform 0.3s ease; }

        /* Lobby Controls (Aage/Pichhe) */
        .lobby-controls { position: absolute; right: 20px; top: 40%; display: flex; flex-direction: column; gap: 10px; z-index: 10; }
        .btn-lobby-move { background: rgba(0,0,0,0.7); border: 1px solid #00ffcc; color: #00ffcc; padding: 10px; border-radius: 50%; cursor: pointer; }

        /* Start Game Button */
        .btn-start-game { background: #00ffcc; color: #000; font-size: 22px; font-weight: bold; border: none; padding: 15px 40px; border-radius: 30px; cursor: pointer; box-shadow: 0 0 15px #00ffcc; align-self: center; margin-bottom: 10px; }

        /* Settings Modal */
        .modal { display: none; position: fixed; top: 0; left:0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.85); z-index: 1000; justify-content: center; align-items: center; }
        .modal-content { background: #111b21; border: 2px solid #00ffcc; width: 350px; padding: 20px; border-radius: 12px; color: white; }
        .setting-row { margin: 15px 0; display: flex; justify-content: space-between; align-items: center; }
        .setting-row label { font-size: 14px; }
        .setting-row input[type="range"] { width: 140px; }

        /* Game Canvas */
        #gameCanvas { display: none; background: #222; border: 2px solid #00ffcc; }
    </style>
</head>
<body>

    <!-- Brightness Control Overlay -->
    <div id="brightnessOverlay"></div>

    <!-- Landscape Rotate Screen Notice -->
    <div id="rotateNotice">
        <i class="fa-solid fa-mobile-screen-button fa-rotate-90" style="font-size: 50px; margin-bottom: 15px;"></i>
        <h2>Kripya Phone Rotate Karein 🔄</h2>
        <p style="font-size: 12px; color: #8696a0; margin-top: 8px;">Aachha gaming anubhav ke liye landscape mode me khelein!</p>
    </div>

    <!-- Auth Container (Login / Register / Forgot Pass) -->
    <div class="auth-container" id="authBox">
        <h2>🏎️ BK KAR</h2>
        <div id="formFields">
            <input type="text" id="authName" placeholder="Full Name">
            <input type="tel" id="authMobile" placeholder="Mobile Number">
            <input type="password" id="authPassword" placeholder="Strong Password">
        </div>
        <button id="authBtn" onclick="submitAuth('register')">Register & Play</button>
        
        <div class="auth-toggle" onclick="toggleAuthMode()" id="toggleText">Pehle se account hai? Login Karein</div>
        <div class="auth-toggle" style="color:#ff5555; margin-top:5px;" onclick="forgotPassword()">Password Bhool Gaye?</div>
    </div>

    <!-- Lobby Screen -->
    <div id="lobbyScreen">
        <div class="lobby-header">
            <div class="player-info"><i class="fa-solid fa-user"></i> <span id="pName">Player</span></div>
            <h2 style="color: #00ffcc; letter-spacing: 2px;">BK KAR</h2>
            <button style="background: none; border: none; color: #00ffcc; font-size: 24px; cursor: pointer;" onclick="openSettings()">
                <i class="fa-solid fa-gear"></i>
            </button>
        </div>

        <div class="lobby-stage">
            <div class="stage-platform"></div>
            <div class="lobby-entities" id="lobbyEntities">
                <div class="character-avatar"><i class="fa-solid fa-user-ninja"></i></div>
                <div class="vehicle-avatar" id="vehicleIcon"><i class="fa-solid fa-car"></i></div>
            </div>

            <!-- Lobby Vehicle Movement Controls -->
            <div class="lobby-controls">
                <button class="btn-lobby-move" onclick="moveVehicleLobby(-20)"><i class="fa-solid fa-arrow-up"></i></button>
                <button class="btn-lobby-move" onclick="moveVehicleLobby(20)"><i class="fa-solid fa-arrow-down"></i></button>
            </div>
        </div>

        <button class="btn-start-game" onclick="startGame()">RACE START 🏁</button>
    </div>

    <!-- Settings Modal -->
    <div class="modal" id="settingsModal">
        <div class="modal-content">
            <h3 style="color:#00ffcc; text-align:center; margin-bottom:15px;"><i class="fa-solid fa-sliders"></i> Game Settings</h3>
            
            <div class="setting-row">
                <label>Sensitivity:</label>
                <input type="range" id="sensRange" min="10" max="100" value="50" onchange="saveSettings()">
            </div>
            
            <div class="setting-row">
                <label>Brightness (Roshni):</label>
                <input type="range" id="brightRange" min="0" max="80" value="0" oninput="adjustBrightness(this.value)" onchange="saveSettings()">
            </div>

            <div class="setting-row">
                <label>Vehicle Choose:</label>
                <select id="vehicleSelect" onchange="changeVehicle(this.value)" style="background:#1f2c34; color:white; padding:5px; border-radius:5px;">
                    <option value="car">Car 🏎️</option>
                    <option value="bike">Bike 🏍️</option>
                </select>
            </div>

            <div class="setting-row">
                <label>Graphics:</label>
                <select style="background:#1f2c34; color:white; padding:5px; border-radius:5px;">
                    <option>High (Ultra)</option>
                    <option>Smooth (Low)</option>
                </select>
            </div>

            <button onclick="closeSettings()" style="width:100%; padding:10px; background:#00ffcc; border:none; border-radius:6px; font-weight:bold; margin-top:10px; cursor:pointer;">Save & Close</button>
            <button onclick="logout()" style="width:100%; padding:8px; background:#ff4444; border:none; border-radius:6px; color:white; font-weight:bold; margin-top:8px; cursor:pointer;">Logout</button>
        </div>
    </div>

    <!-- Game Canvas -->
    <canvas id="gameCanvas" width="500" height="300"></canvas>

    <script>
        let isLoginMode = false;
        let currentUser = null;
        let vehiclePosOffset = 0;

        function toggleAuthMode() {
            isLoginMode = !isLoginMode;
            document.getElementById('authName').style.display = isLoginMode ? 'none' : 'block';
            document.getElementById('authBtn').innerText = isLoginMode ? 'Login' : 'Register & Play';
            document.getElementById('toggleText').innerText = isLoginMode ? "Naye user hain? Account Banayein" : "Pehle se account hai? Login Karein";
        }

        function submitAuth(type) {
            let name = document.getElementById('authName').value;
            let mobile = document.getElementById('authMobile').value;
            let password = document.getElementById('authPassword').value;

            if(!mobile || !password) { alert('Kripya Mobile aur Password bharein!'); return; }

            fetch('/auth', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ action: isLoginMode ? 'login' : 'register', name, mobile, password })
            })
            .then(res => res.json())
            .then(data => {
                if(data.status === 'ok') {
                    currentUser = data.user;
                    loadLobby();
                } else {
                    alert(data.message);
                }
            });
        }

        function forgotPassword() {
            let mob = prompt("Apna registered mobile number daalein:");
            if(mob) alert("Aapko Password reset link mobile number par bhej diya jayega!");
        }

        function loadLobby() {
            document.getElementById('authBox').style.display = 'none';
            document.getElementById('lobbyScreen').style.display = 'flex';
            document.getElementById('pName').innerText = currentUser.name || 'Racer';
            
            if(currentUser.brightness) {
                document.getElementById('brightRange').value = currentUser.brightness;
                adjustBrightness(currentUser.brightness);
            }
            if(currentUser.vehicle) {
                changeVehicle(currentUser.vehicle);
            }
        }

        function moveVehicleLobby(val) {
            vehiclePosOffset += val;
            document.getElementById('vehicleIcon').style.transform = `translateY(${vehiclePosOffset}px)`;
        }

        function adjustBrightness(val) {
            document.getElementById('brightnessOverlay').style.opacity = val / 100;
        }

        function changeVehicle(type) {
            let icon = document.getElementById('vehicleIcon');
            if(type === 'bike') {
                icon.innerHTML = '<i class="fa-solid fa-motorcycle"></i>';
            } else {
                icon.innerHTML = '<i class="fa-solid fa-car"></i>';
            }
        }

        function openSettings() { document.getElementById('settingsModal').style.display = 'flex'; }
        function closeSettings() { document.getElementById('settingsModal').style.display = 'none'; }

        function saveSettings() {
            let sens = document.getElementById('sensRange').value;
            let bright = document.getElementById('brightRange').value;
            let veh = document.getElementById('vehicleSelect').value;

            fetch('/update_settings', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ sensitivity: sens, brightness: bright, vehicle: veh })
            });
        }

        function logout() {
            location.reload();
        }

        function startGame() {
            alert("🏎️ Race shuru ho rahi hai! Controls: Phone ko left/right rotate karein!");
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
            c.execute("SELECT name, mobile, sensitivity, brightness, vehicle FROM users WHERE mobile=?", (data['mobile'],))
            user = c.fetchone()
            conn.close()
            return jsonify({'status': 'ok', 'user': {'name': user[0], 'mobile': user[1], 'sensitivity': user[2], 'brightness': user[3], 'vehicle': user[4]}})
        except:
            conn.close()
            return jsonify({'status': 'error', 'message': 'Mobile number pehle se registered hai!'})
            
    elif data['action'] == 'login':
        c.execute("SELECT name, mobile, sensitivity, brightness, vehicle FROM users WHERE mobile=? AND password=?", 
                  (data['mobile'], data['password']))
        user = c.fetchone()
        conn.close()
        if user:
            return jsonify({'status': 'ok', 'user': {'name': user[0], 'mobile': user[1], 'sensitivity': user[2], 'brightness': user[3], 'vehicle': user[4]}})
        else:
            return jsonify({'status': 'error', 'message': 'Galat Mobile Number ya Password!'})

@app.route('/update_settings', methods=['POST'])
def update_settings():
    data = request.json
    conn = get_db()
    conn.execute("UPDATE users SET sensitivity=?, brightness=?, vehicle=? WHERE id=1", 
                 (data['sensitivity'], data['brightness'], data['vehicle']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
