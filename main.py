from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'janseva_chat_secret_key_2026'

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, sender TEXT, content TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# --- HTML / CSS / JS UI ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Janseva Chat App</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { background-color: #0f172a; color: #f8fafc; height: 100vh; display: flex; justify-content: center; align-items: center; }
        .container { width: 100%; max-width: 420px; height: 100vh; max-height: 680px; background: #1e293b; display: flex; flex-direction: column; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
        .header { background: #0284c7; padding: 15px; text-align: center; font-size: 1.1rem; font-weight: bold; display: flex; justify-content: space-between; align-items: center; }
        .header a { color: #fff; text-decoration: none; font-size: 0.85rem; background: #ef4444; padding: 5px 12px; border-radius: 6px; }
        .auth-box { padding: 30px; display: flex; flex-direction: column; gap: 15px; }
        .auth-box h2 { text-align: center; color: #38bdf8; margin-bottom: 10px; }
        input { width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #334155; background: #0f172a; color: #fff; outline: none; margin-bottom: 10px; }
        button { width: 100%; padding: 12px; border-radius: 8px; border: none; background: #0284c7; color: white; font-weight: bold; cursor: pointer; font-size: 1rem; }
        button:hover { background: #0369a1; }
        .toggle-btn { text-align: center; color: #94a3b8; font-size: 0.9rem; cursor: pointer; margin-top: 10px; }
        .toggle-btn span { color: #38bdf8; text-decoration: underline; }
        .chat-box { flex: 1; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
        .msg { max-width: 80%; padding: 10px 14px; border-radius: 12px; font-size: 0.95rem; word-wrap: break-word; }
        .msg.sent { align-self: flex-end; background: #0284c7; color: white; border-bottom-right-radius: 2px; }
        .msg.received { align-self: flex-start; background: #334155; color: white; border-bottom-left-radius: 2px; }
        .sender-name { font-size: 0.75rem; color: #94a3b8; margin-bottom: 3px; display: block; }
        .input-area { padding: 12px; background: #0f172a; display: flex; gap: 10px; }
        .input-area input { flex: 1; margin-bottom: 0; }
        .input-area button { width: auto; padding: 0 20px; }
        .error { color: #ef4444; font-size: 0.85rem; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        {% if not session.username %}
        <!-- AUTH SECTION -->
        <div id="login-form" class="auth-box">
            <h2>Janseva Chat</h2>
            {% if error %}<p class="error">{{ error }}</p>{% endif %}
            <form action="/login" method="POST">
                <input type="text" name="username" placeholder="Username" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>
            <div class="toggle-btn" onclick="toggleAuth()">Naya Account Banayein? <span>Register</span></div>
        </div>

        <div id="signup-form" class="auth-box" style="display: none;">
            <h2>Register</h2>
            <form action="/signup" method="POST">
                <input type="text" name="username" placeholder="Choose Username" required>
                <input type="password" name="password" placeholder="Choose Password" required>
                <button type="submit">Sign Up</button>
            </form>
            <div class="toggle-btn" onclick="toggleAuth()">Pehle se account hai? <span>Login</span></div>
        </div>

        <script>
            function toggleAuth() {
                var l = document.getElementById('login-form');
                var s = document.getElementById('signup-form');
                if (l.style.display === 'none') {
                    l.style.display = 'block';
                    s.style.display = 'none';
                } else {
                    l.style.display = 'none';
                    s.style.display = 'block';
                }
            }
        </script>

        {% else %}
        <!-- CHAT SECTION -->
        <div class="header">
            <span>👤 {{ session.username }}</span>
            <a href="/logout">Logout</a>
        </div>
        
        <div class="chat-box" id="chatBox"></div>

        <div class="input-area">
            <input type="text" id="messageInput" placeholder="Message likhein..." onkeypress="handleKey(event)">
            <button onclick="sendMessage()">Send</button>
        </div>

        <script>
            const currentUser = "{{ session.username }}";

            function fetchMessages() {
                fetch('/get_messages')
                    .then(res => res.json())
                    .then(data => {
                        const chatBox = document.getElementById('chatBox');
                        chatBox.innerHTML = '';
                        data.forEach(msg => {
                            const isMe = msg.sender === currentUser;
                            const div = document.createElement('div');
                            div.className = 'msg ' + (isMe ? 'sent' : 'received');
                            div.innerHTML = `<span class="sender-name">${isMe ? 'You' : msg.sender}</span>${msg.content}`;
                            chatBox.appendChild(div);
                        });
                    });
            }

            function sendMessage() {
                const input = document.getElementById('messageInput');
                const content = input.value.trim();
                if (!content) return;

                fetch('/send_message', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: new URLSearchParams({'content': content})
                }).then(() => {
                    input.value = '';
                    fetchMessages();
                    setTimeout(() => {
                        const chatBox = document.getElementById('chatBox');
                        chatBox.scrollTop = chatBox.scrollHeight;
                    }, 200);
                });
            }

            function handleKey(e) {
                if (e.key === 'Enter') sendMessage();
            }

            setInterval(fetchMessages, 2000);
            fetchMessages();
        </script>
        {% endif %}
    </div>
</body>
</html>
"""

# --- ROUTES ---
@app.route('/')
def home():
    error = request.args.get('error')
    return render_template_string(HTML_TEMPLATE, error=error)

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
    except sqlite3.IntegrityError:
        conn.close()
        return redirect(url_for('home', error="Username pehle se liya gaya hai!"))
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
    else:
        return redirect(url_for('home', error="Galat Username ya Password!"))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/get_messages')
def get_messages():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("SELECT sender, content FROM messages ORDER BY id ASC")
    rows = c.fetchall()
    conn.close()
    
    messages = [{'sender': row[0], 'content': row[1]} for row in rows]
    return jsonify(messages)

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    content = request.form.get('content')
    if content:
        conn = sqlite3.connect('chat.db')
        c = conn.cursor()
        c.execute("INSERT INTO messages (sender, content) VALUES (?, ?)", (session['username'], content))
        conn.commit()
        conn.close()
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
 
