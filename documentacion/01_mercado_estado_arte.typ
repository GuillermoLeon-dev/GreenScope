#import "tema/greenscope.typ": *
#import "tema/diagramas.typ": *

#show: documento.with(
  titulo: "Mercado y estado del arte",
  subtitulo: "Contexto, competidores y ciencia aplicada al déficit de verde urbano",
  version: "0.4", fecha: "25 de octubre de 2026",
)

= Resumen y criterio de lectura

Este documento sitúa GreenScope en su contexto: por qué el déficit de verde urbano es un problema medible, qué herramientas existen hoy, qué ha demostrado la investigación reciente y dónde queda un hueco de mercado que una solución con fusión de datos puede ocupar.

#nota[
  *Convención de veracidad.* #tag-verificado indica una cifra o afirmación procedente de una fuente pública enlazada en las referencias. #tag-estimado indica una valoración propia del equipo (la comparativa de capacidades se basa en la documentación pública de cada producto, no en pruebas de uso). La atribución fina de cada métrica científica a su artículo debe revisarse contra la fuente original antes de citarla fuera de la organización.
]

*Conclusión principal.* Existen buenas herramientas para _medir_ el verde (cobertura arbórea, regla 3-30-300) pero ninguna de las analizadas combina, en un mismo flujo: (1) detección a escala de manzana, (2) series temporales de degradación, (3) *propuesta priorizada de intervenciones* tipo parque de bolsillo, (4) *decisión humana guiada por umbrales* y (5) *demanda real* basada en movilidad. Ese conjunto es el espacio que ocupa GreenScope.

= Contexto: el problema del verde urbano

== Referencias de salud pública y planificación

- *OMS.* La Organización Mundial de la Salud se cita habitualmente como referencia orientativa de entre 9 y 15 m² de zona verde por habitante. #dato[El rango 9–15 m²/hab es la cifra comúnmente atribuida a la OMS.] Es una referencia de planificación, no una norma vinculante; GreenScope la usa como _umbral inicial_ configurable, no como verdad normativa.
- *Regla 3-30-300* (Cecil Konijnendijk). Propone que cada persona vea al menos *3 árboles* desde su vivienda, que cada barrio tenga un *30 %* de cobertura arbórea y que exista un espacio verde a menos de *300 m*. #dato[Documentada y difundida como estándar emergente en las fuentes [1] y [2].]
- *ISGlobal.* Un estudio sobre ciudades españolas concluye que *el 84 % de la población de Madrid y el 95 % de la de Barcelona* no tiene un espacio verde de más de 0,5 ha a 300 m de su domicilio. #dato[Cifras de ISGlobal recogidas en [7].] La misma cobertura periodística asocia polución, ruido y calor a unas 1.900 muertes prematuras anuales entre ambas ciudades.

#figura(
  {
    let caja(titulo, cifra, desc, col) = block(width: 100%, inset: 10pt, radius: 8pt, fill: col.lighten(85%), stroke: 1pt + col,
      align(center)[#text(size: 8pt, weight: 700, fill: col.darken(15%), tracking: 0.5pt)[#upper(titulo)] \
        #text(size: 30pt, weight: 700, fill: azul-osc)[#cifra] \ #text(size: 8.5pt, fill: gris6)[#desc]])
    grid(columns: (1fr, 1fr, 1fr), column-gutter: 10pt,
      caja("Ver", "3", "árboles visibles desde cada vivienda", azul),
      caja("Cobertura", "30 %", "de copa arbórea en el barrio", ok),
      caja("Acceso", "300 m", "al espacio verde público más cercano", critico))
  },
  [La regla 3-30-300: tres indicadores simples y auditables (fuentes [1], [2]).],
)

== Por qué los parques de bolsillo

Madrid y Barcelona tienen poco suelo libre: la vía realista para cerrar el déficit no es el gran parque nuevo, sino la intervención *pequeña y distribuida* (solares vacantes, aparcamientos reconvertibles, chaflanes, calles pacificables) que acerca un verde de proximidad a quien hoy está a más de 300 m. Esa lógica exige localizar _dónde_ importa más (déficit + calor + población servida) y _qué_ parcelas son viables, que es exactamente el problema que resuelve GreenScope.

= Mapa competitivo

== Productos y servicios analizados

#tabla(
  columns: (1.1fr, 1.5fr, 1.5fr),
  [Solución], [Qué hace (según su documentación pública)], [Límite respecto a GreenScope],
  [*Urban Forest 3-30-300* (Treeconomics, Reino Unido)], [Herramienta de mapeo que lleva el estándar 3-30-300 al Reino Unido; evalúa el cumplimiento por ubicación [1].], [Mide cumplimiento; no propone intervenciones ni incorpora decisión por umbrales ni movilidad.],
  [*Tygron* (Países Bajos)], [Plataforma de gemelo digital con un proyecto demo 3-30-300 [2].], [Orientada a simulación y participación; la analítica de propuestas depende del modelador.],
  [*Davey* (EE. UU.)], [Servicio de consultoría con mapeo 3-30-300 e información de silvicultura urbana [3].], [Servicio manual/consultor, sin producto self-service ni ciclo de decisión auditado.],
  [*Herramienta ENEA* (Florencia, Aix-en-Provence)], [Evaluación de 3-30-300 con imágenes de muy alta resolución y OSM en dos ciudades piloto [4].], [Resultado de investigación; sin operación continua ni propuesta de intervenciones.],
  [*Google Tree Canopy Lab / Environmental Insights Explorer*], [Estimaciones de cobertura arbórea y de sombra a escala de ciudad.], [Inventario descriptivo; sin priorización ni propuestas; cobertura sujeta a las ciudades que Google publica.],
  [*greehill* (+ alianza con Civica, abr. 2026)], [Gemelo digital 4D del arbolado e IA para gestión forestal urbana; alianza con Civica anunciada en 2026 [5].], [Gestión del arbolado existente (inventario, riesgos); no genera propuestas de nuevos parques de bolsillo.],
  [*EarthDefine + PlanIT Geo (TreePlotter)*], [Alianza para ofrecer datos de cobertura arbórea bajo demanda e IA sobre el inventario de TreePlotter [6].], [Inventario y datos de copa; sin capa de demanda real ni decisión guiada por umbrales.],
)

