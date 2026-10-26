Dataset: cmems_mod_glo_phy_my_0.083deg_P1D-m (GLORYS12V1)
Extensión espacial: -93,7° ; -87,5° ; -3,5° ; 3,5°
Variables: uo y vo
Periodo: 01/01/2016 – 31/12/2025 
import os
import copernicusmarine
base_salida = r"C:\Users\josej\Documents\tfm_galapagos\datos_ambientales\copernicus"

meses = [
    ("enero", 1), ("febrero", 2), ("marzo", 3), ("abril", 4),
    ("mayo", 5), ("junio", 6), ("julio", 7), ("agosto", 8),
    ("septiembre", 9), ("octubre", 10), ("noviembre", 11), ("diciembre", 12)
]
anios = range(2016, 2026)

for anio in anios:
    for nombre_mes, mes_num in meses:
        carpeta_mes = os.path.join(base_salida, nombre_mes)
        os.makedirs(carpeta_mes, exist_ok=True)
        archivo = f"corrientes_{nombre_mes}_{anio}.nc"
        ruta_archivo = os.path.join(carpeta_mes, archivo)
        if os.path.exists(ruta_archivo):
            print(f"Ya existe: {archivo}")
            continue
        inicio = f"{anio}-{mes_num:02d}-01T00:00:00"
        if mes_num == 12:
            fin = f"{anio+1}-01-01T00:00:00"
        else:
            fin = f"{anio}-{mes_num+1:02d}-01T00:00:00"
        print(f"\nDescargando {nombre_mes} {anio}...")
        print(f"{inicio} → {fin}")
        copernicusmarine.subset(
            dataset_id="cmems_mod_glo_phy_my_0.083deg_P1D-m",
            variables=["uo", "vo"],
            minimum_longitude=-93.5,
            maximum_longitude=-87.5,
            minimum_latitude=-3.5,
            maximum_latitude=3.5,
            minimum_depth=0.49402499198913574,
            maximum_depth=0.49402499198913574,
            start_datetime=inicio,
            end_datetime=fin,
            output_directory=carpeta_mes,
            output_filename=archivo,
            overwrite=False
        )
print("\nDescarga Copernicus 2016–2025 completada.")
