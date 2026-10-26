# tfm_galapagos_vulnerabilidad
Vulnerabilidad de la fauna marina ante derrames de hidrocarburos en las Islas Galápagos
Trabajo Fin de Máster (TFM)

Autora: Katheryne Solange Campaña Vaca
Año: 2026
Área de estudio: Reserva Marina de Galápagos, Ecuador
Periodo de análisis: 2016–2025
Lenguaje de programación: Python
Repositorio: tfm_galapagos_vulnerabilidad

1. Descripción del proyecto
Este repositorio contiene los scripts desarrollados y utilizados en el Trabajo Fin de Máster sobre la evaluación de la vulnerabilidad de la fauna marina ante posibles derrames de hidrocarburos en las Islas Galápagos.
La investigación integra información sobre tráfico marítimo, distribución espacial de especies marinas y simulaciones de transporte de hidrocarburos, con el propósito de identificar áreas potencialmente expuestas y aportar información técnica para la prevención, preparación y respuesta ante eventos de contaminación marina.
Los códigos se encuentran organizados de acuerdo con los anexos metodológicos de la investigación, permitiendo consultar los procedimientos computacionales empleados.

2. Objetivo del repositorio
Facilitar el acceso, la revisión y la reproducibilidad de los procedimientos computacionales utilizados en la investigación, incluyendo:
Procesamiento y análisis de datos de tráfico marítimo mediante AIS.
Tratamiento de registros de presencia de fauna marina procedentes de GBIF.
Elaboración de superficies de densidad mediante estimación de densidad de Kernel (KDE).
Normalización y ponderación de indicadores de vulnerabilidad.
Construcción de un índice espacial integrado de vulnerabilidad de fauna marina.
Simulación de trayectorias de derrames de hidrocarburos utilizando OpenDrift/OpenOil.
Análisis espacial de exposición y riesgo.
Evaluación de sensibilidad de los parámetros de simulación.

3. Metodología general
La metodología de la investigación se estructura en cuatro componentes principales.
Análisis del tráfico marítimo: procesamiento de información AIS para caracterizar la distribución espacial y temporal de la actividad de las embarcaciones e identificar zonas de interés para la simulación de derrames.
Evaluación de vulnerabilidad de fauna marina: integración de registros de presencia de especies mediante técnicas de análisis espacial, estimación de densidad Kernel, normalización y suma ponderada de indicadores.
Simulación de derrames de hidrocarburos: aplicación del modelo OpenDrift/OpenOil para representar el transporte y destino de partículas de hidrocarburos bajo diferentes condiciones ambientales y escenarios geográficos.
Análisis espacial del riesgo: integración de los resultados de las simulaciones con el índice de vulnerabilidad de fauna marina, permitiendo identificar las áreas de mayor exposición potencial.

4. Organización de los anexos digitales
Los scripts se organizan en carpetas identificadas mediante la misma denominación utilizada en los anexos del Trabajo Fin de Máster.
Cada carpeta contiene los archivos correspondientes a los procedimientos computacionales descritos en la metodología.
La numeración y denominación de las carpetas se corresponden con las referencias a los anexos digitales realizadas en el documento académico.

5. Entorno computacional
Los procedimientos fueron desarrollados principalmente en Python, mediante bibliotecas especializadas en procesamiento de datos, análisis espacial y simulación numérica.
Entre las herramientas utilizadas se encuentra OpenDrift/OpenOil, empleado para las simulaciones de derrames de hidrocarburos.
Las versiones específicas de las bibliotecas y dependencias utilizadas se documentan mediante los scripts de verificación del entorno computacional.

6. Reproducibilidad y disponibilidad de datos
Los scripts se publican con fines académicos, de transparencia metodológica y reproducibilidad científica.
La ejecución de determinados procedimientos requiere disponer de los datos de entrada correspondientes, incluidos registros de tráfico marítimo, observaciones de fauna marina e información ambiental.
La disponibilidad y reutilización de estos datos están sujetas a las condiciones establecidas por sus respectivas fuentes.
Los resultados de las simulaciones deben interpretarse considerando los supuestos, limitaciones y configuraciones metodológicas descritos en el Trabajo Fin de Máster.
