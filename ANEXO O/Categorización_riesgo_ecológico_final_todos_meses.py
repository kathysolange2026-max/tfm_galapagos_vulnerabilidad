# preparar_resultados_finales_12_meses.py
# Resume los resultados mensuales de Itabaca y crea
# 12 rasters clasificados comparables entre sí.
# NO vuelve a simular OpenDrift.
# Salidas:
# 1) resumen_resultados_mensuales_FINAL.csv
# 2) umbrales_globales_riesgo.txt
# 3) 12 rasters:
#    04_riesgo_clases_globales_<mes>.tif
# Clasificación común para los 12 meses:
#   0 = sin riesgo (R = 0)
#   1 = bajo     (0 < R <= Q1 global)
#   2 = medio    (Q1 < R <= Q3 global)
#   3 = alto     (R > Q3 global)
# Los cuartiles se calculan juntando TODOS los valores
# positivos de riesgo de los 12 meses, para que las clases
# signifiquen lo mismo en todos los mapas.
from pathlib import Path
import csv
import numpy as np
import xarray as xr
import rasterio
BASE = Path(r"C:\Users\josej\Documents\tfm_galapagos")
CARPETA_NC = BASE / "opendrift_resultados" / "itabaca_12_meses_FINAL"
CARPETA_CRUCE = BASE / "opendrift_resultados" / "cruce_vulnerabilidad_FINAL"
CARPETA_SALIDA = CARPETA_CRUCE / "RESULTADOS_FINALES_12_MESES"
CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)
LON0 = -90.285050
LAT0 = -0.487890
MESES = [
    (1, "enero"), (2, "febrero"), (3, "marzo"), (4, "abril"),
    (5, "mayo"), (6, "junio"), (7, "julio"), (8, "agosto"),
    (9, "septiembre"), (10, "octubre"), (11, "noviembre"), (12, "diciembre"),
]
def haversine_km(lon1, lat1, lon2, lat2):
    R = 6371.0088
    lon1 = np.radians(lon1)
    lat1 = np.radians(lat1)
    lon2 = np.radians(lon2)
    lat2 = np.radians(lat2)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c
def ultimo_estado_valido(status):
    salida = np.full(status.shape[0], np.nan, dtype=float)
    for i in range(status.shape[0]):
        idx = np.where(np.isfinite(status[i, :]))[0]
        if len(idx):
            salida[i] = status[i, idx[-1]]
    return salida
def primer_varamiento_h(status, tiempos):
    t0 = np.datetime64(tiempos[0])
    valores = []
    for i in range(status.shape[0]):
        idx = np.where(status[i, :] == 1)[0]
        if len(idx):
            ti = np.datetime64(tiempos[idx[0]])
            horas = float((ti - t0) / np.timedelta64(1, "h"))
            valores.append(horas)
    if not valores:
        return np.nan
    return float(np.min(valores))
def buscar_nc(mes):
    archivos = list(CARPETA_NC.glob(f"itabaca_{mes}_FINAL_*.nc"))
    if not archivos:
        return None
    return max(archivos, key=lambda p: p.stat().st_mtime)
# PRIMERA PASADA: reunir todos los valores positivos de riesgo
todos_riesgos_positivos = []
datos_raster = {}
print("\n" + "=" * 80)
print("LEYENDO LOS 12 MAPAS DE RIESGO")
print("=" * 80)
for numero, mes in MESES:
    ruta = CARPETA_CRUCE / mes / f"03_riesgo_ecologico_{mes}_0a1.tif"
    if not ruta.exists():
        raise FileNotFoundError(f"No existe:\n{ruta}")
    with rasterio.open(ruta) as src:
        arr = src.read(1).astype(np.float32)
        perfil = src.profile.copy()
        nodata = src.nodata
    valida = np.isfinite(arr)
    if nodata is not None:
        valida &= (arr != nodata)
    positivos = arr[valida & (arr > 0)]
    datos_raster[mes] = {
        "arr": arr,
        "perfil": perfil,
        "nodata": nodata,
        "valida": valida,
        "positivos": positivos,
    }
    if len(positivos):
        todos_riesgos_positivos.append(positivos)
    print(f"{mes.upper():12s}: {len(positivos)} celdas con R > 0")
