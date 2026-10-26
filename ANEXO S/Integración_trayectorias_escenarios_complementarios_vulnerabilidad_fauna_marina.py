# TFM GALÁPAGOS
# Cruce de 3 escenarios complementarios OpenDrift/OpenOil
# con el raster integrado de vulnerabilidad de fauna marina.
# Metodología:
#   1) Rasteriza cada trayectoria sobre el raster de vulnerabilidad (EPSG:4326, 0.005°).
#   2) Cada partícula cuenta como máximo una vez por celda.
#   3) Exposición relativa: E(x) = partículas únicas que tocaron x / 1000
#   4) Riesgo ecológico potencial: R(x) = V(x) * E(x)
#   5) Clasificación con los mismos umbrales usados en los 12 mapas mensuales de Itabaca:
#   1 BAJO  : 0 < R <= 0.0001364388
#         2 MEDIO : 0.0001364388 < R <= 0.0026645004
#         3 ALTO  : R > 0.0026645004
# Además genera distancias por clase desde el punto de
# liberación (mínima, media, mediana y máxima).
from pathlib import Path
import math
import csv
import numpy as np
import pandas as pd
import xarray as xr
import rasterio
from rasterio.features import rasterize
from shapely.geometry import LineString, Point

# 1. RUTAS
BASE = Path(r"C:\Users\josej\Documents\tfm_galapagos")
RASTER_VULNERABILIDAD = (
    BASE
    / "resultados"
    / "vulnerabilidad_fauna_integrada_norm_final_positivos_nodata.tif"
)
BASE_NC = (
    BASE
    / "opendrift_resultados"
    / "escenarios_complementarios_FINAL"
)
SALIDA = (
    BASE
    / "opendrift_resultados"
    / "cruce_vulnerabilidad_escenarios_complementarios_FINAL"
)
SALIDA.mkdir(parents=True, exist_ok=True)

# 2. ESCENARIOS
ESCENARIOS = [
    {
        "sitio": "Puerto Ayora",
        "slug": "puerto_ayora",
        "mes": "septiembre",
        "ais_h": 80.256,
        "lat0": -0.75209,
        "lon0": -90.3028,
        "nc": (
            BASE_NC
            / "puerto_ayora"
            / "puerto_ayora_septiembre_FINAL_2016_2025_1000part_r0_procON_10min_72h.nc"
        ),
    },
    {
        "sitio": "Wolf/Darwin Norte",
        "slug": "wolf_darwin_norte",
        "mes": "octubre",
        "ais_h": 54.248,
        "lat0": 1.40000,
        "lon0": -91.800003,
        "nc": (
            BASE_NC
            / "wolf_darwin_norte"
            / "wolf_darwin_norte_octubre_FINAL_2016_2025_1000part_r0_procON_10min_72h.nc"
        ),
    },
    {
        "sitio": "Puerto Baquerizo Moreno",
        "slug": "puerto_baquerizo_moreno",
        "mes": "abril",
        "ais_h": 48.971,
        "lat0": -0.89657,
        "lon0": -89.61293,
        "nc": (
            BASE_NC
            / "puerto_baquerizo_moreno"
            / "puerto_baquerizo_moreno_abril_FINAL_2016_2025_1000part_r0_procON_10min_72h.nc"
        ),
    },
]

# 3. UMBRALES FIJOS DE CLASIFICACIÓN
# (los mismos de Itabaca)
Q1_GLOBAL_ITABACA = 0.0001364388
Q3_GLOBAL_ITABACA = 0.0026645004

NODATA_FLOAT = -9999.0
NODATA_CLASS = 255

