from datetime import datetime, timedelta
from pathlib import Path
from opendrift.models.openoil import OpenOil
from opendrift.readers import reader_netCDF_CF_generic

# RUTAS
BASE = Path(r"C:\Users\josej\Documents\tfm_galapagos")
CARPETA_CORRIENTES = (
    BASE / "datos_ambientales" / "climatologias" / "corrientes"
)
CARPETA_VIENTO = (
    BASE / "datos_ambientales" / "climatologias" / "viento"
)
CARPETA_NC = (
    BASE / "opendrift_resultados" / "escenarios_complementarios_FINAL"
)
CARPETA_VISUALES = (
    BASE / "opendrift_resultados" / "visualizaciones_complementarios_FINAL"
)
CARPETA_NC.mkdir(parents=True, exist_ok=True)
CARPETA_VISUALES.mkdir(parents=True, exist_ok=True)

# PARÁMETROS FINALES COMUNES
NUMERO_PARTICULAS = 1000
RADIO_INICIAL_METROS = 0
# Parámetro utilizado por OpenOil.
TASA_LIBERACION_M3_H = 10.0
TIPO_PETROLEO = "GENERIC MEDIUM CRUDE"
DURACION_HORAS = 72
PASO_MINUTOS = 10
SALIDA_MINUTOS = 10
CURRENT_UNCERTAINTY = 0.05
WIND_UNCERTAINTY = 0.5
SEMILLA = 0
BUFFER_VISUALIZACION = 0.25
FPS_VIDEO = 8

# ESCENARIOS COMPLEMENTARIOS
ESCENARIOS = [
    {
        "id": "puerto_ayora",
        "nombre": "Puerto Ayora",
        "numero_mes": 9,
        "mes": "septiembre",
        "lon": -90.3028,
        "lat": -0.75209,
    },
    {
        "id": "wolf_darwin_norte",
        "nombre": "Wolf/Darwin Norte",
        "numero_mes": 10,
        "mes": "octubre",
        "lon": -91.800003,
        "lat": 1.400000,
    },
    {
        "id": "puerto_baquerizo_moreno",
        "nombre": "Puerto Baquerizo Moreno",
        "numero_mes": 4,
        "mes": "abril",
        "lon": -89.61293,
        "lat": -0.89657,
    },
]

