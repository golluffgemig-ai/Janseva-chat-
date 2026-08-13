from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify, send_from_directory
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'janseva_chat_ultra_secret_2026'

# Folder setup for file uploads
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, bio TEXT DEFAULT '', avatar TEXT DEFAULT '')''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, sender TEXT, room TEXT DEFAULT 'public', content TEXT, msg_type TEXT DEFAULT 'text', file_url TEXT DEFAULT '', timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS follows
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, follower TEXT, followed TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS groups
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, created_by TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reactions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, msg_id INTEGER, username TEXT, emoji TEXT)''')
    
    # Default Public Room
    try:
        c.execute("INSERT INTO groups (name, created_by) VALUES ('Public Room', 'System')")
    except:
        pass
    conn.commit()
    conn.close()

init_db()

# --- HTML / UI CODE ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Janseva Chat Pro</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { background-color: #0f172a; color: #f8fafc; height: 100vh; display: flex; justify-content: center; align-items: center; }
        .container { width: 100%; max-width: 450px; height: 100vh; max-height: 750px; background: #1e293b; display: flex; flex-direction: column; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
        .header { background: #0284c7; padding: 12px 15px; display: flex; justify-content: space-between; align-items: center; font-weight: bold; }
        .header-actions { display: flex; gap: 8px; align-items: center; }
        .btn-sm { background: #334155; color: white; border: none; padding: 6px 10px; border-radius: 6px; cursor: pointer; font-size: 0.8rem; }
        .btn-danger { background: #ef4444; }
        
        /* Navigation Tabs */
        .tabs { display: flex; background: #0f172a; border-bottom: 1px solid #334155; }
        .tab { flex: 1; text-align: center; padding: 10px; cursor: pointer; font-size: 0.85rem; color: #94a3b8; }
        .tab.active { color: #38bdf8; border-bottom: 2px solid #38bdf8; font-weight: bold; }
        
        .section { display: none; flex: 1; flex-direction: column; overflow-y: auto; padding: 15px; }
        .section.active { display: flex; }

        /* Auth */
        .auth-box { padding: 30px; display: flex; flex-direction: column; gap: 15px; }
        input, select { width: 100%; padding: 10px; border-radius: 8px; border: 1px solid #334155; background: #0f172a; color: #fff; outline: none; margin-bottom: 10px; }
        button.btn-main { width: 100%; padding: 12px; border-radius: 8px; border: none; background: #0284c7; color: white; font-weight: bold; cursor: pointer; }
        
        /* Chat Box */
        .chat-box { flex: 1; padding: 10px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
        .msg { max-width: 82%; padding: 8px 12px; border-radius: 12px; font-size: 0.9rem; position: relative; word-wrap: break-word; }
        .msg.sent { align-self: flex-end; background: #0284c7; color: white; }
        .msg.received { align-self: flex-start; background: #334155; color: white; }
        .msg img, .msg video { max-width: 100%; border-radius: 8px; margin-top: 5px; }
        .sender-name { font-size: 0.7rem; color: #cbd5e1; font-weight: bold; display: block; margin-bottom: 2px; }
        
        /* Reactions */
        .reaction-bar { display: flex; gap: 4px; font-size: 0.75rem; background: rgba(0,0,0,0.3); padding: 2px 6px; border-radius: 10px; margin-top: 4px; width: fit-content; }

        /* Controls / Input Area */
        .input-area { padding: 10px; background: #0f172a; display: flex; flex-direction: column; gap: 8px; }
        .input-row { display: flex; gap: 6px; align-items: center; }
        .media-btns { display: flex; gap: 8px; font-size: 1.2rem; cursor: pointer; }

        /* User List & Profile */
        .user-card { display: flex; justify-content: space-between; align-items: center; background: #334155; padding: 10px; border-radius: 8px; margin-bottom: 8px; }
        .avatar { width: 35px; height: 35px; border-radius: 50%; background: #0284c7; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 8px; }
    </style>
</head>
<body>
    <div class="container">
        {% if not session.username %}
        <!-- AUTH SECTION -->
        <div class="auth-box">
            <h2 style="text-align: center; color: #38bdf8;">Janseva Chat Pro</h2>
            <form action="/login" method="POST">
                <input type="text" name="username" placeholder="Username" required>
                <input type="password" name="password" placeholder="Password" required>
                <button class="btn-main" type="submit">Login</button>
            </form>
            <hr style="border-color: #334155; margin: 10px 0;">
            <h3>Naya Account:</h3>
            <form action="/signup" method="POST">
                <input type="text" name="username" placeholder="Choose Username" required>
                <input type="password" name="password" placeholder="Choose Password" required>
                <button class="btn-main" style="background:#10b981;" type="submit">Register</button>
            </form>
        </div>
        {% else %}
        <!-- HEADER -->
        <div class="header">
            <div>👤 {{ session.username }}</div>
            <div class="header-actions">
                <button class="btn-sm" id="silentBtn" onclick="toggleSilent()">🔔 Sound ON</button>
                <a href="/logout" class="btn-sm btn-danger" style="text-decoration:none;">Exit</a>
            </div>
        </div>

        <!-- TABS -->
        <div class="tabs">
            <div class="tab active" onclick="switchTab('chats')">💬 Chat</div>
            <div class="tab" onclick="switchTab('groups')">👨‍👩‍👧‍👦 Groups</div>
            <div class="tab" onclick="switchTab('search')">🔍 Search</div>
            <div class="tab" onclick="switchTab('profile')">⚙️ Profile</div>
        </div>

        <!-- TAB 1: CHATS -->
        <div id="chats" class="section active" style="padding: 0;">
            <div style="background: #0f172a; padding: 8px 15px; font-size: 0.8rem; color: #38bdf8;" id="roomTitle">
                Current Room: Public Room
            </div>
            <div class="chat-box" id="chatBox"></div>

            <div class="input-area">
                <div class="media-btns">
                    <label style="cursor:pointer;" title="Photo/Video/Audio Select Karein">
                        📁 <input type="file" id="fileInput" style="display:none;" onchange="uploadFile()">
                    </label>
                    <span id="recBtn" onclick="toggleRecord()" title="Voice Message Record Karein">🎙️</span>
                </div>
                <div class="input-row">
                    <input type="text" id="messageInput" placeholder="Message likhein..." style="margin-bottom:0;" onkeypress="if(event.key==='Enter') sendMessage()">
                    <button class="btn-sm" style="background:#0284c7; height:40px; padding:0 15px;" onclick="sendMessage()">Send</button>
                </div>
            </div>
        </div>

        <!-- TAB 2: GROUPS -->
        <div id="groups" class="section">
            <h3>Naya Group Banayein:</h3>
            <input type="text" id="groupNameInput" placeholder="Group ka naam...">
            <button class="btn-main" onclick="createGroup()">Create Group</button>
            <br><hr style="border-color:#334155;"><br>
            <h3>Sabhi Groups:</h3>
            <div id="groupList" style="margin-top:10px;"></div>
        </div>

        <!-- TAB 3: SEARCH & FOLLOW -->
        <div id="search" class="section">
            <input type="text" id="searchInput" placeholder="User ko dhundhein..." onkeyup="searchUsers()">
            <div id="searchResults" style="margin-top:10px;"></div>
        </div>

        <!-- TAB 4: PROFILE -->
        <div id="profile" class="section">
            <h3>Profile Settings</h3>
            <br>
            <form action="/update_profile" method="POST" enctype="multipart/form-data">
                <label>Bio Change Karein:</label>
                <input type="text" name="bio" placeholder="Apna bio likhein...">
                <button class="btn-main" type="submit">Save Profile</button>
            </form>
        </div>

        <script>
            let currentRoom = 'Public Room';
            let currentUser = "{{ session.username }}";
            let silentMode = false;
            let mediaRecorder, audioChunks = [];
            let isRecording = false;

            function switchTab(tabId) {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
                event.target.classList.add('active');
                document.getElementById(tabId).classList.add('active');
                if(tabId === 'groups') loadGroups();
            }

            function toggleSilent() {
                silentMode = !silentMode;
                document.getElementById('silentBtn').innerText = silentMode ? '🔕 Silent' : '🔔 Sound ON';
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
                            if(msg.msg_type === 'image') {
                                contentHtml += `<img src="${msg.file_url}">`;
                            } else if(msg.msg_type === 'video') {
                                contentHtml += `<video src="${msg.file_url}" controls></video>`;
                            } else if(msg.msg_type === 'audio') {
                                contentHtml += `<audio src="${msg.file_url}" controls style="max-width:200px; margin-top:5px;"></audio>`;
                            }

                            div.innerHTML = `<span class="sender-name">${isMe ? 'You' : msg.sender}</span>${contentHtml}
                                <div class="reaction-bar" onclick="addReaction(${msg.id})">❤️ 👍 😂 <span>+</span></div>`;
                            chatBox.appendChild(div);
                        });
                    });
            }

            function sendMessage() {
                const input = document.getElementById('messageInput');
                const content = input.value.trim();
                if(!content) return;

                fetch('/send_message', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: new URLSearchParams({'content': content, 'room': currentRoom, 'msg_type': 'text'})
                }).then(() => {
                    input.value = '';
                    fetchMessages();
                });
            }

            function uploadFile() {
                const fileInput = document.getElementById('fileInput');
                if(!fileInput.files[0]) return;

                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                formData.append('room', currentRoom);

                fetch('/upload_media', { method: 'POST', body: formData })
                    .then(() => {
                        fileInput.value = '';
                        fetchMessages();
                    });
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
                        document.getElementById('recBtn').innerText = '🛑 Recording...';
                    });
                } else {
                    mediaRecorder.stop();
                    isRecording = false;
                    document.getElementById('recBtn').innerText = '🎙️';
                }
            }

            function createGroup() {
                const name = document.getElementById('groupNameInput').value.trim();
                if(!name) return;
                fetch('/create_group', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: new URLSearchParams({'name': name})
                }).then(() => {
                    document.getElementById('groupNameInput').value = '';
                    loadGroups();
                });
            }

            function loadGroups() {
                fetch('/get_groups').then(res => res.json()).then(data => {
                    const list = document.getElementById('groupList');
                    list.innerHTML = '';
                    data.forEach(g => {
                        list.innerHTML += `<div class="user-card">
                            <span><b># ${g.name}</b></span>
                            <button class="btn-sm" onclick="joinGroup('${g.name}')">Join Chat</button>
                        </div>`;
                    });
                });
            }

            function joinGroup(groupName) {
                currentRoom = groupName;
                document.getElementById('roomTitle').innerText = "Current Room: " + currentRoom;
                switchTab('chats');
                fetchMessages();
            }

            function searchUsers() {
                const query = document.getElementById('searchInput').value.trim();
                if(!query) return;
                fetch('/search_users?q=' + encodeURIComponent(query))
                    .then(res => res.json())
                    .then(users => {
                        const resDiv = document.getElementById('searchResults');
                        resDiv.innerHTML = '';
                        users.forEach(u => {
                            resDiv.innerHTML += `<div class="user-card">
                                <div><span class="avatar">${u.username[0].toUpperCase()}</span> <b>${u.username}</b></div>
                                <button class="btn-sm" onclick="followUser('${u.username}')">Follow</button>
                            </div>`;
                        });
                    });
            }

            function followUser(username) {
                fetch('/follow_user', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: new URLSearchParams({'target': username})
                }).then(() => alert(username + " ko Follow kar liya gaya hai!"));
            }

            setInterval(fetchMessages, 2500);
            fetchMessages();
        </script>
        {% endif %}
    </div>
</body>
</html>
"""

# --- BACKEND ROUTES ---
@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form.get('username')
    password = request.form.get('password')
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        session['username'] = username
    except:
        pass
    conn.close()
    return redirect(url_for('home'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    if user:
        session['username'] = username
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
    
    messages = [{'id': r[0], 'sender': r[1], 'content': r[2], 'msg_type': r[3], 'file_url': r[4]} for r in rows]
    return jsonify(messages)

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    content = request.form.get('content', '')
    room = request.form.get('room', 'Public Room')
    msg_type = request.form.get('msg_type', 'text')
    
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages (sender, room, content, msg_type) VALUES (?, ?, ?, ?)",
              (session['username'], room, content, msg_type))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/upload_media', methods=['POST'])
def upload_media():
    if 'username' not in session or 'file' not in request.files:
        return jsonify({'error': 'Failed'}), 400
    
    file = request.files['file']
    room = request.form.get('room', 'Public Room')
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    file_url = '/' + filepath
    
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
              (session['username'], room, '', msg_type, file_url))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/create_group', methods=['POST'])
def create_group():
    name = request.form.get('name')
    if name and 'username' in session:
        conn = sqlite3.connect('chat.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO groups (name, created_by) VALUES (?, ?)", (name, session['username']))
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
    q = request.args.get('q', '')
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE username LIKE ?", ('%' + q + '%',))
    rows = c.fetchall()
    conn.close()
    return jsonify([{'username': r[0]} for r in rows if r[0] != session.get('username')])

@app.route('/follow_user', methods=['POST'])
def follow_user():
    target = request.form.get('target')
    if target and 'username' in session:
        conn = sqlite3.connect('chat.db')
        c = conn.cursor()
        c.execute("INSERT INTO follows (follower, followed) VALUES (?, ?)", (session['username'], target))
        conn.commit()
        conn.close()
    return jsonify({'status': 'ok'})

@app.route('/update_profile', methods=['POST'])
def update_profile():
    bio = request.form.get('bio', '')
    if 'username' in session:
        conn = sqlite3.connect('chat.db')
        c = conn.cursor()
        c.execute("UPDATE users SET bio=? WHERE username=?", (bio, session['username']))
        conn.commit()
        conn.close()
    return redirect(url_for('home'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
