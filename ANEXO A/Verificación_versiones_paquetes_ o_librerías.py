import sys
import importlib
import importlib.metadata
import platform
import subprocess
print("=" * 65)
print("VERIFICACIÓN DEL ENTORNO COMPUTACIONAL - TFM")
print("=" * 65)
# Python
print(f"\n{'Python':25} {platform.python_version()}")
# Paquetes: nombre mostrado -> (módulo de importación, nombre del paquete)
paquetes = {
    "OpenDrift": ("opendrift", "opendrift"),
    "xarray": ("xarray", "xarray"),
    "netCDF4": ("netCDF4", "netCDF4"),
    "NumPy": ("numpy", "numpy"),
    "Pandas": ("pandas", "pandas"),
    "GeoPandas": ("geopandas", "geopandas"),
    "Rasterio": ("rasterio", "rasterio"),
    "Matplotlib": ("matplotlib", "matplotlib"),
    "Copernicus Marine": ("copernicusmarine", "copernicusmarine"),
    "CDS API": ("cdsapi", "cdsapi"),
}
print("\nVERSIONES DE LIBRERÍAS")
print("-" * 65)
for nombre, (modulo, paquete) in paquetes.items():
    try:
        importlib.import_module(modulo)
        try:
            version = importlib.metadata.version(paquete)
        except importlib.metadata.PackageNotFoundError:
            version = "instalado - versión no identificada"
        print(f"{nombre:25} {version}")
    except Exception as e:
        print(f"{nombre:25} NO DISPONIBLE ({type(e).__name__})")
# GDAL
print("\nGDAL")
print("-" * 65)
try:
    from osgeo import gdal
    print(f"{'GDAL':25} {gdal.VersionInfo('--version')}")
except Exception:
    try:
        resultado = subprocess.run(
            ["gdalinfo", "--version"],
            capture_output=True,
            text=True,
            check=False
        )
        if resultado.stdout.strip():
            print(f"{'GDAL':25} {resultado.stdout.strip()}")
        else:
            print(f"{'GDAL':25} NO DISPONIBLE")
    except Exception:
        print(f"{'GDAL':25} NO DISPONIBLE")
# Información del entorno
print("\nINFORMACIÓN DEL ENTORNO")
print("-" * 65)
print(f"{'Ejecutable Python:':25} {sys.executable}")
print(f"{'Sistema operativo:':25} {platform.platform()}")
try:
    import os
    entorno = os.environ.get("CONDA_DEFAULT_ENV", "No identificado")
    prefijo = os.environ.get("CONDA_PREFIX", "No identificado")
    print(f"{'Entorno Conda:':25} {entorno}")
    print(f"{'Ruta Conda:':25} {prefijo}")
except Exception:
    pass
print("\n" + "=" * 65)
print("FIN DE LA VERIFICACIÓN")
print("=" * 65)
