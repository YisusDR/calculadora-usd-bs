# -*- coding: utf-8 -*-
"""
Calculadora de Supermercado VES/USD
Backend Flask con soporte para PDF y edición de precios.
"""

import os
import json
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
import pandas as pd
from datetime import datetime

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False

# ── Configuración base ──────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "data")
JSON_PATH  = os.path.join(UPLOAD_DIR, "productos.json")
PDF_PATH   = os.path.join(UPLOAD_DIR, "factura.pdf")
FONT_DIR   = os.path.join(BASE_DIR, "static", "fonts")

os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB


# ── Helpers ─────────────────────────────────────────────────────────────────
def load_productos() -> list[dict]:
    if not os.path.exists(JSON_PATH):
        return []
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_productos(productos: list[dict]) -> None:
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(productos, f, ensure_ascii=False, indent=2)


# ── Rutas principales ────────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def index():
    productos = load_productos()
    return render_template("index.html", productos=productos)


@app.route("/upload", methods=["POST"])
def upload():
    """Recibe el .xlsx, lo procesa con Pandas y guarda productos.json."""
    file = request.files.get("archivo")
    if not file or not file.filename.endswith(".xlsx"):
        return jsonify({"error": "Sube un archivo .xlsx válido."}), 400

    try:
        df = pd.read_excel(file, dtype=str)
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        # Acepta columnas flexibles: 'producto'/'nombre', 'precio'/'precio_ves'
        col_nombre = next((c for c in df.columns if "producto" in c or "nombre" in c), None)
        col_precio = next((c for c in df.columns if "precio" in c), None)

        if not col_nombre or not col_precio:
            return jsonify({
                "error": f"Columnas requeridas no encontradas. Encontradas: {list(df.columns)}"
            }), 400

        productos = []
        for _, row in df.iterrows():
            nombre = str(row[col_nombre]).strip()
            try:
                precio_ves = float(str(row[col_precio]).replace(",", ".").replace(" ", ""))
            except ValueError:
                precio_ves = 0.0
            if nombre and nombre.lower() != "nan":
                productos.append({"nombre": nombre, "precio_ves": precio_ves})

        save_productos(productos)
        return jsonify({"ok": True, "total": len(productos)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/productos", methods=["GET"])
def api_productos():
    """Devuelve la lista de productos como JSON."""
    return jsonify(load_productos())


@app.route("/api/productos/<int:idx>", methods=["PATCH"])
def api_update_precio(idx: int):
    """Actualiza el precio VES de un producto por su índice."""
    productos = load_productos()
    if idx < 0 or idx >= len(productos):
        return jsonify({"error": "Índice fuera de rango"}), 404

    data = request.get_json(force=True)
    try:
        nuevo_precio = float(data["precio_ves"])
    except (KeyError, ValueError, TypeError):
        return jsonify({"error": "precio_ves inválido"}), 400

    productos[idx]["precio_ves"] = nuevo_precio
    save_productos(productos)
    return jsonify({"ok": True, "producto": productos[idx]})


@app.route("/api/productos/<int:idx>", methods=["DELETE"])
def api_delete_producto(idx: int):
    """Elimina un producto por su índice."""
    productos = load_productos()
    if idx < 0 or idx >= len(productos):
        return jsonify({"error": "Índice fuera de rango"}), 404
    eliminado = productos.pop(idx)
    save_productos(productos)
    return jsonify({"ok": True, "eliminado": eliminado})


# ── Generación de PDF ─────────────────────────────────────────────────────────
@app.route("/descargar-pdf")
def descargar_pdf():
    """Genera y descarga la factura en PDF."""
    if not FPDF_AVAILABLE:
        return (
            "fpdf2 no está instalado. Ejecuta: pip install fpdf2",
            500,
        )
    try:
        tasa = float(request.args.get("tasa", 1))
    except ValueError:
        tasa = 1.0

    productos = load_productos()
    if not productos:
        return "No hay productos cargados.", 400

    _generar_pdf(productos, tasa)
    return send_file(PDF_PATH, as_attachment=True, download_name="factura_supermercado.pdf")


def _generar_pdf(productos: list[dict], tasa: float) -> None:
    """Construye el PDF con fpdf2 (soporte UTF-8 nativo)."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # ── Encabezado ──
    pdf.set_fill_color(30, 30, 30)
    pdf.rect(0, 0, 210, 38, style="F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_xy(10, 8)
    pdf.cell(0, 10, "CALCULADORA DE SUPERMERCADO", align="L")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(10, 22)
    pdf.cell(0, 6, f"Fecha: {datetime.now().strftime('%d/%m/%Y  %H:%M')}", align="L")
    pdf.set_xy(10, 28)
    pdf.cell(0, 6, f"Tasa de cambio: {tasa:,.2f} VES / USD", align="L")

    pdf.set_text_color(0, 0, 0)
    pdf.set_xy(10, 46)

    # ── Cabecera de tabla ──
    col_w = [90, 42, 42]
    headers = ["Producto", "Precio VES", "Precio USD"]
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Helvetica", "B", 10)
    for header, w in zip(headers, col_w):
        pdf.cell(w, 8, header, border=1, align="C", fill=True)
    pdf.ln()

    # ── Filas ──
    pdf.set_font("Helvetica", "", 9)
    total_ves = 0.0
    total_usd = 0.0
    fill = False
    for p in productos:
        precio_ves = p.get("precio_ves", 0)
        precio_usd = precio_ves / tasa if tasa else 0
        total_ves += precio_ves
        total_usd += precio_usd
        fill_color = (252, 252, 252) if fill else (255, 255, 255)
        pdf.set_fill_color(*fill_color)
        # Truncar nombre si es muy largo
        nombre = p.get("nombre", "")[:48]
        pdf.cell(col_w[0], 7, nombre, border=1, fill=True)
        pdf.cell(col_w[1], 7, f"{precio_ves:,.2f}", border=1, align="R", fill=True)
        pdf.cell(col_w[2], 7, f"$ {precio_usd:,.2f}", border=1, align="R", fill=True)
        pdf.ln()
        fill = not fill

    # ── Totales ──
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(30, 30, 30)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(col_w[0], 9, "TOTAL", border=1, align="C", fill=True)
    pdf.cell(col_w[1], 9, f"{total_ves:,.2f}", border=1, align="R", fill=True)
    pdf.cell(col_w[2], 9, f"$ {total_usd:,.4f}", border=1, align="R", fill=True)
    pdf.ln(14)

    # ── Pie de página ──
    pdf.set_text_color(160, 160, 160)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 6, "Generado con Calculadora Supermercado VES/USD", align="C")

    pdf.output(PDF_PATH)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=5000)
