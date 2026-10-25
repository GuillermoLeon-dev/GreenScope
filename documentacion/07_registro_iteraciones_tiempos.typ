#import "tema/greenscope.typ": *
#import "tema/diagramas.typ": *

#show: documento.with(
  titulo: "Registro de iteraciones y tiempos",
  subtitulo: "Cronometraje del experimento, Gantt e historial de versiones",
  version: "0.3", fecha: "25 de octubre de 2026",
)

// ---------- Lectura del cronómetro (build.py copia tiempos/cronometro.log a datos/) ----------
#let crudo = read("datos/cronometro.log").trim().split("\n").slice(1).map(l => l.trim()).filter(l => l != "")
#let seg(ts) = {
  // 2026-10-25T02:28:22+02:00 → segundos desde la medianoche del día 1 del mes (suficiente para un experimento de pocos días)
  let dia = int(ts.slice(8, 10))
  let h = int(ts.slice(11, 13))
  let m = int(ts.slice(14, 16))
  let s = int(ts.slice(17, 19))
  dia * 86400 + h * 3600 + m * 60 + s
}
#let hora(ts) = ts.slice(11, 19)
#let eventos = crudo.map(l => {
  let p = l.split(",")
  (etapa: p.at(0), ev: p.at(1), ts: p.at(2), t: seg(p.at(2)))
})
#let orden = eventos.map(e => e.etapa).dedup()
#let t-final-log = calc.max(..eventos.map(e => e.t))
#let t-ini = calc.min(..eventos.map(e => e.t))
#let etapas = orden.map(n => {
  let ini = eventos.filter(e => e.etapa == n and e.ev == "start")
  let fin = eventos.filter(e => e.etapa == n and e.ev == "stop")
  let a = ini.first()
  let b = if fin.len() > 0 { fin.last() } else { none }
  (nombre: n, ini: a.t, fin: if b == none { t-final-log } else { b.t }, abierta: b == none,
   h-ini: hora(a.ts), h-fin: if b == none { "—" } else { hora(b.ts) })
})
#let mmss(s) = {
  let m = calc.quo(s, 60)
  let r = calc.rem(s, 60)
  [#m min #r s]
}
#let etiquetas = (
  "0_preparacion": "Preparación del entorno",
  "1_analisis_mercado_estado_arte": "Análisis de mercado y estado del arte",
  "2_diseno_contratos": "Diseño y contratos",
  "3_impl_backend_ml": "Implementación backend + ML",
  "4_impl_frontend": "Implementación frontend",
  "5_documentacion": "Documentación (Typst)",
  "6_integracion_verificacion": "Integración y verificación",
  "7_cierre_publicacion": "Cierre: README, git y recompilación",
)
#let etiqueta(n) = etiquetas.at(n, default: n)

= Cronometraje del experimento

El experimento registra cada etapa con `tiempos/crono.sh start|stop <etapa>`, que añade una línea `etapa,evento,timestamp` a `tiempos/cronometro.log`. Este documento *lee ese fichero al compilar* y calcula las duraciones; no hay cifras escritas a mano.

#nota[
  *Estado al compilar.* Versión final del experimento: todas las etapas están cerradas. La etapa 1 incluye, además del estudio de mercado, la redacción del plan y las preguntas de aclaración con el usuario (tiempo de espera de respuesta incluido). La compilación final de los PDF ocurre justo después del cierre de la etapa 7 y no se cronometra. *Horas en UTC*: durante el experimento entró el cambio al horario de invierno (25-10-2026, 03:00 CEST → 02:00 CET), por lo que el registro se normalizó a UTC para que las duraciones sean correctas.
]

== Tabla de etapas

