# Tokens de marca de VerdeScope

Proyecto independiente, sin afiliación con Telefónica ni con ninguna otra empresa. En portadas se usa el texto "VerdeScope Lab" compuesto con la tipografía + un punto/círculo
como recurso gráfico. No usar logotipos ni nombres de marcas de terceros como identidad.

## Tipografía
- Principal (SIL OFL): **Hanken Grotesk** (Google Fonts), pesos 300/400/500/700.
  Ficheros en `documentacion/fuentes/` (Typst) y cargada desde Google Fonts en la web.
- Monoespaciada para código: **JetBrains Mono** (OFL) si está disponible; si no, la de sistema.

## Color
| token | hex | uso |
|---|---|---|
| `blue` | `#0066FF` | color principal, titulares, acciones |
| `blue-dark` | `#0B2739` | fondos oscuros, texto de títulos |
| `blue-light` | `#E5F0FF` | fondos de bloques, tablas cebra |
| `blue-mid` | `#8DB9FB` | elementos secundarios de diagramas |
| `grey-900` | `#1A1A1A` | texto cuerpo |
| `grey-600` | `#58617A` | texto secundario, pies |
| `grey-200` | `#DDDDDD` | líneas, bordes |
| `white` | `#FFFFFF` | fondo |
| `ok` | `#00A88E` | sin déficit / aprobado |
| `review` | `#F2A900` | revisar |
| `critical` | `#E63780` | déficit crítico / rechazado (magenta) |

Escala secuencial de déficit (0→1): `#E5F0FF` → `#8DB9FB` → `#F2A900` → `#E63780`.

## Estilo
- Mucho blanco, titulares grandes en `blue-dark` peso 700, subrayados/acentos en `blue`.
- Esquinas redondeadas (8 px / 2 mm), sin sombras pesadas, iconografía lineal.
- Documentos A4: portada a sangre en `blue` con título blanco; cabecera con "VerdeScope · Proyecto independiente"
  y pie con nº de página y "Proyecto independiente — sin afiliación con Telefónica · Experimento".
