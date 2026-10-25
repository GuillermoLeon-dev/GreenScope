# Tokens de marca (inspirados en la identidad Telefónica 2021+)

Documento interno de un experimento; no usar el logotipo registrado de Telefónica. En portadas se
usa el texto "Telefónica" compuesto con la tipografía + un punto/círculo azul como recurso gráfico.

## Tipografía
- Corporativa: Telefónica Sans (TT Hoves personalizada, propietaria) → **no disponible**.
- Sustituta libre (SIL OFL): **Hanken Grotesk** (Google Fonts), pesos 300/400/500/700.
  Ficheros en `documentacion/fuentes/` (Typst) y cargada desde Google Fonts en la web.
- Monoespaciada para código: **JetBrains Mono** (OFL) si está disponible; si no, la de sistema.

## Color
| token | hex | uso |
|---|---|---|
| `blue` (Telefónica Blue) | `#0066FF` | color principal, titulares, acciones |
| `blue-dark` | `#0B2739` | fondos oscuros, texto de títulos |
| `blue-light` | `#E5F0FF` | fondos de bloques, tablas cebra |
| `blue-mid` | `#8DB9FB` | elementos secundarios de diagramas |
| `grey-900` | `#1A1A1A` | texto cuerpo |
| `grey-600` | `#58617A` | texto secundario, pies |
| `grey-200` | `#DDDDDD` | líneas, bordes |
| `white` | `#FFFFFF` | fondo |
| `ok` | `#00A88E` | sin déficit / aprobado |
| `review` | `#F2A900` | revisar |
| `critical` | `#E63780` | déficit crítico / rechazado (tono Telefónica magenta-pink) |

Escala secuencial de déficit (0→1): `#E5F0FF` → `#8DB9FB` → `#F2A900` → `#E63780`.

## Estilo
- Mucho blanco, titulares grandes en `blue-dark` peso 700, subrayados/acentos en `blue`.
- Esquinas redondeadas (8 px / 2 mm), sin sombras pesadas, iconografía lineal.
- Documentos A4: portada a sangre en `blue` con título blanco; cabecera con "VerdeScope · Telefónica Tech"
  y pie con nº de página y "Uso interno — Experimento".
