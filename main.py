from flask import Flask, render_template_string, request, jsonify
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'bk_kar_fixed_key_2026'

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
                    brightness INTEGER DEFAULT 0,
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
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BK Kar Game 🏎️</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: sans-serif; }
        body { background-color: #0b131f; color: #ffffff; min-height: 100vh; display: flex; justify-content: center; align-items: center; padding: 15px; }

        /* Auth Screen Box */
        .auth-box { background: #132238; border: 2px solid #00e5ff; padding: 25px; border-radius: 12px; width: 100%; max-width: 350px; text-align: center; box-shadow: 0 0 15px rgba(0, 229, 255, 0.2); }
        .auth-box h1 { color: #00e5ff; margin-bottom: 20px; font-size: 26px; }
        .auth-box input { width: 100%; padding: 12px; margin: 8px 0; background: #1c2d42; border: 1px solid #00e5ff; color: #fff; border-radius: 6px; outline: none; font-size: 14px; }
        .auth-box button { width: 100%; padding: 12px; background: #00e5ff; border: none; color: #000; font-weight: bold; font-size: 16px; border-radius: 6px; cursor: pointer; margin-top: 12px; }
        .toggle-btn { margin-top: 15px; font-size: 13px; color: #88a0c0; cursor: pointer; text-decoration: underline; }

        /* Lobby Screen */
        #lobbyScreen { display: none; width: 100%; max-width: 500px; background: #132238; border: 2px solid #00e5ff; border-radius: 12px; padding: 20px; text-align: center; }
        .lobby-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .player-tag { background: #1c2d42; padding: 6px 12px; border-radius: 20px; color: #00e5ff; font-weight: bold; border: 1px solid #00e5ff; }
        
        .stage { background: #0b131f; height: 180px; border-radius: 10px; border: 1px dashed #00e5ff; display: flex; justify-content: center; align-items: center; gap: 20px; margin-bottom: 20px; position: relative; }
        .avatar { font-size: 60px; color: #ffca28; }
        .vehicle { font-size: 70px; color: #00e5ff; transition: transform 0.2s; }

        .start-btn { background: #00e5ff; color: #000; font-size: 20px; font-weight: bold; padding: 12px 30px; border: none; border-radius: 25px; cursor: pointer; width: 100%; box-shadow: 0 0 10px #00e5ff; }

        /* Settings Modal */
        #settingsModal { display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.85); justify-content: center; align-items: center; padding: 20px; }
        .modal-box { background: #132238; border: 2px solid #00e5ff; padding: 20px; border-radius: 10px; width: 100%; max-width: 320px; text-align: left; }
        .setting-item { margin: 15px 0; }
        .setting-item label { display: block; margin-bottom: 5px; font-size: 14px; color: #88a0c0; }
        .setting-item select, .setting-item input { width: 100%; padding: 8px; background: #1c2d42; border: 1px solid #00e5ff; color: white; border-radius: 5px; }
    </style>
</head>
<body>

    <!-- Login / Register Form -->
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

    <!-- Main Game Lobby -->
    <div id="lobbyScreen">
        <div class="lobby-header">
            <div class="player-tag"><i class="fa-solid fa-user"></i> <span id="pName">Player</span></div>
            <h2 style="color: #00e5ff;">BK KAR</h2>
            <i class="fa-solid fa-gear" style="font-size: 24px; color: #00e5ff; cursor: pointer;" onclick="toggleSettings(true)"></i>
        </div>

        <div class="stage">
            <div class="avatar"><i class="fa-solid fa-user-ninja"></i></div>
            <div class="vehicle" id="vIcon"><i class="fa-solid fa-car"></i></div>
        </div>

        <button class="start-btn" onclick="alert('🏎️ Race Shuru Ho Rahi Hai!')">RACE START 🏁</button>
    </div>

    <!-- Settings Popup -->
    <div id="settingsModal">
        <div class="modal-box">
            <h3 style="color: #00e5ff; text-align: center; margin-bottom: 15px;">⚙️ Game Settings</h3>
            
            <div class="setting-item">
                <label>Vehicle Choose:</label>
                <select id="vSelect" onchange="changeVehicle(this.value)">
                    <option value="car">Car 🏎️</option>
                    <option value="bike">Bike 🏍️</option>
                </select>
            </div>

            <div class="setting-item">
                <label>Sensitivity:</label>
                <input type="range" min="10" max="100" value="50">
            </div>

            <button onclick="toggleSettings(false)" style="width: 100%; padding: 10px; background: #00e5ff; border: none; font-weight: bold; border-radius: 5px; margin-top: 10px; cursor: pointer;">Save & Close</button>
            <button onclick="location.reload()" style="width: 100%; padding: 8px; background: #ff5252; border: none; color: white; font-weight: bold; border-radius: 5px; margin-top: 8px; cursor: pointer;">Logout</button>
        </div>
    </div>

    <script>
        let isLoginMode = false;

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

            if(!mobile || !password) {
                alert('Mobile number aur Password dono bharein!');
                return;
            }

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
            let icon = document.getElementById('vIcon');
            icon.innerHTML = (type === 'bike') ? '<i class="fa-solid fa-motorcycle"></i>' : '<i class="fa-solid fa-car"></i>';
        }

        function toggleSettings(show) {
            document.getElementById('settingsModal').style.display = show ? 'flex' : 'none';
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
