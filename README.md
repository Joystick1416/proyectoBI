# Informe de Business Intelligence — Datamart Residuos Sólidos Perú 2019–2024

---

## 1. Marco Teórico

### 1.1 Business Intelligence

El Business Intelligence (BI) comprende el conjunto de metodologías y tecnologías que permiten transformar datos en bruto en información significativa para la toma de decisiones estratégicas. A través del BI, las organizaciones pueden analizar el comportamiento histórico de sus procesos, identificar tendencias y anticipar escenarios futuros con base en evidencia. En el presente trabajo, el BI se aplica sobre los datos de SIGERSOL para dotar al MINAM de una herramienta analítica que facilite el monitoreo de la gestión de residuos sólidos a nivel nacional.

### 1.2 OLAP y Modelo Dimensional

OLAP (On-Line Analytical Processing) es una solución de BI que agiliza la consulta de grandes volúmenes de datos mediante estructuras multidimensionales, permitiendo analizar causas, encontrar patrones y obtener respuestas rápidas a preguntas complejas.

El modelo dimensional, propuesto por Ralph Kimball, es la base de diseño de estos sistemas. Organiza los datos en **tablas de hechos** — que contienen las métricas cuantitativas — y **tablas de dimensiones** — que proveen el contexto de análisis respondiendo las preguntas *¿quién?, ¿qué?, ¿cuándo?, ¿dónde?, ¿cómo?* La estructura recomendada es el **modelo en estrella**, donde la tabla de hechos se ubica al centro conectada a sus dimensiones, priorizando simplicidad y velocidad de consulta.

### 1.3 ETL y SQL

El proceso **ETL** (Extract, Transform, Load) permite construir el datamart extrayendo datos de las fuentes originales, transformándolos y limpiándolos según el modelo dimensional, y cargándolos en las tablas finales para su consulta. En nuestro proyecto, este proceso está implementado en los módulos `extract.py`, `transform.py` y `load.py`, ejecutándose de forma automatizada mediante un pipeline con CI/CD.

**SQL** (Structured Query Language) es el lenguaje utilizado para consultar el datamart, permitiendo calcular indicadores como tasas de valorización por departamento, evolución anual de generación de residuos o rankings de municipalidades por desempeño ambiental.

---

## 2. Descripción de la empresa

El **Ministerio del Ambiente (MINAM)** es el organismo rector de la política ambiental en el Perú, responsable de diseñar, establecer y supervisar la gestión sostenible de los recursos naturales a nivel nacional. En materia de residuos sólidos, el MINAM articula esfuerzos con gobiernos locales y regionales, y administra el **Sistema de Información para la Gestión de Residuos Sólidos (SIGERSOL)**, plataforma que centraliza el reporte anual de generación, valorización y disposición final de residuos a nivel distrital en todo el país.

En la actualidad, el MINAM ejecuta el programa **"Desarrollo de Sistemas de Gestión de Residuos Sólidos en Zonas Priorizadas"**, cofinanciado por el BID, cuyo objetivo es multiplicar el número de municipios ecoeficientes y garantizar el cumplimiento de las metas del Plan Nacional de Acción Ambiental. Si bien este programa alcanzó el 100% de sus metas comprometidas en su componente BID — recuperando 264 hectáreas degradadas y beneficiando a más de un millón de peruanos — la escala de intervención aún es insuficiente frente a la magnitud del problema ambiental nacional.

### 2.1 Problemática

Uno de los principales obstáculos que enfrenta el MINAM no es únicamente operativo, sino **de información y visibilidad**. Si bien SIGERSOL centraliza anualmente miles de registros distritales, esta información no se encuentra estructurada para el análisis, lo que genera una brecha entre los datos disponibles y la capacidad real de toma de decisiones, manifestada en:

