# -*- coding: utf-8 -*-
import os
import pandas as pd
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from fpdf import FPDF

app = Flask(__name__, 
            template_folder="../templates", 
            static_folder="../static")

# Configuración de seguridad y rutas temporales
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
UPLOAD_DIR = "/tmp"
PDF_PATH = os.path.join(UPLOAD_DIR, "factura_supermercado.pdf")

# ── RUTAS ───────────────────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def index():
    # Ahora solo cargamos la página. La lista de productos empezará vacía en el navegador.
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    """Procesa el Excel y devuelve el JSON al navegador (sin guardar nada)"""
    file = request.files.get("archivo")
    if not file or not file.filename.endswith(".xlsx"):
        return jsonify({"error": "Sube un archivo .xlsx válido."}), 400

    try:
        df = pd.read_excel(file, dtype=str)
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        col_nombre = next((c for c in df.columns if "producto" in c or "nombre" in c), None)
        col_precio = next((c for c in df.columns if "precio" in c), None)

        if not col_nombre or not col_precio:
            return jsonify({"error": "No se encontraron las columnas 'Producto' y 'Precio'."}), 400

        productos = []
        for _, row in df.iterrows():
            nombre = str(row[col_nombre]).strip()
            try:
                precio_ves = float(str(row[col_precio]).replace(",", ".").replace(" ", ""))
            except:
                precio_ves = 0.0
            
            if nombre and nombre.lower() != "nan":
                productos.append({"nombre": nombre, "precio_ves": precio_ves})

        return jsonify(productos)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/descargar-pdf", methods=["POST"])
def descargar_pdf():
    """Recibe la lista del navegador y genera el PDF al vuelo"""
    data = request.get_json()
    productos = data.get("productos", [])
    tasa = float(data.get("tasa", 1))

    if not productos:
        return jsonify({"error": "No hay productos para generar el PDF"}), 400

    _generar_pdf_logic(productos, tasa)
    return send_file(PDF_PATH, as_attachment=True, download_name="factura_supermercado.pdf")

# ── LÓGICA DEL PDF (Diseño Original) ────────────────────────────────────────

def _generar_pdf_logic(productos, tasa):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado oscuro
    pdf.set_fill_color(30, 30, 30)
    pdf.rect(0, 0, 210, 40, style="F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_xy(10, 10)
    pdf.cell(0, 10, "CALCULADORA DE SUPERMERCADO", align="L")
    
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(10, 25)
    pdf.cell(0, 6, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", align="L")
    pdf.cell(0, 6, f"Tasa: {tasa:,.2f} VES/USD", align="R")
    pdf.ln(20)

    # Tabla
    pdf.set_text_color(0, 0, 0)
    col_w = [100, 45, 45]
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    
    headers = ["Producto", "Precio VES", "Precio USD"]
    for h, w in zip(headers, col_w):
        pdf.cell(w, 10, h, border=1, align="C", fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 9)
    total_ves = 0
    for p in productos:
        precio_ves = p['precio_ves']
        precio_usd = precio_ves / tasa if tasa > 0 else 0
        total_ves += precio_ves
        
        pdf.cell(col_w[0], 8, p['nombre'][:50], border=1)
        pdf.cell(col_w[1], 8, f"{precio_ves:,.2f}", border=1, align="R")
        pdf.cell(col_w[2], 8, f"$ {precio_usd:,.2f}", border=1, align="R")
        pdf.ln()

    # Totales
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_fill_color(30, 30, 30)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(col_w[0], 10, "TOTAL", border=1, align="C", fill=True)
    pdf.cell(col_w[1], 10, f"{total_ves:,.2f} Bs", border=1, align="R", fill=True)
    pdf.cell(col_w[2], 10, f"$ {total_ves/tasa:,.2f}", border=1, align="R", fill=True)

    pdf.output(PDF_PATH)

if __name__ == "__main__":
    app.run(debug=True)