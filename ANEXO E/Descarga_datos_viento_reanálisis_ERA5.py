Dataset: reanalysis-era5-single-levels (ERA5 hourly data on single levels from 1940 to present)
Extensión espacial: -93,7° ; -87,5° ; -3,5° ; 3,5°
Variables: u10 y v10 viento a 10 m
Periodo: 01/01/2016 – 31/12/2025 
Herramienta de acceso: cdsapi
import os
import time
from pathlib import Path
import cdsapi
BASE_SALIDA = Path(
    r"C:\Users\josej\Documents\tfm_galapagos"
    r"\datos_ambientales\era5"
)
DATASET = "reanalysis-era5-single-levels"
MESES = [
    ("enero", “01”), ("febrero", “02”), ("marzo", “03”), ("abril", “04”),
    ("mayo", “05”), ("junio", “06”), ("julio", “07”), ("agosto", “08”),
    ("septiembre", “09”), ("octubre", “10”), ("noviembre", “11”), ("diciembre", “12”),
]
ANIOS = range(2016, 2026)
AREA_GALAPAGOS = [
    3.5,     # norte
    -93.5,   # oeste
    -3.5,    # sur
    -87.5,   # este
]
HORAS = [f"{hora:02d}:00" for hora in range(24)]
def dias_del_mes(anio: int, mes: int) -> list[str]:
    import calendar
    total = calendar.monthrange(anio, mes)[1]
    return [f"{dia:02d}" for dia in range(1, total + 1)]
def archivo_valido(ruta: Path) -> bool:
    return ruta.exists() and ruta.stat().st_size > 10_000
cliente = cdsapi.Client()
fallidos = []
descargados = 0
omitidos = 0
for anio in ANIOS:
    for nombre_mes, mes_str in MESES:
        mes_num = int(mes_str)
        carpeta_mes = BASE_SALIDA / nombre_mes
        carpeta_mes.mkdir(parents=True, exist_ok=True)
        archivo = carpeta_mes / f"viento_{nombre_mes}_{anio}.nc"
        if archivo_valido(archivo):
            print(f"Ya existe: {archivo.name}")
            omitidos += 1
            continue
        solicitud = {
            "product_type": ["reanalysis"],
            "variable": [
                "10m_u_component_of_wind",
                "10m_v_component_of_wind",
            ],
            "year": [str(anio)],
            "month": [mes_str],
            "day": dias_del_mes(anio, mes_num),
            "time": HORAS,
            "area": AREA_GALAPAGOS,
            "data_format": "netcdf",
            "download_format": "unarchived",
        }
        exito = False
        for intento in range(1, 4):
            try:
                print(
                    f"\nDescargando {nombre_mes} {anio} "
                    f"- intento {intento}"
                )
                cliente.retrieve(
                    DATASET,
                    solicitud,
                    str(archivo)
                )
                if not archivo_valido(archivo):
                    raise RuntimeError(
                        "El archivo fue creado, pero parece incompleto."
                    )
                print(f"Guardado: {archivo}")
                descargados += 1
                exito = True
                break
            except Exception as error:
                print(f"Error en {nombre_mes} {anio}: {error}")
                if archivo.exists():
                    try:
                        archivo.unlink()
                    except OSError:
                        pass
                if intento < 3:
                    print("Esperando 30 segundos antes de reintentar...")
                    time.sleep(30)
        if not exito:
            fallidos.append(f"{nombre_mes}_{anio}")
print("\n" + "=" * 60)
print("DESCARGA ERA5 FINALIZADA")
print(f"Descargados: {descargados}")
print(f"Omitidos: {omitidos}")
print(f"Fallidos: {len(fallidos)}")
if fallidos:
    print("Archivos fallidos:")
    for item in fallidos:
        print(f" - {item}")
    log = BASE_SALIDA / "era5_descargas_fallidas.txt"
    log.write_text("\n".join(fallidos), encoding="utf-8")
    print(f"Log guardado en: {log}")
else:
    print("No hubo descargas fallidas.")
