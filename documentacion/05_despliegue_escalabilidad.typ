#import "tema/verdescope.typ": *
#import "tema/diagramas.typ": *

#show: documento.with(
  titulo: "Despliegue y escalabilidad",
  subtitulo: "De GitHub Pages a una plataforma multi-ciudad sostenible",
  version: "0.2", fecha: "25 de octubre de 2026",
)

= Dos modos de despliegue

VerdeScope se entrega en dos configuraciones con el mismo dominio: una *demo estática* sin coste de infraestructura (GitHub Pages) y una *plataforma productiva* multiusuario. La web detecta mediante `config.json` si hay API y elige el adaptador de decisiones correspondiente.

#tabla(
  columns: (auto, 1fr, 1fr),
  [Aspecto], [Demo (GitHub Pages)], [Producción objetivo],
  [Cómputo], [Pipeline offline en la máquina del desarrollador o en GitHub Actions.], [Jobs batch orquestados (Prefect/Airflow) en Kubernetes.],
  [Datos], [JSON estáticos en `docs/data/`.], [PostGIS + object storage (COG/Zarr).],
  [Decisiones], [`LocalDecisionStore` (localStorage + exportación JSON).], [`ApiDecisionStore` → FastAPI → PostGIS, auditoría central.],
  [Usuarios], [Anónimo, sólo lectura + decisiones locales.], [SSO corporativo/municipal (OIDC) con roles.],
  [Coste], [≈ 0 €], [Véase documento 06.],
)

= Diagrama de despliegue de la demo

#figura(
  dg(sp: (30mm, 13mm),
    nodo((0, 0), [Desarrollador\ `git push`], tono: "claro"),
    nodo((1, 0), [Repositorio\ GitHub], tono: "oscuro"),
    nodo((2, 0), [Actions: instalar\ uv + dependencias], tono: "azul"),
    nodo((3, 0), [pytest\ (puerta de calidad)], tono: "azul"),
    nodo((3, 1), [Pipeline offline\ datos + modelos], tono: "azul"),
    nodo((2, 1), [Compilar Typst\ → PDF], tono: "azul"),
    nodo((1, 1), [Empaquetar\ artefactos `docs/`], tono: "azul"),
    nodo((0, 1), [`deploy-pages`], tono: "azul"),
    nodo((0, 2), [GitHub Pages\ (CDN estático)], tono: "ok"),
    nodo((1, 2), [Navegador\ del técnico], tono: "claro"),
    nodo((3, 2), [Overpass (OSM)\ caché en repo], tono: "gris"),
    flecha((0, 0), (1, 0)), flecha((1, 0), (2, 0)), flecha((2, 0), (3, 0)), flecha((3, 0), (3, 1)),
    flecha((3, 1), (2, 1)), flecha((2, 1), (1, 1)), flecha((1, 1), (0, 1)), flecha((0, 1), (0, 2)),
    flecha((0, 2), (1, 2)), flecha((3, 2), (3, 1), tipo: "-->", etiqueta: "caché"),
  ),
  [Despliegue de la demo: el repositorio es la única fuente; los datos y los PDF se regeneran en cada push (todo el bloque central corre en un runner de GitHub Actions).],
)

#decision[
  *Doble vía de publicación.* Además de Actions, los datos y los PDF generados se versionan en el repositorio, de modo que Pages puede servirse en modo _Deploy from a branch → `/docs`_ sin depender del workflow. Todas las rutas son relativas (`usuario.github.io/repo/`).
]

= Diagrama de despliegue productivo

#figura(
  dg(sp: (34mm, 14mm),
    nodo((0, 0), [Técnicos y\ planificadores], tono: "claro"),
    nodo((1, 0), [CDN + WAF], tono: "azul"),
    nodo((2, 0), [Ingress + IAM\ (OIDC)], tono: "azul"),
    contenedor(((1, 1), (3, 2)), "Kubernetes (cloud pública o soberana)", tono: "gris"),
    nodo((1, 1), [Web estática\ (pods Nginx)], tono: "claro"),
    nodo((2, 1), [API FastAPI\ (autoescalado)], tono: "claro"),
    nodo((3, 1), [Workers batch\ (inferencia)], tono: "claro"),
    nodo((1, 2), [Orquestador\ Prefect / Airflow], tono: "claro"),
    nodo((2, 2), [MLflow\ registro de modelos], tono: "claro"),
    nodo((3, 2), [Observabilidad\ Prometheus · Grafana], tono: "claro"),
    nodo((0, 3.4), [Secretos / KMS\ + backups], tono: "oscuro"),
    nodo((1, 3.4), [PostGIS\ (gestionado)], tono: "oscuro"),
    nodo((2, 3.4), [Object storage\ COG · Zarr], tono: "oscuro"),
    nodo((3, 3.4), [Fuentes: Sentinel-2\ INE · Smart Steps], tono: "ok"),
    flecha((0, 0), (1, 0)), flecha((1, 0), (2, 0)),
    flecha((2, 0), (1, 1)), flecha((2, 0), (2, 1)),
    flecha((2, 1), (1, 3.4)), flecha((3, 1), (2, 3.4)),
    flecha((3, 3.4), (2, 3.4)), flecha((1, 2), (3, 1)), flecha((3, 1), (2, 2), tipo: "<->"),
    flecha((3, 2), (2, 1), tipo: "-->"),
  ),
  [Despliegue objetivo en Kubernetes con almacén geoespacial, orquestación batch y registro de modelos.],
)

= Escalabilidad

