import os
import pandas as pd
carpeta = r"C:\Users\josej\Documents\tfm_galapagos\scripts\patrones_mensuales_ais"
salida = r"C:\Users\josej\Documents\tfm_galapagos\capas\hotspots_ais_zonas_ampliadas.csv"
meses = [
    "enero", "febrero", "marzo", "abril",
    "mayo", "junio", "julio", "agosto",
    "septiembre", "octubre", "noviembre", "diciembre"
]
zonas = {
    "Canal_Itabaca_Baltra": {
        "lat_min": -0.65,
        "lat_max": -0.30,
        "lon_min": -90.45,
        "lon_max": -90.15
    },
    "Puerto_Ayora_Santa_Cruz": {
        "lat_min": -0.95,
        "lat_max": -0.65,
        "lon_min": -90.55,
        "lon_max": -90.15
    },
    "Puerto_Baquerizo_San_Cristobal": {
        "lat_min": -1.05,
        "lat_max": -0.75,
        "lon_min": -89.75,
        "lon_max": -89.40
    },
    "Wolf_Darwin_Norte": {
        "lat_min": 1.10,
        "lat_max": 1.70,
        "lon_min": -92.10,
        "lon_max": -91.50
    },
    "Isabela_Norte": {
        "lat_min": 0.00,
        "lat_max": 0.55,
        "lon_min": -91.80,
        "lon_max": -91.00
    },
    "Isabela_Sur": {
        "lat_min": -1.45,
        "lat_max": -0.90,
        "lon_min": -91.60,
        "lon_max": -90.70
    },
    "Canal_Isabela_Fernandina": {
        "lat_min": -0.80,
        "lat_max": -0.05,
        "lon_min": -92.00,
        "lon_max": -91.25
    },
    "Isla_Pinta": {
        "lat_min": 0.30,
        "lat_max": 0.90,
        "lon_min": -91.10,
        "lon_max": -90.40
    }
}

resultados = []
for mes in meses:
    archivo = f"ais_patron_{mes}_2016_2025.csv"
    ruta = os.path.join(carpeta, archivo)
    df = pd.read_csv(ruta)
    print(f"\nProcesando {mes}...")
    for nombre_zona, z in zonas.items():
        df_zona = df[
            (df["lat"] >= z["lat_min"]) &
            (df["lat"] <= z["lat_max"]) &
            (df["lon"] >= z["lon_min"]) &
            (df["lon"] <= z["lon_max"])
        ]
        if df_zona.empty:
            print(f"{nombre_zona}: sin datos")
            continue
        fila = df_zona.sort_values("horas_promedio", ascending=False).iloc[0]
        resultados.append({
            "mes": mes,
            "zona": nombre_zona,
            "lat": fila["lat"],
            "lon": fila["lon"],
            "horas_promedio": fila["horas_promedio"],
            "horas_total": fila["horas_total"],
            "registros": fila["registros"],
            "embarcaciones": fila["embarcaciones"]
        })
        print(
            f"{nombre_zona}: lat={fila['lat']}, lon={fila['lon']}, "
            f"horas_promedio={fila['horas_promedio']:.2f}"
        )
pd.DataFrame(resultados).to_csv(salida, index=False, encoding="utf-8-sig")
print("\nArchivo generado:")
print(salida)
