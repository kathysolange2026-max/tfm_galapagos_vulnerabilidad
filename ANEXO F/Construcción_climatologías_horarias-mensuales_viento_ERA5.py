Extensión espacial: -93,7° ; -87,5° ; -3,5° ; 3,5°
Variables: u10 y v10
Datos de entrada: Viento ERA5 mensuales de cada año
Periodo: 2016 – 2025
from pathlib import Path
import calendar

import pandas as pd
import xarray as xr

# CONFIGURACIÓN
CARPETA_ENTRADA = Path(
    r"C:\Users\josej\Documents\tfm_galapagos"
    r"\datos_ambientales\era5"
)
CARPETA_SALIDA = Path(
    r"C:\Users\josej\Documents\tfm_galapagos"
    r"\datos_ambientales\climatologias\viento"
)
CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)
MESES = [
    ("enero", 1), ("febrero", 2), ("marzo", 3), ("abril", 4),
    ("mayo", 5), ("junio", 6), ("julio", 7), ("agosto", 8),
    ("septiembre", 9), ("octubre", 10), ("noviembre", 11), ("diciembre", 12),
]
ANIOS = range(2016, 2026)
# Calendario sintético que utilizará OpenDrift.
ANIO_REFERENCIA = 2024

# PREPARAR UN ARCHIVO ERA5
def preparar_archivo(
    ruta: Path,
    anio: int,
    numero_mes: int,
) -> xr.Dataset:
    """
    Abre un archivo mensual ERA5, conserva únicamente el mes
    correspondiente y lo organiza por hora climatológica del mes.
    """

    with xr.open_dataset(ruta) as original:
        variables_requeridas = {"u10", "v10"}
        faltantes = variables_requeridas.difference(original.data_vars)
        if faltantes:
            raise ValueError(
                f"{ruta.name} no contiene las variables requeridas: "
                f"{sorted(faltantes)}"
            )

        # ERA5 descargado desde CDS usa normalmente valid_time.
        if "valid_time" in original.coords:
            nombre_tiempo = "valid_time"
        elif "time" in original.coords:
            nombre_tiempo = "time"
        else:
            raise ValueError(
                f"{ruta.name} no contiene valid_time ni time."
            )
        ds = original[["u10", "v10"]]
        # Eliminar coordenadas auxiliares que no necesitamos.
        coordenadas_auxiliares = [
            coord
            for coord in ["expver", "number"]
            if coord in ds.coords
        ]
        if coordenadas_auxiliares:
            ds = ds.drop_vars(
                coordenadas_auxiliares,
                errors="ignore",
            )
        tiempo = ds[nombre_tiempo]
        # Conservar únicamente el año y mes correctos.
        mascara = (
            (tiempo.dt.year == anio)
            & (tiempo.dt.month == numero_mes)
        )
        ds = ds.where(mascara, drop=True)
        if ds.sizes.get(nombre_tiempo, 0) == 0:
            raise ValueError(
                f"{ruta.name} no contiene datos válidos para "
                f"{anio}-{numero_mes:02d}."
            )

        # Índice horario dentro del mes:
        # 0 = día 1, 00:00
        # 1 = día 1, 01:00
        # ...
        # 24 = día 2, 00:00
        indice_hora = (
            (ds[nombre_tiempo].dt.day - 1) * 24
            + ds[nombre_tiempo].dt.hour
        ).values
        ds = ds.assign_coords(
            hora_mes=(nombre_tiempo, indice_hora)
        )

        # Si hubiera tiempos repetidos, se promedian.
        ds_horario = ds.groupby("hora_mes").mean(
            dim=nombre_tiempo,
            skipna=True,
            keep_attrs=True,
        )
        ds_horario = ds_horario.load()
    ds_horario = ds_horario.expand_dims(
        anio_muestra=[anio]
    )
    return ds_horario

