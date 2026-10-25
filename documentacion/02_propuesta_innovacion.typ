#import "tema/verdescope.typ": *
#import "tema/diagramas.typ": *

#show: documento.with(
  titulo: "Propuesta de innovación",
  subtitulo: "Valor, usuarios, decisión humana y data fusion",
  version: "0.2", fecha: "25 de octubre de 2026",
)

= Problema y propuesta de valor

== El problema

Los ayuntamientos saben que les falta verde de proximidad, pero deciden con información fragmentada: inventarios de arbolado, planos de zonas verdes, padrón anual y estudios puntuales de consultoría. Tres carencias recurrentes:

+ *No se ve el déficit a escala de manzana.* Las medias por distrito ocultan bolsas de población sin verde a 300 m (véase documento 01: 84 % de Madrid según ISGlobal).
+ *No se vigila en el tiempo.* El verde se degrada (sequía, obras, pérdida de arbolado) y nadie lo detecta hasta que hay quejas.
+ *No se sabe dónde actuar primero.* Falta un criterio explícito y auditable que combine déficit, calor, vulnerabilidad, población realmente servida y coste.

== Propuesta de valor

VerdeScope es una aplicación de _apoyo a la decisión_ que *detecta* zonas con déficit de verde, *explica* por qué, *vigila* su evolución y *propone* parques de bolsillo candidatos priorizados. El técnico municipal fija los umbrales y *aprueba, rechaza o ajusta* cada propuesta; cada decisión queda registrada y mejora el sistema.

#figura(
  dg(sp: (34mm, 14mm),
    nodo((0, 0), [*Detectar*\ déficit por celda H3\ (≈ 0,1 km²)], tono: "azul"),
    nodo((1, 0), [*Explicar*\ factores SHAP\ + incertidumbre], tono: "azul"),
    nodo((2, 0), [*Proponer*\ parques de bolsillo\ priorizados], tono: "azul"),
    nodo((0, 1), [*Vigilar*\ series temporales\ y anomalías], tono: "claro"),
    nodo((1, 1), [*Decidir*\ técnico: aprobar,\ rechazar, ajustar], tono: "ok"),
    nodo((2, 1), [*Aprender*\ decisiones →\ etiquetas], tono: "claro"),
    flecha((0, 0), (1, 0)), flecha((1, 0), (2, 0)), flecha((2, 0), (2, 1)),
    flecha((2, 1), (1, 1), tipo: "<-"), flecha((1, 1), (0, 1), tipo: "<-"), flecha((0, 1), (0, 0)),
  ),
  [Propuesta de valor como ciclo continuo: detectar, explicar, proponer, decidir, aprender, vigilar.],
)

= Usuarios y necesidades

#tabla(
  columns: (1fr, 1.4fr, 1.4fr),
  [Usuario], [Necesidad principal], [Qué ofrece VerdeScope],
  [*Técnico municipal* (medio ambiente / parques)], [Revisar casos con criterio y justificar la decisión ante superiores y vecindario.], [Cola de propuestas con «por qué se propone», factores SHAP, incertidumbre, aprobar/rechazar/ajustar con comentario y auditoría exportable.],
  [*Planificador urbano*], [Priorizar inversión y simular escenarios de umbral.], [Mapa de celdas con déficit, calor y vulnerabilidad; sliders de umbral; ranking multicriterio; series temporales y previsión.],
  [*Dirección / concejalía*], [Visión agregada, rendición de cuentas y retorno.], [Indicadores resumidos (m²/hab, población servida, ahorro de calor), histórico de decisiones y estado del plan.],
)

= Flujo human-in-the-loop con umbrales

El modelo entrega *puntuaciones continuas* de déficit (0–1, donde 1 es el peor caso). La *clasificación* en crítico, revisar o correcto *no está en los datos*: se calcula en el navegador con los umbrales que fija el técnico, de modo que cambiar un umbral recalcula la vista al instante y sin servidor.

#tabla(
  columns: (auto, auto, 1fr),
  [Clase], [Regla (valores por defecto)], [Acción prevista],
  [Crítico], [déficit ≥ 0,70], [Genera propuestas de máxima prioridad; revisión obligatoria por técnico.],
  [Revisar], [0,40 ≤ déficit < 0,70], [Se muestra al técnico; puede escalar o descartar.],
  [Correcto], [déficit < 0,40], [Sin acción; vigilancia por series temporales.],
)

