# 🛒 SuperCalc VES/USD - Calculadora de Supermercado

Una aplicación web rápida, privada y sin estado (stateless) para procesar listas de compras en Excel, calcular conversiones de Bolívares (VES) a Dólares (USD) en tiempo real, y generar facturas en PDF.

Desplegada en **Vercel** como una arquitectura Serverless.

---

## ✨ Características Principales

* **Privacidad por Diseño (Stateless):** Los datos se procesan en la memoria del navegador (`localStorage` y arrays de JS). No se guarda información en bases de datos, permitiendo que múltiples usuarios usen la app al mismo tiempo de forma 100% independiente y privada.
* **Procesamiento de Excel:** Carga archivos `.xlsx` mediante Drag & Drop. El backend extrae automáticamente los productos y precios usando `pandas`.
* **Cálculos en Tiempo Real:** Edición de precios *inline* directamente en la tabla con actualización instantánea de totales y gráficas.
* **Visualización de Datos:** Gráfica de dona interactiva (Chart.js) para analizar la distribución de gastos.
* **Generación de PDF:** Creación dinámica de facturas en formato PDF lista para descargar (`fpdf2`).
* **Plantilla Descargable:** Opción integrada para descargar el formato base de Excel requerido.

---

## 🏗️ Arquitectura del Proyecto

El proyecto está diseñado para funcionar como **Serverless Functions** en Vercel:

```text
calculadora-usd-bs/
├── api/
│   └── index.py         # Backend (Flask Serverless: procesa Excel y PDF)
├── templates/
│   └── index.html       # Frontend (UI + Lógica de estado en Vanilla JS)
├── static/
│   └── plantilla.xlsx   # Archivo de ejemplo descargable
├── requirements.txt     # Dependencias de Python
└── vercel.json          # Reglas de enrutamiento para el despliegue
```
## Instalación

```bash
# 1. Crear entorno virtual
python -m venv venv

# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. (Opcional) Generar archivo de prueba
python generar_demo.py

# 4. Ejecutar la aplicación
python app.py
```

Luego abre: **http://localhost:5000**

## Uso

1. **Ingresa la tasa de cambio** del día en el panel izquierdo (ej: `36.50`).
2. **Sube tu archivo .xlsx** — necesita columnas `Producto` y `Precio`.
3. La tabla muestra los precios en VES y su equivalente en USD.
4. **Edita cualquier precio** haciendo clic sobre él en la tabla.
5. **Descarga la factura PDF** con el botón del panel lateral.

## Formato del Excel

| Producto          | Precio  |
|-------------------|---------|
| Arroz Diana 1kg   | 18500   |
| Aceite 900ml      | 42000   |

Las columnas se detectan automáticamente (acepta variantes como `nombre`, `precio_ves`, etc.)

## API interna

| Método   | Ruta                   | Descripción                      |
|----------|------------------------|----------------------------------|
| `POST`   | `/upload`              | Sube y procesa el .xlsx          |
| `GET`    | `/api/productos`       | Lista todos los productos        |
| `PATCH`  | `/api/productos/<idx>` | Actualiza `precio_ves` de un ítem |
| `DELETE` | `/api/productos/<idx>` | Elimina un ítem                  |
| `GET`    | `/descargar-pdf?tasa=` | Genera y descarga la factura PDF |
