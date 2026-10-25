#import "tema/telefonica.typ": *
#import "tema/diagramas.typ": *

#show: documento.with(
  titulo: "Viabilidad económica",
  subtitulo: "CAPEX, OPEX, modelo SaaS, escenarios, ROI y coste-beneficio",
  version: "0.2", fecha: "25 de octubre de 2026",
)

// ---------- Modelo de cálculo (todas las cifras en miles de euros, k€) ----------
#let k(x, d: 0) = {
  let neg = x < 0
  let v = calc.abs(x)
  let s = if d == 0 { str(int(calc.round(v))) } else { str(calc.round(v, digits: d)) }
  let partes = s.split(".")
  let ent = partes.at(0)
  let n = ent.len()
  let out = ""
  for (i, c) in ent.clusters().enumerate() {
    if i > 0 and calc.rem(n - i, 3) == 0 { out += "." }
    out += c
  }
  (if neg { "−" } else { "" }) + out + (if d > 0 and partes.len() > 1 { "," + partes.at(1) } else { "" })
}

// Equipo MVP → producto (6 meses). Coste empresa mensual por perfil (k€/mes)
#let equipo = (
  ("Project manager", 1, 7.0),
  ("Data scientist", 2, 6.5),
  ("Ingeniero geoespacial / datos", 1, 6.2),
  ("Desarrollador frontend", 1, 5.8),
  ("UX / diseño", 0.5, 5.5),
)
#let meses = 6
#let coste-equipo = equipo.map(e => e.at(1) * e.at(2) * meses).sum()
#let otros = (("Cloud de desarrollo y pruebas", 12.0), ("Legal, EIPD y seguridad", 15.0), ("Licencias y herramientas", 6.0))
#let subtotal = coste-equipo + otros.map(o => o.at(1)).sum()
#let conting = 0.15 * subtotal
#let capex = subtotal + conting

// Tramos SaaS por población (k€ por ciudad y año)
#let tramos = (
  (nombre: "S (< 100.000 hab.)", precio: 24.0, nube: 2.0, datos: 6.0, soporte: 5.0, mix: 0.40),
  (nombre: "M (100.000–500.000)", precio: 60.0, nube: 5.0, datos: 14.0, soporte: 10.0, mix: 0.40),
  (nombre: "L (> 500.000 hab.)", precio: 140.0, nube: 12.0, datos: 30.0, soporte: 22.0, mix: 0.20),
)
#let opex-t(t) = t.nube + t.datos + t.soporte
#let ingreso-medio = tramos.map(t => t.precio * t.mix).sum()
#let opex-medio = tramos.map(t => opex-t(t) * t.mix).sum()
#let fijos = 170.0  // equipo de producto mínimo + infraestructura común (k€/año)
#let comercial = 0.10  // % de ingresos

#let escenarios = (
  (n: "Pesimista", col: critico, c: (1, 2, 4, 6, 8)),
  (n: "Base", col: azul, c: (2, 5, 10, 16, 24)),
  (n: "Optimista", col: ok, c: (3, 9, 20, 35, 55)),
)
#let flujo(c) = c * (ingreso-medio - opex-medio) - fijos - comercial * c * ingreso-medio
#let calcular(esc) = {
  let flujos = esc.c.map(flujo)
  let acum = ()
  let s = -capex
  for f in flujos { s += f; acum.push(s) }
  // payback con interpolación lineal
  let pb = none
  let previo = -capex
  for (i, a) in acum.enumerate() {
    if pb == none and a >= 0 { pb = i + (-previo) / (a - previo) }
    previo = a
  }
  let ingresos = esc.c.map(c => c * ingreso-medio)
  (flujos: flujos, acum: acum, pb: pb, roi: (acum.last()) / capex, ingresos: ingresos)
}
#let res = escenarios.map(calcular)

= Aviso y supuestos

#riesgo[
  *Todas las cifras de este documento son estimaciones con supuestos explícitos, no datos de mercado ni compromisos comerciales.* Los costes de personal, los precios y el número de ciudades son hipótesis de trabajo del equipo para evaluar la viabilidad; deben validarse con ventas, finanzas y clientes piloto. El cálculo está parametrizado en el propio documento (Typst), de modo que cambiar un supuesto recalcula todas las tablas.
]

