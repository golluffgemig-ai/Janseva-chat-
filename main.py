from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'janseva_mega_secret_key_99'

# Database initialization
def init_db():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT UNIQUE, 
                  password TEXT, 
                  bio TEXT DEFAULT 'Jan Seva Member', 
                  avatar TEXT DEFAULT 'https://via.placeholder.com/150')''')
                 
    # Followers table
    c.execute('''CREATE TABLE IF NOT EXISTS follows 
                 (follower TEXT, followed TEXT)''')
                 
    # Messages table (with reaction & group support)
    c.execute('''CREATE TABLE IF NOT EXISTS messages 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  sender TEXT, 
                  receiver TEXT DEFAULT 'public', 
                  content TEXT, 
                  reaction TEXT DEFAULT '', 
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
                 
    # Groups table
    c.execute('''CREATE TABLE IF NOT EXISTS groups 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, created_by TEXT)''')
                 
    conn.commit()
    conn.close()

init_db()

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="google-site-verification" content="3kNbyk_8NLgDGWLmoXRJWjb7gFWUfTwhIXTbHW-K" />
    <title>Jan Seva Free Chat & Social</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background: #121212; color: #fff; display: flex; flex-direction: column; height: 100vh; }
        
        /* Top Navigation */
        .nav-bar { background: #1f1f1f; padding: 12px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #333; }
        .nav-title { font-size: 18px; font-weight: bold; color: #00e676; }
        .nav-tabs { display: flex; gap: 15px; }
        .tab-btn { background: none; border: none; color: #aaa; font-size: 14px; cursor: pointer; padding: 5px; }
        .tab-btn.active { color: #00e676; border-bottom: 2px solid #00e676; font-weight: bold; }

        /* Main Container */
        .content-area { flex: 1; overflow-y: auto; padding: 10px; display: none; flex-direction: column; }
        .content-area.active { display: flex; }

        /* Chat Styles */
        #chat-box { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; padding-bottom: 10px; }
        .msg-card { background: #262626; padding: 8px 12px; border-radius: 12px; max-width: 80%; width: fit-content; position: relative; }
        .msg-card.me { align-self: flex-end; background: #005c4b; }
        .msg-user { font-size: 11px; color: #00e676; font-weight: bold; margin-bottom: 2px; }
        .msg-text { font-size: 14px; word-break: break-word; }
        .reactions { font-size: 12px; margin-top: 4px; display: flex; gap: 5px; }
        .react-btn { background: none; border: none; cursor: pointer; font-size: 12px; }

        .input-bar { background: #1f1f1f; padding: 10px; display: flex; gap: 8px; border-top: 1px solid #333; }
        .input-bar input { flex: 1; background: #2a2a2a; border: 1px solid #444; color: white; padding: 10px; border-radius: 20px; outline: none; }
        .input-bar button { background: #00e676; color: black; border: none; padding: 8px 18px; border-radius: 20px; font-weight: bold; cursor: pointer; }

        /* Search & User Cards */
        .user-card { background: #1f1f1f; padding: 12px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
        .follow-btn { background: #3797f0; color: white; border: none; padding: 6px 14px; border-radius: 6px; font-weight: bold; cursor: pointer; }

        /* Profile & Settings */
        .profile-header { text-align: center; padding: 20px 0; }
        .profile-img { width: 80px; height: 80px; border-radius: 50%; border: 2px solid #00e676; object-fit: cover; }
        .stats-bar { display: flex; justify-content: center; gap: 30px; margin: 15px 0; }
        .stat-item { text-align: center; }
        .stat-num { font-weight: bold; font-size: 16px; }
        .stat-label { color: #8e8e8e; font-size: 12px; }

        .setting-row { display: flex; justify-content: space-between; padding: 15px; background: #1f1f1f; margin-bottom: 8px; border-radius: 8px; }

        /* Auth Screen */
        .auth-container { padding: 30px 20px; text-align: center; max-width: 350px; margin: auto; }
        .auth-input { width: 100%; padding: 12px; margin: 8px 0; background: #2a2a2a; border: 1px solid #444; color: white; border-radius: 6px; }
        .auth-btn { width: 100%; padding: 12px; background: #00e676; color: black; border: none; border-radius: 6px; font-weight: bold; margin-top: 10px; cursor: pointer; }
    </style>
</head>
<body>

    {% if not session.get('user') %}
    <div class="auth-container">
        <h2>🚀 Jan Seva</h2>
        <p style="color: #8e8e8e; font-size: 13px; margin-bottom: 20px;">Social & Free Chat Network</p>
        <form method="POST" action="/login">
            <input type="text" name="username" class="auth-input" placeholder="Username" required>
            <input type="password" name="password" class="auth-input" placeholder="Password" required>
            <button type="submit" class="auth-btn">Login / Sign Up</button>
        </form>
    </div>
    {% else %}

    <!-- Top Navigation -->
    <div class="nav-bar">
        <div class="nav-title">Jan Seva</div>
        <div class="nav-tabs">
            <button class="tab-btn active" onclick="switchTab('chats')">Chats</button>
            <button class="tab-btn" onclick="switchTab('search')">Search</button>
            <button class="tab-btn" onclick="switchTab('profile')">Profile</button>
            <button class="tab-btn" onclick="switchTab('settings')">⚙️</button>
        </div>
    </div>

    <!-- TAB 1: Public & Group Chats -->
    <div id="chats-tab" class="content-area active">
        <div id="chat-box"></div>
        <div class="input-bar">
            <input type="text" id="msgInput" placeholder="Message likhein..." autocomplete="off">
            <button onclick="sendMessage()">Send</button>
        </div>
    </div>

    <!-- TAB 2: Search Users & Follow -->
    <div id="search-tab" class="content-area">
        <div class="input-bar" style="margin-bottom: 12px;">
            <input type="text" id="searchInput" placeholder="Search username...">
            <button onclick="searchUsers()">Search</button>
        </div>
        <div id="searchResults"></div>
    </div>

    <!-- TAB 3: Profile Screen -->
    <div id="profile-tab" class="content-area">
        <div class="profile-header">
            <img src="https://via.placeholder.com/150" class="profile-img" id="myAvatar">
            <h3 id="myUsername" style="margin-top: 10px;">{{ session['user'] }}</h3>
            <p id="myBio" style="color: #aaa; font-size: 13px;">Jan Seva Member</p>
        </div>
        <div class="stats-bar">
            <div class="stat-item"><div class="stat-num" id="followersCount">0</div><div class="stat-label">Followers</div></div>
            <div class="stat-item"><div class="stat-num" id="followingCount">0</div><div class="stat-label">Following</div></div>
        </div>
    </div>

    <!-- TAB 4: Settings -->
    <div id="settings-tab" class="content-area">
        <div class="setting-row">
            <span>🔕 Silent Mode (Notifications)</span>
            <input type="checkbox" id="silentToggle">
        </div>
        <div class="setting-row" style="color: #ff5252; cursor: pointer;" onclick="window.location.href='/logout'">
            <span>🚪 Logout</span>
        </div>
    </div>

    <script>
        const currentUser = "{{ session['user'] }}";

        function switchTab(tabName) {
            document.querySelectorAll('.content-area').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            
            document.getElementById(tabName + '-tab').classList.add('active');
            if(tabName === 'profile') loadProfile();
        }

        // Fetch & Load Messages
        function loadMessages() {
            fetch('/get_messages')
                .then(res => res.json())
                .then(data => {
                    const box = document.getElementById('chat-box');
                    box.innerHTML = '';
                    data.forEach(msg => {
                        const div = document.createElement('div');
                        div.className = 'msg-card ' + (msg.sender === currentUser ? 'me' : '');
                        div.innerHTML = `
                            <div class="msg-user">${msg.sender}</div>
                            <div class="msg-text">${msg.content}</div>
                            <div class="reactions">
                                <button class="react-btn" onclick="addReaction(${msg.id}, '❤️')">❤️ ${msg.reaction || ''}</button>
                                <button class="react-btn" onclick="addReaction(${msg.id}, '😂')">😂</button>
                            </div>
                        `;
                        box.appendChild(div);
                    });
                });
        }

        function sendMessage() {
            const input = document.getElementById('msgInput');
            if(!input.value) return;
            
            const formData = new FormData();
            formData.append('content', input.value);

            fetch('/send_message', { method: 'POST', body: formData })
                .then(() => {
                    input.value = '';
                    loadMessages();
                });
        }

        function addReaction(msgId, emoji) {
            const formData = new FormData();
            formData.append('msg_id', msgId);
            formData.append('emoji', emoji);
            fetch('/react', { method: 'POST', body: formData }).then(() => loadMessages());
        }

        // Search Users
        function searchUsers() {
            const q = document.getElementById('searchInput').value;
            fetch('/search_user?q=' + q)
                .then(res => res.json())
                .then(users => {
                    const resDiv = document.getElementById('searchResults');
                    resDiv.innerHTML = '';
                    users.forEach(u => {
                        resDiv.innerHTML += `
                            <div class="user-card">
                                <div><b>${u.username}</b></div>
                                <button class="follow-btn" onclick="followUser('${u.username}')">Follow</button>
                            </div>
                        `;
                    });
                });
        }

        function followUser(username) {
            const formData = new FormData();
            formData.append('target', username);
            fetch('/follow', { method: 'POST', body: formData })
                .then(() => alert('Followed ' + username));
        }

        function loadProfile() {
            fetch('/get_profile')
                .then(res => res.json())
                .then(data => {
                    document.getElementById('followersCount').innerText = data.followers;
                    document.getElementById('followingCount').innerText = data.following;
                });
        }

        setInterval(loadMessages, 2000);
        loadMessages();
    </script>
    {% endif %}

</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    conn.close()
    
    session['user'] = username
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

@app.route('/get_messages')
def get_messages():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("SELECT id, sender, content, reaction FROM messages ORDER BY id ASC")
    rows = c.fetchall()
    conn.close()
    return jsonify([{'id': r[0], 'sender': r[1], 'content': r[2], 'reaction': r[3]} for r in rows])

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user' in session:
        content = request.form.get('content')
        if content:
            conn = sqlite3.connect('chat.db')
            c = conn.cursor()
            c.execute("INSERT INTO messages (sender, content) VALUES (?, ?)", (session['user'], content))
            conn.commit()
            conn.close()
    return jsonify({'status': 'ok'})

@app.route('/react', methods=['POST'])
def react():
    msg_id = request.form.get('msg_id')
    emoji = request.form.get('emoji')
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("UPDATE messages SET reaction = ? WHERE id = ?", (emoji, msg_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/search_user')
def search_user():
    q = request.args.get('q', '')
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE username LIKE ? AND username != ?", ('%'+q+'%', session.get('user', '')))
    rows = c.fetchall()
    conn.close()
    return jsonify([{'username': r[0]} for r in rows])

@app.route('/follow', methods=['POST'])
def follow():
    if 'user' in session:
        target = request.form.get('target')
        conn = sqlite3.connect('chat.db')
        c = conn.cursor()
        c.execute("INSERT INTO follows (follower, followed) VALUES (?, ?)", (session['user'], target))
        conn.commit()
        conn.close()
    return jsonify({'status': 'ok'})

@app.route('/get_profile')
def get_profile():
    if 'user' in session:
        user = session['user']
        conn = sqlite3.connect('chat.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM follows WHERE followed = ?", (user,))
        followers = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM follows WHERE follower = ?", (user,))
        following = c.fetchone()[0]
        conn.close()
        return jsonify({'followers': followers, 'following': following})
    return jsonify({'followers': 0, 'following': 0})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

