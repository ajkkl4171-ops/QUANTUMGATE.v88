import time
import threading
from flask import Flask
from flask_cors import CORS
import webbrowser
import os

# Configuración del servidor local "seguro"
app = Flask(__name__)
CORS(app)  # Permite que checker.html hable con este exe

print(">>> QUANTUM AUTH v2.1 INICIANDO...")
print(">>> NO CIERRES ESTA VENTANA PARA MANTENER EL ACCESO.")

@app.route('/heartbeat')
def heartbeat():
    # Esta es la señal que busca la página web
    return {"status": "secure_access_granted", "key": "quantum_v8_auth"}

def open_browser():
    # Opcional: Abre el checker automáticamente al iniciar el exe
    time.sleep(2)
    webbrowser.open("http://127.0.0.1:5000/checker.html")

if __name__ == '__main__':
    # Ejecutar en un hilo separado para no bloquear
    threading.Thread(target=open_browser).start()
    
    # Puerto 1337 (Puerto "Elite" para la autenticación)
    try:
        app.run(host='127.0.0.1', port=1337, debug=False)
    except:
        print("Error: El puerto de autenticación está ocupado.")
        input()