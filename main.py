import os
import sqlite3
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify, send_from_directory

app = Flask(__name__)
app.secret_key = "janseva_secret_key"
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Database Setup
def init_db():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, content TEXT, type TEXT)''')
    conn.commit()
    conn.close()

init_db()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jan Seva Free Chat</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: sans-serif; }
        body { background-color: #e5ddd5; display: flex; justify-content: center; height: 100vh; }
        .app-container { width: 100%; max-width: 450px; background: #fff; display: flex; flex-direction: column; height: 100vh; border-radius: 10px; overflow: hidden; }
        .header { background: #006652; color: white; padding: 12px; text-align: center; position: relative; }
        .header h2 { font-size: 18px; margin-bottom: 2px; }
        .header p { font-size: 12px; opacity: 0.9; }
        .sub-bar { background: #004d3d; color: #fff; padding: 6px 12px; display: flex; justify-content: space-between; align-items: center; font-size: 13px; }
        .lang-select { background: #fff; color: #333; border: none; padding: 2px 6px; border-radius: 4px; font-size: 12px; }
        .chat-box { flex: 1; padding: 10px; overflow-y: auto; background: #efeae2; display: flex; flex-direction: column; gap: 8px; }
        .msg { max-width: 80%; padding: 8px 12px; border-radius: 8px; font-size: 14px; word-wrap: break-word; }
        .msg-self { background: #dcf8c6; align-self: flex-end; }
        .msg-other { background: #ffffff; align-self: flex-start; border: 1px solid #ddd; }
        .user-name { font-weight: bold; font-size: 11px; color: #006652; margin-bottom: 3px; }
        .input-area { padding: 10px; background: #f0f0f0; display: flex; flex-direction: column; gap: 8px; border-top: 1px solid #ccc; }
        .text-row { display: flex; gap: 5px; }
        .text-row input { flex: 1; padding: 10px; border: 1px solid #ccc; border-radius: 20px; font-size: 14px; outline: none; }
        .text-row button { background: #008a70; color: white; border: none; padding: 8px 16px; border-radius: 20px; font-weight: bold; cursor: pointer; }
        .btn-row { display: flex; gap: 8px; }
        .btn-row label, .btn-row button { flex: 1; background: #34b7f1; color: white; text-align: center; padding: 8px; border-radius: 20px; font-size: 12px; border: none; font-weight: bold; cursor: pointer; }
        .btn-row .voice-btn { background: #e55151; }
        .login-box { padding: 20px; text-align: center; margin-auto; width: 90%; }
        .login-box input { width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #ccc; border-radius: 8px; }
        .login-box button { width: 100%; padding: 10px; background: #006652; color: white; border: none; border-radius: 8px; font-weight: bold; margin-top: 10px; }
   
    
    <meta name="google-site-verification" content="3kNbyk_8NLgDGWLmoXRJWjb7gFWUfTWhIXTbHW-KcyA" />  </style>
</head>
<body>

<div class="app-container">
    <div class="header">
        <h2>🚀 Jan Seva Free Chat</h2>
        <p id="subtitle">Bina Recharge Chat & Share</p>
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
        <div>
            <select class="lang-select" onchange="changeLanguage(this.value)">
                <option value="hinglish">Hinglish</option>
                <option value="hindi">हिंदी</option>
                <option value="english">English</option>
            </select>
            <a href="/logout" style="color:#ffdddd; margin-left:8px; text-decoration:none;" id="logoutText">Logout</a>
        </div>
    </div>

    <div class="chat-box" id="chatBox"></div>

    <div class="input-area">
        <form id="msgForm" class="text-row">
            <input type="text" id="messageInput" placeholder="Message likhein..." required autocomplete="off">
            <button type="submit" id="sendBtn">Send</button>
        </form>
        <div class="btn-row">
            <label id="photoBtn">📷 Photo Bhejein
                <input type="file" id="photoInput" accept="image/*" style="display:none;" onchange="uploadPhoto()">
            </label>
            <button class="voice-btn" id="voiceBtn" onclick="toggleVoice()">🎙️ Voice Record</button>
        </div>
    </div>
    {% endif %}
</div>

<script>
let userIsScrolling = false;
const chatBox = document.getElementById('chatBox');

if (chatBox) {
    // Detect if user scrolls up manually
    chatBox.addEventListener('scroll', () => {
        const isAtBottom = chatBox.scrollHeight - chatBox.clientHeight <= chatBox.scrollTop + 60;
        userIsScrolling = !isAtBottom;
    });
}

function fetchMessages() {
    if (!chatBox) return;
    fetch('/get_messages')
        .then(res => res.json())
        .then(data => {
            let html = '';
            data.forEach(m => {
                let isSelf = m.user === "{{ session.get('user') }}";
                let cls = isSelf ? 'msg-self' : 'msg-other';
                html += `<div class="msg ${cls}">
                            <div class="user-name">${m.user}</div>`;
                if(m.type === 'text') {
                    html += `<div>${m.content}</div>`;
                } else if(m.type === 'image') {
                    html += `<img src="${m.content}" style="max-width:100%; border-radius:5px;">`;
                } else if(m.type === 'audio') {
                    html += `<audio controls src="${m.content}" style="width:100%;"></audio>`;
                }
                html += `</div>`;
            });
            chatBox.innerHTML = html;
            
            // Auto-scroll logic: scroll down ONLY if user hasn't scrolled up manually
            if (!userIsScrolling) {
                chatBox.scrollTop = chatBox.scrollHeight;
            }
        });
}

if (document.getElementById('msgForm')) {
    document.getElementById('msgForm').addEventListener('submit', function(e) {
        e.preventDefault();
        let input = document.getElementById('messageInput');
        let text = input.value;
        if (!text) return;
        fetch('/send', {
            method: 'POST',
            headers: {'Content-Type': 'application/x-www-form-encoding'},
            body: new URLSearchParams({'content': text, 'type': 'text'})
        }).then(() => {
            input.value = '';
            userIsScrolling = false; // Force scroll to bottom on new message send
            fetchMessages();
        });
    });

    setInterval(fetchMessages, 2000);
    fetchMessages();
}

function uploadPhoto() {
    let file = document.getElementById('photoInput').files[0];
    if (!file) return;
    let formData = new FormData();
    formData.append('file', file);
    fetch('/upload_file', { method: 'POST', body: formData })
    .then(() => { userIsScrolling = false; fetchMessages(); });
}

// Language Switcher
const langData = {
    hinglish: {
        subtitle: "Bina Recharge Chat & Share",
        placeholder: "Message likhein...",
        send: "Send",
        photo: "📷 Photo Bhejein",
        voice: "🎙️ Voice Record",
        logout: "Logout"
    },
    hindi: {
        subtitle: "बिना रिचार्ज चैट और शेयर करें",
        placeholder: "संदेश लिखें...",
        send: "भेजें",
        photo: "📷 फोटो भेजें",
        voice: "🎙️ आवाज़ रिकॉर्ड करें",
        logout: "लॉग आउट"
    },
    english: {
        subtitle: "Free Chat & Media Sharing",
        placeholder: "Type a message...",
        send: "Send",
        photo: "📷 Send Photo",
        voice: "🎙️ Voice Record",
        logout: "Logout"
    }
};

function changeLanguage(lang) {
    let t = langData[lang];
    document.getElementById('subtitle').innerText = t.subtitle;
    document.getElementById('messageInput').placeholder = t.placeholder;
    document.getElementById('sendBtn').innerText = t.send;
    document.getElementById('photoBtn').childNodes[0].nodeValue = t.photo + ' ';
    document.getElementById('voiceBtn').innerText = t.voice;
    document.getElementById('logoutText').innerText = t.logout;
}
</script>

</body>
</html>
"""

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
    c.execute("SELECT user, content, type FROM messages ORDER BY id ASC")
    rows = c.fetchall()
    conn.close()
    messages = [{'user': r[0], 'content': r[1], 'type': r[2]} for r in rows]
    return jsonify(messages)

@app.route('/send', methods=['POST'])
def send():
    user = session.get('user', 'Guest')
    content = request.form.get('content')
    mtype = request.form.get('type', 'text')
    if content:
        conn = sqlite3.connect('chat.db')
        c = conn.cursor()
        c.execute("INSERT INTO messages (user, content, type) VALUES (?, ?, ?)", (user, content, mtype))
        conn.commit()
        conn.close()
    return jsonify({'status': 'ok'})

@app.route('/upload_file', methods=['POST'])
def upload_file():
    user = session.get('user', 'Guest')
    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            file_url = f"/uploads/{file.filename}"
            
            mtype = 'image' if file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')) else 'audio'
            
            conn = sqlite3.connect('chat.db')
            c = conn.cursor()
            c.execute("INSERT INTO messages (user, content, type) VALUES (?, ?, ?)", (user, file_url, mtype))
            conn.commit()
            conn.close()
    return jsonify({'status': 'ok'})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