#figura(
  dg(sp: (22mm, 12mm),
    nodo((0, 0), [Datos fusionados\ por celda H3], tono: "claro"),
    nodo((1, 0), [Modelo de déficit\ score 0–1 + SHAP], tono: "azul"),
    nodo((2, 0), [Umbrales\ del técnico\ (cliente)], tono: "revisar"),
    nodo((3, -0.8), [Crítico], tono: "critico"),
    nodo((3, 0), [Revisar], tono: "revisar"),
    nodo((3, 0.8), [Correcto\ (vigilancia)], tono: "ok"),
    nodo((3, 2), [Propuesta de\ parque de bolsillo], tono: "claro"),
    nodo((2, 2), [Decisión humana\ aprobar · rechazar\ · ajustar], tono: "ok"),
    nodo((1, 2), [Registro auditado\ (DecisionStore)], tono: "oscuro"),
    nodo((0, 2), [Active learning:\ reentrenamiento], tono: "azul"),
    flecha((0, 0), (1, 0)), flecha((1, 0), (2, 0)),
    flecha((2, 0), (3, -0.8)), flecha((2, 0), (3, 0)), flecha((2, 0), (3, 0.8)),
    flecha((3, -0.8), (3, 2), bend: -40deg), flecha((3, 0), (3, 2), tipo: "-"),
    flecha((3, 2), (2, 2)), flecha((2, 2), (1, 2)), flecha((1, 2), (0, 2)),
    flecha((0, 2), (1, 0), tipo: "-->", etiqueta: "nuevo modelo"),
  ),
  [Flujo con decisión humana: el sistema propone, el técnico decide, la decisión realimenta el modelo.],
)

#decision[
  *Decisión de diseño.* Ninguna propuesta se ejecuta ni se archiva sin acción humana registrada (usuario, fecha, comentario, versión de modelo y umbrales vigentes). La automatización total queda descartada por razones de responsabilidad pública y de calidad de datos.
]

= Data fusion como ventaja competitiva

== Fuentes y qué aporta cada una

