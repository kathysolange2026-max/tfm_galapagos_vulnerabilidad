from datetime import datetime, timedelta
from pathlib import Path
import sys
import xarray as xr
from opendrift.models.openoil import OpenOil
from opendrift.readers import reader_netCDF_CF_generic

# CONFIGURACIÓN GENERAL
BASE = Path(
    r"C:\Users\josej\Documents\tfm_galapagos"
)
ARCHIVO_CORRIENTES = (
    BASE
    / "datos_ambientales"
    / "climatologias"
    / "corrientes"
    / "corrientes_climatologia_enero_2016_2025.nc"
)
ARCHIVO_VIENTO = (
    BASE
    / "datos_ambientales"
    / "climatologias"
    / "viento"
    / "viento_climatologia_enero_2016_2025.nc"
)
CARPETA_SALIDA = (
    BASE
    / "opendrift_resultados"
    / "prueba_final"
)
CARPETA_SALIDA.mkdir(
    parents=True,
    exist_ok=True
)
ARCHIVO_SALIDA = (
    CARPETA_SALIDA
    / "sensibilidad_dt15_sin_incertidumbre.nc"
)

# PARÁMETROS DEL ESCENARIO
# Punto final de Itabaca/Baltra verificado en QGIS.
LATITUD = -0.487890
LONGITUD = -90.285050
# Fecha sintética de la climatología de enero.
FECHA_INICIO = datetime(
    2024,
    1,
    15,
    0,
    0,
    0
)
# Número de elementos lagrangianos.
NUMERO_PARTICULAS = 1000
# Radio alrededor del punto inicial.
RADIO_INICIAL_METROS = 0
# Volumen total del derrame hipotético.
VOLUMEN_DERRAME_M3 = 10.0
# Duración de la simulación.
DURACION_HORAS = 72
# Tipo de hidrocarburo seleccionado.
TIPO_PETROLEO = "GENERIC MEDIUM CRUDE"
# Paso interno de integración.
PASO_MINUTOS = 5
# Frecuencia de almacenamiento de resultados.
SALIDA_MINUTOS = 5

# FUNCIONES
def verificar_archivos() -> None:
    """
    Comprueba que existan los archivos de corrientes
    y viento antes de iniciar la simulación.
    """

    faltantes = []
    if not ARCHIVO_CORRIENTES.exists():
        faltantes.append(
            str(ARCHIVO_CORRIENTES)
        )
    if not ARCHIVO_VIENTO.exists():
        faltantes.append(
            str(ARCHIVO_VIENTO)
        )
    if faltantes:
        print(
            "\nERROR: faltan los siguientes archivos:"
        )
        for ruta in faltantes:
            print(f" - {ruta}")
        sys.exit(1)
def inspeccionar_resultado(
    ruta: Path
) -> None:
    """
    Muestra un resumen básico del NetCDF
    generado por OpenDrift.
    """
    if not ruta.exists():
        raise FileNotFoundError(
            f"No se generó el archivo esperado: {ruta}"
        )

    if ruta.stat().st_size == 0:
        raise RuntimeError(
            "El archivo de salida existe, "
            "pero está vacío."
        )
    with xr.open_dataset(ruta) as ds:
        print(
            "\n"
            + "=" * 70
        )
        print(
            "VALIDACIÓN DEL ARCHIVO DE SALIDA"
        )
        print(
            "=" * 70
        )
        print(ds)
        print(
            "\nTamaño del archivo: "
            f"{ruta.stat().st_size / 1024**2:.2f} MB"
        )
        
        # Dimensiones
        if "trajectory" in ds.sizes:
            print(
                "Número de trayectorias guardadas: "
                f"{ds.sizes['trajectory']}"
            )
        if "time" in ds.sizes:
            print(
                "Número de tiempos guardados: "
                f"{ds.sizes['time']}"
            )

        # Posición inicial y final
                if (
            "lon" in ds.variables
            and "lat" in ds.variables
        ):
            lon_inicial = (
                ds["lon"]
                .isel(time=0)
                .mean(skipna=True)
                .item()
            )
            lat_inicial = (
                ds["lat"]
                .isel(time=0)
                .mean(skipna=True)
                .item()
            )
            lon_final = (
                ds["lon"]
                .isel(time=-1)
                .mean(skipna=True)
                .item()
            )
            lat_final = (
                ds["lat"]
                .isel(time=-1)
                .mean(skipna=True)
                .item()
            )
            print(
                f"Longitud media inicial: "
                f"{lon_inicial:.6f}"
            )
            print(
                f"Latitud media inicial: "
                f"{lat_inicial:.6f}"
            )
            print(
                f"Longitud media final: "
                f"{lon_final:.6f}"
            )
            print(
                f"Latitud media final: "
                f"{lat_final:.6f}"
            )

        # Rango temporal
        if "time" in ds.coords:
            print(
                "Primer tiempo guardado: "
                f"{ds['time'].values[0]}"
            )
            print(
                "Último tiempo guardado: "
                f"{ds['time'].values[-1]}"
            )

        # Estados de las partículas
        if "status" in ds.variables:
           estado_final = (
                ds["status"]
                .isel(time=-1)
                .values
            )
            import numpy as np
           valores, conteos = np.unique(
                estado_final[
                    ~np.isnan(estado_final)
                ],
                return_counts=True
            )
            print(
                "\nEstados finales "
                "almacenados en el NetCDF:"
            )
            for valor, cantidad in zip(
                valores,
                conteos
            ):
                print(
                    f"  Estado {valor}: "
                    f"{cantidad} partículas"
                )
