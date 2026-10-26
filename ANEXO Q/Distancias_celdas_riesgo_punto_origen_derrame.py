from pathlib import Path
import numpy as np
import pandas as pd
import rasterio

BASE = Path(r"C:\Users\josej\Documents\tfm_galapagos")
CARPETA_RIESGO = BASE / "opendrift_resultados" / "cruce_vulnerabilidad_FINAL"
SALIDA = CARPETA_RIESGO / "RESUMEN_12_MESES" / "distancias_por_clase_riesgo_itabaca_12_meses.csv"
SALIDA.parent.mkdir(parents=True, exist_ok=True)

MESES = [
    "enero", "febrero", "marzo", "abril",
    "mayo", "junio", "julio", "agosto",
    "septiembre", "octubre", "noviembre", "diciembre"
]

LON_ORIGEN = -90.285050
LAT_ORIGEN = -0.487890

UMBRAL_BAJO = 0.0001364388
UMBRAL_MEDIO = 0.0026645004

def haversine_km(lon1, lat1, lon2, lat2):
    R = 6371.0088
    lon1 = np.radians(lon1)
    lat1 = np.radians(lat1)
    lon2 = np.radians(lon2)
    lat2 = np.radians(lat2)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0)**2
    c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
    return R * c

resultados = []

for mes in MESES:
    archivo = CARPETA_RIESGO / mes / f"03_riesgo_ecologico_{mes}_0a1.tif"

    print("\n" + "=" * 78)
    print(mes.upper())
    print("=" * 78)

    if not archivo.exists():
        print(f"NO SE ENCONTRÓ: {archivo}")
        continue

    with rasterio.open(archivo) as src:
        riesgo = src.read(1).astype("float64")
        nodata = src.nodata
        transform = src.transform
        crs = src.crs

    if crs is None or not crs.is_geographic:
        raise ValueError(f"{archivo.name}: se esperaba un raster geográfico EPSG:4326 y se encontró {crs}")

    valida = np.isfinite(riesgo)
    if nodata is not None:
        valida &= riesgo != nodata

    positiva = valida & (riesgo > 0)
    filas, columnas = np.where(positiva)

    if len(filas) == 0:
        print("No existen celdas con riesgo positivo.")
        continue

    xs, ys = rasterio.transform.xy(transform, filas, columnas, offset="center")
    lons = np.asarray(xs, dtype=float)
    lats = np.asarray(ys, dtype=float)
    valores = riesgo[filas, columnas]

    distancias = haversine_km(LON_ORIGEN, LAT_ORIGEN, lons, lats)

    clases = np.empty(valores.shape, dtype=object)
    clases[(valores > 0) & (valores <= UMBRAL_BAJO)] = "Bajo"
    clases[(valores > UMBRAL_BAJO) & (valores <= UMBRAL_MEDIO)] = "Medio"
    clases[valores > UMBRAL_MEDIO] = "Alto"

    for clase in ["Bajo", "Medio", "Alto"]:
        d = distancias[clases == clase]

        if d.size == 0:
            resultados.append({
                "mes": mes,
                "clase": clase,
                "celdas": 0,
                "distancia_min_km": np.nan,
                "distancia_mediana_km": np.nan,
                "distancia_media_km": np.nan,
                "distancia_max_km": np.nan,
            })
            print(f"{clase:>5}: 0 celdas")
            continue

        fila = {
            "mes": mes,
            "clase": clase,
            "celdas": int(d.size),
            "distancia_min_km": float(np.min(d)),
            "distancia_mediana_km": float(np.median(d)),
            "distancia_media_km": float(np.mean(d)),
            "distancia_max_km": float(np.max(d)),
        }
        resultados.append(fila)

        print(
            f"{clase:>5}: {d.size:4d} celdas | "
            f"mín={fila['distancia_min_km']:.2f} km | "
            f"mediana={fila['distancia_mediana_km']:.2f} km | "
            f"media={fila['distancia_media_km']:.2f} km | "
            f"máx={fila['distancia_max_km']:.2f} km"
        )

df = pd.DataFrame(resultados)

print("\n" + "=" * 78)
print("RESUMEN FINAL")
print("=" * 78)
print(df.to_string(index=False))

df.to_csv(SALIDA, index=False, encoding="utf-8-sig")

print("\nCSV creado:")
print(SALIDA)

tabla_max = df.pivot(index="mes", columns="clase", values="distancia_max_km")
tabla_max = tabla_max.reindex([m for m in MESES if m in tabla_max.index])

print("\nALCANCE MÁXIMO POR CLASE (km)")
print(tabla_max.round(2).to_string())
