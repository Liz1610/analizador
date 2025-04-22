from flask import Flask, render_template, request
import os
import sys
import re
from datetime import datetime

app = Flask(__name__)

# Ruta de logs locales para pruebas
LOGS = {
    "apache_access": "/var/log/apache2/access.log",
    "apache_error": "/var/log/apache2/error.log",
    "vsftpd": "/var/log/vsftpd.log"
}

# Clasifica las líneas de log por tipo de evento
def clasificar_linea(linea):
    if "error" in linea.lower():
        return ("Error", linea)
    elif "warn" in linea.lower():
        return ("Advertencia", linea)
    elif "fail" in linea.lower() or "denied" in linea.lower():
        return ("Fallo", linea)
    else:
        return ("Info", linea)

# Extrae la IP si existe
def extraer_ip(linea):
    ip_match = re.search(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", linea)
    return ip_match.group(0) if ip_match else "Desconocido"

# Extrae fecha si existe en formato común
def extraer_fecha(linea):
    fecha_match = re.search(r"\d{2}/\w{3}/\d{4}", linea)  # Ej: 12/Apr/2024
    return fecha_match.group(0) if fecha_match else ""

@app.route("/", methods=["GET", "POST"])
def index():
    log_data = []
    resumen = {"Error": 0, "Advertencia": 0, "Fallo": 0, "Info": 0}
    ip_counter = {}

    log_tipo = request.form.get("log_tipo")
    filtro = request.form.get("filtro", "").lower()
    filtro_ip = request.form.get("filtro_ip", "").strip()
    filtro_fecha = request.form.get("filtro_fecha", "").strip()

    if request.method == "POST" and log_tipo in LOGS:
        path = LOGS[log_tipo]
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for linea in f:
                    if filtro and filtro not in linea.lower():
                        continue
                    if filtro_ip and filtro_ip not in linea:
                        continue
                    if filtro_fecha and filtro_fecha not in linea:
                        continue

                    tipo, texto = clasificar_linea(linea)
                    resumen[tipo] += 1
                    ip = extraer_ip(linea)
                    ip_counter[ip] = ip_counter.get(ip, 0) + 1
                    log_data.append({"tipo": tipo, "texto": texto})
        else:
            log_data.append({"tipo": "Error", "texto": f"Archivo no encontrado: {path}"})

    top_ips = sorted(ip_counter.items(), key=lambda x: x[1], reverse=True)[:5]

    return render_template("index.html",
                           log_data=log_data,
                           log_tipo=log_tipo,
                           logs_disponibles=LOGS,
                           resumen=resumen,
                           top_ips=top_ips)

if __name__ == "__main__":
    try:
        import socket
        print(f"Servidor iniciado en: http://{socket.gethostbyname(socket.gethostname())}:5000")
        app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
    except Exception as e:
        print("Error al iniciar la aplicación Flask:", e)

