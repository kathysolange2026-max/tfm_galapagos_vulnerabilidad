# cruzar_opendrift_con_vulnerabilidad_FINAL.py
# INTEGRACIÓN FINAL:
# OpenDrift mensual + raster de vulnerabilidad ecológica
# PRODUCTOS POR MES:
# 1) conteo de trayectorias únicas por celda (0-1000)
# 2) exposición normalizada (0-1)
# 3) índice de riesgo ecológico potencial: R = Vulnerabilidad * Exposición
# PRODUCTOS RESUMEN DE LOS 12 MESES:
# - exposición promedio
# - exposición máxima
# - frecuencia de exposición (0-12 meses)
# - riesgo promedio
# - riesgo máximo
# - mes de máximo riesgo (1-12)
# - CSV resumen mensual

# IMPORTANTE:
# - NO modifica los NetCDF originales.
# - NO modifica el raster de vulnerabilidad.
# - NO vuelve a simular OpenDrift.
# - Usa exactamente la malla del raster de vulnerabilidad.
# - Cada trayectoria cuenta UNA sola vez por celda,
#   aunque pase varias veces o permanezca varada allí.

from pathlib import Path
import csv
import math
import traceback
import numpy as np
import xarray as xr
import rasterio
from rasterio.features import rasterize
from rasterio.windows import Window
from rasterio.windows import transform as window_transform
from shapely.geometry import LineString, Point

# 1. RUTAS
BASE = Path(
    r"C:\Users\josej\Documents\tfm_galapagos"
)
CARPETA_NC = (
    BASE
    / "opendrift_resultados"
    / "itabaca_12_meses_FINAL"
)
CARPETA_SALIDA = (
    BASE
    / "opendrift_resultados"
    / "cruce_vulnerabilidad_FINAL"
)
CARPETA_SALIDA.mkdir(
    parents=True,
    exist_ok=True
)
NOMBRE_RASTER = (
    "vulnerabilidad_fauna_integrada_"
    "norm_final_positivos_nodata.tif"
)
CANDIDATOS_RASTER = [
    BASE
    / "resultados"
    / NOMBRE_RASTER,
    Path.home()
    / "Documents"
    / "tfm_galapagos"
    / "resultados"
    / NOMBRE_RASTER,
    Path(
        r"C:\Users\PERSONAL\Documents\tfm_galapagos\resultados"
    )
    / NOMBRE_RASTER,
]

# 2. MESES
MESES = [
    (1, "enero"),
    (2, "febrero"),
    (3, "marzo"),
    (4, "abril"),
    (5, "mayo"),
    (6, "junio"),
    (7, "julio"),
    (8, "agosto"),
    (9, "septiembre"),
    (10, "octubre"),
    (11, "noviembre"),
    (12, "diciembre"),
]

NUMERO_PARTICULAS = 1000
NODATA_FLOAT = -9999.0
NODATA_INT = -9999

# 3. LOCALIZAR RASTER DE VULNERABILIDAD
RASTER_VULNERABILIDAD = None
for candidato in CANDIDATOS_RASTER:
    if candidato.exists():
        RASTER_VULNERABILIDAD = candidato
        break
if RASTER_VULNERABILIDAD is None:
    raiz_busqueda = (
        Path.home()
        / "Documents"
    )
    if raiz_busqueda.exists():
        encontrados = list(
            raiz_busqueda.rglob(
                NOMBRE_RASTER
            )
        )
        if encontrados:
            RASTER_VULNERABILIDAD = (
                encontrados[0]
            )

if RASTER_VULNERABILIDAD is None:
    raise FileNotFoundError(
        "\nNo se encontró el raster:\n"
        f"{NOMBRE_RASTER}\n\n"
        "Copia el archivo dentro de:\n"
        f"{BASE / 'resultados'}\n"
        "o modifica CANDIDATOS_RASTER al inicio del script."
    )

# 4. LOCALIZAR NETCDF FINAL DE CADA MES
def buscar_netcdf_final(mes):
    candidatos = sorted(
        CARPETA_NC.glob(
            f"itabaca_{mes}_FINAL_*.nc"
        )
    )
    if not candidatos:
        return None
    return max(
        candidatos,
        key=lambda p: p.stat().st_mtime
    )

