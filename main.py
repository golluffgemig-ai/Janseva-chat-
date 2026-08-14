afrom flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'janseva_secret_2026_fixed'

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Database Helper Function
def get_db():
    conn = sqlite3.connect('chat.db', check_same_thread=False, timeout=20)
    return conn

# Init Tables
def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, bio TEXT DEFAULT '', lock_enabled INTEGER DEFAULT 0, screen_pin TEXT DEFAULT '')''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, sender TEXT, room TEXT, content TEXT, msg_type TEXT, file_url TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS follows (id INTEGER PRIMARY KEY AUTOINCREMENT, follower TEXT, followed TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS groups (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)''')
    conn.commit()
    conn.close()

init_db()

# Full HTML & JS Logic
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { background: #0b141a; color: white !important; font-family: sans-serif; margin: 0; }
        .container { max-width: 500px; margin: auto; height: 100vh; display: flex; flex-direction: column; background: #111b21; }
        .msg { padding: 10px; margin: 5px; border-radius: 10px; color: white !important; }
        .sent { background: #005c4b; align-self: flex-end; }
        .received { background: #202c33; align-self: flex-start; }
        input { background: #202c33 !important; color: white !important; border: 1px solid #333; padding: 10px; width: 90%; }
        button { background: #00a884; border: none; padding: 10px 20px; cursor: pointer; color: white; font-weight: bold; }
        .tab-content { display: none; flex: 1; overflow-y: auto; padding: 10px; }
        .active-tab { display: flex; flex-direction: column; }
    </style>
</head>
<body>
    <div class="container">
        {% if not user %}
        <div style="text-align:center; padding: 50px;">
            <h1>Janseva Chat</h1>
            <form action="/login" method="POST"><input name="username" placeholder="Username" required><br><br><input name="password" type="password" placeholder="Password" required><br><br><button type="submit">Login</button></form>
            <form action="/signup" method="POST" style="margin-top:20px;"><button type="submit" style="background:transparent; border:1px solid #00a884;">Create Account</button></form>
        </div>
        {% else %}
        <div style="background:#202c33; padding:15px; display:flex; justify-content:space-between;">
            <div>{{ user }}</div>
            <a href="/logout" style="color:red;">Exit</a>
        </div>
        <div style="display:flex; background:#111b21;">
            <button onclick="showTab('chat')">Chat</button><button onclick="showTab('profile')">Profile</button>
        </div>
        
        <div id="chat" class="tab-content active-tab">
            <div id="chatBox" style="flex:1; overflow-y:auto;"></div>
            <div style="display:flex;">
                <input id="msgInp" placeholder="Message...">
                <button onclick="sendMsg()">Send</button>
            </div>
        </div>
        
        <div id="profile" class="tab-content">
            <h3>Profile</h3>
            <input id="bioInp" placeholder="New Bio...">
            <button onclick="updateBio()">Save Bio</button>
        </div>

        <script>
            function showTab(id) {
                document.querySelectorAll('.tab-content').forEach(t => t.style.display='none');
                document.getElementById(id).style.display='flex';
            }
            function sendMsg() {
                let inp = document.getElementById('msgInp');
                fetch('/send_msg', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:'content='+inp.value+'&room=Public'}).then(() => {inp.value=''; loadMsg();});
            }
            function loadMsg() {
                fetch('/get_msg').then(res=>res.json()).then(data => {
                    let box = document.getElementById('chatBox');
                    box.innerHTML = data.map(m => `<div class="msg ${m.sender=='{{user}}'?'sent':'received'}">${m.content}</div>`).join('');
                });
            }
            function updateBio() {
                let bio = document.getElementById('bioInp').value;
                fetch('/update_bio', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:'bio='+bio}).then(() => alert('Bio Saved!'));
            }
            setInterval(loadMsg, 2000);
            loadMsg();
        </script>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def home(): return render_template_string(HTML_TEMPLATE, user=session.get('username'))

@app.route('/login', methods=['POST'])
def login():
    session['username'] = request.form.get('username')
    return redirect('/')

@app.route('/signup', methods=['POST'])
def signup(): return redirect('/')

@app.route('/logout')
def logout(): session.clear(); return redirect('/')

@app.route('/send_msg', methods=['POST'])
def send_msg():
    conn = get_db()
    conn.execute("INSERT INTO messages (sender, room, content) VALUES (?, ?, ?)", (session['username'], 'Public', request.form.get('content')))
    conn.commit()
    conn.close()
    return jsonify({'status':'ok'})

@app.route('/get_msg')
def get_msg():
    conn = get_db()
    rows = conn.execute("SELECT sender, content FROM messages").fetchall()
    conn.close()
    return jsonify([{'sender': r[0], 'content': r[1]} for r in rows])

@app.route('/update_bio', methods=['POST'])
def update_bio():
    conn = get_db()
    conn.execute("UPDATE users SET bio=? WHERE username=?", (request.form.get('bio'), session['username']))
    conn.commit()
    conn.close()
    return jsonify({'status':'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
gunicorn main:app --workers 1 --threads 4