#estimado[La columna «Límite» es una valoración propia basada en documentación pública; no se ha probado el software de terceros.]

== Comparativa de capacidades

Leyenda: círculo lleno = cubre de forma nativa · círculo claro = parcial o indirecto · círculo vacío = no evidenciado en la documentación consultada.

#let c(x) = cap(if x == "●" { 2 } else if x == "◐" { 1 } else { 0 })
#block(breakable: false, tabla(
  columns: (2fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1fr),
  [Solución], [Detección del déficit], [Series temporales], [Propuestas], [Human-in-the-loop], [Movilidad real], [Open data],
  [Urban Forest 3-30-300], c("●"), c("○"), c("○"), c("○"), c("○"), c("◐"),
  [Tygron], c("●"), c("◐"), c("◐"), c("◐"), c("○"), c("◐"),
  [Davey], c("●"), c("○"), c("◐"), c("◐"), c("○"), c("○"),
  [ENEA (Florencia/Aix)], c("●"), c("○"), c("○"), c("○"), c("○"), c("●"),
  [Google Tree Canopy / EIE], c("◐"), c("◐"), c("○"), c("○"), c("○"), c("◐"),
  [greehill + Civica], c("●"), c("●"), c("○"), c("◐"), c("○"), c("○"),
  [EarthDefine + PlanIT Geo], c("●"), c("◐"), c("○"), c("◐"), c("○"), c("○"),
  table.cell(fill: azul-med)[*GreenScope (objetivo)*], table.cell(fill: azul-med, cap(2)), table.cell(fill: azul-med, cap(2)), table.cell(fill: azul-med, cap(2)), table.cell(fill: azul-med, cap(2)), table.cell(fill: azul-med, cap(2)), table.cell(fill: azul-med, cap(2)),
))
#estimado[Valoración cualitativa propia; sujeta a revisión con demos y pruebas de los productos.]

== Mapa de posicionamiento

#figura(
  {
    let W = 330pt
    let H = 200pt
    let punto(x, y, txt, col: azul, dx: 6pt) = {
      place(top + left, dx: x * W - 4pt, dy: (1 - y) * H - 4pt, circle(radius: 4pt, fill: col, stroke: none))
      place(top + left, dx: x * W + dx, dy: (1 - y) * H - 7pt, text(size: 7.5pt, fill: azul-osc, txt))
    }
    box(width: W + 30pt, height: H + 34pt, {
      place(top + left, dx: 22pt, dy: 0pt, rect(width: W, height: H, fill: azul-cl.lighten(60%), stroke: 0.6pt + gris2, radius: 4pt))
      place(top + left, dx: 22pt + W / 2, dy: 0pt, line(start: (0pt, 0pt), end: (0pt, H), stroke: (paint: gris2, dash: "dashed")))
      place(top + left, dx: 22pt, dy: H / 2, line(length: W, stroke: (paint: gris2, dash: "dashed")))
      place(top + left, dx: 22pt + W / 2 - 80pt, dy: H + 6pt, text(size: 8pt, fill: gris6)[Cobertura analítica (datos fusionados) →])
      place(top + left, dx: -62pt, dy: H / 2 - 4pt, rotate(-90deg, text(size: 8pt, fill: gris6)[Accionabilidad →]))
      place(top + left, dx: 22pt, dy: 0pt, {
        punto(0.08, 0.16, [Google Canopy/EIE], col: azul-med)
        punto(0.14, 0.40, [Urban Forest 3-30-300], col: azul-med)
        punto(0.28, 0.27, [ENEA], col: azul-med)
        punto(0.34, 0.54, [Davey (consultoría)], col: azul-med)
        punto(0.50, 0.40, [Tygron], col: azul-med)
        punto(0.56, 0.64, [greehill + Civica], col: azul-med)
        punto(0.38, 0.14, [EarthDefine + PlanIT], col: azul-med)
        punto(0.86, 0.86, [*GreenScope*], col: critico, dx: -52pt)
      })
    })
  },
  [Posicionamiento cualitativo (valoración propia, escala relativa 0–1). Los competidores no se han probado en uso real.],
)

