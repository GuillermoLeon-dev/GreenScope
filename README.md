# GreenScope · Déficit de verde y parques de bolsillo

Aplicación web que **detecta zonas urbanas con déficit de zonas verdes** y **propone parques de
bolsillo**. Combina observación de la Tierra, OpenStreetMap, padrón y movilidad (data fusion) con
ML y series temporales dentro de una metodología **CRISP-ML(Q)**. El modelo propone y el técnico
decide: los umbrales son configurables y cada propuesta requiere aprobación humana.

Piloto: **Madrid central** (763 celdas H3 de resolución 9). Experimento personal.

> **Aviso:** Proyecto independiente, sin afiliación con Telefónica ni con ninguna otra empresa. Las menciones a Smart Steps (Telefónica Tech) se refieren a un producto de
> terceros citado como posible fuente de datos; en la demo esos datos son sintéticos.

## Estructura

| Carpeta | Contenido |
|---|---|
| `docs/` | **Web estática** (GitHub Pages): MapLibre GL + Chart.js, ES modules sin build. `docs/data/` contiene los artefactos del pipeline y `docs/pdf/` la documentación. |
| `backend/` | Python 3.12 + uv con arquitectura hexagonal (`domain`, `application`, `infrastructure`, `api`): pipeline ML, API FastAPI opcional y tests. |
| `documentacion/` | Documentos Typst (00–07) con tema propio y fuente Hanken Grotesk (OFL), además de `build.py`. |
| `contratos/` | Contrato de datos entre el pipeline y la web, y tokens de marca. |
| `tiempos/` | Cronometraje del experimento (`cronometro.log`, en UTC). |
| `.github/workflows/` | `ci.yml` (lint + tests) y `pages.yml` (regenerar y desplegar, manual). |

## Publicar en GitHub Pages

1. Crea un repositorio vacío en GitHub y sube este proyecto:
   ```bash
   git remote add origin https://github.com/<usuario>/<repo>.git
   git push -u origin main
   ```
2. En GitHub ve a **Settings → Pages → Build and deployment → Deploy from a branch → `main` / `/docs`**.
3. En 1–2 minutos estará disponible en `https://<usuario>.github.io/<repo>/`.

Si quieres que los datos y los PDFs se regeneren en GitHub, usa la opción alternativa:
*Source: GitHub Actions* y ejecuta manualmente el workflow **Pages (regenerar y desplegar)**.

Las decisiones del técnico se guardan en el navegador (localStorage) y se exportan e importan en JSON
para auditoría. Con la API (`docs/config.json → api_base_url`) se centralizan en el servidor.

## Uso local

```bash
cd backend
uv sync
uv run pytest                     # 54 tests
uv run greenscope pipeline        # regenera docs/data (OSM vía Overpass; --offline usa la caché)
uv run greenscope serve           # API + web en http://localhost:8000
```

Documentación:

```bash
cd documentacion
uv run --python 3.12 --with typst python build.py
```

## Modelo, en una frase por pieza

- **Features por celda:** m² de verde por habitante (OMS 9 m²), distancia al verde ≥ 0,5 ha (300 m), cobertura vegetal (3-30-300), LST, tendencia de NDVI, vulnerabilidad, población residente y flotante (datos de operador tipo Smart Steps).
- **Déficit:** índice compuesto más LightGBM con supervisión débil, calibrado, con explicaciones SHAP e incertidumbre.
- **Series temporales:** STL, tendencia Theil-Sen, detección de anomalías y previsión Holt-Winters a 12 meses.
- **Propuestas:** solares, aparcamientos, interbloques, chaflanes y calles pacificables, ordenados por un ranking multicriterio con coste, enfriamiento y CO₂ estimados.

**Datos de la demo:** OSM es real. Sentinel-2, LST, INE y Smart Steps son **sintéticos realistas**, y sus conectores reales están preparados tras interfaces y desactivados. Las métricas del manifest (AUC 0,992, F1 0,641, MAE NDVI 0,024) solo comprueban la coherencia frente a etiquetas débiles; no miden el rendimiento real.

## Documentación (PDF)

`docs/pdf/`: 00 Resumen ejecutivo · 01 Mercado y estado del arte · 02 Propuesta e innovación ·
03 Arquitectura y tecnologías · 04 ML y CRISP-ML · 05 Despliegue y escalabilidad ·
06 Viabilidad económica · 07 Registro de iteraciones y tiempos.

## Tiempos del experimento

| Etapa | Duración |
|---|---|
| Preparación del entorno | 0 min 16 s |
| Análisis de mercado, estado del arte y plan (incl. preguntas al usuario) | 10 min 14 s |
| Diseño: contratos de datos y marca | 1 min 16 s |
| Implementación backend + ML (subagente Sonnet) | 17 min 32 s |
| Implementación frontend (subagente Sonnet) | 10 min 12 s |
| Documentación Typst (subagente Sonnet) | 14 min 48 s |
| Integración y verificación (Opus) | 2 min 54 s |
| Cierre: README, git, recompilación | 0 min 43 s |
| **Suma de etapas** | **57 min 55 s** |
| **Tiempo de reloj total** | **34 min 12 s** |

Las etapas 3, 4 y 5 se ejecutaron en paralelo, por eso la suma supera al tiempo de reloj. Detalle y Gantt en `docs/pdf/07_registro_iteraciones_tiempos.pdf`.

## Licencia

Código bajo MIT. Las fuentes Hanken Grotesk y JetBrains Mono están bajo SIL OFL 1.1. Los datos de OpenStreetMap son © de sus colaboradores (ODbL).
