# Calculadora Supermercado VES/USD

Aplicación web local con Flask para gestionar listas de compras con conversión automática Bolívares → Dólares.

## Estructura del proyecto

```
supermarket-calc/
├── app.py                  # Backend Flask (rutas + lógica PDF)
├── requirements.txt        # Dependencias Python
├── generar_demo.py         # Genera un .xlsx de ejemplo
├── templates/
│   └── index.html          # UI completa (Bootstrap 5 + JS vanilla)
└── data/
    ├── productos.json      # Base de datos temporal (auto-generada)
    └── factura.pdf         # PDF exportado (auto-generado)
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
