# -*- coding: utf-8 -*-
import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, send_file
from supabase import create_client, Client


# ── CONFIGURACIÓN FLASK ──────────────────────────────────────────────────────
app = Flask(__name__, template_folder="../templates", static_folder="../static")

app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
# ── CONFIGURACIÓN DE SUPABASE ────────────────────────────────────────────────
# 1. Cargar las variables desde el archivo .env
load_dotenv()

# 2. Extraer los valores usando os.getenv
# Si no encuentra la variable, devuelve None por seguridad
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# 3. Inicializar el cliente (ahora es dinámico)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# Directorio para archivos temporales (como el PDF)
"""BASE_DIR   = os.path.dirname(os.path.abspath(__file__))"""
UPLOAD_DIR = "/tmp"
PDF_PATH   = os.path.join(UPLOAD_DIR, "factura.pdf")
os.makedirs(UPLOAD_DIR, exist_ok=True)

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False

# ── HELPERS (Ahora hablan con Supabase) ──────────────────────────────────────
def get_all_productos():
    """Trae todos los productos de la nube, ordenados por ID."""
    response = supabase.table("productos").select("*").order("id").execute()
    return response.data

# ── RUTAS PRINCIPALES ────────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def index():
    # Al cargar la página, traemos los datos de la nube
    productos = get_all_productos()
    return render_template("index.html", productos=productos)

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("archivo")
    if not file or not file.filename.endswith(".xlsx"):
        return jsonify({"error": "Sube un archivo .xlsx válido."}), 400

    try:
        df = pd.read_excel(file, dtype=str)
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        col_nombre = next((c for c in df.columns if "producto" in c or "nombre" in c), None)
        col_precio = next((c for c in df.columns if "precio" in c), None)

        if not col_nombre or not col_precio:
            return jsonify({"error": "Columnas 'Producto' y 'Precio' no encontradas."}), 400

        # Preparamos la lista para insertar en Supabase
        lista_productos = []
        for _, row in df.iterrows():
            nombre = str(row[col_nombre]).strip()
            try:
                precio_ves = float(str(row[col_precio]).replace(",", ".").replace(" ", ""))
            except ValueError:
                precio_ves = 0.0
            
            if nombre and nombre.lower() != "nan":
                lista_productos.append({"nombre": nombre, "precio_ves": precio_ves})

        # 1. Limpiamos la tabla vieja (para que sea una carga limpia como antes)
        supabase.table("productos").delete().neq("id", 0).execute()
        
        # 2. Insertamos la nueva lista en la nube
        if lista_productos:
            supabase.table("productos").insert(lista_productos).execute()

        return jsonify({"ok": True, "total": len(lista_productos)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/productos", methods=["GET"])
def api_productos():
    return jsonify(get_all_productos())

@app.route("/api/productos/<int:idx>", methods=["PATCH"])
def api_update_precio(idx: int):
    """Actualiza el precio usando el ID de la fila en Supabase."""
    data = request.get_json(force=True)
    productos = get_all_productos()
    
    if idx < 0 or idx >= len(productos):
        return jsonify({"error": "Índice inválido"}), 404

    # Obtenemos el ID real de la base de datos para ese índice
    db_id = productos[idx]['id']
    nuevo_precio = float(data.get("precio_ves", 0))

    # Actualizamos en la nube
    supabase.table("productos").update({"precio_ves": nuevo_precio}).eq("id", db_id).execute()
    
    return jsonify({"ok": True})

@app.route("/api/productos/<int:idx>", methods=["DELETE"])
def api_delete_producto(idx: int):
    """Elimina un producto de la nube."""
    productos = get_all_productos()
    if idx < 0 or idx >= len(productos):
        return jsonify({"error": "Índice inválido"}), 404

    db_id = productos[idx]['id']
    supabase.table("productos").delete().eq("id", db_id).execute()
    
    return jsonify({"ok": True})

# ── PDF (Misma lógica, pero con datos de Supabase) ───────────────────────────
@app.route("/descargar-pdf")
def descargar_pdf():
    if not FPDF_AVAILABLE:
        return "Instala fpdf2 para generar PDFs.", 500
    
    tasa = float(request.args.get("tasa", 1))
    productos = get_all_productos()
    
    if not productos:
        return "No hay productos.", 400

    _generar_pdf(productos, tasa)
    return send_file(PDF_PATH, as_attachment=True, download_name="factura.pdf")

def _generar_pdf(productos, tasa):
    pdf = FPDF()
    pdf.add_page()
    # ... (Tu lógica de PDF se mantiene igual, ya que 'productos' es la misma lista de dicts)
    # Solo asegúrate de llamar a pdf.output(PDF_PATH) al final
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "FACTURA DE SUPERMERCADO", ln=True, align='C')
    pdf.ln(10)
    
    # Ejemplo rápido de tabla en PDF
    for p in productos:
        linea = f"{p['nombre']} - {p['precio_ves']:,.2f} VES (${p['precio_ves']/tasa:,.2f})"
        pdf.cell(0, 10, linea, ln=True)
    
    pdf.output(PDF_PATH)

if __name__ == "__main__":
    app.run(debug=True, port=5000)