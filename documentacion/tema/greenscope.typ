// GreenScope · tema documental propio del proyecto
// Tipografía: Hanken Grotesk (SIL OFL).

#let azul = rgb("#0066FF")
#let azul-osc = rgb("#0B2739")
#let azul-cl = rgb("#E5F0FF")
#let azul-med = rgb("#8DB9FB")
#let gris9 = rgb("#1A1A1A")
#let gris6 = rgb("#58617A")
#let gris2 = rgb("#DDDDDD")
#let ok = rgb("#00A88E")
#let revisar = rgb("#F2A900")
#let critico = rgb("#E63780")

#let fuente = "Hanken Grotesk"
#let mono = ("JetBrains Mono", "DejaVu Sans Mono")

// ---------- Etiquetas de veracidad ----------
#let _chip(txt, col) = box(
  fill: col.lighten(82%), stroke: 0.6pt + col, radius: 3pt,
  inset: (x: 4pt, y: 1.5pt), baseline: 1.5pt,
  text(size: 7.5pt, weight: 700, fill: col.darken(25%), tracking: 0.4pt, upper(txt)),
)
#let dato(body) = [#body #_chip("dato verificado", ok)]
#let estimado(body) = [#body #_chip("estimación", revisar)]
#let tag-verificado = _chip("dato verificado", ok)
#let tag-estimado = _chip("estimación", revisar)
#let tag-sintetico = _chip("dato sintético", azul)

// ---------- Callouts ----------
#let _callout(titulo, col, body) = block(
  width: 100%, breakable: false, inset: (x: 12pt, y: 9pt), radius: 6pt,
  fill: col.lighten(88%), stroke: (left: 3.5pt + col),
  [#text(size: 8.5pt, weight: 700, fill: col.darken(20%), tracking: 0.6pt)[#upper(titulo)] \
   #v(2pt) #body],
)
#let nota(body) = _callout("Nota", azul, body)
#let decision(body) = _callout("Decisión", ok, body)
#let riesgo(body) = _callout("Riesgo", critico, body)
#let atencion(body) = _callout("Atención", revisar, body)

// ---------- Tablas ----------
#let tabla(..args) = {
  show table.cell.where(y: 0): set text(fill: white, weight: 700)
  set par(justify: false)
  set text(size: 9.5pt)
  table(
    stroke: (x, y) => (bottom: 0.5pt + gris2),
    fill: (x, y) => if y == 0 { azul } else if calc.odd(y) { azul-cl } else { white },
    inset: (x: 6pt, y: 5pt),
    align: left + horizon,
    ..args,
  )
}

// ---------- Historial de versiones ----------
#let historial(filas) = [
  #text(size: 9pt, weight: 700, fill: azul)[HISTORIAL DE VERSIONES]
  #v(-2pt)
  #tabla(
    columns: (auto, auto, 1fr),
    [Versión], [Fecha], [Cambios],
    ..filas.map(f => (f.at(0), f.at(1), f.at(2))).flatten(),
  )
]

// ---------- Figuras ----------
#let figura(body, pie) = figure(body, caption: pie, supplement: [Figura], kind: image)