# 5. CREAR MÁSCARA ÚNICA DE UNA TRAYECTORIA
def rasterizar_trayectoria_unica(
    lon,
    lat,
    transform,
    height,
    width
):
    """
    Rasteriza UNA trayectoria en una ventana local.
    Cada celda tocada aparece una sola vez para esta trayectoria.
    Se usa all_touched=True para incluir también las celdas
    cruzadas por los segmentos entre posiciones consecutivas.
    """
    valido = (
        np.isfinite(lon)
        & np.isfinite(lat)
    )
    x = np.asarray(
        lon[valido],
        dtype=float
    )
    y = np.asarray(
        lat[valido],
        dtype=float
    )
    if len(x) == 0:
        return (
            np.array([], dtype=int),
            np.array([], dtype=int)
        )
    if len(x) > 1:
        cambio = np.ones(
            len(x),
            dtype=bool
        )
        cambio[1:] = (
            (x[1:] != x[:-1])
            | (y[1:] != y[:-1])
        )
        x = x[cambio]
        y = y[cambio]
    if len(x) == 1:
        geom = Point(
            float(x[0]),
            float(y[0])
        )
    else:
        geom = LineString(
            np.column_stack(
                [x, y]
            )
        )
    if geom.is_empty:
        return (
            np.array([], dtype=int),
            np.array([], dtype=int)
        )
    minx, miny, maxx, maxy = (
        geom.bounds
    )
    xres = float(
        transform.a
    )
    yres = abs(
        float(
            transform.e
        )
    )
    west = float(
        transform.c
    )
    north = float(
        transform.f
    )
    c0 = int(
        math.floor(
            (minx - west)
            / xres
        )
    ) - 1
    c1 = int(
        math.ceil(
            (maxx - west)
            / xres
        )
    ) + 1
    r0 = int(
        math.floor(
            (north - maxy)
            / yres
        )
    ) - 1
    r1 = int(
        math.ceil(
            (north - miny)
            / yres
        )
    ) + 1
    c0 = max(
        0,
        c0
    )
    r0 = max(
        0,
        r0
    )
    c1 = min(
        width,
        c1
    )
    r1 = min(
        height,
        r1
    )
    if (
        c1 <= c0
        or r1 <= r0
    ):
        return (
            np.array([], dtype=int),
            np.array([], dtype=int)
        )
 ventana = Window(
        c0,
        r0,
        c1 - c0,
        r1 - r0
    )
    trans_local = (
        window_transform(
            ventana,
            transform
        )
    )
    mascara = rasterize(
        [(geom, 1)],
        out_shape=(
            int(
                ventana.height
            ),
            int(
                ventana.width
            ),
        ),
        transform=trans_local,
        fill=0,
        all_touched=True,
        dtype="uint8",
    )
    rr, cc = np.where(
        mascara == 1
    )
    return (
        rr + r0,
        cc + c0
    )

# 6. ESCRIBIR RASTER
def guardar_float(
    ruta,
    matriz,
    perfil_base
):
    perfil = (
        perfil_base.copy()
    )
   perfil.update(
        dtype="float32",
        count=1,
        nodata=NODATA_FLOAT,
        compress="deflate",
        predictor=3,
    )
    with rasterio.open(
        ruta,
        "w",
        **perfil
    ) as dst:
        dst.write(
            matriz.astype(
                np.float32
            ),
            1
        )
def guardar_int16(
    ruta,
    matriz,
    perfil_base
):
    perfil = (
        perfil_base.copy()
    )
    perfil.update(
        dtype="int16",
        count=1,
        nodata=NODATA_INT,
        compress="deflate",
    )
    with rasterio.open(
        ruta,
        "w",
        **perfil
    ) as dst:
        dst.write(
            matriz.astype(
                np.int16
            ),
            1
        )

# 7. LEER RASTER MAESTRO
print("\n")
print("=" * 80)
print("CRUCE OPENDRIFT + VULNERABILIDAD ECOLÓGICA")
print("=" * 80)
print(
    "\nRaster maestro:"
)
print(
    RASTER_VULNERABILIDAD
)
with rasterio.open(
    RASTER_VULNERABILIDAD
) as src:
    vulnerabilidad = (
        src.read(1)
        .astype(
            np.float32
        )
    )
    perfil_base = (
        src.profile.copy()
    )
    transform = src.transform
    crs = src.crs
    height = src.height
    width = src.width
    nodata_original = src.nodata

# 8. VALIDACIONES DEL RASTER
if crs is None:
    raise RuntimeError(
        "El raster de vulnerabilidad no tiene CRS."
    )
if crs.to_epsg() != 4326:
    raise RuntimeError(
        "El raster maestro debe estar en EPSG:4326. "
        f"CRS detectado: {crs}"
    )

