import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import os

# Archivos NetCDF
archivos = {
    "Enero": "viento_climatologia_enero_2016_2025.nc",
    "Abril": "viento_climatologia_abril_2016_2025.nc",
    "Julio": "viento_climatologia_julio_2016_2025.nc",
    "Octubre": "viento_climatologia_octubre_2016_2025.nc"
}

# Carpeta de salida
salida = "salidas_viento"
os.makedirs(salida, exist_ok=True)

for mes, archivo in archivos.items():
    ds = xr.open_dataset(archivo)

    # Detectar nombres de variables de coordenadas
    if "longitude" in ds.coords:
        lon = ds["longitude"]
    else:
        lon = ds["lon"]

    if "latitude" in ds.coords:
        lat = ds["latitude"]
    else:
        lat = ds["lat"]

    # Variables del viento ERA5
    u = ds["u10"]
    v = ds["v10"]

    # Si existe dimensión temporal, promediar
    if "time" in u.dims:
        u = u.mean(dim="time")
        v = v.mean(dim="time")

    # Magnitud del viento
    velocidad = np.sqrt(u**2 + v**2)

    # Crear malla
    lon2d, lat2d = np.meshgrid(lon, lat)

    # Reducir densidad de flechas
    paso = 3
    lon_q = lon2d[::paso, ::paso]
    lat_q = lat2d[::paso, ::paso]
    u_q = u.values[::paso, ::paso]
    v_q = v.values[::paso, ::paso]

    # Figura
    fig = plt.figure(figsize=(10, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())

    # Extensión aproximada de Galápagos
    ax.set_extent([-92.5, -89.0, -2.2, 1.8], crs=ccrs.PlateCarree())

    # Fondo con velocidad
    pcm = ax.pcolormesh(
        lon, lat, velocidad,
        cmap="viridis",
        shading="auto",
        transform=ccrs.PlateCarree()
    )

    # Flechas del viento
    ax.quiver(
        lon_q, lat_q, u_q, v_q,
        transform=ccrs.PlateCarree(),
        color="black",
        scale=80,
        width=0.002
    )

    # Elementos cartográficos
    ax.coastlines(resolution="10m", linewidth=0.8)
    ax.add_feature(cfeature.LAND, facecolor="lightgray")
    ax.add_feature(cfeature.BORDERS, linestyle=":")
    ax.gridlines(draw_labels=True, linestyle="--", alpha=0.4)

    # Título
    ax.set_title(f"Climatología representativa del viento a 10 m en Galápagos ({mes}, 2016–2025)", fontsize=12)

    # Colorbar
    cbar = plt.colorbar(pcm, ax=ax, orientation="horizontal", pad=0.05, shrink=0.8)
    cbar.set_label("Velocidad del viento a 10 m (m/s)")

    # Guardar
    nombre_salida = os.path.join(salida, f"viento_{mes.lower()}.png")
    plt.savefig(nombre_salida, dpi=300, bbox_inches="tight")
    plt.close()

print("Mapas generados correctamente en la carpeta 'salidas_viento'.") Anexo H
Script de descarga de los datos de presencia AIS 
import asyncio
import os
import pandas as pd
import gfwapiclient as gfw
# Solución para asyncio en Windows
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
# Leer token
with open("token_gfw_tfm_galapagos.txt", "r") as f:
    token = f.readline().strip()
# Crear cliente GFW
gfw_client = gfw.Client(access_token=token)
# Polígono aproximado de Galápagos
galapagos_polygon = {
    "type": "Polygon",
    "coordinates": [[
        [-92.5, -1.5],
        [-92.5, 1.5],
        [-88.0, 1.5],
        [-88.0, -1.5],
        [-92.5, -1.5]
    ]]
}

async def descargar_anio(anio, intentos=3):
    archivo = f"ais_presence_galapagos_{anio}.csv"
    if os.path.exists(archivo):
        print(f"⏭️ {anio} ya existe, se omite.")
        return pd.read_csv(archivo)
    inicio = f"{anio}-01-01"
    fin = f"{anio + 1}-01-01"
    for intento in range(1, intentos + 1):
        try:
            print(f"Descargando AIS Presence {anio}... intento {intento}")
            resultado = await gfw_client.fourwings.create_ais_presence_report(
                spatial_resolution="LOW",
                temporal_resolution="MONTHLY",
                start_date=inicio,
                end_date=fin,
                geojson=galapagos_polygon
            )
            df = resultado.df()
            df["anio"] = anio
            df.to_csv(archivo, index=False)
            print(f"{anio}: {len(df)} registros guardados en {archivo}")
            return df
        except Exception as e:
            print(f"Error en {anio}, intento {intento}: {e}")
    print(f"No se pudo descargar {anio}")
    return pd.DataFrame()
async def main():
    lista_dfs = []

    for anio in range(2016, 2026):
        df = await descargar_anio(anio)
        if not df.empty:
            lista_dfs.append(df)
    df_total = pd.concat(lista_dfs, ignore_index=True)
    df_total.to_csv(
        "ais_presence_galapagos_2016_2025.csv",
        index=False
    )
    print("\nCSV total guardado: ais_presence_galapagos_2016_2025.csv")
    print(f"Total de registros: {len(df_total)}")
    print("\nColumnas:")
    print(df_total.columns)
if __name__ == "__main__":
    asyncio.run(main())
