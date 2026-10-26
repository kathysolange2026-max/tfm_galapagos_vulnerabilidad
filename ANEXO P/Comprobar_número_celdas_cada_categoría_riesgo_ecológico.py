from pathlib import Path
import numpy as np
import rasterio
BASE = Path(
    r"C:\Users\josej\Documents\tfm_galapagos"
    r"\opendrift_resultados\cruce_vulnerabilidad_FINAL"
    r"\RESULTADOS_FINALES_12_MESES"
)
MESES = [
    "enero","febrero","marzo","abril","mayo","junio",
    "julio","agosto","septiembre","octubre","noviembre","diciembre"
]
print("\nVERIFICACIÓN REAL DE CLASES 0-1-2-3\n")
for mes in MESES:
    ruta = BASE / f"04_riesgo_clases_globales_{mes}.tif"
    with rasterio.open(ruta) as src:
        a = src.read(1)
        nodata = src.nodata
    valid = a != nodata if nodata is not None else np.isfinite(a)
    vals, counts = np.unique(a[valid], return_counts=True)
    print(f"{mes.upper():12s} -> ", end="")
    print(", ".join(f"{int(v)}: {int(c)} celdas" for v, c in zip(vals, counts)))