#tabla(
  columns: (auto, 1fr, auto, auto, auto),
  [Etapa], [Descripción], [Inicio], [Fin], [Duración],
  ..etapas.map(e => (
    [*#e.nombre.split("_").first()*], [#etiqueta(e.nombre)], [#e.h-ini], [#if e.abierta [en curso] else [#e.h-fin]],
    [#mmss(e.fin - e.ini)#if e.abierta [ (parcial)]],
  )).flatten(),
)

#let total-suma = etapas.map(e => e.fin - e.ini).sum()
#let total-reloj = calc.max(..etapas.map(e => e.fin)) - t-ini
#let paralelas = etapas.filter(e => e.nombre.starts-with("3_") or e.nombre.starts-with("4_") or e.nombre.starts-with("5_"))
#let sec = (c: (total-suma, total-reloj))
#tabla(
  columns: (1fr, auto),
  [Indicador], [Valor],
  [Tiempo total de trabajo (suma de etapas)], [#mmss(total-suma)],
  [Tiempo de reloj (inicio → último evento)], [#mmss(total-reloj)],
  [Ahorro por paralelización (suma − reloj)], [#mmss(total-suma - total-reloj)],
)
#estimado[Las duraciones son tiempo de reloj entre `start` y `stop`; incluyen esperas de agentes y herramientas y no equivalen a esfuerzo humano.]

== Diagrama de Gantt

#figura(
  {
    let W = 400pt
    let fila = 22pt
    let H = fila * etapas.len() + 24pt
    let dur = calc.max(total-reloj, 1)
    let x(t) = 150pt + (t - t-ini) / dur * (W - 150pt)
    let cols = (azul-med, azul-med, azul-med, azul, azul, azul, ok)
    box(width: W + 10pt, height: H + 10pt, {
      // rejilla de minutos
      let pasos = 6
      for i in range(0, pasos + 1) {
        let t = t-ini + calc.round(dur * i / pasos)
        let xx = x(t)
        place(top + left, dx: xx, dy: 0pt, line(start: (0pt, 0pt), end: (0pt, fila * etapas.len()), stroke: 0.4pt + gris2))
        let m = calc.quo(calc.round(dur * i / pasos), 60)
        place(top + left, dx: xx - 8pt, dy: fila * etapas.len() + 4pt, text(size: 7pt, fill: gris6)[+#m min])
      }
      for (i, e) in etapas.enumerate() {
        let y = i * fila
        place(top + left, dx: 0pt, dy: y + 5pt, text(size: 8pt, fill: azul-osc)[#etiqueta(e.nombre)])
        let w = calc.max(x(e.fin) - x(e.ini), 3pt)
        place(top + left, dx: x(e.ini), dy: y + 3pt,
          rect(width: w, height: fila - 8pt, radius: 3pt,
            fill: if e.abierta { gradient.linear(azul, white, angle: 0deg) } else { cols.at(calc.min(i, cols.len() - 1)) },
            stroke: none))
        place(top + left, dx: x(e.fin) + 4pt, dy: y + 5pt, text(size: 7pt, fill: gris6)[#mmss(e.fin - e.ini)])
      }
    })
  },
  [Gantt de las etapas registradas. Las etapas 3, 4 y 5 se ejecutaron en paralelo con subagentes; la barra degradada indica etapa abierta al compilar.],
)

#figura(
  dg(sp: (22mm, 12mm),
    nodo((0, 0), [0–2\ Preparación,\ mercado, contratos], tono: "claro"),
    nodo((1, -1), [3 Backend + ML], tono: "azul"),
    nodo((1, 0), [4 Frontend], tono: "azul"),
    nodo((1, 1), [5 Documentación], tono: "azul"),
    nodo((2, 0), [6 Integración\ y pruebas\ (orquestador)], tono: "ok"),
    flecha((0, 0), (1, -1)), flecha((0, 0), (1, 0)), flecha((0, 0), (1, 1)),
    flecha((1, -1), (2, 0)), flecha((1, 0), (2, 0)), flecha((1, 1), (2, 0)),
  ),
  [Estructura de dependencias: tras fijar los contratos, tres equipos trabajan en paralelo.],
)

= Iteraciones del experimento

#tabla(
  columns: (auto, auto, 1fr),
  [Versión], [Fecha], [Contenido],
  [v0.1], [25-10-2026], [*Plan.* Estudio de mercado, decisiones con el usuario (Madrid, datos híbridos, Hanken Grotesk), contratos de datos y de marca.],
  [v0.2], [25-10-2026], [*Implementación paralela.* Orquestación por un agente Opus 5.5; tres subagentes Sonnet 5.5 en paralelo: backend + ML, frontend estático y documentación Typst. Cada uno registra su etapa con `crono.sh`.],
  [v0.3], [25-10-2026], [*Integración.* Pipeline real (OSM vía Overpass + fuentes sintéticas), 54 tests y lint en verde, web probada bajo subruta tipo GitHub Pages con datos reales (umbrales, decisiones con trazabilidad), revisión y corrección de referencias del documento 01.],
  [v0.4], [25-10-2026], [*Cierre.* README, repositorio git local con commit inicial, workflows de CI y Pages, recompilación de todos los PDF. La subida a GitHub queda a cargo del usuario.],
)

#decision[
  *Documentos iterativos.* Cada documento incluye su propio historial de versiones. Los PDF se regeneran con `build.py` y se copian a `docs/pdf/` para que la web los enlace.
]

= Pendientes y límites conocidos

- Siguiente iteración propuesta: conectores reales (STAC Sentinel-2, INE, Smart Steps) y validación de campo con técnicos municipales.
- Los datos de EO, INE y Smart Steps de la demo son sintéticos; las métricas del documento 04 reflejan esa naturaleza.
- Proyecto independiente, sin afiliación con Telefónica ni con ninguna otra empresa. Tipografía Hanken Grotesk (SIL OFL).

#v(10pt)
#historial((
  ("0.1", "25-10-2026", "Plan e inicio del cronometraje."),
  ("0.2", "25-10-2026", "Lectura automática de cronometro.log, tabla de duraciones, Gantt y tabla de iteraciones."),
  ("0.3", "25-10-2026", "Cierre de todas las etapas, iteraciones v0.3 y v0.4 completadas."),
))