#tabla(
  columns: (auto, 1fr),
  [Palanca], [Diseño],
  [*Tiles H3 por ciudad*], [La unidad es la celda H3 res. 9: cada ciudad es una colección de celdas independiente; la partición `ciudad/h3_padre` permite procesamiento y caché paralelos.],
  [*Procesamiento por lotes particionado*], [El pipeline es mensual (cadencia de Sentinel-2 y Landsat) y por lotes: se reparte por ciudad y por partición H3; los reintentos son idempotentes.],
  [*Multi-ciudad / multi-tenant*], [Aislamiento lógico por `tenant_id` (esquemas o filas con RLS en PostGIS), umbrales y pesos por ciudad, claves de cifrado separadas.],
  [*Entrega*], [La web consume artefactos pre-calculados; la lectura escala con CDN y no con cómputo.],
  [*Modelos*], [Un modelo base compartido + ajuste fino ligero por ciudad con embeddings (Prithvi/Clay), evitando reentrenar desde cero.],
)

#figura(
  dg(sp: (26mm, 12mm),
    nodo((0, 0), [Catálogo de\ ciudades], tono: "oscuro"),
    nodo((1, -1), [Madrid\ (H3 partición A…n)], tono: "claro"),
    nodo((1, 0), [Valencia\ (H3 partición A…n)], tono: "claro"),
    nodo((1, 1), [Ciudad N\ (H3 partición A…n)], tono: "claro"),
    nodo((2, 0), [Cola de lotes\ + workers\ elásticos], tono: "azul"),
    nodo((3, 0), [Artefactos por\ ciudad (CDN)], tono: "ok"),
    flecha((0, 0), (1, -1)), flecha((0, 0), (1, 0)), flecha((0, 0), (1, 1)),
    flecha((1, -1), (2, 0)), flecha((1, 0), (2, 0)), flecha((1, 1), (2, 0)), flecha((2, 0), (3, 0)),
  ),
  [Escalado horizontal por ciudad y partición H3.],
)

= Sostenibilidad (green software)

- *Cómputo batch mensual* en lugar de tiempo real: el estado del verde cambia lentamente; se evita infraestructura siempre encendida.
- *Inferencia ligera*: LightGBM en CPU para el déficit; modelos profundos sólo para segmentación y con embeddings congelados.
- *Reutilizar foundation models* (Prithvi-EO-2.0, Clay) en vez de entrenar desde cero.
- *Cómputo en regiones de bajo carbono* y autoescalado a cero entre lotes.
- *Datos eficientes*: formatos COG/Zarr con lectura parcial y compresión; la web sirve JSON ligeros.

#tabla(
  columns: (1fr, auto, auto),
  [Escenario (por ciudad y año)], [Energía], [CO#sub[2]e],
  [Pipeline batch mensual (12 × 4 vCPU × 3 h)], [≈ 1,4 kWh], [≈ 0,3 kg],
  [Entrenar un modelo profundo desde cero (8 GPU × 100 h)], [≈ 240 kWh], [≈ 48 kg],
)
#estimado[Orden de magnitud con supuestos: 10 W por vCPU, 300 W por GPU y 0,2 kg CO#sub[2]e/kWh. No es una medición; debe sustituirse por datos del proveedor cloud real.]

= Seguridad y cumplimiento

- *Identidad y acceso*: OIDC/SSO, roles (técnico, planificador, administrador), mínimo privilegio.
- *Datos*: cifrado en tránsito (TLS) y en reposo (KMS); copias de seguridad; segregación por tenant.
- *Privacidad*: Smart Steps sólo en *agregados anonimizados* con umbral mínimo de conteo; EIPD y registro de tratamiento; sin datos personales en repositorio ni logs.
- *Cadena de suministro*: dependencias bloqueadas (`uv.lock`), escaneo de vulnerabilidades, versiones CDN fijas con integridad.
- *Auditoría*: cada decisión se almacena con usuario, hora, versión de modelo y umbrales; registros inmutables (append-only).

= Observabilidad

#tabla(
  columns: (auto, 1fr),
  [Señal], [Qué se mide],
  [Métricas técnicas], [Latencia de API, errores, duración y éxito de lotes, uso de recursos.],
  [Métricas de datos], [Frescura de cada fuente, completitud, esquema, drift de features.],
  [Métricas de modelo], [Distribución de scores, estabilidad del ranking, calibración, equidad por distrito.],
  [Métricas de producto], [Tasa de aprobación/rechazo/ajuste, tiempo de decisión, propuestas pendientes.],
)

= CI/CD

#figura(
  dg(sp: (22mm, 12mm),
    nodo((0, 0), [Commit / PR], tono: "claro"),
    nodo((1, 0), [Lint + tipos\ (ruff)], tono: "azul"),
    nodo((2, 0), [Tests\ unit · contrato], tono: "azul"),
    nodo((3, 0), [Pipeline +\ puerta de métricas], tono: "azul"),
    nodo((4, 0), [Build web\ + PDF Typst], tono: "azul"),
    nodo((5, 0), [Despliegue\ (Pages / GitOps)], tono: "ok"),
    flecha((0, 0), (1, 0)), flecha((1, 0), (2, 0)), flecha((2, 0), (3, 0)), flecha((3, 0), (4, 0)), flecha((4, 0), (5, 0)),
  ),
  [Etapas de integración y despliegue continuos.],
)

#riesgo[
  *Riesgo operativo.* La demo no cubre alta disponibilidad, multiusuario ni gestión de secretos. Cualquier uso con datos reales requiere el despliegue productivo y una revisión de seguridad previa.
]

#v(10pt)
#historial((
  ("0.1", "25-10-2026", "Esquema de despliegue del plan."),
  ("0.2", "25-10-2026", "Diagramas de despliegue demo y producción, escalabilidad, green software, seguridad, observabilidad y CI/CD."),
))
