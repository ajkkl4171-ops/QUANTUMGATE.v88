import sqlite3
import os
import sys
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS

# --- MODO DIAGNÓSTICO: CALCULANDO RUTAS ---
try:
    # Intenta encontrar la ruta base del proyecto
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_dir = os.path.join(base_dir, 'templates')
    static_dir = os.path.join(base_dir, 'static')
    
    # Comprobación de seguridad: ¿Existen las carpetas?
    templates_exist = os.path.exists(template_dir)
    static_exist = os.path.exists(static_dir)

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    CORS(app)
except Exception as e:
    # Si falla al iniciar, esto se imprimirá en los logs de Vercel
    print(f"CRITICAL STARTUP ERROR: {e}")
    raise e

# DB en memoria temporal
DB_NAME = '/tmp/quantum_users.db' 
AUTH_FILE_NAME = "QuantumAUTH v2.1.exe"

# --- MANEJADOR DE ERRORES VISUAL ---
# Esto hará que el error salga en tu pantalla en vez de "Internal Server Error"
@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({
        "status": "CRASHED",
        "error_message": str(e),
        "diagnosis": {
            "current_working_dir": os.getcwd(),
            "base_dir_calculated": base_dir,
            "templates_path": template_dir,
            "templates_found": templates_exist,
            "static_path": static_dir,
            "files_in_templates": os.listdir(template_dir) if templates_exist else "FOLDER NOT FOUND",
            "files_in_static": os.listdir(static_dir) if static_exist else "FOLDER NOT FOUND"
        }
    }), 500

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (contact TEXT PRIMARY KEY, password TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

# --- RUTAS ---

@app.route('/')
def serve_index():
    # Intenta inicializar la DB aquí para atrapar errores
    init_db()
    # Intenta renderizar
    if not os.path.exists(os.path.join(template_dir, 'index.html')):
        return "Error: index.html no está en la carpeta templates", 404
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
    contact = data.get('contact')
    password = data.get('password')
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (contact, password) VALUES (?, ?)", (contact, password))
        conn.commit()
        return jsonify({"status": "success", "redirect": "/checker.html"})
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": "User exists"}), 409
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login_user():
    init_db()
    data = request.json
    contact = data.get('contact')
    password = data.get('password')
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE contact=? AND password=?", (contact, password))
    user = c.fetchone()
    conn.close()
    if user:
        return jsonify({"status": "success", "redirect": "/checker.html"})
    else:
        return jsonify({"status": "error", "message": "Invalid credentials"}), 401

# Para entorno local
if __name__ == '__main__':
    app.run(debug=True)
