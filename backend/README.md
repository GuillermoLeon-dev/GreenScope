# VerdeScope - backend y pipeline ML

Detección de déficit de zonas verdes y propuesta de parques de bolsillo (piloto: Madrid central,
bbox `[-3.75, 40.38, -3.64, 40.46]`, celdas H3 res. 9). Produce los artefactos del contrato
`contratos/datos.md` en `docs/data/` y `docs/config.json`; la web estática los consume.

## Ejecutar

```bash
cd backend
uv sync                          # Python 3.12 (uv lo instala si falta)
uv run verdescope pipeline       # usa la caché OSM; si no existe descarga de Overpass
uv run verdescope pipeline --offline   # nunca usa la red (caché o fallback sintético)
uv run pytest                    # tests
uv run ruff check                # lint
uv run verdescope serve          # API + web estática en http://127.0.0.1:8000
# equivalente: uv run uvicorn verdescope.api.main:app
```

Opcionales: `uv sync --extra stac` (Planetary Computer), `--extra dl` (torch para `UNetSegmenter`).
Primera ejecución del pipeline completo: ~1 min (la mayor parte, previsión Holt-Winters por celda).

## Arquitectura (hexagonal)

```
src/verdescope/
  domain/          entidades (Cell, Proposal, Decision, Thresholds), reglas puras (clasificación,
                   índice compuesto, etiquetas débiles, prioridad, coste/enfriamiento/CO2), policies
  application/     casos de uso: BuildFeatures, ForecastVegetation, ScoreDeficit, GenerateProposals,
                   RecordDecision, ExportArtifacts + RunPipeline; puertos (ports.py)
  infrastructure/  adaptadores: OverpassOsmSource (real, caché), SyntheticOsmSource (fallback),
                   Synthetic{Sentinel2,Lst,Ine,SmartSteps}Source, conectores reales desactivados
                   (Stac/Ine/SmartSteps), segmentadores, FusionDeficitModel (LightGBM+SHAP),
                   StlTheilSenForecaster, repositorios JSON, escritor de artefactos
  api/main.py      FastAPI: /api/health, GET/POST /api/decisions, sirve docs/ estático (CORS abierto)
  config.py        configuración central (umbrales 0.70/0.40/0.50, pesos, supuestos, rutas)
  bootstrap.py     raíz de composición; cli.py  línea de comandos
```

Puertos: `DataSource`, `VectorSource`, `VegetationSegmenter`, `DeficitModel`, `Forecaster`,
`DecisionRepository`, `ArtifactWriter`. Para producción basta con otro adaptador (PostGIS para
decisiones, STAC/INE/Smart Steps reales para fuentes, Prithvi-EO-2.0/Clay para segmentación).

## Modelo

- **Fusión**: OSM (real) + NDVI Sentinel-2, LST Landsat, padrón INE y Smart Steps (sintéticos,
  deterministas con semilla, coherentes con la geometría OSM) -> features por celda.
- **Segmentación**: baseline NDVI >= 0,40 sobre parches 8x8 (`NdviThresholdSegmenter`). `UNetSegmenter`
  (torch perezoso) es opcional y no se usa por defecto.
- **Series**: STL robusto + pendiente Theil-Sen (IC 90 %); anomalía si la pendiente es
  significativamente negativa (<= -0,01/año) o el residuo reciente es extremo. Previsión a 12 meses
  con Holt-Winters (tendencia amortiguada, estacional aditiva) y banda al 90 %.
- **Déficit**: `score = 0,5 * índice compuesto + 0,5 * P(LightGBM calibrada)`. El índice pondera
  OMS 9 m²/hab, acceso a 300 m, copas 30 %, calor, vulnerabilidad, demanda (residentes + flotantes) y
  degradación. LightGBM se entrena con **etiquetas débiles** por reglas (+8 % de ruido) y validación
  cruzada espacial (GroupKFold por celda H3 res. 7), calibración de Platt y SHAP (`top_factors`,
  normalizados por la suma de |SHAP|; positivo = aumenta el déficit). `uncertainty` = desviación
  entre estimadores (índice + modelos de cada fold) / 0,5.
- **Métricas** (manifest): AUC y F1 al umbral crítico se miden **fuera de muestra frente a la
  etiqueta débil limpia** (no es verdad-terreno; con datos sintéticos son un chequeo de coherencia,
  no una estimación de rendimiento real). MAE de previsión: backtest de los últimos 12 meses en 80 celdas.

## Propuestas

Candidatas: solares (`landuse=brownfield|vacant|construction`) y aparcamientos en superficie de OSM +
candidatas sintéticas (`interbloque`, `chaflan`, `calle_pacificable`) en celdas con score >= umbral
de revisión (2 si score >= 0,70). Filtro de área 150-5000 m². IDs `P-0001...` asignados por orden
geométrico (lat, lon, tipo): estables mientras no cambie el conjunto de candidatas. Se exportan las
de prioridad >= 0,30; la web filtra con `min_proposal_priority`.

Supuestos (todos en `domain/policies.py`, configurables):

| Supuesto | Valor |
|---|---|
| Coste €/m²: solar / aparcamiento (desasfaltado) / interbloque / chaflán / calle | 180 / 260 / 120 / 220 / 300 |
| Enfriamiento local | `2,5 °C x (1 - exp(-A/2000 m²)) x factor` (aparcamiento 1,2; calle 1,1; solar 1,0; resto 0,9) |
| CO2 | `A x 0,6 (fracción con copa) x 1,5 kg CO2/m² copa/año` |
| Población servida | residentes + 0,5 x flotantes en un radio de 300 m, ponderados por solape de celda y por la ganancia de acceso (0 si ya hay verde a <150 m, 1 si >300 m) |
| Prioridad | 0,35 déficit + 0,25 población servida (ref. 3000) + 0,15 LST + 0,10 vulnerabilidad + 0,15 eficiencia de coste (ref. 600 000 €) |

Son órdenes de magnitud para priorizar, no presupuestos.

## Datos y reproducibilidad

- Caché OSM commiteable: `backend/data/cache/osm_madrid.json` (respuesta cruda de Overpass).
- Todo es determinista (`Settings.seed = 42`). Geometría y distancias en EPSG:25830.
- Las decisiones de la API se guardan en `backend/data/decisions.json` (ignorado por git).
