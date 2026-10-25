// Componentes reutilizables para diagramas (sobre fletcher), paleta Telefónica.
#import "@preview/fletcher:0.5.8": diagram, node, edge
#import "telefonica.typ": *

#let tonos = (
  azul: (fill: azul, stroke: azul, txt: white),
  claro: (fill: azul-cl, stroke: azul-med, txt: azul-osc),
  oscuro: (fill: azul-osc, stroke: azul-osc, txt: white),
  medio: (fill: azul-med, stroke: azul-med, txt: azul-osc),
  ok: (fill: ok.lighten(80%), stroke: ok, txt: azul-osc),
  revisar: (fill: revisar.lighten(78%), stroke: revisar, txt: azul-osc),
  critico: (fill: critico.lighten(82%), stroke: critico, txt: azul-osc),
  blanco: (fill: white, stroke: azul-med, txt: azul-osc),
  gris: (fill: rgb("#F3F4F7"), stroke: gris2, txt: gris6),
)

/// Nodo con tono corporativo. `pos`: coordenada fletcher; `cuerpo`: contenido.
#let nodo(pos, cuerpo, tono: "claro", w: auto, h: auto, forma: rect, tam: 8.5pt, ..args) = {
  let t = tonos.at(tono)
  node(pos, align(center, { show raw: it => text(font: mono, it.text); text(size: tam, fill: t.txt, cuerpo) }),
    fill: t.fill, stroke: 0.9pt + t.stroke, corner-radius: 5pt, shape: forma,
    inset: 6pt, width: w, height: h, ..args)
}

/// Contenedor (agrupa nodos). `esquinas`: ((x0,y0),(x1,y1)); el título se coloca en una fila
/// superior propia (y0 - 0.55), que queda incluida en el recuadro.
#let contenedor(esquinas, titulo, tono: "gris", ..args) = {
  let t = tonos.at(tono)
  let (a, b) = esquinas
  let xm = (a.at(0) + b.at(0)) / 2
  (
    node((a.at(0), a.at(1) - 0.62), box(width: 0pt, height: 0pt, place(top + left, dx: -17mm, dy: -4pt, box(width: 120mm, text(size: 7.5pt, weight: 700, fill: azul, tracking: 0.4pt, upper(titulo))))),
      stroke: none, inset: 0pt, snap: false),
    node(enclose: (esquinas.at(0), esquinas.at(1), (a.at(0), a.at(1) - 0.62)), none,
      fill: t.fill, stroke: (paint: t.stroke, thickness: 0.9pt, dash: "dashed"),
      corner-radius: 8pt, inset: 10pt, snap: false, layer: -1, ..args),
  ).join()
}

/// Flecha entre nodos. Tipos: "->", "<->", "--", "..>" etc.
#let flecha(a, b, tipo: "->", etiqueta: none, col: azul-osc, ..args) = {
  edge(a, b, tipo, label: if etiqueta != none { text(size: 7.5pt, fill: gris6, etiqueta) },
    stroke: 0.9pt + col, label-fill: white, ..args)
}

/// Diagrama con espaciado y estilo por defecto; se reduce automáticamente si excede el ancho útil.
#let dg(..args, sp: (24mm, 14mm)) = layout(size => {
  let d = diagram(spacing: sp, node-inset: 6pt, edge-corner-radius: 4pt, ..args)
  let m = measure(d)
  let f = if m.width > size.width { size.width / m.width * 100% } else { 100% }
  align(center, scale(f, reflow: true, d))
})
