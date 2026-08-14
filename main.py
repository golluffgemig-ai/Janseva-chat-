from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'janseva_chat_whatsapp_ultra_key_2026'

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def init_db():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT UNIQUE, 
                  password TEXT, 
                  bio TEXT DEFAULT 'Hey there! I am using Janseva Chat', 
                  avatar TEXT DEFAULT '',
                  lock_enabled INTEGER DEFAULT 0,
                  screen_pin TEXT DEFAULT '')''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  sender TEXT, 
                  room TEXT DEFAULT 'Public Room', 
                  content TEXT, 
                  msg_type TEXT DEFAULT 'text', 
                  file_url TEXT DEFAULT '', 
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS follows
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, follower TEXT, followed TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS groups
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, created_by TEXT)''')

    try:
        c.execute("INSERT INTO groups (name, created_by) VALUES ('Public Room', 'System')")
    except:
        pass
    conn.commit()
    conn.close()

init_db()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Janseva Chat</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; }
        body { background-color: #0b141a; color: #e9edef; height: 100vh; display: flex; justify-content: center; align-items: center; overflow: hidden; }
        .container { width: 100%; max-width: 450px; height: 100vh; background: #111b21; display: flex; flex-direction: column; position: relative; }
        .header { background: #202c33; padding: 10px 14px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #222d34; }
        .user-info { display: flex; align-items: center; gap: 8px; font-weight: bold; font-size: 1rem; color: #e9edef; }
        .online-dot { width: 9px; height: 9px; background-color: #25d366; border-radius: 50%; display: inline-block; }
        .btn-sm { background: #2a3942; color: #d1d7db; border: none; padding: 6px 10px; border-radius: 6px; cursor: pointer; font-size: 0.8rem; }
        .btn-danger { background: #ea868f; color: #000; font-weight: bold; }
        .tabs { display: flex; background: #111b21; border-bottom: 2px solid #222d34; }
        .tab { flex: 1; text-align: center; padding: 12px 0; cursor: pointer; font-size: 0.9rem; color: #8696a0; font-weight: 500; }
        .tab.active { color: #00a884; border-bottom: 3px solid #00a884; font-weight: bold; }
        .section { display: none; flex: 1; flex-direction: column; overflow-y: auto; padding: 12px; position: relative; }
        .section.active { display: flex; }
        .auth-box { padding: 25px 20px; display: flex; flex-direction: column; gap: 14px; text-align: center; justify-content: center; height: 100%; }
        input { width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #2a3942; background: #202c33; color: #e9edef; outline: none; margin-bottom: 8px; font-size: 0.95rem; }
        button.btn-main { width: 100%; padding: 12px; border-radius: 8px; border: none; background: #00a884; color: #111b21; font-weight: bold; cursor: pointer; font-size: 1rem; }
        .chat-box { flex: 1; padding: 10px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; background-color: #0b141a; }
        .msg { max-width: 80%; padding: 8px 10px; border-radius: 8px; font-size: 0.9rem; position: relative; word-wrap: break-word; }
        .msg.sent { align-self: flex-end; background: #005c4b; color: #e9edef; }
        .msg.received { align-self: flex-start; background: #202c33; color: #e9edef; }
        .msg img, .msg video { max-width: 100%; border-radius: 6px; margin-top: 5px; }
        .sender-name { font-size: 0.72rem; color: #00a884; font-weight: bold; display: block; margin-bottom: 2px; }
        .msg-time { font-size: 0.65rem; color: #8696a0; text-align: right; margin-top: 4px; display: block; }
        .input-area { padding: 8px; background: #202c33; display: flex; flex-direction: column; gap: 6px; }
        .input-row { display: flex; gap: 6px; align-items: center; }
        .icon-btn { font-size: 1.3rem; cursor: pointer; padding: 6px; color: #8696a0; }
        .emoji-picker { display: none; background: #111b21; padding: 8px; border-radius: 8px; border: 1px solid #2a3942; flex-wrap: wrap; gap: 8px; max-height: 100px; overflow-y: auto; }
        .emoji-picker span { font-size: 1.3rem; cursor: pointer; }
        .card { background: #202c33; padding: 12px; border-radius: 8px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
        .avatar { width: 36px; height: 36px; border-radius: 50%; background: #00a884; color: #111b21; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 8px; }
        #lockScreen { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: #0b141a; z-index: 9999; display: none; flex-direction: column; justify-content: center; align-items: center; padding: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div id="lockScreen">
            <h2 style="color:#00a884; margin-bottom:15px;">🔒 App Locked</h2>
            <input type="password" id="unlockPin" placeholder="Enter PIN/Password" style="width:200px; text-align:center;">
            <button class="btn-main" style="width:200px;" onclick="unlockApp()">Unlock</button>
        </div>

        {% if not user %}
        <div class="auth-box">
            <h1 style="color: #00a884;">Janseva Chat</h1>
            <form action="/login" method="POST">
                <input type="text" name="username" placeholder="Username" required>
                <input type="password" name="password" placeholder="Password" required>
                <button class="btn-main" type="submit">Login</button>
            </form>
            <div style="color:#8696a0;">OR</div>
            <form action="/signup" method="POST">
                <input type="text" name="username" placeholder="Choose Username" required>
                <input type="password" name="password" placeholder="Choose Password" required>
                <button class="btn-main" style="background:#202c33; color:#00a884; border:1px solid #00a884;" type="submit">Create Account</button>
            </form>
        </div>
        {% else %}
        <div class="header">
            <div class="user-info">
                <span class="avatar">{{ user[0].upper() }}</span>
                <div>
                    <div>{{ user }}</div>
                    <div style="font-size:0.68rem; color:#25d366;"><span class="online-dot"></span> Online</div>
                </div>
            </div>
            <a href="/logout" class="btn-sm btn-danger" style="text-decoration:none;">Exit</a>
        </div>

        <div class="tabs">
            <div class="tab active" onclick="switchTab('chats', this)">💬 Chat</div>
            <div class="tab" onclick="switchTab('groups', this)">👨‍👩‍👧‍👦 Groups</div>
            <div class="tab" onclick="switchTab('search', this)">🔍 Search</div>
            <div class="tab" onclick="switchTab('profile', this)">⚙️ Profile</div>
        </div>

        <div id="chats" class="section active" style="padding: 0;">
            <div style="background: #202c33; padding: 8px 12px; font-size: 0.8rem; color: #00a884; font-weight:bold;" id="roomTitle">
                Current Room: Public Room
            </div>
            <div class="chat-box" id="chatBox"></div>
            <div class="input-area">
                <div class="emoji-picker" id="emojiPicker">
                    <span onclick="addEmoji('😊')">😊</span><span onclick="addEmoji('😂')">😂</span><span onclick="addEmoji('❤️')">❤️</span><span onclick="addEmoji('👍')">👍</span><span onclick="addEmoji('🔥')">🔥</span>
                </div>
                <div class="input-row">
                    <span class="icon-btn" onclick="toggleEmojiPicker()">😀</span>
                    <label class="icon-btn">📁 <input type="file" id="fileInput" style="display:none;" onchange="uploadFile()"></label>
                    <span class="icon-btn" id="recBtn" onclick="toggleRecord()">🎙️</span>
                    <input type="text" id="messageInput" placeholder="Message likhein..." style="margin-bottom:0;" onkeypress="if(event.key==='Enter') sendMessage()">
                    <button class="btn-sm" style="background:#00a884; color:#111b21; height:42px; padding:0 16px; font-weight:bold;" onclick="sendMessage()">Send</button>
                </div>
            </div>
        </div>

        <div id="groups" class="section">
            <h3 style="color:#00a884; margin-bottom:10px;">Naya Group Banayein:</h3>
            <input type="text" id="groupNameInput" placeholder="Group ka naam...">
            <button class="btn-main" onclick="createGroup()">Create Group</button>
            <br><hr style="border-color:#2a3942;"><br>
            <div id="groupList"></div>
        </div>

        <div id="search" class="section">
            <input type="text" id="searchInput" placeholder="User search karein..." onkeyup="searchUsers()">
            <div id="searchResults" style="margin-top:10px;"></div>
        </div>

        <div id="profile" class="section">
            <h2 style="color:#00a884; margin-bottom:15px;">⚙️ Profile Settings</h2>
            <div class="card" style="flex-direction:column; align-items:flex-start;">
                <div><b>Username:</b> {{ user }}</div>
                <div id="userBio"><b>Bio:</b> Loading...</div>
            </div>
            <br>
            <input type="text" id="newBioInput" placeholder="Apna naya bio likhein...">
            <button class="btn-main" onclick="updateBio()">Save Bio</button>
            <br><hr style="border-color:#2a3942;"><br>
            <h4 style="color:#00a884; margin-bottom:8px;">🔒 Screen Password:</h4>
            <label><input type="checkbox" id="lockToggle"> Enable Screen Lock</label>
            <input type="password" id="screenPinInput" placeholder="Set PIN/Password">
            <button class="btn-main" onclick="saveLockSetting()">Save Lock</button>
        </div>

        <script>
            let currentRoom = 'Public Room';
            let currentUser = "{{ user }}";
            let mediaRecorder, audioChunks = [];
            let isRecording = false;
            let screenLockEnabled = false, screenPin = '';

            function switchTab(tabId, element) {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
                if(element) element.classList.add('active');
                document.getElementById(tabId).classList.add('active');
                if(tabId === 'groups') loadGroups();
                if(tabId === 'profile') loadProfileData();
            }

            function toggleEmojiPicker() {
                const p = document.getElementById('emojiPicker');
                p.style.display = (p.style.display === 'flex') ? 'none' : 'flex';
            }

            function addEmoji(e) {
                document.getElementById('messageInput').value += e;
                toggleEmojiPicker();
            }

            function fetchMessages() {
                fetch('/get_messages?room=' + encodeURIComponent(currentRoom))
                    .then(res => res.json())
                    .then(data => {
                        const chatBox = document.getElementById('chatBox');
                        chatBox.innerHTML = '';
                        data.forEach(msg => {
                            const isMe = msg.sender === currentUser;
                            const div = document.createElement('div');
                            div.className = 'msg ' + (isMe ? 'sent' : 'received');
                            let contentHtml = `<div>${msg.content}</div>`;
                            if(msg.msg_type === 'image') contentHtml += `<img src="${msg.file_url}">`;
                            if(msg.msg_type === 'video') contentHtml += `<video src="${msg.file_url}" controls></video>`;
                            if(msg.msg_type === 'audio') contentHtml += `<audio src="${msg.file_url}" controls style="max-width:210px;"></audio>`;
                            div.innerHTML = `<span class="sender-name">${isMe ? 'You' : msg.sender}</span>${contentHtml}<span class="msg-time">✓✓</span>`;
                            chatBox.appendChild(div);
                        });
                    });
            }

            function sendMessage() {
                const input = document.getElementById('messageInput');
                if(!input.value.trim()) return;
                fetch('/send_message', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: new URLSearchParams({'content': input.value, 'room': currentRoom, 'msg_type': 'text'})
                }).then(() => { input.value = ''; fetchMessages(); });
            }

            function uploadFile() {
                const fileInput = document.getElementById('fileInput');
                if(!fileInput.files[0]) return;
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                formData.append('room', currentRoom);
                fetch('/upload_media', { method: 'POST', body: formData }).then(() => { fileInput.value = ''; fetchMessages(); });
            }

            function toggleRecord() {
                if(!isRecording) {
                    navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
                        mediaRecorder = new MediaRecorder(stream);
                        audioChunks = [];
                        mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
                        mediaRecorder.onstop = () => {
                            const blob = new Blob(audioChunks, { type: 'audio/mp3' });
                            const formData = new FormData();
                            formData.append('file', blob, 'voice.mp3');
                            formData.append('room', currentRoom);
                            fetch('/upload_media', { method: 'POST', body: formData }).then(() => fetchMessages());
                        };
                        mediaRecorder.start();
                        isRecording = true;
                        document.getElementById('recBtn').style.color = '#ef4444';
                    });
                } else {
                    mediaRecorder.stop();
                    isRecording = false;
                    document.getElementById('recBtn').style.color = '#8696a0';
                }
            }

            function createGroup() {
                const name = document.getElementById('groupNameInput').value.trim();
                if(!name) return;
                fetch('/create_group', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: new URLSearchParams({'name': name})
                }).then(() => { document.getElementById('groupNameInput').value = ''; loadGroups(); });
            }

            function loadGroups() {
                fetch('/get_groups').then(res => res.json()).then(data => {
                    const list = document.getElementById('groupList');
                    list.innerHTML = '';
                    data.forEach(g => {
                        list.innerHTML += `<div class="card"><span><b># ${g.name}</b></span><button class="btn-sm" style="background:#00a884; color:#111b21;" onclick="joinGroup('${g.name}')">Join Chat</button></div>`;
                    });
                });
            }

            function joinGroup(groupName) {
                currentRoom = groupName;
                document.getElementById('roomTitle').innerText = "Current Room: " + currentRoom;
                switchTab('chats', document.querySelectorAll('.tab')[0]);
                fetchMessages();
            }

            function searchUsers() {
                const q = document.getElementById('searchInput').value.trim();
                if(!q) return;
                fetch('/search_users?q=' + encodeURIComponent(q)).then(res => res.json()).then(users => {
                    const resDiv = document.getElementById('searchResults');
                    resDiv.innerHTML = '';
                    users.forEach(u => {
                        resDiv.innerHTML += `<div class="card"><div><span class="avatar">${u.username[0].toUpperCase()}</span> <b>${u.username}</b></div><button class="btn-sm" style="background:#00a884; color:#111b21;" onclick="followUser('${u.username}')">Follow</button></div>`;
                    });
                });
            }

            function followUser(username) {
                fetch('/follow_user', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: new URLSearchParams({'target': username})
                }).then(() => alert(username + " ko Follow kiya!"));
            }

            function loadProfileData() {
                fetch('/get_profile').then(res => res.json()).then(data => {
                    if(data && data.bio !== undefined) {
                        document.getElementById('userBio').innerHTML = "<b>Bio:</b> " + (data.bio || 'None');
                        document.getElementById('lockToggle').checked = data.lock_enabled === 1;
                        screenLockEnabled = data.lock_enabled === 1;
                        screenPin = data.screen_pin || '';
                        if(screenLockEnabled && screenPin) document.getElementById('lockScreen').style.display = 'flex';
                    }
                });
            }

            function updateBio() {
                fetch('/update_profile', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: new URLSearchParams({'bio': document.getElementById('newBioInput').value})
                }).then(() => { alert("Bio Updated!"); loadProfileData(); });
            }

            function saveLockSetting() {
                const enabled = document.getElementById('lockToggle').checked ? 1 : 0;
                const pin = document.getElementById('screenPinInput').value;
                fetch('/save_lock_setting', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: new URLSearchParams({'enabled': enabled, 'pin': pin})
                }).then(() => alert("Lock Saved!"));
            }

            function unlockApp() {
                if(document.getElementById('unlockPin').value === screenPin) {
                    document.getElementById('lockScreen').style.display = 'none';
                } else {
                    alert("Wrong PIN!");
                }
            }

            setInterval(fetchMessages, 2500);
            fetchMessages();
            loadProfileData();
        </script>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    user = session.get('username')
    return render_template_string(HTML_TEMPLATE, user=user)

@app.route('/signup', methods=['POST'])
def signup():
    u, p = request.form.get('username'), request.form.get('password')
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (u, p))
        conn.commit()
        session['username'] = u
    except:
        pass
    conn.close()
    return redirect(url_for('home'))

@app.route('/login', methods=['POST'])
def login():
    u, p = request.form.get('username'), request.form.get('password')
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
    if c.fetchone():
        session['username'] = u
    conn.close()
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/get_messages')
def get_messages():
    room = request.args.get('room', 'Public Room')
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("SELECT id, sender, content, msg_type, file_url FROM messages WHERE room=? ORDER BY id ASC", (room,))
    rows = c.fetchall()
    conn.close()
    return jsonify([{'id': r[0], 'sender': r[1], 'content': r[2], 'msg_type': r[3], 'file_url': r[4]} for r in rows])

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages (sender, room, content, msg_type) VALUES (?, ?, ?, ?)",
              (session['username'], request.form.get('room'), request.form.get('content'), request.form.get('msg_type')))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/upload_media', methods=['POST'])
def upload_media():
    if 'username' not in session or 'file' not in request.files:
        return jsonify({'error': 'Failed'}), 400
    file = request.files['file']
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    msg_type = 'file'
    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        msg_type = 'image'
    elif filename.lower().endswith(('.mp4', '.mkv', '.webm')):
        msg_type = 'video'
    elif filename.lower().endswith(('.mp3', '.wav', '.ogg')):
        msg_type = 'audio'
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages (sender, room, content, msg_type, file_url) VALUES (?, ?, ?, ?, ?)",
              (session['username'], request.form.get('room'), '', msg_type, '/' + filepath))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/create_group', methods=['POST'])
def create_group():
    if 'username' in session and request.form.get('name'):
        conn = sqlite3.connect('chat.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO groups (name, created_by) VALUES (?, ?)", (request.form.get('name'), session['username']))
            conn.commit()
        except:
            pass
        conn.close()
    return jsonify({'status': 'ok'})

@app.route('/get_groups')
def get_groups():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("SELECT name FROM groups")
    rows = c.fetchall()
    conn.close()
    return jsonify([{'name': r[0]} for r in rows])

@app.route('/search_users')
def search_users():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE username LIKE ?", ('%' + request.args.get('q', '') + '%',))
    rows = c.fetchall()
    conn.close()
    return jsonify([{'username': r[0]} for r in rows if r[0] != session.get('username')])

@app.route('/follow_user', methods=['POST'])
def follow_user():
    if 'username' in session and request.form.get('target'):
        conn = sqlite3.connect('chat.db')
        c = conn.cursor()
        c.execute("INSERT INTO follows (follower, followed) VALUES (?, ?)", (session['username'], request.form.get('target')))
        conn.commit()
        conn.close()
    return jsonify({'status': 'ok'})

@app.route('/get_profile')
def get_profile():
    if 'username' not in session:
        return jsonify({})
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("SELECT bio, lock_enabled, screen_pin FROM users WHERE username=?", (session['username'],))
    row = c.fetchone()
    conn.close()
    if row:
        return jsonify({'bio': row[0], 'lock_enabled': row[1], 'screen_pin': row[2]})
    return jsonify({})

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'username' in session:
        conn = sqlite3.connect('chat.db')
        c = conn.cursor()
        c.execute("UPDATE users SET bio=? WHERE username=?", (request.form.get('bio', ''), session['username']))
        conn.commit()
        conn.close()
    return jsonify({'status': 'ok'})

@app.route('/save_lock_setting', methods=['POST'])
def save_lock_setting():
    if 'username' in session:
        conn = sqlite3.connect('chat.db')
        c = conn.cursor()
        c.execute("UPDATE users SET lock_enabled=?, screen_pin=? WHERE username=?", 
                  (request.form.get('enabled', 0), request.form.get('pin', ''), session['username']))
        conn.commit()
        conn.close()
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

