#import "tema/greenscope.typ": *
#import "tema/diagramas.typ": *

#show: documento.with(
  titulo: "GreenScope",
  subtitulo: "Resumen ejecutivo y guía de la documentación",
  version: "0.2", fecha: "25 de octubre de 2026",
)

= Resumen ejecutivo

*GreenScope* es una aplicación web de apoyo a la decisión que detecta zonas urbanas con déficit de verde, explica por qué, vigila su evolución y *propone parques de bolsillo* priorizados. El técnico municipal fija los umbrales y decide —aprueba, rechaza o ajusta— cada propuesta; cada decisión queda auditada y mejora el modelo. El piloto es *Madrid* (distritos centrales) y la demo es desplegable como sitio estático en GitHub Pages.

== Por qué ahora y por qué la fusión de datos

- #dato[Según ISGlobal, el 84 % de la población de Madrid no tiene un espacio verde de más de 0,5 ha a 300 m.] Existen herramientas para medir el verde (3-30-300, cobertura arbórea), pero ninguna de las analizadas prioriza y propone intervenciones con decisión humana y demanda real (documento 01).
- *Data fusion:* observación terrestre + OSM/catastro + padrón + *Smart Steps* (población flotante agregada y anonimizada). Es la ventaja diferencial de la propuesta (documento 02).
- *Rigor metodológico:* CRISP-ML(Q), series temporales (STL, Theil-Sen, Holt-Winters), LightGBM + SHAP, active learning (documento 04).

#figura(
  dg(sp: (28mm, 12mm),
    nodo((0, 0), [Fuentes fusionadas\ EO · OSM · INE\ Smart Steps], tono: "claro"),
    nodo((1, 0), [Modelos\ déficit · series\ propuestas], tono: "azul"),
    nodo((2, 0), [Técnico municipal\ umbrales y decisión], tono: "ok"),
    nodo((3, 0), [Registro auditado\ + aprendizaje], tono: "oscuro"),
    flecha((0, 0), (1, 0)), flecha((1, 0), (2, 0)), flecha((2, 0), (3, 0)),
    flecha((3, 0), (1, 0), tipo: "-->", bend: 40deg, etiqueta: "etiquetas"),
  ),
  [GreenScope de un vistazo.],
)

== Cifras clave y su estatus

#tabla(
  columns: (1fr, auto, auto),
  [Indicador], [Valor], [Estatus],
  [Población de Madrid sin verde > 0,5 ha a 300 m], [84 %], [#tag-verificado],
  [Referencia OMS de verde por habitante], [9–15 m²], [#tag-verificado],
  [Unidad de análisis], [H3 res. 9 (≈ 0,1 km²)], [Diseño],
  [CAPEX de desarrollo MVP → producto], [≈ 278 k€], [#tag-estimado],
  [Payback en el escenario base], [≈ 4,2 años], [#tag-estimado],
  [Datos EO, INE y Smart Steps de la demo], [Sintéticos], [#tag-sintetico],
)

#nota[Los datos de la demo son sintéticos salvo la geometría OpenStreetMap; no deben utilizarse para decisiones reales. Las cifras económicas son estimaciones con supuestos explícitos (documento 06).]

= Guía de documentos

#tabla(
  columns: (auto, 1fr, auto),
  [Doc.], [Contenido], [PDF],
  [01], [Mercado, mapa competitivo, estado del arte científico y gap de mercado.], [#link("01_mercado_estado_arte.pdf")[abrir]],
  [02], [Problema, propuesta de valor, usuarios, flujo human-in-the-loop, data fusion, innovación y riesgos éticos.], [#link("02_propuesta_innovacion.pdf")[abrir]],
  [03], [Arquitectura hexagonal, componentes, flujo de datos, stack, ADR, Clean Code y testing.], [#link("03_arquitectura_tecnologias.pdf")[abrir]],
  [04], [CRISP-ML(Q), features, series temporales, modelo de déficit, ranking, métricas y monitorización.], [#link("04_ml_crisp_ml.pdf")[abrir]],
  [05], [Despliegue de la demo y de producción, escalabilidad, sostenibilidad, seguridad y CI/CD.], [#link("05_despliegue_escalabilidad.pdf")[abrir]],
  [06], [CAPEX, OPEX, modelo SaaS, escenarios, ROI, payback y coste-beneficio municipal.], [#link("06_viabilidad_economica.pdf")[abrir]],
  [07], [Registro de iteraciones, cronometraje de etapas y Gantt.], [#link("07_registro_iteraciones_tiempos.pdf")[abrir]],
)

#decision[
  *Principio rector.* El sistema _propone_, el humano _decide_. Ninguna intervención se aprueba automáticamente.
]

#v(10pt)
#historial((
  ("0.1", "25-10-2026", "Plan y estudio de mercado."),
  ("0.2", "25-10-2026", "Resumen ejecutivo y guía de la documentación."),
))
