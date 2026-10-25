#import "tema/greenscope.typ": *
#import "tema/diagramas.typ": *

#show: documento.with(
  titulo: "ML y CRISP-ML(Q)",
  subtitulo: "Modelos, series temporales, métricas y gestión de calidad",
  version: "0.2", fecha: "25 de octubre de 2026",
)

// Métricas reales si el pipeline ya generó el manifest (build.py lo copia a datos/)
#let hay-manifest = read("datos/manifest.presente").trim() == "1"
#let man = if hay-manifest { json("datos/manifest.json") } else { none }
#let fmt(x, d: 3) = if x == none { "—" } else { str(calc.round(x, digits: d)).replace(".", ",") }

= Marco metodológico: CRISP-ML(Q)

CRISP-ML(Q) extiende CRISP-DM con una *fase de monitorización y mantenimiento* y con la *gestión de calidad (Q)* en cada fase: riesgos, métricas de aceptación y criterios de parada. Es el marco apropiado para un sistema que se opera en el tiempo y cuyos datos derivan.

#figura(
  dg(sp: (34mm, 26mm),
    nodo((-150deg, 1.2), [*1. Comprensión de negocio\ y de los datos*], tono: "azul", w: 44mm),
    nodo((-90deg, 1.2), [*2. Preparación\ de datos*], tono: "azul", w: 44mm),
    nodo((-30deg, 1.2), [*3. Modelado*], tono: "azul", w: 44mm),
    nodo((30deg, 1.2), [*4. Evaluación*], tono: "azul", w: 44mm),
    nodo((90deg, 1.2), [*5. Despliegue*], tono: "azul", w: 44mm),
    nodo((150deg, 1.2), [*6. Monitorización\ y mantenimiento*], tono: "azul", w: 44mm),
    nodo((0, 0), [*Q*\ gestión de calidad\ en cada fase], tono: "revisar", forma: circle),
    flecha((-150deg, 1.2), (-90deg, 1.2), bend: -20deg), flecha((-90deg, 1.2), (-30deg, 1.2), bend: -20deg),
    flecha((-30deg, 1.2), (30deg, 1.2), bend: -20deg), flecha((30deg, 1.2), (90deg, 1.2), bend: -20deg),
    flecha((90deg, 1.2), (150deg, 1.2), bend: -20deg),
    flecha((150deg, 1.2), (-150deg, 1.2), bend: -20deg, tipo: "-->", etiqueta: "reentrenar / nueva iteración"),
  ),
  [Ciclo de las seis fases de CRISP-ML(Q) con gestión de calidad transversal.],
)

= Fase a fase aplicada a GreenScope

#tabla(
  columns: (auto, 1fr, 1fr),
  [Fase], [Actividades en el caso], [Gestión de calidad (Q)],
  [1. Negocio y datos], [Objetivo: priorizar dónde actuar y qué parcelas proponer. Éxito: el técnico aprueba o ajusta una proporción alta de propuestas y reduce el tiempo de análisis. Inventario de fuentes y su licencia.], [Riesgo: datos sintéticos tomados por reales; sesgo de OSM. Criterio: etiquetado de origen en cada fuente.],
  [2. Preparación], [Proyección a malla H3 res. 9; features por celda; tratamiento de huecos por nubes; escalado a [0,1].], [Validación de esquema, rangos y completitud; pruebas con semilla fija.],
  [3. Modelado], [Segmentación de vegetación, series temporales, modelo de déficit, ranking de propuestas (secciones siguientes).], [Comparar con un baseline simple; registrar versión de modelo.],
  [4. Evaluación], [AUC, F1 en el umbral crítico, MAE de previsión, estabilidad; revisión de equidad por distrito.], [Criterios de aceptación definidos antes de entrenar.],
  [5. Despliegue], [Artefactos estáticos (`docs/data`) y API opcional; umbrales en cliente.], [Plan de reversión: versión anterior del manifest.],
  [6. Monitorización], [Drift de features y de scores, calidad de datos, tasa de aprobación del técnico, reentrenamiento por active learning.], [Alertas y revisión periódica (mensual).],
)

= Datos y features

Cada celda H3 (res. 9, ≈ 0,1 km²) recibe las variables siguientes (contrato de datos v1):

