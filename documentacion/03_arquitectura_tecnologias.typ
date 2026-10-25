#import "tema/telefonica.typ": *
#import "tema/diagramas.typ": *

#show: documento.with(
  titulo: "Arquitectura y tecnologías",
  subtitulo: "Arquitectura hexagonal, flujo de datos, stack y decisiones",
  version: "0.2", fecha: "25 de octubre de 2026",
)

= Visión general

VerdeScope separa con claridad el *dominio* (reglas de negocio puras), los *casos de uso*, la *infraestructura* (datos, modelos, persistencia) y las *interfaces* (API FastAPI y web estática). El resultado es un sistema que se despliega de dos formas con el mismo código de dominio: como *sitio estático* (GitHub Pages) y como *servicio corporativo* con API y base de datos.

= Arquitectura hexagonal

#figura(
  dg(sp: (38mm, 11mm),
    contenedor(((0, 0), (3, 0)), "Interfaces (adaptadores de entrada)", tono: "gris"),
    nodo((0, 0), [*web*\ SPA estática\ MapLibre], tono: "claro"),
    nodo((1, 0), [*api*\ FastAPI\ /api/decisions], tono: "claro"),
    nodo((2, 0), [*cli*\ `verdescope pipeline`], tono: "claro"),
    nodo((3, 0), [*GitHub Actions*\ CI/CD], tono: "claro"),
    contenedor(((0, 2), (3, 2)), "Aplicación (casos de uso)", tono: "gris"),
    nodo((0, 2), [Ejecutar pipeline], tono: "azul"),
    nodo((1, 2), [Clasificar con umbrales], tono: "azul"),
    nodo((2, 2), [Rankear propuestas], tono: "azul"),
    nodo((3, 2), [Registrar decisión], tono: "azul"),
    contenedor(((0, 4), (3, 4)), "Dominio (núcleo puro, sin I/O)", tono: "gris"),
    nodo((0, 4), [Entidades\ Celda · Propuesta], tono: "oscuro"),
    nodo((1, 4), [Reglas\ déficit · umbrales], tono: "oscuro"),
    nodo((2, 4), [Políticas\ priorización], tono: "oscuro"),
    nodo((3, 4), [Puertos\ DataSource\ DecisionStore], tono: "oscuro"),
    contenedor(((0, 6), (3, 6)), "Infraestructura (adaptadores de salida)", tono: "gris"),
    nodo((0, 6), [Conectores\ OSM · Sentinel-2\ INE · Smart Steps], tono: "ok"),
    nodo((1, 6), [Modelos\ LightGBM · STL\ U-Net], tono: "ok"),
    nodo((2, 6), [Persistencia\ localStorage\ PostGIS], tono: "ok"),
    nodo((3, 6), [Exportadores\ GeoJSON · JSON], tono: "ok"),
    flecha((0, 0), (0, 2)), flecha((1, 0), (1, 2)), flecha((2, 0), (2, 2)), flecha((3, 0), (3, 2)),
    flecha((0, 2), (0, 4)), flecha((1, 2), (1, 4)), flecha((2, 2), (2, 4)), flecha((3, 2), (3, 4)),
    flecha((0, 6), (0, 4)), flecha((1, 6), (1, 4)), flecha((2, 6), (2, 4)), flecha((3, 6), (3, 4)),
  ),
  [Capas domain, application, infrastructure, api y web. La regla de dependencia apunta siempre hacia el dominio.],
)

#decision[
  *Regla de dependencia.* `domain` no importa nada de las demás capas ni de librerías de E/S. `application` sólo conoce los puertos del dominio. `infrastructure` y `api` implementan o consumen esos puertos. Esto permite sustituir una fuente sintética por Sentinel-2 real o el almacenamiento local por PostGIS sin tocar reglas de negocio.
]

#tabla(
  columns: (auto, 1fr),
  [Capa], [Responsabilidad y contenido (backend/src/verdescope/)],
  [`domain`], [Entidades (celda, propuesta, decisión), reglas puras (clasificación por umbrales, normalización), políticas de priorización. Probable de probar sin mocks.],
  [`application`], [Casos de uso: ejecutar el pipeline, calcular propuestas, registrar decisiones. Orquesta puertos.],
  [`infrastructure`], [Conectores `DataSource` (OSM/Overpass, STAC, INE, Smart Steps), modelos (LightGBM, SHAP, STL, Theil-Sen), exportadores de artefactos.],
  [`api`], [FastAPI: `GET/POST /api/decisions`; capa opcional para producción.],
  [`web`], [SPA estática en `docs/`: lee los JSON del pipeline, aplica umbrales en el cliente y guarda decisiones mediante `DecisionStore`.],
)

= Diagrama de componentes

