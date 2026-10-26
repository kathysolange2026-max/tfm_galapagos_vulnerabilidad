import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np

archivos = {
    "Enero": "corrientes_climatologia_enero_2016_2025.nc",
    "Abril": "corrientes_climatologia_abril_2016_2025.nc",
    "Julio": "corrientes_climatologia_julio_2016_2025.nc",
    "Octubre": "corrientes_climatologia_octubre_2016_2025.nc"
}

for mes, archivo in archivos.items():
    ds = xr.open_dataset(archivo)

    u = ds["uo"].isel(time=0, depth=0)
    v = ds["vo"].isel(time=0, depth=0)

    lon = ds["longitude"]
    lat = ds["latitude"]

    mag = np.sqrt(u**2 + v**2)

    fig = plt.figure(figsize=(8, 7))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_extent([-92, -88, -2, 2], crs=ccrs.PlateCarree())

    pcm = ax.pcolormesh(lon, lat, mag, transform=ccrs.PlateCarree(), shading="auto")
    ax.quiver(
        lon[::3], lat[::3],
        u.values[::3, ::3], v.values[::3, ::3],
        transform=ccrs.PlateCarree(),
        scale=8, color="black", width=0.002
    )

    ax.add_feature(cfeature.LAND, facecolor="lightgray")
    ax.add_feature(cfeature.COASTLINE, linewidth=0.5)

    plt.colorbar(pcm, ax=ax, orientation="horizontal", pad=0.05, label="Magnitud de la corriente (m/s)")
    ax.set_title(f"Climatología representativa de corrientes superficiales - {mes} (2016–2025)")

    plt.savefig(f"corrientes_{mes.lower()}.png", dpi=300, bbox_inches="tight")
    plt.close()
