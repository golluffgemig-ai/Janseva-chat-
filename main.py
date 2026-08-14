from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'janseva_whatsapp_ui_key_2026'

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Database Helper
def get_db():
    conn = sqlite3.connect('chat.db', check_same_thread=False, timeout=20)
    return conn

# Database Tables Setup
def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    username TEXT UNIQUE, 
                    password TEXT, 
                    bio TEXT DEFAULT 'Hey there! I am using WhatsApp.', 
                    lock_enabled INTEGER DEFAULT 0, 
                    screen_pin TEXT DEFAULT ''
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    sender TEXT, 
                    room TEXT DEFAULT 'Public', 
                    content TEXT, 
                    msg_type TEXT DEFAULT 'text', 
                    file_url TEXT DEFAULT ''
                )''')
    conn.commit()
    conn.close()

init_db()

# Full UI + Backend HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WhatsApp Web App</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: Arial, sans-serif; }
        body { background-color: #0b141a; color: #e9edef; display: flex; flex-direction: column; height: 100vh; }
        
        .top-bar { background-color: #111b21; padding: 12px 16px; display: flex; justify-content: space-between; align-items: center; }
        .top-bar .title { font-size: 20px; font-weight: bold; }
        .top-icons i { margin-left: 20px; font-size: 18px; cursor: pointer; }

        .content { flex: 1; padding: 10px; overflow-y: auto; display: flex; flex-direction: column; }

        .dropdown-menu { display: none; position: absolute; top: 45px; right: 10px; background-color: #233138; border-radius: 8px; width: 180px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); z-index: 100; }
        .dropdown-menu ul { list-style: none; }
        .dropdown-menu ul li { padding: 12px 16px; font-size: 14px; cursor: pointer; color: #e9edef; }
        .dropdown-menu ul li:hover { background-color: #182229; }
        .dropdown-menu ul li a { color: #ff5555; text-decoration: none; }

        .bottom-nav { background-color: #111b21; display: flex; justify-content: space-around; padding: 10px 0; border-top: 1px solid #222d34; }
        .nav-item { display: flex; flex-direction: column; align-items: center; font-size: 12px; color: #8696a0; cursor: pointer; }
        .nav-item.active { color: #00a884; }
        .nav-item i { font-size: 20px; margin-bottom: 4px; }

        /* Chat Styles */
        #chat-box { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; padding-bottom: 10px; }
        .msg { max-width: 75%; padding: 8px 12px; border-radius: 8px; font-size: 14px; word-wrap: break-word; }
        .sent { background-color: #005c4b; align-self: flex-end; color: white; }
        .received { background-color: #202c33; align-self: flex-start; color: white; }
        .msg-sender { font-size: 10px; color: #8696a0; margin-bottom: 2px; }

        .input-bar { display: flex; gap: 8px; padding: 5px 0; background-color: #111b21; }
        .input-bar input { flex: 1; background-color: #2a3942; border: none; outline: none; padding: 10px; border-radius: 8px; color: white; }
        .input-bar button { background-color: #00a884; border: none; padding: 10px 15px; border-radius: 8px; color: white; cursor: pointer; font-weight: bold; }

        .auth-box { max-width: 320px; margin: 50px auto; background: #111b21; padding: 20px; border-radius: 10px; text-align: center; }
        .auth-box input { width: 100%; padding: 10px; margin: 10px 0; background: #2a3942; border: none; color: white; border-radius: 5px; }
        .auth-box button { width: 100%; padding: 10px; background: #00a884; border: none; color: white; font-weight: bold; border-radius: 5px; cursor: pointer; }
    </style>
</head>
<body>

    {% if not user %}
    <!-- Login Screen -->
    <div class="auth-box">
        <h2 style="color: #00a884; margin-bottom: 15px;"><i class="fa-brands fa-whatsapp"></i> WhatsApp</h2>
        <form action="/login" method="POST">
            <input type="text" name="username" placeholder="Enter Username" required>
            <input type="password" name="password" placeholder="Enter Password" required>
            <button type="submit">Login / Register</button>
        </form>
    </div>
    {% else %}

    <!-- Top Bar -->
    <div class="top-bar">
        <div class="title" id="page-title">WhatsApp</div>
        <div class="top-icons">
            <i class="fa-solid fa-magnifying-glass"></i>
            <i class="fa-solid fa-ellipsis-vertical" onclick="toggleMenu()"></i>
        </div>
    </div>

    <!-- 3-Dots Menu -->
    <div class="dropdown-menu" id="menu">
        <ul>
            <li>User: <b>{{ user }}</b></li>
            <li onclick="alert('Bio: {{ bio }}')">My Profile</li>
            <li>Settings</li>
            <li><a href="/logout">Logout</a></li>
        </ul>
    </div>

    <!-- Main Content Area -->
    <div class="content" id="main-content">
        <!-- Default: Chats Screen -->
        <div id="chat-box"></div>
        <div class="input-bar">
            <input type="text" id="msgInput" placeholder="Message...">
            <button onclick="sendMessage()"><i class="fa-solid fa-paper-plane"></i></button>
        </div>
    </div>

    <!-- Bottom Navigation Bar -->
    <div class="bottom-nav">
        <div class="nav-item active" onclick="changeTab('Chats', this)">
            <i class="fa-solid fa-comment-dots"></i>
            <span>Chats</span>
        </div>
        <div class="nav-item" onclick="changeTab('Updates', this)">
            <i class="fa-regular fa-circle-dot"></i>
            <span>Updates</span>
        </div>
        <div class="nav-item" onclick="changeTab('Communities', this)">
            <i class="fa-solid fa-user-group"></i>
            <span>Communities</span>
        </div>
        <div class="nav-item" onclick="changeTab('Calls', this)">
            <i class="fa-solid fa-phone"></i>
            <span>Calls</span>
        </div>
    </div>

    <script>
        const currentUser = "{{ user }}";

        function toggleMenu() {
            var menu = document.getElementById("menu");
            menu.style.display = (menu.style.display === "block") ? "none" : "block";
        }

        function changeTab(tabName, element) {
            document.getElementById("page-title").innerText = tabName;
            document.querySelectorAll(".nav-item").forEach(item => item.classList.remove("active"));
            element.classList.add("active");

            var content = document.getElementById("main-content");
            
            if(tabName === 'Chats') {
                content.innerHTML = `
                    <div id="chat-box"></div>
                    <div class="input-bar">
                        <input type="text" id="msgInput" placeholder="Message...">
                        <button onclick="sendMessage()"><i class="fa-solid fa-paper-plane"></i></button>
                    </div>`;
                loadMessages();
            } else if(tabName === 'Updates') {
                content.innerHTML = "<h3>Status & Channels</h3><p style='color: #8696a0; margin-top: 10px;'>Yahan Status dikhenge...</p>";
            } else {
                content.innerHTML = "<h3>" + tabName + " Screen</h3><p style='color: #8696a0; margin-top: 10px;'>Yahan aapka content dikhega...</p>";
            }
        }

        function sendMessage() {
            let input = document.getElementById('msgInput');
            let txt = input.value.trim();
            if(!txt) return;

            fetch('/send_msg', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: 'content=' + encodeURIComponent(txt)
            }).then(res => res.json()).then(data => {
                input.value = '';
                loadMessages();
            });
        }

        function loadMessages() {
            let box = document.getElementById('chat-box');
            if(!box) return;

            fetch('/get_msg')
                .then(res => res.json())
                .then(data => {
                    box.innerHTML = data.map(m => {
                        let isMe = (m.sender === currentUser);
                        return `
                            <div class="msg ${isMe ? 'sent' : 'received'}">
                                ${!isMe ? `<div class="msg-sender">${m.sender}</div>` : ''}
                                <div>${m.content}</div>
                            </div>
                        `;
                    }).join('');
                    box.scrollTop = box.scrollHeight;
                });
        }

        // Live refresh every 2 seconds
        setInterval(() => {
            if(document.getElementById('chat-box')) {
                loadMessages();
            }
        }, 2000);

        loadMessages();
    </script>
    {% endif %}

</body>
</html>
"""

@app.route('/')
def home():
    user = session.get('username')
    bio = session.get('bio', 'Hey there! I am using WhatsApp.')
    return render_template_string(HTML_TEMPLATE, user=user, bio=bio)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()
    
    if not user:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        bio = 'Hey there! I am using WhatsApp.'
    else:
        bio = user[3] if user[3] else 'Hey there! I am using WhatsApp.'

    conn.close()
    
    session['username'] = username
    session['bio'] = bio
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/send_msg', methods=['POST'])
def send_msg():
    if 'username' not in session:
        return jsonify({'status': 'error'})
    
    content = request.form.get('content')
    conn = get_db()
    conn.execute("INSERT INTO messages (sender, content) VALUES (?, ?)", (session['username'], content))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/get_msg')
def get_msg():
    conn = get_db()
    rows = conn.execute("SELECT sender, content FROM messages ORDER BY id ASC").fetchall()
    conn.close()
    return jsonify([{'sender': r[0], 'content': r[1]} for r in rows])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