#figura(
  dg(sp: (28mm, 13mm),
    nodo((0, 0), [Fuentes\ OSM · EO · INE\ Smart Steps], tono: "claro"),
    nodo((1, 0), [Pipeline offline\ (Python 3.12 · uv)], tono: "azul"),
    nodo((2, 0), [Artefactos\ `docs/data/*.json`], tono: "oscuro"),
    nodo((3, 0), [Web estática\ (navegador)], tono: "azul"),
    nodo((3, 1.4), [`DecisionStore`\ (adaptador)], tono: "revisar"),
    nodo((2, 1.4), [`LocalDecisionStore`\ localStorage + JSON], tono: "ok"),
    nodo((3, 2.8), [`ApiDecisionStore`\ HTTP], tono: "ok"),
    nodo((2, 2.8), [API FastAPI\ + PostGIS], tono: "claro"),
    nodo((1, 1.4), [Reentrenamiento\ (active learning)], tono: "claro"),
    flecha((0, 0), (1, 0)), flecha((1, 0), (2, 0)), flecha((2, 0), (3, 0), etiqueta: "fetch"),
    flecha((3, 0), (3, 1.4)), flecha((3, 1.4), (2, 1.4)), flecha((3, 1.4), (3, 2.8)),
    flecha((3, 2.8), (2, 2.8)), flecha((2, 1.4), (1, 1.4), tipo: "-->"), flecha((2, 2.8), (1, 1.4), tipo: "-->"),
    flecha((1, 1.4), (1, 0), tipo: "-->"),
  ),
  [Componentes y adaptadores. La web elige el adaptador según `config.json` (`api_base_url`: `null` → local).],
)

= Flujo de datos

#figura(
  dg(sp: (24mm, 12mm),
    nodo((0, 0), [1. Ingesta\ `DataSource`], tono: "claro"),
    nodo((1, 0), [2. Armonización\ malla H3 res. 9], tono: "claro"),
    nodo((2, 0), [3. Features\ por celda], tono: "claro"),
    nodo((3, 0), [4. Modelos\ déficit + series], tono: "azul"),
    nodo((3, 1), [5. Propuestas\ ranking], tono: "azul"),
    nodo((2, 1), [6. Exportación\ GeoJSON/JSON], tono: "oscuro"),
    nodo((1, 1), [7. Web\ umbrales + mapa], tono: "ok"),
    nodo((0, 1), [8. Decisión\ + auditoría], tono: "ok"),
    flecha((0, 0), (1, 0)), flecha((1, 0), (2, 0)), flecha((2, 0), (3, 0)), flecha((3, 0), (3, 1)),
    flecha((3, 1), (2, 1)), flecha((2, 1), (1, 1)), flecha((1, 1), (0, 1)),
    flecha((0, 1), (0, 0), tipo: "-->", etiqueta: "etiquetas"),
  ),
  [De la ingesta a la decisión: el bucle se cierra con las decisiones como etiquetas.],
)

Los artefactos siguen un contrato de datos versionado (`schema_version` en `manifest.json`): `cells.geojson` (hexágonos con `deficit_score`, `uncertainty`, `top_factors`…), `proposals.geojson`, `timeseries.json` y `green_areas.geojson`. La clasificación crítico/revisar/ok *no se persiste*: se calcula en el cliente con los umbrales vigentes.

= Tecnologías

== Stack de la demo y objetivo de producción

#figura(
  {
    set par(justify: false)
    let chip(t, col) = box(fill: col.lighten(80%), stroke: 0.8pt + col, radius: 4pt, inset: (x: 5pt, y: 3pt), text(size: 8pt, fill: azul-osc, t))
    let fila(capa, demo, prod) = (
      block(fill: azul-osc, radius: 4pt, inset: 6pt, width: 100%, text(size: 8pt, weight: 700, fill: white, capa)),
      block(width: 100%, inset: 2pt, demo.map(t => chip(t, azul)).join(" ")),
      block(width: 100%, inset: 2pt, prod.map(t => chip(t, ok)).join(" ")),
    )
    grid(columns: (26mm, 1fr, 1fr), column-gutter: 8pt, row-gutter: 7pt, align: horizon,
      [], text(size: 8pt, weight: 700, fill: azul, tracking: 0.5pt)[DEMO (GITHUB PAGES)], text(size: 8pt, weight: 700, fill: ok, tracking: 0.5pt)[PRODUCCIÓN OBJETIVO],
      ..fila("Datos / ML", ("Python 3.12", "uv", "pandas", "LightGBM", "SHAP", "statsmodels", "SciPy", "scikit-learn"), ("Prithvi-EO-2.0", "Clay", "MLflow", "Prefect / Airflow")),
      ..fila("Geoespacial", ("H3 res. 9", "Shapely", "pyproj", "OSM (Overpass)"), ("PostGIS", "COG / Zarr", "STAC")),
      ..fila("API / web", ("MapLibre GL", "h3-js", "Chart.js", "FastAPI (opcional)"), ("FastAPI", "CDN", "OIDC / IAM")),
      ..fila("Plataforma", ("GitHub Actions", "GitHub Pages"), ("Kubernetes", "GitOps", "Prometheus", "Grafana")),
      ..fila("Documentación", ("Typst (typst-py)", "Hanken Grotesk"), ("Typst", "Portal interno")),
    )
  },
  [Stack por capa: demo (azul) y objetivo de producción (verde).],
)

