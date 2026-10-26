import os
import pandas as pd
# Leer archivo maestro
df = pd.read_csv("ais_presence_galapagos_2016_2025.csv")
# Convertir columna date a fecha
df["date"] = pd.to_datetime(df["date"])
# Extraer mes
df["mes"] = df["date"].dt.month
# Crear carpeta de salida
os.makedirs("patrones_mensuales_ais", exist_ok=True)
# Nombres de meses
meses = {
    1: "enero",
    2: "febrero",
    3: "marzo",
    4: "abril",
    5: "mayo",
    6: "junio",
    7: "julio",
    8: "agosto",
    9: "septiembre",
    10: "octubre",
    11: "noviembre",
    12: "diciembre"
}
for numero_mes, nombre_mes in meses.items():
    df_mes = df[df["mes"] == numero_mes]
    patron_mes = (
        df_mes
        .groupby(["lat", "lon"], as_index=False)
        .agg(
            horas_promedio=("hours", "mean"),
            horas_total=("hours", "sum"),
            registros=("hours", "count"),
            embarcaciones=("vessel_id", "nunique")
        )
        .sort_values("horas_promedio", ascending=False)
    )
    salida = f"patrones_mensuales_ais/ais_patron_{nombre_mes}_2016_2025.csv"
    patron_mes.to_csv(salida, index=False)
    print(f"{nombre_mes}: {len(patron_mes)} celdas guardadas")
    print(patron_mes.head(3))
    print("-" * 60)
print("\nListo. Se generaron los 12 patrones mensuales AIS.") 
