Extensión espacial: -93,7° ; -87,5° ; -3,5° ; 3,5°
Variables: uo y vo
Datos de entrada: Corrientes mensuales de cada año
Periodo: 2016 – 2025
from pathlib import Path
import calendar
import pandas as pd
import xarray as xr

# CONFIGURACIÓN
CARPETA_ENTRADA = Path(
    r"C:\Users\josej\Documents\tfm_galapagos"
    r"\datos_ambientales\copernicus"
)
CARPETA_SALIDA = Path(
    r"C:\Users\josej\Documents\tfm_galapagos"
    r"\datos_ambientales\climatologias\corrientes"
)
CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)
MESES = [
    ("enero", 1), ("febrero", 2), ("marzo", 3), ("abril", 4),
    ("mayo", 5), ("junio", 6), ("julio", 7), ("agosto", 8),
    ("septiembre", 9), ("octubre", 10), ("noviembre", 11), ("diciembre", 12),
]
ANIOS = range(2016, 2026)
# Año sintético que empelaremos en la fase de simulación con OpenDrift.
ANIO_REFERENCIA = 2024

# PROCESAR CADA ARCHIVO
def preparar_archivo(
    ruta: Path,
    anio: int,
    numero_mes: int,
) -> xr.Dataset:
    """
    Abre un archivo Copernicus mensual, elimina cualquier fecha
    perteneciente al mes siguiente y agrupa por día del mes.
    """
    with xr.open_dataset(ruta) as original:
        variables_requeridas = {"uo", "vo"}
        faltantes = variables_requeridas.difference(original.data_vars)
        if faltantes:
            raise ValueError(
                f"{ruta.name} no contiene las variables: "
                f"{sorted(faltantes)}"
            )

        if "time" not in original.coords:
            raise ValueError(
                f"{ruta.name} no contiene la coordenada temporal 'time'."
            )
        ds = original[["uo", "vo"]]

        # FILTRO PRINCIPAL
        # Mantiene únicamente el mes y año que corresponde al nombre del archivo.
        mascara_mes = (
            (ds["time"].dt.year == anio)
            & (ds["time"].dt.month == numero_mes)
        )
        ds = ds.where(mascara_mes, drop=True)
        if ds.sizes.get("time", 0) == 0:
            raise ValueError(
                f"{ruta.name} no contiene fechas válidas para "
                f"{anio}-{numero_mes:02d}."
            )
        # Si hubiera múltiples registros en el mismo día,
        # se calcula primero su promedio diario.
        ds_diario = ds.groupby("time.day").mean(
            dim="time",
            skipna=True,
            keep_attrs=True,
        )
 # Realizar una copia en memoria de los datos para proceder a cerrar el archivo.
        ds_diario = ds_diario.load()
    # Agregar una dimensión del año de procedencia.
    ds_diario = ds_diario.expand_dims(
        anio_muestra=[anio]
    )
    return ds_diario