#estimado[El stack de producción es una propuesta de referencia; la elección final (proveedor cloud, orquestador) depende del cliente y de los requisitos de soberanía del dato.]

== Justificación de elecciones clave

#tabla(
  columns: (auto, 1fr),
  [Tecnología], [Por qué],
  [Python 3.12 + uv], [Ecosistema geoespacial y de ML; `uv` da entornos reproducibles y rápidos con `uv.lock`.],
  [LightGBM + SHAP], [Boosting eficaz con pocos datos tabulares; SHAP proporciona explicación local por celda.],
  [statsmodels (STL) + SciPy (Theil-Sen)], [Descomposición estacional y tendencia robusta a valores atípicos (nubes, huecos).],
  [H3 res. 9], [Malla jerárquica uniforme (≈ 0,1 km²), agregable y fácil de teselar por ciudad.],
  [MapLibre GL + Chart.js], [Mapa vectorial y gráficos sin build step; versión fija por CDN.],
  [Typst], [Documentación reproducible desde texto, rápida y con control tipográfico.],
)

= Decisiones de arquitectura (ADR)

#tabla(
  columns: (auto, 1fr, 1.2fr),
  [ADR], [Decisión], [Motivo y consecuencia],
  [ADR-01], [*Static-first* para GitHub Pages.], [Pages sólo sirve ficheros estáticos; el pipeline corre offline y publica JSON. Coste de mantenimiento mínimo; la API pasa a ser opcional.],
  [ADR-02], [*H3 resolución 9* como unidad de análisis.], [Equilibrio entre detalle de manzana y volumen de datos; permite escalar por tiles H3 a más ciudades.],
  [ADR-03], [*Umbrales aplicados en el cliente.*], [El modelo entrega scores continuos; el técnico mueve el slider y la vista se recalcula al instante, sin servidor. Los umbrales vigentes se guardan en cada decisión.],
  [ADR-04], [Adaptador *DecisionStore* con dos implementaciones.], [`LocalDecisionStore` (localStorage + exportación JSON) en Pages; `ApiDecisionStore` en producción. Misma interfaz, sin cambios en la UI.],
  [ADR-05], [Rutas *relativas* y sin dependencias de `localhost`.], [Funciona bajo `usuario.github.io/repo/`.],
  [ADR-06], [Datos sintéticos *deterministas* con semilla.], [Reproducibilidad y pruebas estables; claramente etiquetados como sintéticos.],
)

= Principios Clean Code aplicados

- *Responsabilidad única* y funciones pequeñas con nombres de dominio (`classify_cell`, `rank_proposals`).
- *Inversión de dependencias*: el dominio define puertos (`DataSource`, `DecisionStore`); la infraestructura los implementa.
- *Sin efectos laterales en el dominio*: funciones puras, entidades inmutables y tipado estático (Pydantic, `dataclass(frozen=True)`).
- *Configuración explícita* (`config.py`, `config.json`) en lugar de constantes mágicas; umbrales con valores por defecto documentados.
- *Errores explícitos y trazabilidad*: cada artefacto lleva `model_version`, `generated_at` y `schema_version`.
- *Linter y formato*: `ruff`; revisión por pares y CI obligatoria.

= Estrategia de testing

#tabla(
  columns: (auto, 1fr, auto),
  [Nivel], [Qué se prueba], [Herramienta],
  [Unitario (dominio)], [Clasificación por umbrales, normalización de scores, reglas de priorización.], [pytest],
  [Casos de uso], [Pipeline con fuentes sintéticas y semillas; contrato de salida (esquema).], [pytest],
  [Contrato de datos], [Validación de `manifest.json`, `cells.geojson`, etc. frente al esquema versionado.], [pytest + Pydantic],
  [API], [`GET/POST /api/decisions` y esquema de registros.], [httpx / TestClient],
  [Modelo], [AUC, F1 en el umbral crítico, MAE de previsión; comprobación de drift.], [pytest + métricas],
  [Web (manual / E2E)], [Mapa con capas H3, umbrales, aprobar/rechazar, exportación, consola sin errores; ruta `/repo/` simulada.], [navegador + servidor estático],
)

#v(10pt)
#historial((
  ("0.1", "25-10-2026", "Estructura prevista en el plan."),
  ("0.2", "25-10-2026", "Arquitectura hexagonal, componentes, flujo, stack, ADR, Clean Code y testing alineados con el contrato de datos v1."),
))