== Gap de mercado

#decision[
  *Hueco identificado.* Ninguna solución analizada integra a la vez: _(a)_ detección a nivel de manzana, _(b)_ vigilancia temporal del verde, _(c)_ propuestas de intervención priorizadas y explicadas, _(d)_ decisión humana auditada guiada por umbrales y _(e)_ demanda real a partir de movilidad agregada. GreenScope se diseña como producto de _apoyo a la decisión_ —no de automatización total— para el técnico municipal.
]

La ventaja diferencial propuesta es integrar *datos de movilidad de operador*, anonimizados y agregados, como los que comercializa Telefónica Tech con *Smart Steps*. #dato[Telefónica Tech aplica Smart Steps en proyectos municipales, p. ej. con el Ayuntamiento de Xàtiva (nota de prensa, 2025) [10].] Esa señal permite estimar *población flotante diurna* (quién usa realmente cada zona), que ni el padrón ni la imagen satelital capturan.

= Estado del arte científico

#tabla(
  columns: (1.1fr, 1.5fr, 1.5fr),
  [Línea], [Resultado relevante], [Implicación para GreenScope],
  [Segmentación en Sentinel-2 (U-Net, ResNet)], [Modelo híbrido U-Net + ResNet-50 en 16 ciudades: ≈ 90 % de acierto identificando espacios verdes, pero *fallos en parches pequeños* [8].], [Los parques de bolsillo son justamente parches pequeños: combinar NDVI con OSM y catastro y reservar la imagen de muy alta resolución para validar.],
  [Park-NET], [U-Net y U-Net/ResNet-34 sobre Sentinel-2 para parques públicos: IoU medio de test ≈ 0,56 [9].], [Un IoU moderado aconseja usar la segmentación como _señal_ y no como verdad: de ahí el modelo de déficit con incertidumbre.],
  [CNN + active learning sobre street view (Nanjing, 2024)], [CNN + aprendizaje activo sobre imágenes de calle para identificar emplazamientos potenciales de parques de bolsillo [12].], [Respalda el *bucle de decisiones del técnico → etiquetas* como active learning.],
  [F-AHP para idoneidad (Nanjing)], [F-AHP + SIG para ubicar parques urbanos: almacenamiento de carbono, NDVI e isla de calor como factores de mayor peso [11].], [Inspira el *ranking multicriterio* explícito con pesos configurables.],
  [ML interpretable (Shenzhen, 2025)], [Potencial y selección de emplazamientos de parques con ML interpretable (Li y He, 2025); métodos no contrastados en detalle.], [Justifica LightGBM + SHAP como estándar de explicabilidad.],
  [Foundation models (Prithvi-EO-2.0, Clay)], [Modelos preentrenados multitemporales sobre HLS (Harmonized Landsat Sentinel-2) para segmentación y clasificación [13].], [Ruta de producción: reutilizar embeddings en lugar de entrenar desde cero (menos coste y huella).],
  [Earth embeddings], [Representaciones densas por píxel/celda listas para consulta y búsqueda por similitud.], [Permiten escalar a ciudades nuevas sin etiquetas propias.],
)

#nota[
  Las cifras de U-Net/ResNet y Park-NET proceden de los trabajos citados ([8], [9]) y no son reproducciones propias. Los resultados de GreenScope sobre datos sintéticos no son comparables con ellos (véase el documento 04).
]

