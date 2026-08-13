from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'janseva_secret_key_123'

# Database setup
def init_db():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, content TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
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
    <title>Jan Seva Free Chat</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: sans-serif; }
        body { background: #f0eee6; display: flex; flex-direction: column; height: 100vh; }
        .header { background: #005f4e; color: white; padding: 10px; text-align: center; }
        .sub-bar { background: #004d3f; color: white; padding: 8px 12px; display: flex; justify-content: space-between; align-items: center; font-size: 14px; }
        .sub-bar a { color: #ffdd57; text-decoration: none; font-weight: bold; }
        #chat-box { flex: 1; overflow-y: auto; padding: 15px; display: flex; flex-direction: column; gap: 10px; }
        .msg { background: white; padding: 8px 12px; border-radius: 8px; max-width: 80%; box-shadow: 0 1px 2px rgba(0,0,0,0.1); word-wrap: break-word; }
        .msg.me { align-self: flex-end; background: #dcf8c6; }
        .msg-user { font-weight: bold; font-size: 12px; color: #005f4e; margin-bottom: 2px; }
        .input-area { background: #fff; padding: 10px; display: flex; flex-direction: column; gap: 8px; border-top: 1px solid #ccc; }
        .text-row { display: flex; gap: 8px; }
        .text-row input { flex: 1; padding: 10px; border: 1px solid #ccc; border-radius: 20px; font-size: 15px; outline: none; }
        .text-row button { background: #008a70; color: white; border: none; padding: 8px 16px; border-radius: 20px; font-weight: bold; cursor: pointer; }
        .btn-row { display: flex; gap: 8px; }
        .btn-row button { flex: 1; background: #34b7f1; color: white; text-align: center; padding: 8px; border-radius: 20px; font-size: 13px; font-weight: bold; border: none; cursor: pointer; }
        .btn-row .voice-btn { background: #e55151; }
        .login-box { padding: 20px; text-align: center; margin: auto; width: 90%; background: white; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
        .login-box input { width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #ccc; border-radius: 5px; }
        .login-box button { width: 100%; padding: 10px; background: #006652; color: white; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; }
    </style>
</head>
<body>

    <div class="header">
        <h2>🚀 Jan Seva Free Chat</h2>
        <p>Bina Recharge Chat & Share</p>
    </div>

    {% if not session.get('user') %}
    <div class="login-box">
        <h3>Login / Register</h3>
        <form method="POST" action="/login">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Enter Chat App</button>
        </form>
    </div>
    {% else %}
    <div class="sub-bar">
        <span>👤 Logged in as: <b>{{ session['user'] }}</b></span>
        <a href="/logout">Logout</a>
    </div>

    <div id="chat-box"></div>

    <div class="input-area">
        <form id="msgForm" class="text-row">
            <input type="text" id="msgInput" placeholder="Message likhein..." required autocomplete="off">
            <button type="submit">Send</button>
        </form>
        <div class="btn-row">
            <button type="button">📷 Photo Bhejein</button>
            <button type="button" class="voice-btn">🎙️ Voice Record</button>
        </div>
    </div>

    <script>
        const currentUser = "{{ session['user'] }}";

        function loadMessages() {
            fetch('/get_messages')
                .then(res => res.json())
                .then(data => {
                    const box = document.getElementById('chat-box');
                    box.innerHTML = '';
                    data.forEach(msg => {
                        const div = document.createElement('div');
                        div.className = 'msg ' + (msg.username === currentUser ? 'me' : '');
                        div.innerHTML = `<div class="msg-user">${msg.username}</div><div>${msg.content}</div>`;
                        box.appendChild(div);
                    });
                }).catch(err => console.log(err));
        }

        document.getElementById('msgForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const input = document.getElementById('msgInput');
            const text = input.value;
            if(!text) return;
            
            const formData = new FormData();
            formData.append('content', text);

            fetch('/send_message', {
                method: 'POST',
                body: formData
            }).then(() => {
                input.value = '';
                loadMessages();
            });
        });

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
    if username:
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
    c.execute("SELECT username, content FROM messages ORDER BY id ASC")
    rows = c.fetchall()
    conn.close()
    return jsonify([{'username': r[0], 'content': r[1]} for r in rows])

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user' in session:
        content = request.form.get('content')
        if content:
            conn = sqlite3.connect('chat.db')
            c = conn.cursor()
            c.execute("INSERT INTO messages (username, content) VALUES (?, ?)", (session['user'], content))
            conn.commit()
            conn.close()
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

