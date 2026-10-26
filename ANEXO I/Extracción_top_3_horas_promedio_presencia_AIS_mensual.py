import os
import pandas as pd
carpeta = r"C:\Users\josej\Documents\tfm_galapagos\scripts\patrones_mensuales_ais"
meses = [
    "enero", "febrero", "marzo", "abril",
    "mayo", "junio", "julio", "agosto",
    "septiembre", "octubre", "noviembre", "diciembre"
]
resultados = []
for mes in meses:
    archivo = f"ais_patron_{mes}_2016_2025.csv"
    ruta = os.path.join(carpeta, archivo)
    df = pd.read_csv(ruta)
    top3 = df.sort_values("horas_promedio", ascending=False).head(3)
    for ranking, fila in enumerate(top3.itertuples(index=False), start=1):
        resultados.append({
            "mes": mes,
            "ranking": ranking,
            "lat": fila.lat,
            "lon": fila.lon,
            "horas_promedio": fila.horas_promedio,
            "horas_total": fila.horas_total,
            "registros": fila.registros,
            "embarcaciones": fila.embarcaciones
        })
salida = r"C:\Users\josej\Documents\tfm_galapagos\capas\top3_horas_promedio_csv_ais.csv"
pd.DataFrame(resultados).to_csv(salida, index=False)
print("Archivo generado:")
print(salida)