// ---------- Plantilla ----------
#let documento(
  titulo: "", subtitulo: "", version: "0.1", fecha: "", autor: "GreenScope Labs · proyecto independiente",
  indice: true, cuerpo,
) = {
  set document(title: titulo + " — GreenScope", author: autor)
  set text(font: fuente, size: 10.5pt, lang: "es", fill: gris9)
  set par(justify: true, leading: 0.68em, spacing: 0.95em)

  // ---- Portada a sangre ----
  page(margin: 0pt, fill: azul, header: none, footer: none)[
    #place(top + left, dx: 0pt, dy: 0pt, rect(width: 100%, height: 100%, fill: azul, stroke: none))
    // recurso gráfico: círculos concéntricos
    #place(top + right, dx: 60pt, dy: -60pt, circle(radius: 150pt, fill: rgb("#1A7AFF"), stroke: none))
    #place(top + right, dx: 20pt, dy: 190pt, circle(radius: 55pt, fill: white, stroke: none))
    #place(bottom + left, dx: -80pt, dy: 80pt, circle(radius: 170pt, fill: rgb("#0057E0"), stroke: none))
    #place(top + left, dx: 56pt, dy: 64pt)[
      #text(size: 20pt, weight: 700, fill: white, tracking: -0.2pt)[GreenScope]
      #h(1pt) #box(circle(radius: 3pt, fill: white), baseline: 0pt)
      #h(4pt) #text(size: 20pt, weight: 300, fill: white)[Labs]
    ]
    #place(left + horizon, dx: 56pt, dy: -20pt, block(width: 380pt)[
      #text(size: 11pt, weight: 700, fill: azul-cl, tracking: 1.2pt)[#upper[GreenScope · documentación]]
      #v(10pt)
      #text(size: 40pt, weight: 700, fill: white, tracking: -0.6pt)[#titulo]
      #v(6pt)
      #text(size: 15pt, weight: 300, fill: white)[#subtitulo]
    ])
    #place(bottom + left, dx: 56pt, dy: -56pt)[
      #set text(fill: white, size: 10pt)
      #grid(columns: (auto, auto), column-gutter: 28pt, row-gutter: 4pt,
        text(weight: 700)[Versión], [#version],
        text(weight: 700)[Fecha], [#fecha],
        text(weight: 700)[Autoría], [#autor],
        text(weight: 700)[Estado], [Documento iterativo · experimento personal],
      )
    ]
  ]

  // ---- Cuerpo ----
  set page(
    paper: "a4", margin: (x: 2.3cm, top: 2.6cm, bottom: 2.3cm),
    header: context {
      if counter(page).get().first() > 0 {
        set text(size: 8.5pt, fill: gris6)
        grid(columns: (1fr, auto), [*GreenScope* Labs], [#titulo])
        v(-6pt)
        line(length: 100%, stroke: 0.5pt + gris2)
      }
    },
    footer: context {
      set text(size: 8.5pt, fill: gris6)
      line(length: 100%, stroke: 0.5pt + gris2)
      v(-4pt)
      grid(columns: (1fr, auto),
        [Proyecto independiente — sin afiliación con Telefónica · Experimento],
        [pág. #counter(page).display() / #counter(page).final().first()])
    },
  )
  counter(page).update(1)

  show heading: set text(font: fuente, fill: azul-osc, weight: 700)
  show heading.where(level: 1): it => {
    pagebreak(weak: true)
    v(4pt)
    block(below: 14pt)[
      #if it.numbering != none [#text(size: 22pt, weight: 300, fill: azul)[#counter(heading).display() #h(4pt)]]#text(size: 22pt, tracking: -0.3pt)[#it.body]
      #v(-2pt)
      #line(length: 36pt, stroke: 3pt + azul)
    ]
  }
  show heading.where(level: 2): it => block(above: 18pt, below: 8pt, text(size: 14pt)[#text(fill: azul)[#counter(heading).display()] #h(3pt) #it.body])
  show heading.where(level: 3): it => block(above: 12pt, below: 6pt, text(size: 11.5pt, fill: azul)[#counter(heading).display() #h(3pt) #it.body])
  set heading(numbering: "1.1")

  show link: it => text(fill: azul, underline(it))
  show raw: set text(font: mono, size: 8.8pt)
  show raw.where(block: true): it => block(width: 100%, fill: azul-cl, radius: 5pt, inset: 9pt, it)
  show raw.where(block: false): it => box(fill: azul-cl, radius: 2pt, inset: (x: 3pt), outset: (y: 2.5pt), it)
  set list(marker: text(fill: azul, weight: 700)[•], indent: 4pt, body-indent: 6pt)
  set enum(indent: 4pt, body-indent: 6pt)
  show figure.caption: set text(size: 8.8pt, fill: gris6)
  show figure: set block(above: 14pt, below: 14pt)
  set figure(gap: 8pt)

  if indice {
    text(size: 22pt, weight: 700, fill: azul-osc, tracking: -0.3pt)[Contenido]
    v(-4pt); line(length: 36pt, stroke: 3pt + azul); v(6pt)
    show outline.entry.where(level: 1): set text(weight: 700, fill: azul-osc)
    outline(title: none, depth: 2, indent: 1em)
  }

  cuerpo
}

// Indicador de capacidad: 2 = nativa, 1 = parcial, 0 = no evidenciada
#let cap(n) = align(center, box(baseline: 2pt, circle(radius: 4.5pt,
  fill: if n == 2 { azul } else if n == 1 { azul-med } else { white }, stroke: 1pt + azul)))