#tabla(
  columns: (auto, 1fr),
  [Variable], [Descripción],
  [`green_m2_per_capita`], [m² de verde público accesible por habitante (referencia OMS 9–15).],
  [`dist_green_m`], [Distancia al espacio verde de ≥ 0,5 ha más cercano (regla de 300 m).],
  [`canopy_pct`, `ndvi_mean`, `ndvi_trend`], [Cobertura vegetal, NDVI medio del último año y pendiente Theil-Sen.],
  [`lst_c`], [Temperatura superficial media de verano (calor).],
  [`vulnerability`], [Índice de vulnerabilidad socioeconómica (0–1).],
  [`population`, `floating_population`], [Residentes (INE) y población flotante diurna (Smart Steps).],
)

#nota[En la demo, NDVI, LST, INE y Smart Steps son *sintéticos* (generador determinista con semilla) y sólo la geometría procede de OSM. Las métricas siguientes miden por tanto la capacidad del sistema de recuperar una estructura _construida_, no el rendimiento sobre la realidad.]

= Modelado

== Segmentación de vegetación

*Baseline*: umbral de NDVI (p. ej. > 0,3–0,4) combinado con máscaras OSM. *Mejora*: U-Net ligera sobre Sentinel-2 (interfaz opcional `dl`/PyTorch). *Producción*: embeddings de foundation models (Prithvi-EO-2.0, Clay) con una cabeza ligera ajustada con pocas etiquetas, para tratar los parches pequeños donde fallan U-Net/ResNet (doc. 01).

== Series temporales

#tabla(
  columns: (auto, 1fr),
  [Técnica], [Uso],
  [*STL*], [Descompone NDVI/LST mensual en tendencia, estacionalidad y residuo (robusto a huecos).],
  [*Theil-Sen*], [Pendiente robusta de la tendencia (`ndvi_trend`, unidades/año); insensible a valores atípicos.],
  [*Holt-Winters*], [Previsión a 12 meses del NDVI con intervalos (`ndvi_forecast`, `_lo`, `_hi`).],
  [*Detección de anomalías*], [Residuos STL fuera de ±k·MAD o caída sostenida de tendencia → `anomaly = true`.],
)

#figura(
  dg(sp: (26mm, 12mm),
    nodo((0, 0), [Serie mensual\ NDVI / LST], tono: "claro"),
    nodo((1, 0), [STL\ tendencia · estación\ · residuo], tono: "azul"),
    nodo((2, -0.7), [Theil-Sen\ pendiente anual], tono: "azul"),
    nodo((2, 0.7), [Holt-Winters\ previsión 12 m], tono: "azul"),
    nodo((3, -0.7), [Anomalía\ (residuo / caída)], tono: "critico"),
    nodo((3, 0.7), [Banda de\ incertidumbre], tono: "claro"),
    nodo((4, 0), [Feature\ `ndvi_trend`\ y alertas], tono: "ok"),
    flecha((0, 0), (1, 0)), flecha((1, 0), (2, -0.7)), flecha((1, 0), (2, 0.7)),
    flecha((2, -0.7), (3, -0.7)), flecha((2, 0.7), (3, 0.7)),
    flecha((3, -0.7), (4, 0)), flecha((3, 0.7), (4, 0)),
  ),
  [Pipeline de series temporales por celda.],
)

== Modelo de déficit

+ *Índice compuesto* (conocimiento experto): combinación ponderada normalizada de m²/hab inverso, distancia al verde, calor, vulnerabilidad y demanda efectiva (residentes + flotantes). Sirve como _weak supervision_: genera etiquetas ruidosas (déficit alto/bajo).
+ *LightGBM* entrenado con esas etiquetas débiles más las decisiones humanas disponibles; aprende interacciones no lineales y las generaliza a celdas con datos parciales.
+ *Calibración* de probabilidades (isotónica/Platt) para que el score 0–1 sea interpretable y los umbrales tengan sentido estable.
+ *Incertidumbre* (`uncertainty`): desviación entre modelos del conjunto y/o entre semillas.
+ *SHAP*: contribuciones por celda (`top_factors`, 3–5 variables) que se muestran al técnico.

#atencion[
  La *weak supervision* introduce un riesgo de circularidad: el modelo puede aprender el índice con el que se etiquetó. Mitigación: validar con etiquetas humanas (decisiones del técnico) y reportar la discordancia modelo–índice.
]

== Ranking multicriterio de propuestas

Candidatas: solares vacantes, aparcamientos, interbloques, chaflanes y calles pacificables en celdas con déficit alto. La prioridad combina (pesos configurables, inspirado en F-AHP):

#align(center)[
  #block(inset: 8pt, fill: azul-cl, radius: 6pt)[
    $ "prioridad" = w_1 dot "población servida" + w_2 dot "reducción de calor" + w_3 dot "déficit de la celda" - w_4 dot "coste" $
  ]
]