#tabla(
  columns: (auto, 1fr, auto),
  [Fuente], [Aporte], [Estado en la demo],
  [Sentinel-2 L2A (NDVI/NDWI)], [Cobertura vegetal y su serie mensual.], [#tag-sintetico],
  [Landsat 8/9 (LST)], [Calor superficial en verano; priorización por isla de calor.], [#tag-sintetico],
  [OpenStreetMap / Overpass], [Parques existentes, solares, aparcamientos, viario.], [Real, cacheado],
  [INE (padrón, vulnerabilidad)], [Residentes y vulnerabilidad socioeconómica.], [#tag-sintetico],
  [*Smart Steps (Telefónica Tech)*], [*Población flotante diurna* real: quién usa cada zona.], [#tag-sintetico en la demo],
)

#nota[
  En la demo, todas las fuentes salvo OSM son *sintéticas pero realistas* (generador determinista con semilla). Los conectores reales (STAC, INE, Smart Steps) se implementan tras la misma interfaz `DataSource` y se activan por configuración.
]

== Por qué Smart Steps marca la diferencia

#dato[Smart Steps es una oferta de Telefónica Tech de movilidad anonimizada y agregada, aplicada ya en proyectos municipales como el de Xàtiva (2025); véase [10] en el documento 01.] La población residente subestima la presión de uso en centros de trabajo, comercio y turismo; la imagen satelital sólo mide el verde, no quién lo necesita. Fusionar ambas cosas permite priorizar por *población servida efectiva* (residentes + flotantes ponderados a ≤ 300 m).

#figura(
  dg(sp: (22mm, 9mm),
    contenedor(((0, 0), (0, 4)), "Fuentes", tono: "gris"),
    nodo((0, 0), [Sentinel-2\ NDVI], tono: "claro"), nodo((0, 1), [Landsat LST], tono: "claro"),
    nodo((0, 2), [OSM / catastro], tono: "claro"), nodo((0, 3), [INE padrón], tono: "claro"),
    nodo((0, 4), [*Smart Steps*\ población flotante], tono: "azul"),
    nodo((1, 2), [Armonización\ H3 res. 9\ + calidad], tono: "oscuro"),
    nodo((2, 1), [Features por celda\ m²/hab, distancia al verde,\ LST, tendencia NDVI…], tono: "claro"),
    nodo((2, 3), [Demanda efectiva\ residente + flotante], tono: "azul"),
    nodo((3, 2), [Índice de déficit\ + propuestas], tono: "ok"),
    flecha((0, 0), (1, 2)), flecha((0, 1), (1, 2)), flecha((0, 2), (1, 2)),
    flecha((0, 3), (1, 2)), flecha((0, 4), (1, 2)),
    flecha((1, 2), (2, 1)), flecha((1, 2), (2, 3)),
    flecha((2, 1), (3, 2)), flecha((2, 3), (3, 2)),
  ),
  [Fusión de fuentes: todo se proyecta a una malla común H3 antes de modelar.],
)

= Innovación y madurez

#figura(
  {
    let W = 300pt
    let H = 170pt
    let item(x, y, t, col) = {
      place(top + left, dx: x * W - 4pt, dy: (1 - y) * H - 4pt, circle(radius: 4pt, fill: col, stroke: none))
      place(top + left, dx: x * W + 7pt, dy: (1 - y) * H - 7pt, text(size: 7.5pt, fill: azul-osc, t))
    }
    box(width: W + 40pt, height: H + 34pt, {
      place(top + left, dx: 28pt, rect(width: W, height: H, fill: azul-cl.lighten(60%), stroke: 0.6pt + gris2, radius: 4pt))
      for i in range(1, 9) {
        place(top + left, dx: 28pt + i * W / 9, dy: H + 3pt, text(size: 6.5pt, fill: gris6)[#i])
      }
      place(top + left, dx: 28pt + W / 2 - 20pt, dy: H + 14pt, text(size: 8pt, fill: gris6)[Madurez (TRL) →])
      place(top + left, dx: -42pt, dy: H / 2 - 4pt, rotate(-90deg, text(size: 8pt, fill: gris6)[Grado de innovación →]))
      place(top + left, dx: 28pt, {
        item(0.55, 0.42, [Segmentación NDVI + OSM (TRL 5)], azul-med)
        item(0.50, 0.76, [Data fusion con Smart Steps], critico)
        item(0.50, 0.86, [Propuestas con ranking multicriterio], critico)
        item(0.40, 0.54, [Series temporales + anomalías], azul)
        item(0.35, 0.34, [LightGBM + SHAP], azul-med)
        item(0.10, 0.95, [Foundation models (Prithvi/Clay)], revisar)
        item(0.30, 0.64, [Active learning con decisiones], azul)
        item(0.62, 0.20, [Umbrales + HITL (web)], ok)
      })
    })
  },
  [Matriz innovación vs. madurez (valoración propia). La demo está en TRL 4–5; el piloto real con datos Smart Steps lo llevaría a TRL 6.],
)
#estimado[Las posiciones son una valoración cualitativa del equipo, no una medición.]

= Riesgos éticos y de privacidad

#tabla(
  columns: (1fr, 1.5fr, 1.5fr),
  [Riesgo], [Descripción], [Mitigación],
  [Privacidad de la movilidad], [Los datos de movilidad podrían re-identificar personas si se desagregan en exceso.], [Sólo *datos agregados y anonimizados* por celda H3 con umbral mínimo de conteo; sin trayectorias individuales. Cumplimiento de RGPD y evaluación de impacto (EIPD) previa a producción.],
  [Sesgo de equidad], [Los barrios menos documentados (OSM incompleto, padrón desfasado) pueden salir mal ponderados.], [Índice de vulnerabilidad en el score, métricas por distrito, revisión de equidad en cada versión del modelo.],
  [Gentrificación verde], [Un parque nuevo puede subir precios y desplazar a residentes vulnerables.], [Mostrar efecto sobre vulnerabilidad; recomendar medidas de acompañamiento; decisión humana siempre.],
  [Confianza excesiva en el modelo], [El técnico podría aceptar propuestas sin criterio.], [Incertidumbre visible, factores SHAP, texto explicativo y obligación de registrar la decisión.],
  [Datos sintéticos en la demo], [Los resultados podrían tomarse por reales.], [Etiquetado «sintético» en la web y en cada documento; no usar para decisiones reales.],
)

#riesgo[
  *Límite del experimento.* Esta demo no usa datos personales ni datos reales de Smart Steps. Cualquier piloto real exige acuerdo de datos, base jurídica, EIPD y revisión de seguridad.
]

#v(10pt)
#historial((
  ("0.1", "25-10-2026", "Propuesta inicial en el plan."),
  ("0.2", "25-10-2026", "Flujo HITL, data fusion, matriz de innovación y riesgos éticos."),
))