- **Falta de visibilidad territorial:** No existe una vista consolidada que permita comparar el desempeño de distritos y regiones a lo largo del tiempo.
- **Dificultad para identificar brechas:** Sin un modelo analítico, es complejo detectar qué municipios tienen menor valorización, cuáles no reportan datos o dónde se concentran los mayores volúmenes de residuos sin tratamiento.
- **Decisiones poco basadas en evidencia:** La ausencia de indicadores consolidados limita la capacidad del MINAM para priorizar intervenciones y evaluar el impacto de sus programas a nivel nacional.

### 2.2 Nuestra propuesta

Frente a esta problemática, proponemos un **datamart analítico** construido sobre los datos de SIGERSOL (2019–2024), que estructure la información disponible en un modelo dimensional consultable, permitiendo al MINAM:

- Monitorear la evolución de la valorización y generación de residuos **a nivel distrital y regional**.
- Identificar **municipios críticos** con baja valorización o sin reporte de datos.
- Generar **indicadores comparables** entre períodos, regiones y tipos de municipalidad para apoyar la toma de decisiones estratégicas.

---

## 3. Modelamiento de Data Dimensional

### 3.1 Enfoque metodológico

El modelo dimensional fue construido siguiendo la metodología de Kimball, adoptando un esquema de **constelación de hechos** (*fact constellation* o *galaxy schema*), en el que dos tablas de hechos independientes comparten dimensiones comunes. Este enfoque es apropiado cuando se modelan múltiples procesos de negocio relacionados — en nuestro caso, la **valorización** y la **generación** de residuos sólidos — permitiendo analizarlos de forma independiente o cruzada.

### 3.2 Diagrama del modelo

```
dim_tiempo ───────────┬──── fact_valorizacion
dim_geografica ────────┤──── fact_valorizacion
dim_residuo ───────────┘

dim_tiempo ───────────┬──── fact_generacion
dim_geografica ────────┤──── fact_generacion
dim_municipio ─────────┘
```

### 3.3 Granularidad

| Tabla de hechos | Granularidad |
|---|---|
| `fact_valorizacion` | Un registro por distrito × año × tipo de residuo (orgánico / inorgánico) |
| `fact_generacion` | Un registro por distrito × año |

### 3.4 Dimensiones

#### `dim_tiempo`
Permite analizar la evolución temporal de los indicadores entre 2019 y 2024.

| Columna | Tipo | Descripción |
|---|---|---|
| `anio_id` | int | PK — identificador del año |
| `anio` | int | Año del período (2019–2024) |
| `decada` | int | Década correspondiente |
| `es_ultimo_anio` | bool | True si es el año más reciente del dataset |

#### `dim_geografica`
Provee el contexto territorial de cada registro, desde el nivel distrital hasta la región natural.

| Columna | Tipo | Descripción |
|---|---|---|
| `ubigeo` | int | PK — código de ubigeo INEI |
| `departamento` | str | Nombre del departamento |
| `provincia` | str | Nombre de la provincia |
| `distrito` | str | Nombre del distrito |
| `region_natural` | str | Costa / Sierra / Selva |

**Jerarquía:** `region_natural` → `departamento` → `provincia` → `distrito`

#### `dim_municipio`
Caracteriza cada municipio según su tipo y clasificación presupuestal, permitiendo comparar el desempeño entre distintas categorías de gobierno local.

| Columna | Tipo | Descripción |
|---|---|---|
| `ubigeo` | int | PK — código de ubigeo INEI |
| `tipo_municipalidad` | str | Provincial / Distrital |
| `clasificacion_mef` | str | Clasificación municipal MEF (A–G según capacidad fiscal) |

#### `dim_residuo`
Distingue el tipo de residuo analizado, permitiendo comparar la valorización orgánica e inorgánica bajo el mismo modelo.

| Columna | Tipo | Descripción |
|---|---|---|
| `residuo_id` | int | PK (1 = Orgánico, 2 = Inorgánico) |
| `tipo_residuo` | str | ORGANICO / INORGANICO |
| `descripcion` | str | Descripción del proceso de valorización asociado |

