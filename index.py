import sqlite3
import os
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS

# Configuración para Vercel
app = Flask(__name__, template_folder='../templates', static_folder='../static')
CORS(app)

# --- DB EN MEMORIA TEMPORAL (Vercel no permite persistencia local) ---
# Usamos /tmp porque es el único lugar donde Vercel deja escribir archivos
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
    except Exception as e:
        print(f"DB Error: {e}")

# Inicializar cada vez (necesario en serverless)
init_db()

# --- RUTAS ---

@app.route('/')
def serve_index():
    # Servir login o index
    return render_template('index.html')

@app.route('/login.html')
def serve_login_page():
    return render_template('login.html')

@app.route('/checker.html')
def serve_checker():
    return render_template('checker.html')

# Ruta para descargar el EXE desde la carpeta static
@app.route('/download-auth')
def download_auth():
    try:
        return send_from_directory('../static', AUTH_FILE_NAME, as_attachment=True)
    except Exception as e:
        return f"Error: Archivo no encontrado. {e}", 404

# --- API ENDPOINTS ---

@app.route('/register', methods=['POST'])
def register_user():
    init_db() # Asegurar que la tabla existe (por si Vercel reinició)
    try:
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
            return jsonify({"status": "error", "message": "Usuario ya existe (o DB reiniciada)"}), 409
        finally:
            conn.close()
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/login', methods=['POST'])
def login_user():
    init_db()
    try:
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
            return jsonify({"status": "error", "message": "Credenciales inválidas"}), 401
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Esta línea es importante para compatibilidad local y Vercel
if __name__ == '__main__':
    app.run(debug=True)