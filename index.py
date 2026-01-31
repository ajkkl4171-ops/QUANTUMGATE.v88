import os
import sqlite3
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS

# --- CONFIGURACIÓN DE RUTAS ---
# Esto detecta la carpeta raíz del proyecto de forma más agresiva
current_dir = os.path.dirname(os.path.abspath(__file__)) # carpeta api
parent_dir = os.path.dirname(current_dir) # carpeta raíz

template_dir = os.path.join(parent_dir, 'templates')
static_dir = os.path.join(parent_dir, 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
CORS(app)

DB_NAME = '/tmp/quantum_users.db'
AUTH_FILE_NAME = "QuantumAUTH v2.1.exe"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users 
                     (contact TEXT PRIMARY KEY, password TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()
        conn.close()
    except:
        pass

# --- RUTAS ---

@app.route('/')
def serve_index():
    init_db()
    # Verificación extra: si no lo encuentra, nos dirá dónde lo está buscando
    if not os.path.exists(os.path.join(template_dir, 'index.html')):
        return f"Error: No encuentro index.html en: {template_dir}. Archivos vistos: {os.listdir(template_dir) if os.path.exists(template_dir) else 'Carpeta no existe'}", 404
    return render_template('index.html')

@app.route('/login.html')
def serve_login_page():
    return render_template('login.html')

@app.route('/checker.html')
def serve_checker():
    return render_template('checker.html')

@app.route('/download-auth')
def download_auth():
    return send_from_directory(static_dir, AUTH_FILE_NAME, as_attachment=True)

# --- API ---

@app.route('/register', methods=['POST'])
def register_user():
    init_db()
    data = request.json
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (contact, password) VALUES (?, ?)", (data.get('contact'), data.get('password')))
        conn.commit()
        return jsonify({"status": "success", "redirect": "/checker.html"})
    except:
        return jsonify({"status": "error", "message": "Error al registrar"}), 400
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login_user():
    init_db()
    data = request.json
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE contact=? AND password=?", (data.get('contact'), data.get('password')))
    user = c.fetchone()
    conn.close()
    if user:
        return jsonify({"status": "success", "redirect": "/checker.html"})
    return jsonify({"status": "error", "message": "Credenciales incorrectas"}), 401

if __name__ == '__main__':
    app.run(debug=True)

