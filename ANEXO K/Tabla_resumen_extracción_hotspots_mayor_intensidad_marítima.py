import pandas as pd
entrada = r"C:\Users\josej\Documents\tfm_galapagos\capas\hotspots_ais_zonas_ampliadas.csv"
salida = r"C:\Users\josej\Documents\tfm_galapagos\capas\resumen_hotspots_ais_por_zona.csv"
df = pd.read_csv(entrada)
tipos = {
    "Canal_Itabaca_Baltra": "Principal",
    "Puerto_Ayora_Santa_Cruz": "Secundario",
    "Puerto_Baquerizo_San_Cristobal": "Secundario / validación histórica",
    "Wolf_Darwin_Norte": "Secundario",
    "Isabela_Norte": "Secundario",
    "Isabela_Sur": "Secundario",
    "Canal_Isabela_Fernandina": "Secundario",
    "Isla_Pinta": "Exploratorio"
}
resultados = []
for zona, grupo in df.groupby("zona"):
    fila_max = grupo.loc[grupo["horas_promedio"].idxmax()]
    resultados.append({
        "zona": zona,
        "tipo": tipos.get(zona, "Secundario"),
        "promedio_horas_promedio": round(grupo["horas_promedio"].mean(), 3),
        "maximo_horas_promedio": round(grupo["horas_promedio"].max(), 3),
        "mes_mayor_intensidad": fila_max["mes"],
        "lat_representativa": fila_max["lat"],
        "lon_representativa": fila_max["lon"],
        "promedio_embarcaciones": round(grupo["embarcaciones"].mean(), 1),
        "maximo_embarcaciones": grupo["embarcaciones"].max()
    })
resumen = pd.DataFrame(resultados)
resumen = resumen.sort_values("promedio_horas_promedio", ascending=False)
resumen.to_csv(salida, index=False, encoding="utf-8-sig")
print("Archivo generado:")
print(salida)
print(resumen)