if not todos_riesgos_positivos:
    raise RuntimeError("No se encontraron valores positivos de riesgo.")
pool = np.concatenate(todos_riesgos_positivos)
Q1_GLOBAL = float(np.percentile(pool, 25))
Q2_GLOBAL = float(np.percentile(pool, 50))
Q3_GLOBAL = float(np.percentile(pool, 75))
MAX_GLOBAL = float(np.max(pool))
print("\n" + "=" * 80)
print("UMBRALES GLOBALES")
print("=" * 80)
print(f"Q1 (25%): {Q1_GLOBAL:.10f}")
print(f"Mediana:  {Q2_GLOBAL:.10f}")
print(f"Q3 (75%): {Q3_GLOBAL:.10f}")
print(f"Máximo:   {MAX_GLOBAL:.10f}")
print("\nClases propuestas:")
print(f"BAJO  : 0 < R <= {Q1_GLOBAL:.10f}")
print(f"MEDIO : {Q1_GLOBAL:.10f} < R <= {Q3_GLOBAL:.10f}")
print(f"ALTO  : R > {Q3_GLOBAL:.10f}")
# SEGUNDA PASADA: resumen mensual + raster clasificado
resumen = []
for numero, mes in MESES:
    print("\n" + "=" * 80)
    print(mes.upper())
    print("=" * 80)
    info = datos_raster[mes]
    arr = info["arr"]
    valida = info["valida"]
    positivos = info["positivos"]
    perfil = info["perfil"]
    if len(positivos):
        riesgo_min_positivo = float(np.min(positivos))
        riesgo_q1 = float(np.percentile(positivos, 25))
        riesgo_mediana = float(np.percentile(positivos, 50))
        riesgo_q3 = float(np.percentile(positivos, 75))
        riesgo_max = float(np.max(positivos))
        riesgo_medio = float(np.mean(positivos))
    else:
        riesgo_min_positivo = riesgo_q1 = riesgo_mediana = riesgo_q3 = riesgo_max = riesgo_medio = 0.0
    celdas_riesgo = int(len(positivos))
    ruta_exp = CARPETA_CRUCE / mes / f"02_exposicion_{mes}_0a1.tif"
    with rasterio.open(ruta_exp) as src:
        exp = src.read(1).astype(np.float32)
        exp_nodata = src.nodata
    exp_valida = np.isfinite(exp)
    if exp_nodata is not None:
        exp_valida &= (exp != exp_nodata)
    exp_pos = exp[exp_valida & (exp > 0)]
    exp_max = float(np.max(exp_pos)) if len(exp_pos) else 0.0
    exp_media = float(np.mean(exp_pos)) if len(exp_pos) else 0.0

    nc = buscar_nc(mes)
    if nc is None:
        raise FileNotFoundError(f"No se encontró NetCDF FINAL para {mes}.")
    with xr.open_dataset(nc) as ds:
        lon = ds["lon"].values
        lat = ds["lat"].values
        status = ds["status"].values
        tiempos = ds["time"].values
        duracion_h = float(
            (np.datetime64(tiempos[-1]) - np.datetime64(tiempos[0]))
            / np.timedelta64(1, "h")
        )
        estado_final = ultimo_estado_valido(status)
        activas_final = int(np.sum(estado_final == 0))
        varadas_alguna_vez = int(np.sum(np.any(status == 1, axis=1)))
        pct_varadas = varadas_alguna_vez / status.shape[0] * 100.0
        primer_varamiento = primer_varamiento_h(status, tiempos)
        dist_km = haversine_km(LON0, LAT0, lon, lat)
        distancia_max_km = float(np.nanmax(dist_km))
    clases = np.full(arr.shape, -9999, dtype=np.int16)
    clases[valida] = 0
    clases[valida & (arr > 0) & (arr <= Q1_GLOBAL)] = 1
    clases[valida & (arr > Q1_GLOBAL) & (arr <= Q3_GLOBAL)] = 2
    clases[valida & (arr > Q3_GLOBAL)] = 3
    perfil_clases = perfil.copy()
    perfil_clases.update(dtype="int16", count=1, nodata=-9999, compress="deflate")

    salida_clases = CARPETA_SALIDA / f"04_riesgo_clases_globales_{mes}.tif"
    with rasterio.open(salida_clases, "w", **perfil_clases) as dst:
        dst.write(clases, 1)
    fila = {
        "numero_mes": numero,
        "mes": mes,
        "duracion_efectiva_h": round(duracion_h, 2),
        "primer_varamiento_h": round(primer_varamiento, 2) if np.isfinite(primer_varamiento) else "",
        "porcentaje_varadas": round(pct_varadas, 2),
        "activas_final": activas_final,
        "distancia_maxima_km": round(distancia_max_km, 3),
        "celdas_con_riesgo": celdas_riesgo,
        "exposicion_maxima": round(exp_max, 6),
        "exposicion_media_celdas_expuestas": round(exp_media, 6),
        "riesgo_minimo_positivo": riesgo_min_positivo,
        "riesgo_Q1_mes": riesgo_q1,
        "riesgo_mediana_mes": riesgo_mediana,
        "riesgo_Q3_mes": riesgo_q3,
        "riesgo_maximo": riesgo_max,
        "riesgo_medio_celdas_expuestas": riesgo_medio,
    }
    resumen.append(fila)
    print(f"Duración: {duracion_h:.2f} h")
    print(f"Varadas: {pct_varadas:.1f}%")
    print(f"Distancia máxima: {distancia_max_km:.2f} km")
    print(f"Celdas con riesgo: {celdas_riesgo}")
    print(f"Riesgo máximo: {riesgo_max:.6f}")
    print(f"Riesgo medio: {riesgo_medio:.6f}")
    print(f"Clasificado: {salida_clases}")