if nodata_original is not None:
    mascara_valida = (
        np.isfinite(
            vulnerabilidad
        )
        & (
            vulnerabilidad
            != nodata_original
        )
    )
else:
    mascara_valida = (
        np.isfinite(
            vulnerabilidad
        )
    )
valores_validos = (
    vulnerabilidad[
        mascara_valida
    ]
)
print(
    f"\nDimensiones: "
    f"{width} x {height}"
)
print(
    f"CRS: {crs}"
)
print(
    f"Tamaño píxel: "
    f"{transform.a} x {transform.e}"
)
print(
    f"Vulnerabilidad mínima válida: "
    f"{np.nanmin(valores_validos)}"
)
print(
    f"Vulnerabilidad máxima válida: "
    f"{np.nanmax(valores_validos)}"
)
if (
    np.nanmin(
        valores_validos
    ) < -1e-6
    or np.nanmax(
        valores_validos
    ) > 1.000001
):
    raise RuntimeError(
        "La vulnerabilidad no parece estar normalizada 0-1."
    )

# 9. PROCESAR LOS 12 MESES
exposiciones = []
riesgos = []
nombres_procesados = []
resumen = []
for numero_mes, mes in MESES:
    archivo_nc = (
        buscar_netcdf_final(
            mes
        )
    )
    print("\n")
    print("=" * 80)
    print(
        mes.upper()
    )
    print("=" * 80)
    if archivo_nc is None:
        print(
            "NO se encontró NetCDF FINAL."
        )
        continue
    print(
        "\nNetCDF:"
    )
    print(
        archivo_nc
    )
    try:

        with xr.open_dataset(
            archivo_nc
        ) as ds:
            if (
                "lon" not in ds.variables
                or "lat" not in ds.variables
            ):
                raise RuntimeError(
                    "Faltan variables lon/lat."
                )
            lon = ds[
                "lon"
            ].values
            lat = ds[
                "lat"
            ].values
           n_particulas = (
                lon.shape[0]
            )
            if (
                n_particulas
                != NUMERO_PARTICULAS
            ):
                raise RuntimeError(
                    f"Se esperaban "
                    f"{NUMERO_PARTICULAS} partículas, "
                    f"pero hay {n_particulas}."
                )
            conteo = np.zeros(
                (
                    height,
                    width
                ),
                dtype=np.uint16
            )
            print(
                "\nRasterizando 1000 trayectorias..."
            )
            for i in range(
                n_particulas
            ):
                rr, cc = (
                    rasterizar_trayectoria_unica(
                        lon[i, :],
                        lat[i, :],
                        transform,
                        height,
                        width
                    )
                )
                if len(rr) > 0:
                    conteo[
                        rr,
                        cc
                    ] += 1
                if (
                    (i + 1)
                    % 100
                    == 0
                ):
                    print(
                        f"  {i + 1}/"
                        f"{n_particulas}"
                    )
        exposicion = (
            conteo.astype(
                np.float32
            )
            / float(
                NUMERO_PARTICULAS
            )
        )
        riesgo = np.full(
            (
                height,
                width
            ),
            NODATA_FLOAT,
            dtype=np.float32
        )

        riesgo[
            mascara_valida
        ] = (
            vulnerabilidad[
                mascara_valida
            ]
            * exposicion[
                mascara_valida
            ]
        )
        exposicion_salida = np.full(
            (
                height,
                width
            ),
            NODATA_FLOAT,
            dtype=np.float32
        )
        exposicion_salida[
            mascara_valida
        ] = exposicion[
            mascara_valida
        ]
        conteo_salida = np.full(
            (
                height,
                width
            ),
            NODATA_INT,
            dtype=np.int16
        )
        conteo_salida[
            mascara_valida
        ] = conteo[
            mascara_valida
        ].astype(
            np.int16
        )
        carpeta_mes = (
            CARPETA_SALIDA
            / mes
        )
        carpeta_mes.mkdir(
            parents=True,
            exist_ok=True
        )
        ruta_conteo = (
            carpeta_mes
            / (
                f"01_conteo_trayectorias_"
                f"{mes}.tif"
            )
        )
        ruta_exposicion = (
            carpeta_mes
            / (
                f"02_exposicion_"
                f"{mes}_0a1.tif"
            )
        )
        ruta_riesgo = (
            carpeta_mes
            / (
                f"03_riesgo_ecologico_"
                f"{mes}_0a1.tif"
            )
        )
        guardar_int16(
            ruta_conteo,
            conteo_salida,
            perfil_base
        )
        guardar_float(
            ruta_exposicion,
            exposicion_salida,
            perfil_base
        )
        guardar_float(
            ruta_riesgo,
            riesgo,
            perfil_base
        )
        celdas_expuestas = (
            mascara_valida
            & (
                exposicion > 0
            )
        )
        n_celdas_expuestas = int(
            np.sum(
                celdas_expuestas
            )
        )
        if n_celdas_expuestas > 0:
            riesgo_expuesto = (
                riesgo[
                    celdas_expuestas
                ]
            )
            exposicion_expuesta = (
                exposicion[
                    celdas_expuestas
                ]
            )
            riesgo_max = float(
                np.nanmax(
                    riesgo_expuesto
                )
            )
            riesgo_medio_expuesto = float(
                np.nanmean(
                    riesgo_expuesto
                )
            )
            exp_max = float(
                np.nanmax(
                    exposicion_expuesta
                )
            )
            exp_media_expuesta = float(
                np.nanmean(
                    exposicion_expuesta
                )
            )
            matriz_aux = np.where(
                celdas_expuestas,
                riesgo,
                -np.inf
            )
            rmax, cmax = np.unravel_index(
                np.argmax(
                    matriz_aux
                ),
                matriz_aux.shape
            )
            lon_max, lat_max = (
                rasterio.transform.xy(
                    transform,
                    rmax,
                    cmax,
                    offset="center"
                )
            )
        else:
            riesgo_max = 0.0
            riesgo_medio_expuesto = 0.0
            exp_max = 0.0
            exp_media_expuesta = 0.0
            lon_max = np.nan
            lat_max = np.nan
        print(
            f"\nCeldas válidas expuestas: "
            f"{n_celdas_expuestas}"
        )
        print(
            f"Exposición máxima: "
            f"{exp_max:.4f}"
        )
        print(
            f"Riesgo máximo: "
            f"{riesgo_max:.6f}"
        )
        print(
            f"Riesgo medio en celdas expuestas: "
            f"{riesgo_medio_expuesto:.6f}"
        )
        print(
            "Productos:"
        )
        print(
            f"  {ruta_conteo}"
        )
        print(
            f"  {ruta_exposicion}"
        )
        print(
            f"  {ruta_riesgo}"
        )
        exposiciones.append(
            exposicion.copy()
        )
        riesgo_limpio = np.zeros(
            (
                height,
                width
            ),
            dtype=np.float32
        )
        riesgo_limpio[
            mascara_valida
        ] = riesgo[
            mascara_valida
        ]
        riesgos.append(
            riesgo_limpio
        )
        nombres_procesados.append(
            mes
        )
        resumen.append({
            "numero_mes": numero_mes,
            "mes": mes,
            "archivo_nc": archivo_nc.name,
            "celdas_expuestas_validas": n_celdas_expuestas,
            "exposicion_maxima": exp_max,
            "exposicion_media_celdas_expuestas": exp_media_expuesta,
            "riesgo_maximo": riesgo_max,
            "riesgo_medio_celdas_expuestas": riesgo_medio_expuesto,
            "lon_riesgo_maximo": lon_max,
            "lat_riesgo_maximo": lat_max,
        })
    except Exception as error:
        print(
            "\nERROR:"
        )
        print(
            error
        )
        traceback.print_exc()