# SIMULACIÓN
def main():
    print(
        "\n"
        + "=" * 70
    )
    print(
        "PRUEBA FINAL OPENOIL - ITABACA - ENERO"
    )
    print(
        "=" * 70
    )
    print(
        f"Punto inicial: "
        f"{LATITUD}, {LONGITUD}"
    )
    print(
        f"Fecha inicial: "
        f"{FECHA_INICIO}"
    )
    print(
        f"Partículas: "
        f"{NUMERO_PARTICULAS}"
    )
    print(
        f"Volumen del derrame: "
        f"{VOLUMEN_DERRAME_M3} m³"
    )
    print(
        f"Tipo de petróleo: "
        f"{TIPO_PETROLEO}"
    )
    print(
        f"Radio inicial: "
        f"{RADIO_INICIAL_METROS} m"
    )
    print(
        f"Duración: "
        f"{DURACION_HORAS} horas"
    )
    print(
        f"Paso interno: "
        f"{PASO_MINUTOS} minutos"
    )
    print(
        f"Salida: cada "
        f"{SALIDA_MINUTOS} minutos"
    )
    
    # COMPROBAR ARCHIVOS
    verificar_archivos()
    # CREAR MODELO
    print(
        "\nInicializando OpenOil..."
    )
    modelo = OpenOil(
        loglevel=20
    )
 
    # PRUEBA DE SENSIBILIDAD TEMPORAL
    # Sin incertidumbre estocástica
    modelo.set_config("drift:current_uncertainty", 0)
    modelo.set_config("drift:wind_uncertainty", 0)
    print("\nCONFIGURACIÓN DE INCERTIDUMBRE")
    print("Current uncertainty:",
      modelo.get_config("drift:current_uncertainty"))
    print("Wind uncertainty:",
      modelo.get_config("drift:wind_uncertainty"))
    
    # CARGAR CORRIENTES
    print(
        "\nCargando climatología "
        "de corrientes..."
    )
    lector_corrientes = (
        reader_netCDF_CF_generic.Reader(
            str(
                ARCHIVO_CORRIENTES
            )
        )
    )
    
    # CARGAR VIENTO
    print(
        "Cargando climatología "
        "de viento..."
    )
    lector_viento = (
        reader_netCDF_CF_generic.Reader(
            str(
                ARCHIVO_VIENTO
            )
        )
    )
 
    # AÑADIR LECTORES
     modelo.add_reader(
        [
            lector_corrientes,
            lector_viento,
        ]
    )

    # CONFIGURACIÓN DEL MODELO
    # Meteorización
    # En esta etapa el estudio se concentra en el transporte
    # superficial y el alcance espacial potencial del derrame.
    # No se simulan explícitamente procesos de meteorización
    # que requerirían información ambiental adicional.
       modelo.set_config(
        "processes:evaporation",
        False
    )
    modelo.set_config(
        "processes:emulsification",
        False
    )
    modelo.set_config(
        "processes:dispersion",
        False
    )
    modelo.set_config(
        "drift:vertical_mixing",
        False
    )


    # INTERACCIÓN CON LA COSTA
        modelo.set_config(
        "general:coastline_action",
        "stranding"
    )

    # VARIABLES AMBIENTALES DE RESPALDO
    # Las climatologías utilizadas contienen corrientes
    # superficiales y viento.
    # Las variables siguientes no son forzantes principales
    # del escenario definido y se mantienen en cero.
    modelo.set_config(
        "environment:fallback:"
        "sea_surface_height",
        0.0
    )
    modelo.set_config(
        "environment:fallback:"
        "upward_sea_water_velocity",
        0.0
    )
    modelo.set_config(
        "environment:fallback:"
        "sea_surface_wave_significant_height",
        0.0
    )
    modelo.set_config(
        "environment:fallback:"
        "sea_surface_wave_stokes_drift_x_velocity",
        0.0
    )
    modelo.set_config(
        "environment:fallback:"
        "sea_surface_wave_stokes_drift_y_velocity",
        0.0
    )

    # LIBERACIÓN DEL DERRAME
    print(
        "\nSembrando partículas..."
    )
    modelo.seed_elements(
        lon=LONGITUD,
        lat=LATITUD,
        # Radio máximo alrededor
        # del punto seleccionado.
        radius=RADIO_INICIAL_METROS,
        # Distribución uniforme para
        # mantener las partículas dentro
        # del radio especificado.
        radius_type="uniform",

        number=NUMERO_PARTICULAS,
        # Liberación instantánea.
        time=FECHA_INICIO,
        # Derrame superficial.
        z=0,
        oil_type=TIPO_PETROLEO,
        # Al tratarse de una liberación
        # instantánea, OpenOil interpreta
        # este valor como volumen total.
        m3_per_hour=VOLUMEN_DERRAME_M3,
    )

    # EJECUTAR MODELO
    print(
        "\nEjecutando simulación..."
    )
    modelo.run(
        duration=timedelta(
            hours=DURACION_HORAS
        ),
        time_step=timedelta(
            minutes=PASO_MINUTOS
        ),
        time_step_output=timedelta(
            minutes=SALIDA_MINUTOS
        ),
        outfile=str(
            ARCHIVO_SALIDA
        ),
    )

    # RESULTADO
    print(
        "\n"
        + "=" * 70
    )
    print(
        "SIMULACIÓN FINALIZADA"
    )
    print(
        "=" * 70
    )
    print(
        f"Archivo generado:\n"
        f"{ARCHIVO_SALIDA}"
    )
    inspeccionar_resultado(
        ARCHIVO_SALIDA
    )

# EJECUCIÓN
if __name__ == "__main__":
    main()