# 4. FUNCIONES
def haversine_km(lon1, lat1, lon2, lat2):
    """Distancia geodésica aproximada sobre esfera terrestre."""
    R = 6371.0088
    lon1 = np.radians(lon1)
    lat1 = np.radians(lat1)
    lon2 = np.radians(lon2)
    lat2 = np.radians(lat2)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = (
        np.sin(dlat / 2.0) ** 2
        + np.cos(lat1)
        * np.cos(lat2)
        * np.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * np.arcsin(np.sqrt(a))
    return R * c
def obtener_lon_lat(ds):
    """Busca variables de longitud y latitud en el NetCDF."""
    candidatos_lon = ["lon", "longitude", "x"]
    candidatos_lat = ["lat", "latitude", "y"]
    lon_name = next((x for x in candidatos_lon if x in ds.variables), None)
    lat_name = next((x for x in candidatos_lat if x in ds.variables), None)

    if lon_name is None or lat_name is None:
        raise RuntimeError(
            "No se encontraron variables de lon/lat en el NetCDF. "
            f"Variables disponibles: {list(ds.variables)}"
        )
    lon = np.asarray(ds[lon_name].values)
    lat = np.asarray(ds[lat_name].values)
    # OpenDrift suele producir trajectory x time.
    # Si llegara como time x trajectory, se intenta corregir.
    if lon.ndim != 2 or lat.ndim != 2:
        raise RuntimeError(
            f"lon/lat deben ser 2D. Formas encontradas: "
            f"{lon.shape} / {lat.shape}"
        )
    dims = ds[lon_name].dims
    if len(dims) == 2 and dims[0] == "time":
        lon = lon.T
        lat = lat.T
    return lon, lat
def construir_geometria_trayectoria(lons, lats):
    """
    Construye una geometría por partícula.
    - 1 punto válido -> Point
    - >=2 puntos válidos -> LineString
    """
    mask = np.isfinite(lons) & np.isfinite(lats)
    coords = list(zip(lons[mask], lats[mask]))
    if len(coords) == 0:
        return None
    # Eliminar duplicados consecutivos
    coords_limpias = [coords[0]]
    for c in coords[1:]:
        if c != coords_limpias[-1]:
            coords_limpias.append(c)
    if len(coords_limpias) == 1:
        return Point(coords_limpias[0])
    return LineString(coords_limpias)
def escribir_raster(path, array, profile, dtype, nodata):
    p = profile.copy()
    p.update(
        count=1,
        dtype=dtype,
        nodata=nodata,
        compress="deflate",
    )
    with rasterio.open(path, "w", **p) as dst:
        dst.write(array.astype(dtype), 1)
def estadisticas_distancia_por_clase(
    clases,
    transform,
    lon0,
    lat0,
):
    filas = []
    for clase, etiqueta in [
        (1, "Bajo"),
        (2, "Medio"),
        (3, "Alto"),
    ]:
        rows, cols = np.where(clases == clase)
        if len(rows) == 0:
            filas.append({
                "clase": clase,
                "categoria": etiqueta,
                "celdas": 0,
                "dist_min_km": np.nan,
                "dist_media_km": np.nan,
                "dist_mediana_km": np.nan,
                "dist_max_km": np.nan,
            })
            continue
        xs, ys = rasterio.transform.xy(
            transform,
            rows,
            cols,
            offset="center"
        )
        xs = np.asarray(xs, dtype=float)
        ys = np.asarray(ys, dtype=float)
        dist = haversine_km(
            lon0,
            lat0,
            xs,
            ys
        )
        filas.append({
            "clase": clase,
            "categoria": etiqueta,
            "celdas": int(len(dist)),
            "dist_min_km": float(np.min(dist)),
            "dist_media_km": float(np.mean(dist)),
            "dist_mediana_km": float(np.median(dist)),
            "dist_max_km": float(np.max(dist)),
        })
    return filas

# 5. LEER GRILLA MAESTRA DE VULNERABILIDAD
if not RASTER_VULNERABILIDAD.exists():
    raise FileNotFoundError(
        f"No existe el raster de vulnerabilidad:\n{RASTER_VULNERABILIDAD}"
    )
with rasterio.open(RASTER_VULNERABILIDAD) as src:
    vulnerabilidad = src.read(1).astype(np.float32)
    profile = src.profile.copy()
    transform = src.transform
    crs = src.crs
    width = src.width
    height = src.height
    nodata_v = src.nodata
if nodata_v is None:
    valid_v = np.isfinite(vulnerabilidad)
else:
    valid_v = (
        np.isfinite(vulnerabilidad)
        & (vulnerabilidad != nodata_v)
    )
# Limitar a rango esperado
valid_v &= (vulnerabilidad >= 0) & (vulnerabilidad <= 1)
print("\n" + "=" * 80)
print("CRUCE DE ESCENARIOS COMPLEMENTARIOS CON VULNERABILIDAD")
print("=" * 80)
print(f"Raster maestro: {RASTER_VULNERABILIDAD}")
print(f"Dimensiones: {width} x {height}")
print(f"CRS: {crs}")
print(f"Celdas válidas de vulnerabilidad: {int(valid_v.sum())}")

# 6. PROCESAR CADA ESCENARIO
resumen_general = []
resumen_distancias = []
for e in ESCENARIOS:
    print("\n" + "=" * 80)
    print(f"{e['sitio'].upper()} - {e['mes'].upper()}")
    print("=" * 80)
    if not e["nc"].exists():
        print("ERROR: no existe NetCDF:")
        print(e["nc"])
        continue
    outdir = SALIDA / e["slug"]
    outdir.mkdir(parents=True, exist_ok=True)
    with xr.open_dataset(e["nc"]) as ds:
        lon, lat = obtener_lon_lat(ds)
    n_particulas = lon.shape[0]
    print(f"NetCDF: {e['nc'].name}")
    print(f"Partículas detectadas: {n_particulas}")
    conteo = np.zeros(
        (height, width),
        dtype=np.uint16
    )
    particulas_validas = 0
    for i in range(n_particulas):
        geom = construir_geometria_trayectoria(
            lon[i, :],
            lat[i, :]
        )
        if geom is None:
            continue
        # Raster binario individual:
        # la partícula cuenta solo una vez por celda
        tocadas = rasterize(
            [(geom, 1)],
            out_shape=(height, width),
            transform=transform,
            fill=0,
            all_touched=True,
            dtype="uint8",
        )
        conteo += tocadas.astype(np.uint16)
        particulas_validas += 1
    if n_particulas <= 0:
        raise RuntimeError(
            f"{e['sitio']}: no hay partículas."
        )
    exposicion = (
        conteo.astype(np.float32)
        / float(n_particulas)
    )
    # 01 y 02: trayectorias/exposición completas,
    # independientemente de la máscara de vulnerabilidad.
    raster_conteo = conteo.astype(np.float32)
    raster_exposicion = exposicion.astype(np.float32)
    # 03: riesgo solo donde existe vulnerabilidad válida.
    riesgo = np.full(
        (height, width),
        NODATA_FLOAT,
        dtype=np.float32
    )
    riesgo[valid_v] = (
        vulnerabilidad[valid_v]
        * exposicion[valid_v]
    )
   # 04: clases solo en celdas válidas de vulnerabilidad.
    clases = np.full(
        (height, width),
        NODATA_CLASS,
        dtype=np.uint8
    )
    # Dentro de vulnerabilidad válida, 0 = sin riesgo
    clases[valid_v] = 0
    mask_pos = valid_v & (riesgo > 0)
    clases[
        mask_pos
        & (riesgo <= Q1_GLOBAL_ITABACA)
    ] = 1
    clases[
        mask_pos
        & (riesgo > Q1_GLOBAL_ITABACA)
        & (riesgo <= Q3_GLOBAL_ITABACA)
    ] = 2
    clases[
        mask_pos
        & (riesgo > Q3_GLOBAL_ITABACA)
    ] = 3

    # Guardar rasters
      p01 = (
        outdir
        / f"01_conteo_trayectorias_{e['slug']}_{e['mes']}.tif"
    )
    p02 = (
        outdir
        / f"02_exposicion_{e['slug']}_{e['mes']}_0a1.tif"
    )
    p03 = (
        outdir
        / f"03_riesgo_ecologico_{e['slug']}_{e['mes']}_0a1.tif"
    )
    p04 = (
        outdir
        / f"04_riesgo_clases_{e['slug']}_{e['mes']}.tif"
    )
    escribir_raster(
        p01,
        raster_conteo,
        profile,
        "float32",
        NODATA_FLOAT
    )
    escribir_raster(
        p02,
        raster_exposicion,
        profile,
        "float32",
        NODATA_FLOAT
    )
    escribir_raster(
        p03,
        riesgo,
        profile,
        "float32",
        NODATA_FLOAT
    )
    escribir_raster(
        p04,
        clases,
        profile,
        "uint8",
        NODATA_CLASS
    )

    # Estadísticas
    exp_cells_total = int(
        np.sum(exposicion > 0)
    )
    exp_cells_con_v = int(
        np.sum(valid_v & (exposicion > 0))
    )
    riesgo_pos = riesgo[
        valid_v & (riesgo > 0)
    ]
    if riesgo_pos.size > 0:
        rmax = float(np.max(riesgo_pos))
        rmean = float(np.mean(riesgo_pos))
        rmedian = float(np.median(riesgo_pos))
    else:
        rmax = np.nan
        rmean = np.nan
        rmedian = np.nan
    c1 = int(np.sum(clases == 1))
    c2 = int(np.sum(clases == 2))
    c3 = int(np.sum(clases == 3))
    print(f"Celdas tocadas totales: {exp_cells_total}")
    print(f"Celdas tocadas con vulnerabilidad válida: {exp_cells_con_v}")
    print(f"E máxima: {float(np.max(exposicion)):.6f}")
    print(f"R máxima: {rmax:.10f}")
    print(f"R media (solo R>0): {rmean:.10f}")
    print(f"R mediana (solo R>0): {rmedian:.10f}")
    print(f"Clases -> Bajo: {c1} | Medio: {c2} | Alto: {c3}")
    resumen_general.append({
        "sitio": e["sitio"],
        "mes": e["mes"],
        "ais_h": e["ais_h"],
        "lat0": e["lat0"],
        "lon0": e["lon0"],
        "particulas": n_particulas,
        "particulas_con_geometria": particulas_validas,
        "celdas_expuestas_total": exp_cells_total,
        "celdas_expuestas_con_vulnerabilidad": exp_cells_con_v,
        "E_max": float(np.max(exposicion)),
        "R_max": rmax,
        "R_media_Rmayor0": rmean,
        "R_mediana_Rmayor0": rmedian,
        "celdas_bajo": c1,
        "celdas_medio": c2,
        "celdas_alto": c3,
    })
    dist_rows = estadisticas_distancia_por_clase(
        clases,
        transform,
        e["lon0"],
        e["lat0"],
    )
    for d in dist_rows:
        resumen_distancias.append({
            "sitio": e["sitio"],
            "mes": e["mes"],
            **d
        })
    pd.DataFrame(dist_rows).to_csv(
        outdir
        / f"05_distancias_por_clase_{e['slug']}_{e['mes']}.csv",
        index=False,
        encoding="utf-8-sig"
    )
    print("Distancias por clase:")
    for d in dist_rows:
        if d["celdas"] == 0:
            print(
                f"  {d['categoria']}: sin celdas"
            )
        else:
            print(
                f"  {d['categoria']}: "
                f"min {d['dist_min_km']:.2f} km | "
                f"mediana {d['dist_mediana_km']:.2f} km | "
                f"media {d['dist_media_km']:.2f} km | "
                f"máx {d['dist_max_km']:.2f} km"
            )

# 7. RESÚMENES GENERALES
df_general = pd.DataFrame(resumen_general)
df_dist = pd.DataFrame(resumen_distancias)
csv_general = (
    SALIDA
    / "resumen_riesgo_escenarios_complementarios_FINAL.csv"
)
csv_dist = (
    SALIDA
    / "resumen_distancias_clases_escenarios_complementarios_FINAL.csv"
)
df_general.to_csv(
    csv_general,
    index=False,
    encoding="utf-8-sig"
)
df_dist.to_csv(
    csv_dist,
    index=False,
    encoding="utf-8-sig"
)
txt_metodo = SALIDA / "metodologia_clasificacion_y_distancias.txt"
txt_metodo.write_text(
    f"""METODOLOGÍA - ESCENARIOS COMPLEMENTARIOS
Índice de exposición relativa:
E(x) = número de partículas únicas que tocaron la celda / número total de partículas.
Índice de riesgo ecológico potencial:
R(x) = V(x) * E(x)
Los umbrales de clasificación se mantienen iguales a los utilizados en los
12 mapas mensuales del caso principal Canal de Itabaca:
0 = SIN RIESGO: R = 0
1 = BAJO: 0 < R <= {Q1_GLOBAL_ITABACA:.10f}
2 = MEDIO: {Q1_GLOBAL_ITABACA:.10f} < R <= {Q3_GLOBAL_ITABACA:.10f}
3 = ALTO: R > {Q3_GLOBAL_ITABACA:.10f}

Las distancias por clase corresponden a la distancia geodésica aproximada
entre el punto de liberación y el centro de cada celda raster clasificada.
La distancia máxima de una clase representa el alcance espacial máximo
observado de esa categoría y NO implica que todas las celdas interiores
presenten la misma categoría de riesgo.
""",
    encoding="utf-8"
)
print("\n" + "=" * 80)
print("PROCESO FINALIZADO")
print("=" * 80)
print(f"Resultados: {SALIDA}")
print(f"Resumen riesgo: {csv_general}")
print(f"Resumen distancias: {csv_dist}")
print(f"Metodología: {txt_metodo}")