# 10. PRODUCTOS RESUMEN
if len(exposiciones) == 0:
    raise RuntimeError(
        "No se pudo procesar ningún mes."
    )
stack_exp = np.stack(
    exposiciones,
    axis=0
)
stack_riesgo = np.stack(
    riesgos,
    axis=0
)
exp_promedio = np.mean(
    stack_exp,
    axis=0
).astype(
    np.float32
)
exp_maxima = np.max(
    stack_exp,
    axis=0
).astype(
    np.float32
)
frecuencia = np.sum(
    stack_exp > 0,
    axis=0
).astype(
    np.int16
)
riesgo_promedio = np.mean(
    stack_riesgo,
    axis=0
).astype(
    np.float32
)
riesgo_maximo = np.max(
    stack_riesgo,
    axis=0
).astype(
    np.float32
)
idx_mes_max = np.argmax(
    stack_riesgo,
    axis=0
)
numeros_meses_procesados = np.array(
    [
        next(
            n
            for n, m in MESES
            if m == nombre
        )
        for nombre
        in nombres_procesados
    ],
    dtype=np.int16
)
mes_riesgo_maximo = (
    numeros_meses_procesados[
        idx_mes_max
    ]
).astype(
    np.int16
)
mes_riesgo_maximo[
    exp_maxima == 0
] = 0