### 3.5 Tablas de hechos

#### `fact_valorizacion`
Registra la valorización de residuos orgánicos e inorgánicos a nivel distrital.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | int | PK surrogate |
| `ubigeo` | int | FK → dim_geografica |
| `anio` | int | FK → dim_tiempo |
| `tipo_residuo` | str | FK → dim_residuo |
| `pob_total` | int | Población total del distrito |
| `pob_urbana` | int | Población urbana |
| `pob_rural` | int | Población rural |
| `qresiduos_mun` | float | Residuos municipales generados (t/año) |
| `qresiduos_valorizado` | float | Residuos efectivamente valorizados (t/año) |
| `tasa_valorizacion_pct` | float | Porcentaje de valorización (`qresiduos_valorizado / qresiduos_mun × 100`) |

#### `fact_generacion`
Registra la generación de residuos domiciliarios y municipales a nivel distrital.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | int | PK surrogate |
| `ubigeo` | int | FK → dim_geografica |
| `anio` | int | FK → dim_tiempo |
| `pob_total_inei` | int | Población total (INEI) |
| `pob_urbana_inei` | int | Población urbana (INEI) |
| `pob_rural_inei` | int | Población rural (INEI) |
| `generacion_per_capita_dom` | float | Generación per cápita domiciliaria (kg/hab/día) |
| `generacion_dom_urbana_tdia` | float | Generación domiciliaria urbana (t/día) |
| `generacion_dom_urbana_tanio` | float | Generación domiciliaria urbana (t/año) |
| `generacion_mun_tanio` | float | Generación municipal total (t/año) |
| `generacion_mun_tdia` | float | Generación municipal total (t/día) |
| `generacion_per_capita_municipal` | float | Generación per cápita municipal (kg/hab/día) |
| `ratio_dom_vs_mun_pct` | float | Proporción de residuos domiciliarios sobre el total municipal (%) |

---

## 4. Diseño y Análisis de Resultados de Business Intelligence

### 4.1 Propuesta de mejora

El datamart analítico construido sobre los datos de SIGERSOL permite al MINAM consolidar y analizar información distrital de forma estructurada y eficiente. Gracias al modelo dimensional implementado, es posible responder preguntas analíticas complejas combinando dimensiones y métricas sin necesidad de procesar los archivos fuente cada vez. A continuación se presentan los cuatro análisis más relevantes, destacando cómo el modelo dimensional habilitó cada uno.

### 4.2 Análisis de reportes

#### Reporte 1 — Evolución nacional de la valorización (2019–2024)

Este análisis fue posible gracias a la combinación de `fact_valorizacion` con `dim_tiempo` y `dim_residuo`, permitiendo agrupar las métricas de valorización por año y tipo de residuo en una sola consulta sin necesidad de cruzar múltiples archivos fuente.

| Año | Inorgánico (%) | Orgánico (%) |
|---|---|---|
| 2019 | 0.73 | 0.35 |
| 2020 | 0.31 | 0.43 |
| 2021 | 0.98 | 0.83 |
| 2022 | 0.93 | 0.82 |
| 2023 | 0.85 | 1.26 |
| 2024 | 1.31 | 1.36 |

La tasa de valorización muestra una tendencia creciente hacia 2024, con una caída notable en 2020 atribuible al impacto de la pandemia. En 2024, por primera vez la valorización orgánica supera a la inorgánica (1.36% vs 1.31%), sugiriendo avances en programas de compostaje. Sin embargo, ambas tasas siguen siendo críticamente bajas, confirmando la brecha estructural identificada en la problemática.

#### Reporte 2 — Valorización por región natural (2019–2024)

La jerarquía geográfica definida en `dim_geografica` (`region_natural` → `departamento` → `provincia` → `distrito`) permitió agregar los indicadores de valorización en distintos niveles territoriales con una sola dimensión, sin necesidad de tablas adicionales.