Cada propuesta lleva `rationale` en español (por qué se propone), `served_population`, `est_cost_eur`, `est_cooling_c` y `co2_kg_year`. Estas dos últimas son #tag-estimado basadas en coeficientes de la literatura, no mediciones.

= Métricas y resultados

#tabla(
  columns: (1.2fr, 1fr, 1.3fr),
  [Métrica], [Valor], [Interpretación],
  [AUC (déficit crítico)], [#if hay-manifest and man.metrics.auc > 0 [#fmt(man.metrics.auc)] else [pendiente de la ejecución del pipeline]], [Capacidad de ordenar celdas críticas frente a no críticas.],
  [F1 en el umbral crítico], [#if hay-manifest and man.metrics.f1_at_critical > 0 [#fmt(man.metrics.f1_at_critical)] else [pendiente de la ejecución del pipeline]], [Equilibrio precisión/recall con umbral por defecto 0,70.],
  [MAE de previsión NDVI], [#if hay-manifest and man.metrics.mae_forecast_ndvi > 0 [#fmt(man.metrics.mae_forecast_ndvi, d: 4)] else [pendiente de la ejecución del pipeline]], [Error medio absoluto de Holt-Winters a 12 meses (retención).],
  [Celdas analizadas], [#if hay-manifest and man.metrics.n_cells > 0 [#man.metrics.n_cells] else [pendiente de la ejecución del pipeline]], [Madrid central, H3 res. 9.],
  [Propuestas generadas], [#if hay-manifest and man.metrics.n_proposals > 0 [#man.metrics.n_proposals] else [pendiente de la ejecución del pipeline]], [Candidatas con prioridad ≥ `min_proposal_priority`.],
)

#if hay-manifest [
  #nota[Métricas leídas de `docs/data/manifest.json` (modelo *#man.model_version*, generado el #man.generated_at, esquema v#man.schema_version). Ámbito: bbox #man.bbox.map(str).join(", "), periodo #man.period.start – #man.period.end. Datos con fuentes sintéticas: no extrapolar a la realidad.]
] else [
  #nota[El fichero `manifest.json` aún no estaba disponible al compilar este documento. La plantilla lee las métricas automáticamente cuando el pipeline las genera; esta tabla se actualizará en la siguiente compilación.]
]

= Gestión de calidad, monitorización y active learning

#tabla(
  columns: (auto, 1fr, 1fr),
  [Ámbito], [Indicador], [Acción],
  [Calidad de datos], [Completitud, rango, frescura de cada `DataSource`.], [Bloquear publicación si falla el esquema.],
  [Drift de datos], [PSI/KS de las features frente al entrenamiento.], [Alerta y reentrenamiento programado.],
  [Drift de modelo], [Distribución del score y estabilidad de rankings.], [Revisión humana del cambio de versión.],
  [Equidad], [Error y tasa de propuestas por distrito y vulnerabilidad.], [Recalibrar o ajustar pesos.],
  [Uso humano], [Tasa de aprobación, rechazo y ajuste por tipo de propuesta.], [Priorizar celdas con desacuerdo para etiquetar.],
)

#figura(
  dg(sp: (28mm, 12mm),
    nodo((0, 0), [Modelo v_n\ propone], tono: "azul"),
    nodo((1, 0), [Técnico\ aprueba · rechaza\ · ajusta], tono: "ok"),
    nodo((2, 0), [Registro\ (decisión + contexto)], tono: "oscuro"),
    nodo((2, 1), [Selección de casos\ inciertos o discordantes], tono: "revisar"),
    nodo((1, 1), [Reentrenamiento\ LightGBM], tono: "claro"),
    nodo((0, 1), [Evaluación y\ puerta de calidad], tono: "claro"),
    flecha((0, 0), (1, 0)), flecha((1, 0), (2, 0)), flecha((2, 0), (2, 1)),
    flecha((2, 1), (1, 1)), flecha((1, 1), (0, 1)), flecha((0, 1), (0, 0), etiqueta: "v_n+1"),
  ),
  [Bucle de active learning con las decisiones del técnico.],
)

#decision[
  Un modelo nuevo sólo se publica si supera la puerta de calidad (métricas no peores que la versión anterior y sin deterioro de equidad) y un técnico lo revisa.
]

#v(10pt)
#historial((
  ("0.1", "25-10-2026", "Esquema del plan: modelos y fases."),
  ("0.2", "25-10-2026", "CRISP-ML(Q) por fase, series temporales, modelo de déficit, ranking y plantilla de métricas ligada a manifest.json."),
))