# 11. APLICAR MÁSCARA DEL RASTER MAESTRO
def aplicar_mask_float(
    matriz
):
    salida = np.full(
        (
            height,
            width
        ),
        NODATA_FLOAT,
        dtype=np.float32
    )
    salida[
        mascara_valida
    ] = matriz[
        mascara_valida
    ]
    return salida
def aplicar_mask_int(
    matriz
):
    salida = np.full(
        (
            height,
            width
        ),
        NODATA_INT,
        dtype=np.int16
    )
    salida[
        mascara_valida
    ] = matriz[
        mascara_valida
    ]
    return salida
exp_promedio_out = (
    aplicar_mask_float(
        exp_promedio
    )
)
exp_maxima_out = (
    aplicar_mask_float(
        exp_maxima
    )
)
riesgo_promedio_out = (
    aplicar_mask_float(
        riesgo_promedio
    )
)
riesgo_maximo_out = (
    aplicar_mask_float(
        riesgo_maximo
    )
)
frecuencia_out = (
    aplicar_mask_int(
        frecuencia
    )
)
mes_riesgo_maximo_out = (
    aplicar_mask_int(
        mes_riesgo_maximo
    )
)
# 12. GUARDAR PRODUCTOS RESUMEN
CARPETA_RESUMEN = (
    CARPETA_SALIDA
    / "RESUMEN_12_MESES"
)
CARPETA_RESUMEN.mkdir(
    parents=True,
    exist_ok=True
)
guardar_float(
    CARPETA_RESUMEN
    / "exposicion_promedio_12_meses.tif",
    exp_promedio_out,
    perfil_base
)
guardar_float(
    CARPETA_RESUMEN
    / "exposicion_maxima_12_meses.tif",
    exp_maxima_out,
    perfil_base
)
guardar_int16(
    CARPETA_RESUMEN
    / "frecuencia_exposicion_meses_0a12.tif",
    frecuencia_out,
    perfil_base
)
guardar_float(
    CARPETA_RESUMEN
    / "riesgo_ecologico_promedio_12_meses.tif",
    riesgo_promedio_out,
    perfil_base
)
guardar_float(
    CARPETA_RESUMEN
    / "riesgo_ecologico_maximo_12_meses.tif",
    riesgo_maximo_out,
    perfil_base
)
guardar_int16(
    CARPETA_RESUMEN
    / "mes_de_riesgo_maximo_1a12.tif",
    mes_riesgo_maximo_out,
    perfil_base
)

# 13. CSV RESUMEN
CSV_RESUMEN = (
    CARPETA_RESUMEN
    / "resumen_cruce_vulnerabilidad_12_meses.csv"
)
campos = [
    "numero_mes",
    "mes",
    "archivo_nc",
    "celdas_expuestas_validas",
    "exposicion_maxima",
    "exposicion_media_celdas_expuestas",
    "riesgo_maximo",
    "riesgo_medio_celdas_expuestas",
    "lon_riesgo_maximo",
    "lat_riesgo_maximo",
]
with open(
    CSV_RESUMEN,
    "w",
    newline="",
    encoding="utf-8-sig"
) as f:
    writer = csv.DictWriter(
        f,
        fieldnames=campos
    )
    writer.writeheader()
    for fila in resumen:
        writer.writerow(
            fila
        )

# 14. FIN
print("\n")
print("=" * 80)
print("CRUCE FINALIZADO")
print("=" * 80)
print(
    f"\nMeses procesados: "
    f"{len(nombres_procesados)}"
)
print(
    "\nRaster maestro:"
)
print(
    RASTER_VULNERABILIDAD
)
print(
    "\nCarpeta de salida:"
)
print(
    CARPETA_SALIDA
)
print(
    "\nProductos resumen:"
)
print(
    CARPETA_RESUMEN
)
print(
    "\nCSV:"
)
print(
    CSV_RESUMEN
)
print(
    "\nInterpretación:"
)
print(
    "Exposición 0-1 = proporción de las 1000 trayectorias "
    "que alcanzaron cada celda."
)
print(
    "Riesgo 0-1 = vulnerabilidad ecológica × exposición."
)
print(
    "Frecuencia = número de meses (0-12) en que la celda "
    "fue alcanzada por al menos una trayectoria."
)
