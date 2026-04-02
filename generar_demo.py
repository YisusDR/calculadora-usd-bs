"""
Genera un productos_demo.xlsx de ejemplo para probar la aplicación.
Ejecutar: python generar_demo.py
"""
import pandas as pd
import os

data = {
    "Producto": [
        "Arroz Diana 1kg",
        "Aceite Mazeite 900ml",
        "Leche Parmalat 1L",
        "Pan de sándwich Bimbo",
        "Harina P.A.N. 1kg",
        "Azúcar Morena 1kg",
        "Pasta Capri 500g",
        "Atún Margarita lata 170g",
        "Mayonesa Mavesa 445g",
        "Café Fama de América 200g",
        "Jabón de baño Dove x3",
        "Papel higiénico x4",
        "Detergente Ariel 500g",
        "Desodorante Rexona",
        "Jugo Hit 1L",
    ],
    "Precio": [
        18_500, 42_000, 28_000, 35_000, 21_000,
        19_000, 14_500, 38_000, 55_000, 47_000,
        62_000, 44_000, 58_000, 71_000, 26_000,
    ]
}

df = pd.DataFrame(data)
out = os.path.join(os.path.dirname(__file__), "productos_demo.xlsx")
df.to_excel(out, index=False)
print(f"Archivo generado: {out}")
