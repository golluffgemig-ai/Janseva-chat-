from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'janseva_mega_secret_key_2026'

# Database Setup
def init_db():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    
    # Users Table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  password TEXT,
                  bio TEXT DEFAULT 'Jan Seva Member',
                  avatar TEXT DEFAULT '')''')
                  
    # Follows Table
    c.execute('''CREATE TABLE IF NOT EXISTS follows
                 (follower TEXT, followed TEXT)''')
                  
    # Messages Table
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  sender TEXT,
                  room TEXT DEFAULT 'public',
                  content TEXT,
                  msg_type TEXT DEFAULT 'text',
                  reaction TEXT DEFAULT '')''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return "Janseva Chat App is Live & Running!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


