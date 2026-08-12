import os
import sqlite3
from flask import Flask, render_template_string, request, jsonify, session, redirect, send_from_directory

app = Flask(__name__)
app.secret_key = 'jan_seva_secret_key'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# SQLite Database Init
def init_db():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, type TEXT, data TEXT)''')
    conn.commit()
    conn.close()

init_db()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jan Seva Chat App</title>
    <style>
        * { box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #e5ddd5; margin: 0; padding: 10px; }
        .card { max-width: 450px; margin: auto; background: white; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.15); overflow: hidden; }
        .header { background: #075e54; color: white; padding: 15px; text-align: center; }
        .header h2 { margin: 0; font-size: 20px; }
        .auth-box { padding: 20px; display: flex; flex-direction: column; gap: 10px; }
        .auth-box input { padding: 10px; border: 1px solid #ccc; border-radius: 5px; }
        .auth-box button { background: #075e54; color: white; border: none; padding: 10px; border-radius: 5px; cursor: pointer; }
        .msg-box { height: 380px; overflow-y: auto; padding: 12px; background: #efeae2; }
        .msg { margin-bottom: 10px; padding: 10px; border-radius: 8px; max-width: 80%; background: #ffffff; box-shadow: 0 1px 2px rgba(0,0,0,0.1); word-wrap: break-word; }
        .msg b { color: #075e54; font-size: 13px; display: block; margin-bottom: 3px; }
        .msg img { max-width: 100%; border-radius: 6px; margin-top: 5px; }
        .msg audio { width: 100%; margin-top: 5px; }
        .controls { padding: 12px; background: #f0f0f0; display: flex; flex-direction: column; gap: 8px; }
        .row { display: flex; gap: 6px; }
        input[type="text"] { flex: 1; padding: 10px; border: 1px solid #ccc; border-radius: 20px; outline: none; }
        button { background: #128c7e; color: white; border: none; padding: 10px 15px; border-radius: 20px; font-weight: bold; cursor: pointer; }
        .btn-rec { background: #d9534f; }
        .top-bar { display: flex; justify-content: space-between; align-items: center; padding: 8px 15px; background: #128c7e; color: white; font-size: 14px; }
        .top-bar a { color: #ffeb3b; text-decoration: none; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            <h2>🚀 Jan Seva Free Chat</h2>
            <small>Bina Recharge Chat & Share</small>
        </div>

        {% if not session.user %}
        <div class="auth-box">
            <h3>Login / Register</h3>
            <form action="/login_register" method="POST">
                <input type="text" name="username" placeholder="Apna Naam / Username" required style="width:100%; margin-bottom:8px;">
                <input type="password" name="password" placeholder="Password" required style="width:100%; margin-bottom:12px;">
                <button type="submit" style="width:100%;">Enter Chat App</button>
            </form>
        </div>
        {% else %}
        <div class="top-bar">
            <span>👤 Logged in as: <b>{{ session.user }}</b></span>
            <a href="/logout">Logout</a>
        </div>
        
        <div class="msg-box" id="msgBox"></div>

        <div class="controls">
            <div class="row">
                <input type="text" id="txtInput" placeholder="Message likhein...">
                <button onclick="sendText()">Send</button>
            </div>
            <div class="row">
                <input type="file" id="fileInput" accept="image/*" style="display:none" onchange="uploadPhoto()">
                <button onclick="document.getElementById('fileInput').click()" style="background:#34b7f1; flex:1;">📷 Photo Bhejein</button>
                <button id="recBtn" onclick="toggleRecord()" class="btn-rec" style="flex:1;">🎙️ Voice Record</button>
            </div>
        </div>
        {% endif %}
    </div>

    {% if session.user %}
    <script>
        let mediaRecorder;
        let audioChunks = [];
        let isRecording = false;

        async function loadMessages() {
            let res = await fetch('/get_messages');
            let data = await res.json();
            let box = document.getElementById('msgBox');
            box.innerHTML = '';
            data.forEach(m => {
                let div = document.createElement('div');
                div.className = 'msg';
                let content = `<b>${m.username}</b>`;
                if(m.type === 'text') content += m.data;
                if(m.type === 'image') content += `<img src="${m.data}">`;
                if(m.type === 'audio') content += `<audio controls src="${m.data}"></audio>`;
                div.innerHTML = content;
                box.appendChild(div);
            });
            box.scrollTop = box.scrollHeight;
        }

        async function sendText() {
            let inp = document.getElementById('txtInput');
            if(!inp.value) return;
            await fetch('/send_text', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({text: inp.value})
            });
            inp.value = '';
            loadMessages();
        }

        async function uploadPhoto() {
            let inp = document.getElementById('fileInput');
            if(!inp.files[0]) return;
            let fd = new FormData();
            fd.append('file', inp.files[0]);
            await fetch('/upload', { method: 'POST', body: fd });
            inp.value = '';
            loadMessages();
        }

        async function toggleRecord() {
            let btn = document.getElementById('recBtn');
            if(!isRecording) {
                let stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];
                mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
                mediaRecorder.onstop = async () => {
                    let blob = new Blob(audioChunks, { type: 'audio/webm' });
                    let fd = new FormData();
                    fd.append('file', blob, 'voice.webm');
                    await fetch('/upload', { method: 'POST', body: fd });
                    loadMessages();
                };
                mediaRecorder.start();
                isRecording = true;
                btn.innerText = '⏹️ Stop & Send';
            } else {
                mediaRecorder.stop();
                isRecording = false;
                btn.innerText = '🎙️ Voice Record';
            }
        }

        setInterval(loadMessages, 2000);
        loadMessages();
    </script>
    {% endif %}
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/login_register', methods=['POST'])
def login_register():
    username = request.form['username'].strip()
    password = request.form['password'].strip()
    
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    
    if user:
        if user[2] == password:
            session['user'] = username
        else:
            return "Incorrect Password! <a href='/'>Try again</a>"
    else:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        session['user'] = username
        
    conn.close()
    return redirect('/')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

@app.route('/get_messages')
def get_messages():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("SELECT username, type, data FROM messages")
    rows = c.fetchall()
    conn.close()
    
    msgs = [{'username': r[0], 'type': r[1], 'data': r[2]} for r in rows]
    return jsonify(msgs)

@app.route('/send_text', methods=['POST'])
def send_text():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages (username, type, data) VALUES (?, ?, ?)", (session['user'], 'text', data['text']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/upload', methods=['POST'])
def upload():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    file = request.files['file']
    filename = f"{session['user']}_{file.filename}"
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(path)
    
    file_type = 'audio' if file.filename.endswith('.webm') else 'image'
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages (username, type, data) VALUES (?, ?, ?)", (session['user'], file_type, f'/uploads/{filename}'))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/uploads/<filename>')
def serve_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