# CONSTRUIR CLIMATOLOGÍA DE UN MES
def construir_climatologia_mes(
    nombre_mes: str,
    numero_mes: int,
) -> Path:
    datasets = []
    archivos_usados = []
    print("\n" + "=" * 65)
    print(f"Procesando climatología de {nombre_mes}")
    print("=" * 65)
    for anio in ANIOS:
        ruta = (
            CARPETA_ENTRADA
            / nombre_mes
            / f"corrientes_{nombre_mes}_{anio}.nc"
        )
        if not ruta.exists():
            print(f"Falta: {ruta}")
            continue
        try:
            ds_anio = preparar_archivo(
                ruta=ruta,
                anio=anio,
                numero_mes=numero_mes,
            )
            datasets.append(ds_anio)
            archivos_usados.append(ruta.name)
            print(
                f"{anio}: "
                f"{ds_anio.sizes.get('day', 0)} días válidos"
            )
        except Exception as error:
            print(
                f"No se pudo procesar "
                f"{ruta.name}: {error}"
            )
    if not datasets:
        raise RuntimeError(
            f"No se encontraron archivos válidos para {nombre_mes}."
        )

    # Unir los diez años por la dimensión anio_muestra.
    combinado = xr.concat(
        datasets,
        dim="anio_muestra",
        join="outer",
        compat="override",
        coords="minimal",
    )

    # Promedio climatológico para cada día del mes.
    climatologia = combinado.mean(
        dim="anio_muestra",
        skipna=True,
        keep_attrs=True,
    )
    numero_dias = calendar.monthrange(
        ANIO_REFERENCIA,
        numero_mes,
    )[1]

    # Reindexar asegura un eje ordenado desde día 1 hasta
    # el último día del mes sintético.
    climatologia = climatologia.reindex(
        day=range(1, numero_dias + 1)
    )
    fechas_sinteticas = pd.date_range(
        start=(
            f"{ANIO_REFERENCIA}-"
            f"{numero_mes:02d}-01"
        ),
        periods=numero_dias,
        freq="D",
    )
    # Convertir nuevamente la dimensión 'day' en 'time'.
    climatologia = climatologia.rename(
        {"day": "time"}
    )
    climatologia = climatologia.assign_coords(
        time=("time", fechas_sinteticas)
    )
    # Orden recomendado para facilitar la lectura posterior.
    orden_dimensiones = [
        dimension
        for dimension in [
            "time",
            "depth",
            "latitude",
            "longitude",
        ]
        if dimension in climatologia.dims
    ]
    climatologia = climatologia.transpose(
        *orden_dimensiones
    )

        # METADATOS CF
    climatologia["uo"].attrs.update({
        "long_name": (
            "Climatological eastward sea water velocity"
        ),
        "standard_name": (
            "eastward_sea_water_velocity"
        ),
        "units": "m s-1",
    })
    climatologia["vo"].attrs.update({
        "long_name": (
            "Climatological northward sea water velocity"
        ),
        "standard_name": (
            "northward_sea_water_velocity"
        ),
        "units": "m s-1",
    })
    climatologia["time"].attrs.update({
        "long_name": (
            "Synthetic time for daily monthly climatology"
        ),
        "comment": (
            "Synthetic 2024 calendar assigned to the "
            "2016-2025 daily climatological sequence."
        ),
    })
    climatologia.attrs.update({
        "title": (
            f"Climatología diaria de corrientes de "
            f"{nombre_mes} para Galápagos"
        ),
        "source": (
            "Copernicus Marine GLORYS12V1"
        ),
        "dataset_id": (
            "cmems_mod_glo_phy_my_0.083deg_P1D-m"
        ),
        "climatology_period": "2016-2025",
        "reference_year": str(ANIO_REFERENCIA),
        "method": (
            "Promedio multianual por día del mes de los "
            "campos diarios superficiales uo y vo. "
            "Antes del promedio se eliminaron fechas "
            "correspondientes al mes siguiente."
        ),
        "number_of_years": str(len(datasets)),
        "files_used": ", ".join(archivos_usados),
        "Conventions": "CF-1.8",
    })
    salida = (
        CARPETA_SALIDA
        / (
            f"corrientes_climatologia_{nombre_mes}"
            f"_2016_2025.nc"
        )
    )
    codificacion = {
        "uo": {
            "zlib": True,
            "complevel": 4,
            "dtype": "float32",
        },
        "vo": {
            "zlib": True,
            "complevel": 4,
            "dtype": "float32",
        },
        "time": {
            "dtype": "int32",
            "units": (
                "days since 2024-01-01 00:00:00"
            ),
            "calendar": "proleptic_gregorian",
        },
    }
    climatologia.to_netcdf(
        salida,
        engine="netcdf4",
        encoding=codificacion,
    )
    combinado.close()
    climatologia.close()
    for ds in datasets:
        ds.close()
    print(f"Climatología guardada: {salida}")
    return salida

# EJECUCIÓN PRINCIPAL
def main() -> None:
    generados = []
    fallidos = []
    for nombre_mes, numero_mes in MESES:
        try:
            salida = construir_climatologia_mes(
                nombre_mes=nombre_mes,
                numero_mes=numero_mes,
            )
            generados.append(salida.name)
        except Exception as error:
            fallidos.append(
                (nombre_mes, str(error))
            )
            print(
                f"Error general en {nombre_mes}: "
                f"{error}"
            )
    print("\n" + "=" * 65)
    print("RESUMEN DE CLIMATOLOGÍAS DE CORRIENTES")
    print("=" * 65)
    print(f"Generadas: {len(generados)}")
    print(f"Fallidas: {len(fallidos)}")
    if generados:
        print("\nArchivos generados:")
        for archivo in generados:
            print(f"{archivo}")
    if fallidos:
        print("\nMeses fallidos:")
        for mes, error in fallidos:
            print(f"{mes}: {error}")
if __name__ == "__main__":
    main()