| Región | Tipo | Tasa 2019 (%) | Tasa 2024 (%) |
|---|---|---|---|
| Costa | Orgánico | 0.16 | 0.77 |
| Costa | Inorgánico | 0.75 | 1.37 |
| Sierra | Orgánico | 0.63 | 2.27 |
| Sierra | Inorgánico | 0.70 | 1.32 |
| Selva | Orgánico | 0.76 | 3.61 |
| Selva | Inorgánico | 0.53 | 1.03 |

La Selva lidera el crecimiento en valorización orgánica (0.76% → 3.61%), impulsada por distritos con iniciativas locales específicas. La Costa, pese a concentrar la mayor generación de residuos del país, presenta las tasas más bajas en valorización orgánica, convirtiéndose en la zona de mayor oportunidad de mejora para el MINAM.

#### Reporte 3 — Distritos sin valorización registrada

El cruce entre `fact_valorizacion` y `dim_geografica` permitió identificar rápidamente qué distritos no registran ningún tipo de valorización, filtrando por región natural sin procesamiento adicional.

| Región Natural | Distritos sin valorización |
|---|---|
| Sierra | 1,148 |
| Selva | 272 |
| Costa | 199 |

La Sierra concentra el 73% de los distritos sin valorización registrada, convirtiéndola en la zona de mayor prioridad para intervención. Este hallazgo, difícil de detectar en los archivos fuente originales, emerge de forma inmediata gracias al modelo dimensional.

#### Reporte 4 — Valorización por tipo de municipalidad

`dim_municipio` permitió segmentar los indicadores de valorización según el tipo y clasificación de cada municipio, revelando diferencias estructurales en el desempeño que no eran visibles en los datos originales.

| Tipo | Tipo Residuo | Distritos | Tasa promedio (%) |
|---|---|---|---|
| Distrital | Inorgánico | 1,695 | 0.25 |
| Distrital | Orgánico | 1,695 | 1.29 |
| Provincial | Inorgánico | 196 | 0.83 |
| Provincial | Orgánico | 196 | 5.03 |

Las municipalidades provinciales triplican la tasa de valorización orgánica respecto a las distritales (5.03% vs 1.29%), evidenciando que la capacidad institucional incide directamente en el desempeño ambiental. Este análisis apoya directamente la toma de decisiones del MINAM para focalizar asistencia técnica en municipios distritales.

---

## 5. Conclusiones preliminares

1. La construcción del modelo dimensional permitió estructurar datos dispersos de SIGERSOL en dimensiones bien definidas (`dim_tiempo`, `dim_geografica`, `dim_municipio`, `dim_residuo`), facilitando la segmentación, el filtrado y la generación de indicadores de forma ágil y reproducible.

2. El esquema de constelación de hechos adoptado — con dos tablas de hechos que comparten dimensiones — demostró ser una estructura adecuada para analizar procesos de negocio distintos (valorización y generación) de forma integrada, permitiendo identificar patrones territoriales y temporales que no eran visibles en los archivos fuente originales.

3. Las dimensiones geográfica y de municipio resultaron especialmente útiles para segmentar los indicadores por región natural y tipo de municipalidad, revelando brechas estructurales que constituyen una base sólida para la priorización de intervenciones del MINAM.

4. Este datamart representa un primer paso concreto hacia una gestión de residuos basada en evidencia, dotando al MINAM de una herramienta que centraliza, estandariza y hace consultable la información de 1,891 distritos a lo largo de seis años.

---

## 6. Recomendaciones preliminares

1. **Ampliar el modelo dimensional:** Evaluar la incorporación de nuevas dimensiones o fuentes de datos complementarias (como RENAMU) que enriquezcan el análisis y permitan cruzar la gestión de residuos con variables de capacidad institucional y presupuestal.