#figura(
  dg(sp: (30mm, 14mm),
    nodo((0, 0), [Sentinel-2 / VHR\ _NDVI, U-Net_], tono: "claro"),
    nodo((1, 0), [Foundation models\ _Prithvi, Clay_], tono: "azul"),
    nodo((2, 0), [Embeddings\ _escala multi-ciudad_], tono: "oscuro"),
    nodo((0, 1), [CNN + active learning\ _street view_], tono: "claro"),
    nodo((1, 1), [Boosting + SHAP\ _explicabilidad_], tono: "azul"),
    nodo((2, 1), [Apoyo a la decisión\ _F-AHP, umbrales_], tono: "oscuro"),
    flecha((0, 0), (1, 0)), flecha((1, 0), (2, 0)),
    flecha((0, 1), (1, 1)), flecha((1, 1), (2, 1)),
    flecha((0, 0), (0, 1), tipo: "<->"), flecha((2, 0), (2, 1)),
  ),
  [Evolución del estado del arte: de la segmentación a la explicabilidad y la decisión asistida.],
)

= Conclusiones para el diseño

+ *Combinar fuentes* (EO + OSM + catastro + INE + movilidad), porque ninguna aislada resuelve los parches pequeños.
+ *Explicar cada score* (SHAP) y mostrar su incertidumbre: el técnico debe poder discutirlo.
+ *Mantener la decisión humana* con umbrales ajustables y trazabilidad; las decisiones alimentan el reentrenamiento.
+ *Reutilizar modelos fundacionales* en producción para controlar coste y huella de carbono.

= Referencias

#set text(size: 8.5pt)
+ Chartered Foresters. _New mapping tool brings emerging urban greening standard to the UK._ #link("https://charteredforesters.org/new-mapping-tool-brings-emerging-urban-greening-standard-to-the-uk")
+ Tygron Support Wiki. _Demo 3-30-300 Project._ #link("https://support.tygron.com/wiki/Demo_3-30-300_Project")
+ Davey. _3-30-300 mapping: urban forestry insights._ #link("https://www.davey.com/environmental-consulting-services/3-30-300-mapping-urban-forestry-insights/")
+ ENEA (IRIS). Herramienta 3-30-300 en Florencia y Aix-en-Provence. #link("https://iris.enea.it/handle/20.500.12079/87988")
+ Civica. _greehill AI urban forestry partnership._ #link("https://www.civica.com/en-gb/news-library/greehill-ai-urban-forestry-partnership")
+ Geospatial World. _PlanIT Geo and EarthDefine partnership._ #link("https://geospatialworld.net/news/planit-geo-and-earthdefine-partnership-disruptive-urban-forestry-software-and-ai-driven-canopy-analysis-creates-on-demand-data")
+ elDiario.es / agencias. _Polución, ruido y calor causan 1.900 muertes prematuras anuales en Madrid y Barcelona._ #link("https://www.eldiario.es/agencias/polucion-ruido-calor-causan-1-900-muertes-prematuras-anuales-madrid-barcelona_1_7361604.html")
+ _AI models for detecting urban green spaces: a multi-city and multi-country contexts approach_ (Universiteit Utrecht, 2026). #link("https://utrecht-main-test.atmire.com/items/eabaf7c4-848b-4937-b768-7a2e01e1aafd")
+ _Park-NET: identifying urban parks using multi-source spatial data and Geo-AI_ (tesis, Universiteit Utrecht). #link("https://studenttheses.uu.nl/handle/20.500.12932/42864")
+ Telefónica Tech. _Smart Steps con el Ayuntamiento de Xàtiva_ (nota de prensa, agosto de 2025). #link("https://www.telefonica.es/es/wp-content/uploads/sites/10/2025/08/2025.08.06-NdP-Smart-Steps-Telefonica-Tech-Ayuntamiento-de-Xativa-002.pdf")
+ _Site Selection of Urban Parks Based on Fuzzy-Analytic Hierarchy Process (F-AHP): A Case Study of Nanjing, China_ (PMC9603808). #link("https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9603808/")
+ Zhou et al. (2024), CNN y aprendizaje activo para emplazamientos de parques de bolsillo (Nanjing), _Journal of Urban Technology_ 31(4-5). #link("https://ideas.repec.org/a/taf/cjutxx/v31y2024i4-5p191-217.html")
+ Szwarcman et al. (2024). _Prithvi-EO-2.0: A Versatile Multi-Temporal Foundation Model for Earth Observation Applications_. #link("https://arxiv.org/abs/2412.02732")

#v(10pt)
#historial((
  ("0.1", "25-10-2026", "Resumen del estudio de mercado incluido en el plan inicial."),
  ("0.2", "25-10-2026", "Mapa competitivo, comparativa de capacidades, estado del arte y gap; etiquetado verificado/estimado."),
  ("0.3", "25-10-2026", "Revisión del orquestador: atribución correcta de las referencias científicas."),
  ("0.4", "25-10-2026", "Proyecto independiente: se elimina la identidad de Telefónica; Smart Steps se cita como producto de terceros."),
))