CSV_SALIDA = CARPETA_SALIDA / "resumen_resultados_mensuales_FINAL.csv"
campos = list(resumen[0].keys())
with open(CSV_SALIDA, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=campos)
    writer.writeheader()
    writer.writerows(resumen)
TXT_UMBRALES = CARPETA_SALIDA / "umbrales_globales_riesgo.txt"
with open(TXT_UMBRALES, "w", encoding="utf-8") as f:
    f.write("CLASIFICACION GLOBAL DE RIESGO ECOLOGICO\n")
    f.write("=========================================\n\n")
    f.write(f"Q1 global: {Q1_GLOBAL:.10f}\n")
    f.write(f"Mediana global: {Q2_GLOBAL:.10f}\n")
    f.write(f"Q3 global: {Q3_GLOBAL:.10f}\n")
    f.write(f"Maximo global: {MAX_GLOBAL:.10f}\n\n")
    f.write("0 = SIN RIESGO: R = 0\n")
    f.write(f"1 = BAJO: 0 < R <= {Q1_GLOBAL:.10f}\n")
    f.write(f"2 = MEDIO: {Q1_GLOBAL:.10f} < R <= {Q3_GLOBAL:.10f}\n")
    f.write(f"3 = ALTO: R > {Q3_GLOBAL:.10f}\n")
print("\n" + "=" * 80)
print("RESULTADOS FINALES PREPARADOS")
print("=" * 80)
print("\nCSV:")
print(CSV_SALIDA)
print("\nUmbrales:")
print(TXT_UMBRALES)
print("\nRasters clasificados:")
print(CARPETA_SALIDA)
print("\nEn QGIS:")
print("0 = transparente")
print("1 = verde (bajo)")
print("2 = amarillo (medio)")
print("3 = rojo (alto)")