2. **Desarrollar dashboards interactivos:** Como siguiente paso, implementar una capa de visualización (Power BI, Tableau u otra herramienta de BI) sobre el datamart para facilitar el acceso a los indicadores por parte de tomadores de decisiones del MINAM sin necesidad de consultas SQL.

3. **Validar con usuarios del MINAM:** Contrastar el diseño actual del modelo y los reportes generados con usuarios reales del MINAM para asegurar que los indicadores respondan a sus necesidades operativas y estratégicas.

4. **Automatizar la actualización:** Integrar el pipeline ETL al ciclo anual de reporte de SIGERSOL para garantizar que el datamart se mantenga vigente con cada nueva entrega de datos.


---

## 7. Estructura del repositorio

```
datamart-residuos/
├── data/
│   ├── raw/                   # Archivos originales (CSV / XLSX)
│   ├── processed/             # Datos limpios intermedios (generado por ETL)
│   └── marts/                 # Tablas finales (Parquet + DuckDB)
│       ├── dim_tiempo.parquet
│       ├── dim_geografica.parquet
│       ├── dim_municipio.parquet
│       ├── dim_residuo.parquet
│       ├── fact_valorizacion.parquet
│       ├── fact_generacion.parquet
│       └── datamart_residuos.duckdb
├── etl/
│   ├── extract.py             # Carga y normaliza archivos raw
│   ├── transform.py           # Construye dimensiones y tablas de hechos
│   └── load.py                # Carga a DuckDB y genera reporte de calidad
├── reportes/                       # Generado automáticamente al correr el pipeline
│   ├── 01_evolucion_nacional.png
│   ├── 01_evolucion_toneladas.png
│   ├── 02_top10_organico.png
│   ├── 02_top10_inorganico.png
│   ├── 03_region_natural.png
│   ├── 04_ranking_departamentos.png
│   ├── 05_mejora_organico.png
│   ├── 05_mejora_inorganico.png
│   ├── 06_per_capita.png
│   ├── 07_sin_valorizacion.png
│   ├── 08_tipo_municipalidad.png
│   └── *.txt                       # Versión en texto de cada reporte
├── tests/
│   └── test_marts.py          # Pruebas de integridad referencial y calidad
├── docs/
│   └── diccionario_datos.md   # Diccionario completo de columnas
├── .github/workflows/
│   └── etl.yml                # CI/CD — ejecuta pipeline en cada push
├── run_pipeline.py            # Punto de entrada único del pipeline
├── requirements.txt
└── .gitignore
```

## 8. Cómo usar

### 8.1 Instalar dependencias
```bash
pip install -r requirements.txt
```

### 8.2 Ejecutar el pipeline completo
```bash
python run_pipeline.py
```
Esto genera todos los archivos en `data/processed/` y `data/marts/`.

### 8.3 Correr los tests
```bash
pytest tests/ -v
```

### 8.4 Consultar el datamart con DuckDB
```python
import duckdb
con = duckdb.connect("data/marts/datamart_residuos.duckdb", read_only=True)

# Ejemplo: tasa de valorización orgánica por departamento en 2024
con.execute("""
    SELECT g.departamento,
           ROUND(AVG(v.tasa_valorizacion_pct), 2) AS tasa_promedio
    FROM fact_valorizacion v
    JOIN dim_geografica g USING (ubigeo)
    WHERE v.anio = 2024 AND v.tipo_residuo = 'ORGANICO'
    GROUP BY 1 ORDER BY 2 DESC
""").df()
```

También se puede leer directamente los Parquet con pandas:
```python
import pandas as pd
df = pd.read_parquet("data/marts/fact_valorizacion.parquet")
```

## Fuente de datos

- MINAM — Sistema de Información para la Gestión de Residuos Sólidos (SIGERSOL)
- Datos abiertos: [datosabiertos.gob.pe](https://www.datosabiertos.gob.pe)