# SIMULACIÓN + PNG + MP4
for escenario in ESCENARIOS:
    escenario_id = escenario["id"]
    nombre = escenario["nombre"]
    numero_mes = escenario["numero_mes"]
    nombre_mes = escenario["mes"]
    longitud = escenario["lon"]
    latitud = escenario["lat"]
    print("\n" + "=" * 78)
    print(f"{nombre.upper()} - {nombre_mes.upper()}")
    print("=" * 78)
    archivo_corrientes = (
        CARPETA_CORRIENTES
        / f"corrientes_climatologia_{nombre_mes}_2016_2025.nc"
    )
    archivo_viento = (
        CARPETA_VIENTO
        / f"viento_climatologia_{nombre_mes}_2016_2025.nc"
    )
    archivo_nc = (
        CARPETA_NC
        / (
            f"{escenario_id}_{nombre_mes}_FINAL_2016_2025_"
            f"1000part_r0_10min_72h.nc"
        )
    )
    carpeta_escenario = CARPETA_VISUALES / escenario_id
    carpeta_escenario.mkdir(parents=True, exist_ok=True)
    archivo_png = (
        carpeta_escenario
        / f"{escenario_id}_{nombre_mes}_trayectoria_FINAL.png"
    )
    archivo_mp4 = (
        carpeta_escenario
        / f"{escenario_id}_{nombre_mes}_animacion_FINAL.mp4"
    )

    # COMPROBACIÓN DE ARCHIVOS DE ENTRADA
    if not archivo_corrientes.exists():
        print(f"ERROR: no existe {archivo_corrientes}")
        continue
    if not archivo_viento.exists():
        print(f"ERROR: no existe {archivo_viento}")
        continue

    # FECHA SINTÉTICA DE LA CLIMATOLOGÍA
    fecha_inicio = datetime(
        2024,
        numero_mes,
        15,
        0,
        0,
        0
    )

    # CREAR MODELO
    modelo = OpenOil(
        loglevel=20,
        seed=SEMILLA
    )

    # LECTORES AMBIENTALES
    lector_corrientes = reader_netCDF_CF_generic.Reader(
        str(archivo_corrientes)
    )
    lector_viento = reader_netCDF_CF_generic.Reader(
        str(archivo_viento)
    )
    modelo.add_reader([
        lector_corrientes,
        lector_viento
    ])

    # CONFIGURACIÓN DEL MODELO
    # Se mantiene la misma configuración empleada en Itabaca.
    modelo.set_config("processes:evaporation", True)
    modelo.set_config("processes:emulsification", True)
    modelo.set_config("processes:dispersion", True)
    modelo.set_config("drift:vertical_mixing", True)
    modelo.set_config(
        "general:coastline_action",
        "stranding"
    )
    modelo.set_config(
        "drift:current_uncertainty",
        CURRENT_UNCERTAINTY
    )
    modelo.set_config(
        "drift:wind_uncertainty",
        WIND_UNCERTAINTY
    )
    modelo.set_config(
        "environment:fallback:sea_surface_height",
        0
    )
    modelo.set_config(
        "environment:fallback:upward_sea_water_velocity",
        0
    )
    modelo.set_config(
        "environment:fallback:sea_surface_wave_significant_height",
        0
    )
    modelo.set_config(
        "environment:fallback:x_sea_water_velocity",
        0
    )
    modelo.set_config(
        "environment:fallback:y_sea_water_velocity",
        0
    )

    # LIBERACIÓN
    modelo.seed_elements(
        lon=longitud,
        lat=latitud,
        radius=RADIO_INICIAL_METROS,
        radius_type="uniform",
        number=NUMERO_PARTICULAS,
        time=fecha_inicio,
        z=0,
        oil_type=TIPO_PETROLEO,
        m3_per_hour=TASA_LIBERACION_M3_H,
    )
    print(f"Escenario   : {nombre}")
    print(f"Mes         : {nombre_mes}")
    print(f"Coordenada  : lon={longitud}, lat={latitud}")
    print(f"Corrientes  : {archivo_corrientes.name}")
    print(f"Viento      : {archivo_viento.name}")
    print(f"Inicio      : {fecha_inicio}")
    print(f"Partículas  : {NUMERO_PARTICULAS}")
    print(f"Radio       : {RADIO_INICIAL_METROS} m")
    print(f"Paso        : {PASO_MINUTOS} min")
    print(f"Duración    : máximo {DURACION_HORAS} h")
    print(f"Salida NC   : {archivo_nc.name}")

    # EJECUTAR SIMULACIÓN
    modelo.run(
        duration=timedelta(hours=DURACION_HORAS),
        time_step=timedelta(minutes=PASO_MINUTOS),
        time_step_output=timedelta(minutes=SALIDA_MINUTOS),
        outfile=str(archivo_nc),
    )
    print("Simulación finalizada.")

    # VISUALIZACIÓN NATIVA DE OPENDRIFT
    try:
        modelo.plot(
            filename=str(archivo_png),
            buffer=BUFFER_VISUALIZACION,
            show=False,
        )
        print(f"PNG creado  : {archivo_png.name}")
    except Exception as error:
        print(f"ADVERTENCIA: no se pudo crear el PNG de {nombre}:")
        print(error)
    try:
        modelo.animation(
            filename=str(archivo_mp4),
            buffer=BUFFER_VISUALIZACION,
            fps=FPS_VIDEO,
        )
        print(f"MP4 creado  : {archivo_mp4.name}")
    except Exception as error:
        print(f"ADVERTENCIA: no se pudo crear el MP4 de {nombre}:")
        print(error)
        print(
            "El NetCDF permanece guardado. Si el error está relacionado "
            "con FFmpeg, el video puede generarse posteriormente."
        )

# FIN
print("\n" + "=" * 78)
print("PROCESO FINALIZADO")
print("Se procesaron los 3 escenarios complementarios.")
print("Cada escenario genera: NetCDF + PNG + MP4.")
print("=" * 78)