#tabla(
  columns: (1fr, 1fr),
  [Supuesto], [Valor],
  [Horizonte], [5 años tras el MVP],
  [Equipo MVP → producto], [#meses meses; tarifas coste empresa en España (estimación)],
  [Mix de ciudades], [40 % tramo S · 40 % M · 20 % L],
  [Costes fijos de producto], [#k(fijos) k€/año (equipo mínimo de mantenimiento + infraestructura común)],
  [Coste comercial], [#calc.round(comercial * 100) % de los ingresos],
  [Impuestos, amortización y financiación], [No considerados (análisis antes de impuestos)],
)

= CAPEX: desarrollo MVP → producto

#tabla(
  columns: (1fr, auto, auto, auto),
  [Concepto], [Dedicación], [k€/mes], [Total k€],
  ..equipo.map(e => ([#e.at(0)], [#e.at(1) FTE], [#k(e.at(2), d: 1)], [#k(e.at(1) * e.at(2) * meses)])).flatten(),
  ..otros.map(o => ([#o.at(0)], [—], [—], [#k(o.at(1))])).flatten(),
  [Contingencia (15 %)], [], [], [#k(conting)],
  table.cell(fill: azul-med)[*CAPEX total*], table.cell(fill: azul-med)[], table.cell(fill: azul-med)[], table.cell(fill: azul-med)[*#k(capex) k€*],
)
#estimado[Tarifas de coste empresa mensuales orientativas del mercado español; sin recargo comercial.]

= OPEX por ciudad y modelo de negocio SaaS

El producto se comercializa como *SaaS anual por ciudad*, con precio por tramo de población. Los datos de movilidad (Smart Steps) se incluyen como módulo y su coste se repercute en el OPEX.

#tabla(
  columns: (1.4fr, auto, auto, auto, auto, auto),
  [Tramo], [Precio k€/año], [Nube], [Datos], [Soporte], [Margen bruto],
  ..tramos.map(t => ([#t.nombre], [#k(t.precio)], [#k(t.nube)], [#k(t.datos)], [#k(t.soporte)], [#k(t.precio - opex-t(t)) (#calc.round((t.precio - opex-t(t)) / t.precio * 100) %)])).flatten(),
  table.cell(fill: azul-cl)[*Media ponderada*], table.cell(fill: azul-cl)[*#k(ingreso-medio, d: 1)*], table.cell(fill: azul-cl, colspan: 3)[OPEX medio: *#k(opex-medio, d: 1) k€*], table.cell(fill: azul-cl)[*#k(ingreso-medio - opex-medio, d: 1) k€*],
)

#nota[
  *Qué incluye el OPEX por ciudad.* Nube: cómputo batch mensual, almacenamiento COG/Zarr, PostGIS y CDN. Datos: licencias de Smart Steps y de fuentes comerciales (los datos abiertos Sentinel-2/Landsat/INE/OSM no tienen coste de licencia). Soporte: operación de MLOps, atención a usuarios y revisión mensual del modelo.
]

= Escenarios, ROI y payback

#tabla(
  columns: (1fr, auto, auto, auto, auto, auto),
  [Ciudades acumuladas], [Año 1], [Año 2], [Año 3], [Año 4], [Año 5],
  ..escenarios.map(e => ([*#e.n*], ..e.c.map(c => [#c]))).flatten(),
)

#tabla(
  columns: (1fr, auto, auto, auto, auto, auto),
  [Flujo neto anual (k€)], [Año 1], [Año 2], [Año 3], [Año 4], [Año 5],
  ..escenarios.zip(res).map(((e, r)) => ([*#e.n*], ..r.flujos.map(f => [#k(f)]))).flatten(),
)

#tabla(
  columns: (1fr, auto, auto, auto, auto, auto),
  [Flujo acumulado tras CAPEX (k€)], [Año 1], [Año 2], [Año 3], [Año 4], [Año 5],
  ..escenarios.zip(res).map(((e, r)) => ([*#e.n*], ..r.acum.map(f => [#k(f)]))).flatten(),
)

#tabla(
  columns: (1fr, auto, auto, auto),
  [Indicador (5 años)], [Pesimista], [Base], [Optimista],
  [Ingresos acumulados (k€)], ..res.map(r => [#k(r.ingresos.sum())]),
  [Beneficio neto acumulado tras CAPEX (k€)], ..res.map(r => [#k(r.acum.last())]),
  [*ROI a 5 años* (beneficio neto / CAPEX)], ..res.map(r => [*#calc.round(r.roi * 100) %*]),
  [*Payback*], ..res.map(r => if r.pb == none [no se alcanza en 5 años] else [#str(calc.round(r.pb, digits: 1)).replace(".", ",") años]),
)

#figura(
  {
    let W = 380pt
    let H = 170pt
    let todos = res.map(r => r.acum).flatten() + (-capex,)
    let ymin = calc.min(..todos)
    let ymax = calc.max(..todos)
    let ymin = calc.floor(ymin / 500) * 500
    let ymax = calc.ceil(ymax / 500) * 500
    let px(i) = 32pt + i * (W - 32pt) / 5
    let py(v) = H - (v - ymin) / (ymax - ymin) * H
    box(width: W + 20pt, height: H + 40pt, {
      // rejilla
      for v in range(int(ymin), int(ymax) + 1, step: 500) {
        place(top + left, dy: py(v), line(start: (32pt, 0pt), end: (W, 0pt), stroke: if v == 0 { 1pt + azul-osc } else { 0.4pt + gris2 }))
        place(top + left, dx: 0pt, dy: py(v) - 5pt, text(size: 7pt, fill: gris6)[#k(v)])
      }
      for i in range(0, 6) {
        place(top + left, dx: px(i) - 8pt, dy: H + 5pt, text(size: 7.5pt, fill: gris6)[#if i == 0 [Inicio] else [Año #i]])
      }
      for (e, r) in escenarios.zip(res) {
        let pts = ((0, -capex),) + r.acum.enumerate().map(((i, a)) => (i + 1, a))
        for j in range(0, pts.len() - 1) {
          let (x1, y1) = pts.at(j)
          let (x2, y2) = pts.at(j + 1)
          place(top + left, line(start: (px(x1), py(y1)), end: (px(x2), py(y2)), stroke: 2pt + e.col))
        }
        for (x, y) in pts {
          place(top + left, dx: px(x) - 2.5pt, dy: py(y) - 2.5pt, circle(radius: 2.5pt, fill: e.col, stroke: none))
        }
      }
      place(top + left, dx: 40pt, dy: H + 22pt, stack(dir: ltr, spacing: 14pt,
        ..escenarios.map(e => box[#box(width: 14pt, height: 3pt, fill: e.col, baseline: -1pt) #text(size: 8pt)[ #e.n]])))
    })
  },
  [Flujo de caja acumulado tras CAPEX (k€) por escenario. Estimación con los supuestos de este documento.],
)

#figura(
  {
    let r = res.at(1)
    let W = 380pt
    let H = 120pt
    let costes = escenarios.at(1).c.map(c => c * opex-medio + fijos + comercial * c * ingreso-medio)
    let vmax = calc.max(..r.ingresos, ..costes)
    let vmax = calc.ceil(vmax / 500) * 500
    let bw = 22pt
    box(width: W, height: H + 30pt, {
      place(top + left, dy: H, line(length: W, stroke: 0.8pt + azul-osc))
      for i in range(0, 5) {
        let x = 20pt + i * 72pt
        let hi = r.ingresos.at(i) / vmax * H
        let hc = costes.at(i) / vmax * H
        place(top + left, dx: x, dy: H - hi, rect(width: bw, height: hi, fill: azul, radius: (top: 2pt)))
        place(top + left, dx: x + bw + 3pt, dy: H - hc, rect(width: bw, height: hc, fill: critico, radius: (top: 2pt)))
        place(top + left, dx: x + 2pt, dy: H - hi - 11pt, text(size: 7pt, fill: azul-osc)[#k(r.ingresos.at(i))])
        place(top + left, dx: x + bw + 5pt, dy: H - hc - 11pt, text(size: 7pt, fill: azul-osc)[#k(costes.at(i))])
        place(top + left, dx: x + 8pt, dy: H + 5pt, text(size: 8pt, fill: gris6)[Año #(i + 1)])
      }
      place(top + left, dx: 20pt, dy: H + 18pt, stack(dir: ltr, spacing: 14pt,
        box[#box(width: 10pt, height: 8pt, fill: azul) #text(size: 8pt)[ Ingresos]],
        box[#box(width: 10pt, height: 8pt, fill: critico) #text(size: 8pt)[ Costes operativos (OPEX + fijos + comercial)]]))
    })
  },
  [Escenario base: ingresos y costes operativos anuales (k€).],
)

*Lectura.* En el escenario base la inversión se recupera hacia el año #str(calc.round(res.at(1).pb, digits: 1)).replace(".", ",") y el ROI a cinco años es #calc.round(res.at(1).roi * 100) %. El escenario pesimista no recupera la inversión en cinco años con el equipo fijo supuesto: la sensibilidad principal es el *número de ciudades* y el *coste de los datos de movilidad*.

= Coste-beneficio para el ayuntamiento

== Coste de un parque de bolsillo (estimación)

#tabla(
  columns: (1fr, auto, auto),
  [Partida], [€/m²], [Comentario],
  [Desmontaje y preparación del suelo], [60–120], [Según el estado de la parcela],
  [Sustrato, plantación y arbolado], [90–160], [Especies de bajo consumo hídrico],
  [Riego eficiente y mobiliario], [50–90], [Riego por goteo, bancos, sombra],
  [Proyecto, dirección y contingencia], [30–60], [10–15 % del total],
  [*Total orientativo*], [*230–430*], [Se toma 330 €/m² como valor central],
)
#estimado[Rangos orientativos de obra de urbanización blanda en España; deben contrastarse con los precios unitarios municipales vigentes.]

== Ejemplo: programa de 10 parques de 400 m²

#let m2 = 10 * 400
#let coste-prog = m2 * 330 / 1000
#let ben = ((n: "Salud y bienestar (reducción de exposición a calor y contaminación)", v: 15), (n: "Calor y energía (menor demanda de refrigeración, sombra)", v: 10), (n: "Valor inmobiliario y recaudación asociada", v: 20))
#let ben-m2 = ben.map(b => b.v).sum()
#let ben-anual = m2 * ben-m2 / 1000
#let saas-m = 60.0
#let consultoria = 90.0

#tabla(
  columns: (1fr, auto),
  [Concepto], [Valor],
  [Superficie total del programa], [#k(m2) m²],
  [Inversión en obra (330 €/m²)], [#k(coste-prog) k€],
  ..ben.map(b => ([Beneficio anual: #b.n], [#b.v €/m²·año])).flatten(),
  [Beneficio social y fiscal anual estimado], [#k(ben-anual) k€/año],
  [Retorno simple de la inversión], [#str(calc.round(coste-prog / ben-anual, digits: 1)).replace(".", ",") años],
  [Coste anual de VerdeScope (tramo M)], [#k(saas-m) k€/año],
  [Coste de un estudio manual equivalente de consultoría], [≈ #k(consultoria) k€ por estudio],
)
#estimado[Los beneficios por m² son hipótesis ilustrativas de valoración de servicios ecosistémicos, no mediciones; deben calibrarse con literatura y datos locales. El estudio manual se estima en 60–120 k€ para una ciudad media y no es continuo (sin series temporales ni reevaluación).]

#decision[
  *Valor para el ayuntamiento.* El beneficio principal de VerdeScope no es abaratar la obra sino *acertar dónde invertir primero*: concentrar las parcelas en las celdas con mayor población servida y calor mitiga el riesgo de gastar en zonas de bajo impacto. Con los supuestos anteriores, el coste anual de la herramienta (#k(saas-m) k€) equivale al #str(calc.round(saas-m / coste-prog * 100, digits: 1)).replace(".", ",") % de la inversión del programa de ejemplo y se compara con un estudio manual puntual de #k(consultoria) k€.
]

#atencion[
  El análisis no incluye subvenciones (p. ej. fondos europeos de renaturalización), que pueden mejorar el caso, ni el coste de oportunidad del suelo.
]

#v(10pt)
#historial((
  ("0.1", "25-10-2026", "Estructura prevista en el plan."),
  ("0.2", "25-10-2026", "Modelo paramétrico de CAPEX/OPEX, tramos SaaS, tres escenarios, ROI, payback y coste-beneficio municipal."),
))