# CONSTRUIR CLIMATOLOGÍA DE UN MES
def construir_climatologia_mes(
    nombre_mes: str,
    numero_mes: int,
) -> Path:
    datasets = []
    archivos_usados = []
    print("\n" + "=" * 68)
    print(f"Procesando climatología ERA5 de {nombre_mes}")
    print("=" * 68)
    for anio in ANIOS:
        ruta = (
            CARPETA_ENTRADA
            / nombre_mes
            / f"viento_{nombre_mes}_{anio}.nc"
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
                f"{ds_anio.sizes.get('hora_mes', 0)} "
                f"horas válidas"
            )
        except Exception as error:
            print(
                f"No se pudo procesar {ruta.name}: {error}"
            )

    if not datasets:
        raise RuntimeError(
            f"No existen archivos válidos para {nombre_mes}."
        )
    combinado = xr.concat(
        datasets,
        dim="anio_muestra",
        join="outer",
        compat="override",
        coords="minimal",
    )
    # Promedio 2016–2025 para cada hora del mes.
    climatologia = combinado.mean(
        dim="anio_muestra",
        skipna=True,
        keep_attrs=True,
    )
    numero_dias = calendar.monthrange(
        ANIO_REFERENCIA,
        numero_mes,
    )[1]
    numero_horas = numero_dias * 24
    # Asegurar que existan todas las horas del mes sintético.
    climatologia = climatologia.reindex(
        hora_mes=range(numero_horas)
    )
    fechas_sinteticas = pd.date_range(
        start=f"{ANIO_REFERENCIA}-{numero_mes:02d}-01 00:00:00",
        periods=numero_horas,
        freq="h",
    )
    climatologia = climatologia.rename(
        {"hora_mes": "time"}
    )
    climatologia = climatologia.assign_coords(
        time=("time", fechas_sinteticas)
    )
    # Orden estándar para facilitar la lectura en OpenDrift.
    climatologia = climatologia.transpose(
        "time",
        "latitude",
        "longitude",
    )

    # METADATOS CF
    climatologia["u10"].attrs.update({
        "long_name": (
            "Climatological eastward wind velocity at 10 metres"
        ),
        "standard_name": "eastward_wind",
        "units": "m s-1",
        "height": "10 m",
    })
    climatologia["v10"].attrs.update({
        "long_name": (
            "Climatological northward wind velocity at 10 metres"
        ),
        "standard_name": "northward_wind",
        "units": "m s-1",
        "height": "10 m",
    })
    climatologia["latitude"].attrs.update({
        "standard_name": "latitude",
        "units": "degrees_north",
    })
    climatologia["longitude"].attrs.update({
        "standard_name": "longitude",
        "units": "degrees_east",
    })
    climatologia["time"].attrs.update({
        "long_name": (
            "Synthetic time for hourly monthly climatology"
        ),
        "comment": (
            "Synthetic 2024 calendar assigned to the "
            "2016-2025 hourly climatological sequence."
        ),
    })
    climatologia.attrs.update({
        "title": (
            f"Climatología horaria de viento ERA5 de "
            f"{nombre_mes} para Galápagos"
        ),
        "source": (
            "ERA5 hourly data on single levels"
        ),
        "dataset_id": (
            "reanalysis-era5-single-levels"
        ),
        "climatology_period": "2016-2025",
        "reference_year": str(ANIO_REFERENCIA),
        "method": (
            "Promedio multianual para cada combinación de "
            "día del mes y hora del día de los componentes "
            "u10 y v10."
        ),
        "number_of_years": str(len(datasets)),
        "files_used": ", ".join(archivos_usados),
        "Conventions": "CF-1.8",
    })
    salida = (
        CARPETA_SALIDA
        / (
            f"viento_climatologia_{nombre_mes}"
            f"_2016_2025.nc"
        )
    )
    codificacion = {
        "u10": {
            "zlib": True,
            "complevel": 4,
            "dtype": "float32",
        },
        "v10": {
            "zlib": True,
            "complevel": 4,
            "dtype": "float32",
        },
        "time": {
            "dtype": "int32",
            "units": (
                "hours since 2024-01-01 00:00:00"
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

# EJECUCIÓN
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
            fallidos.append((nombre_mes, str(error)))
            print(
                f"Error general en {nombre_mes}: {error}"
            )
    print("\n" + "=" * 68)
    print("RESUMEN DE CLIMATOLOGÍAS DE VIENTO ERA5")
    print("=" * 68)
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
