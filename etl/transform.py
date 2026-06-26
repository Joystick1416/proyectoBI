"""
transform.py
Construye las dimensiones y tablas de hechos del datamart.

Modelo dimensional (constelación de hechos):
  SIGERSOL (2019–2024):
  - dim_tiempo            : dimensión tiempo anual
  - dim_geografica        : dimensión geográfica (ubigeo) — conformada, compartida por las 3 facts
  - dim_municipio         : dimensión municipio (tipo, clasificación MEF)
  - dim_residuo           : dimensión tipo de residuo (orgánico / inorgánico)
  - fact_valorizacion     : hechos de valorización por distrito × año × tipo residuo
  - fact_generacion       : hechos de generación municipal por distrito × año

  MEF/SIAF:
  - dim_entidad           : entidad ejecutora del gasto
  - dim_presupuesto       : clasificador presupuestal del gasto
  - dim_programa_funcional: estructura funcional del gasto
  - dim_cambio_climatico  : medida/atribución climática (registros de cambio climático)
  - fact_gasto            : hechos de ejecución presupuestal por distrito × año
"""

import unicodedata
import pandas as pd
from pathlib import Path

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
MARTS_DIR = Path(__file__).parent.parent / "data" / "marts"
MARTS_DIR.mkdir(parents=True, exist_ok=True)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _read(filename: str) -> pd.DataFrame:
    return pd.read_csv(PROCESSED_DIR / filename, encoding="utf-8")


def _read_optional(filename: str) -> pd.DataFrame | None:
    path = PROCESSED_DIR / filename
    if not path.exists():
        return None
    return pd.read_csv(path, encoding="utf-8")


def _normalizar_geo(s: pd.Series) -> pd.Series:
    """Convierte a mayúsculas y elimina tildes para joins geográficos robustos."""
    def _strip(x):
        if not isinstance(x, str):
            return x
        return "".join(
            c for c in unicodedata.normalize("NFD", x.upper())
            if unicodedata.category(c) != "Mn"
        )
    return s.map(_strip)


# ── Dimensiones ──────────────────────────────────────────────────────────────

def build_dim_tiempo(df_gen: pd.DataFrame) -> pd.DataFrame:
    anios = sorted(df_gen["ANIO"].unique())
    dim = pd.DataFrame({"anio_id": anios, "anio": anios})
    dim["decada"] = (dim["anio"] // 10) * 10
    dim["es_ultimo_anio"] = dim["anio"] == dim["anio"].max()
    print(f"  dim_tiempo: {len(dim)} filas")
    return dim


def build_dim_geografica(df_gen: pd.DataFrame) -> pd.DataFrame:
    cols = ["UBIGEO", "DEPARTAMENTO", "PROVINCIA", "DISTRITO", "REGION_NATURAL"]
    dim = df_gen[cols].drop_duplicates().copy()
    dim.columns = ["ubigeo", "departamento", "provincia", "distrito", "region_natural"]
    dim = dim.sort_values("ubigeo").reset_index(drop=True)
    print(f"  dim_geografica: {len(dim)} filas (distritos únicos)")
    return dim


def build_dim_municipio(df_gen: pd.DataFrame) -> pd.DataFrame:
    cols = ["UBIGEO", "TIPO_MUNICIPALIDAD", "CLASIFICACION_MUNICIPAL_MEF"]
    dim = df_gen[cols].drop_duplicates(subset=["UBIGEO"]).copy()
    dim.columns = ["ubigeo", "tipo_municipalidad", "clasificacion_mef"]
    dim = dim.sort_values("ubigeo").reset_index(drop=True)
    print(f"  dim_municipio: {len(dim)} filas")
    return dim


def build_dim_residuo() -> pd.DataFrame:
    dim = pd.DataFrame({
        "residuo_id": [1, 2],
        "tipo_residuo": ["ORGANICO", "INORGANICO"],
        "descripcion": [
            "Residuos orgánicos valorizables (compostaje, biodigestión, etc.)",
            "Residuos inorgánicos valorizables (reciclaje de papel, plástico, metal, etc.)"
        ]
    })
    print(f"  dim_residuo: {len(dim)} filas")
    return dim


# ── Tablas de hechos ──────────────────────────────────────────────────────────

def build_fact_valorizacion(df_inorg: pd.DataFrame, df_org: pd.DataFrame) -> pd.DataFrame:
    """Consolida valorización orgánica e inorgánica en una sola tabla de hechos."""

    cols_base = ["UBIGEO", "PERIODO", "TIPO_RESIDUO",
                 "POB_TOTAL", "POB_URBANA", "POB_RURAL",
                 "QRESIDUOS_MUN", "QRESIDUOS_VALORIZADO"]

    # Asegurar columnas presentes
    df_inorg = df_inorg[cols_base].copy()
    df_org = df_org[cols_base].copy()

    fact = pd.concat([df_inorg, df_org], ignore_index=True)
    fact.columns = [c.lower() for c in fact.columns]
    fact = fact.rename(columns={"periodo": "anio"})

    # Métricas derivadas
    fact["tasa_valorizacion_pct"] = (
        fact["qresiduos_valorizado"] / fact["qresiduos_mun"].replace(0, pd.NA) * 100
    ).round(4)

    fact = fact.sort_values(["ubigeo", "anio", "tipo_residuo"]).reset_index(drop=True)
    fact.insert(0, "id", range(1, len(fact) + 1))
    print(f"  fact_valorizacion: {len(fact)} filas")
    return fact


def build_fact_generacion(df_gen: pd.DataFrame) -> pd.DataFrame:
    """Tabla de hechos de generación de residuos municipales y domiciliarios."""
    cols = [
        "UBIGEO", "ANIO",
        "POB_TOTAL_INEI", "POB_URBANA_INEI", "POB_RURAL_INEI",
        "GENERACION_PER_CAPITA_DOM",
        "GENERACION_DOM_URBANA_TDIA",
        "GENERACION_DOM_URBANA_TANIO",
        "GENERACION_MUN_TANIO",
        "GENERACION_MUN_TDIA",
        "GENERACION_PER_CAPITA_MUNICIPAL"
    ]
    fact = df_gen[cols].copy()
    fact.columns = [c.lower() for c in fact.columns]

    # Métricas derivadas
    fact["ratio_dom_vs_mun_pct"] = (
        fact["generacion_dom_urbana_tdia"] / fact["generacion_mun_tdia"].replace(0, pd.NA) * 100
    ).round(4)

    fact = fact.sort_values(["ubigeo", "anio"]).reset_index(drop=True)
    fact.insert(0, "id", range(1, len(fact) + 1))
    print(f"  fact_generacion: {len(fact)} filas")
    return fact


# ── Dimensiones MEF/SIAF ─────────────────────────────────────────────────────

def build_dim_tiempo_presupuestal() -> pd.DataFrame:
    meses_es = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    rows = [
        {"anio": anio, "mes": mes, "nombre_mes": meses_es[mes]}
        for anio in range(2019, 2025)
        for mes in range(1, 13)
    ]
    dim = pd.DataFrame(rows)
    dim.insert(0, "tiempo_id", range(1, len(dim) + 1))
    print(f"  dim_tiempo_presupuestal: {len(dim)} filas")
    return dim


def build_dim_entidad(df_gasto: pd.DataFrame) -> pd.DataFrame:
    cols = ["NIVEL_GOBIERNO_NOMBRE", "SECTOR_NOMBRE", "PLIEGO_NOMBRE", "EJECUTORA_NOMBRE"]
    dim = df_gasto[cols].drop_duplicates().copy()
    dim.columns = ["nivel_gobierno", "sector_nombre", "pliego_nombre", "ejecutora_nombre"]
    dim = dim.sort_values("ejecutora_nombre").reset_index(drop=True)
    dim.insert(0, "entidad_id", range(1, len(dim) + 1))
    print(f"  dim_entidad: {len(dim)} filas")
    return dim


def build_dim_presupuesto(df_gasto: pd.DataFrame) -> pd.DataFrame:
    cols = ["FUENTE_FINANCIAMIENTO_NOMBRE", "RUBRO_NOMBRE",
            "GENERICA_NOMBRE", "SUBGENERICA_NOMBRE", "ESPECIFICA_NOMBRE"]
    dim = df_gasto[cols].drop_duplicates().copy()
    dim.columns = ["fuente_financiamiento", "rubro", "generica", "subgenerica", "especifica"]
    dim = dim.sort_values("fuente_financiamiento").reset_index(drop=True)
    dim.insert(0, "presupuesto_id", range(1, len(dim) + 1))
    print(f"  dim_presupuesto: {len(dim)} filas")
    return dim


def build_dim_programa_funcional(df_gasto: pd.DataFrame) -> pd.DataFrame:
    cols = ["PROGRAMA_PPTO_NOMBRE", "FUNCION_NOMBRE", "DIVISION_FUNCIONAL_NOMBRE",
            "GRUPO_FUNCIONAL_NOMBRE", "ACTIVIDAD_ACCION_OBRA_NOMBRE"]
    dim = df_gasto[cols].drop_duplicates().copy()
    dim.columns = ["programa_ppto_nombre", "funcion_nombre", "division_funcional_nombre",
                   "grupo_funcional_nombre", "actividad_nombre"]
    dim = dim.sort_values("programa_ppto_nombre").reset_index(drop=True)
    dim.insert(0, "programa_id", range(1, len(dim) + 1))
    print(f"  dim_programa_funcional: {len(dim)} filas")
    return dim


def build_dim_cambio_climatico(df_cc: pd.DataFrame) -> pd.DataFrame:
    cols = ["MEDIDA", "ATRIBUCION"]
    dim = df_cc[cols].drop_duplicates().copy()
    dim.columns = ["medida", "atribucion"]
    dim = dim.sort_values("medida").reset_index(drop=True)
    dim.insert(0, "cc_id", range(1, len(dim) + 1))
    print(f"  dim_cambio_climatico: {len(dim)} filas")
    return dim


# ── Nueva tabla de hechos (MEF/SIAF) ─────────────────────────────────────────

def build_fact_gasto(
    df_mant: pd.DataFrame | None,
    df_cc_raw: pd.DataFrame | None,
    dim_geo: pd.DataFrame,
    dim_tiempo_ppto: pd.DataFrame,
    dim_entidad: pd.DataFrame,
    dim_presupuesto: pd.DataFrame,
    dim_programa: pd.DataFrame,
    dim_cc_dim: pd.DataFrame | None,
) -> pd.DataFrame:
    frames = [f for f in [df_mant, df_cc_raw] if f is not None]
    df = pd.concat(frames, ignore_index=True)

    # Filtrar a rango 2019–2024 para consistencia con SIGERSOL
    df = df[df["ANO_EJE"].between(2019, 2024)].copy()

    # Normalizar columnas geográficas de gasto
    for col in ["DEPARTAMENTO_EJECUTORA_NOMBRE", "PROVINCIA_EJECUTORA_NOMBRE", "DISTRITO_EJECUTORA_NOMBRE"]:
        df[col] = _normalizar_geo(df[col])

    # Normalizar dim_geo para el join
    geo = dim_geo[["ubigeo", "departamento", "provincia", "distrito"]].copy()
    geo["departamento"] = _normalizar_geo(geo["departamento"])
    geo["provincia"] = _normalizar_geo(geo["provincia"])
    geo["distrito"] = _normalizar_geo(geo["distrito"])

    df = df.merge(
        geo, how="left",
        left_on=["DEPARTAMENTO_EJECUTORA_NOMBRE", "PROVINCIA_EJECUTORA_NOMBRE", "DISTRITO_EJECUTORA_NOMBRE"],
        right_on=["departamento", "provincia", "distrito"],
    ).drop(columns=["departamento", "provincia", "distrito"])

    # Join con dim_entidad
    df = df.merge(
        dim_entidad[["entidad_id", "nivel_gobierno", "sector_nombre", "pliego_nombre", "ejecutora_nombre"]],
        how="left",
        left_on=["NIVEL_GOBIERNO_NOMBRE", "SECTOR_NOMBRE", "PLIEGO_NOMBRE", "EJECUTORA_NOMBRE"],
        right_on=["nivel_gobierno", "sector_nombre", "pliego_nombre", "ejecutora_nombre"],
    ).drop(columns=["nivel_gobierno", "sector_nombre", "pliego_nombre", "ejecutora_nombre"])

    # Join con dim_presupuesto
    df = df.merge(
        dim_presupuesto[["presupuesto_id", "fuente_financiamiento", "rubro", "generica", "subgenerica", "especifica"]],
        how="left",
        left_on=["FUENTE_FINANCIAMIENTO_NOMBRE", "RUBRO_NOMBRE", "GENERICA_NOMBRE", "SUBGENERICA_NOMBRE", "ESPECIFICA_NOMBRE"],
        right_on=["fuente_financiamiento", "rubro", "generica", "subgenerica", "especifica"],
    ).drop(columns=["fuente_financiamiento", "rubro", "generica", "subgenerica", "especifica"])

    # Join con dim_programa_funcional
    df = df.merge(
        dim_programa[["programa_id", "programa_ppto_nombre", "funcion_nombre",
                      "division_funcional_nombre", "grupo_funcional_nombre", "actividad_nombre"]],
        how="left",
        left_on=["PROGRAMA_PPTO_NOMBRE", "FUNCION_NOMBRE", "DIVISION_FUNCIONAL_NOMBRE",
                 "GRUPO_FUNCIONAL_NOMBRE", "ACTIVIDAD_ACCION_OBRA_NOMBRE"],
        right_on=["programa_ppto_nombre", "funcion_nombre", "division_funcional_nombre",
                  "grupo_funcional_nombre", "actividad_nombre"],
    ).drop(columns=["programa_ppto_nombre", "funcion_nombre", "division_funcional_nombre",
                    "grupo_funcional_nombre", "actividad_nombre"])

    # Join con dim_cambio_climatico (nullable)
    if dim_cc_dim is not None and "MEDIDA" in df.columns:
        df = df.merge(
            dim_cc_dim[["cc_id", "medida", "atribucion"]],
            how="left",
            left_on=["MEDIDA", "ATRIBUCION"],
            right_on=["medida", "atribucion"],
        ).drop(columns=["medida", "atribucion"])
    else:
        df["cc_id"] = pd.NA

    # Join con dim_tiempo_presupuestal para obtener tiempo_id (granularidad mensual)
    df = df.merge(
        dim_tiempo_ppto[["tiempo_id", "anio", "mes"]],
        how="left",
        left_on=["ANO_EJE", "MES_EJE"],
        right_on=["anio", "mes"],
    ).drop(columns=["anio", "mes"])

    # Agregar a nivel mensual
    group_cols = ["ubigeo", "tiempo_id", "entidad_id", "presupuesto_id", "programa_id", "cc_id"]
    fact = df.groupby(group_cols, dropna=False).agg(
        monto_pia=("MONTO_PIA", "sum"),
        monto_pim=("MONTO_PIM", "sum"),
        monto_devengado=("MONTO_DEVENGADO", "sum"),
        monto_girado=("MONTO_GIRADO", "sum"),
    ).reset_index()

    fact = fact.sort_values(["ubigeo", "tiempo_id"]).reset_index(drop=True)
    fact.insert(0, "id", range(1, len(fact) + 1))
    print(f"  fact_gasto: {len(fact)} filas")
    return fact


# ── Runner ────────────────────────────────────────────────────────────────────

def run():
    print("=== TRANSFORMACIÓN ===")
    df_inorg = _read("inorganicos_clean.csv")
    df_org = _read("organicos_clean.csv")
    df_gen = _read("generacion_clean.csv")

    # Dimensiones base (SIGERSOL)
    dim_tiempo = build_dim_tiempo(df_gen)
    dim_geo = build_dim_geografica(df_gen)
    dim_municipio = build_dim_municipio(df_gen)
    dim_residuo = build_dim_residuo()

    # Hechos base (SIGERSOL)
    fact_val = build_fact_valorizacion(df_inorg, df_org)
    fact_gen = build_fact_generacion(df_gen)

    # Guardar tablas base
    dim_tiempo.to_parquet(MARTS_DIR / "dim_tiempo.parquet", index=False)
    dim_geo.to_parquet(MARTS_DIR / "dim_geografica.parquet", index=False)
    dim_municipio.to_parquet(MARTS_DIR / "dim_municipio.parquet", index=False)
    dim_residuo.to_parquet(MARTS_DIR / "dim_residuo.parquet", index=False)
    fact_val.to_parquet(MARTS_DIR / "fact_valorizacion.parquet", index=False)
    fact_gen.to_parquet(MARTS_DIR / "fact_generacion.parquet", index=False)

    dim_tiempo.to_csv(MARTS_DIR / "dim_tiempo.csv", index=False)
    dim_geo.to_csv(MARTS_DIR / "dim_geografica.csv", index=False)
    dim_municipio.to_csv(MARTS_DIR / "dim_municipio.csv", index=False)
    dim_residuo.to_csv(MARTS_DIR / "dim_residuo.csv", index=False)
    fact_val.to_csv(MARTS_DIR / "fact_valorizacion.csv", index=False)
    fact_gen.to_csv(MARTS_DIR / "fact_generacion.csv", index=False)

    # Dimensiones y hechos de gasto (MEF/SIAF) — condicional
    df_mant = _read_optional("gasto_mantenimiento_clean.csv")
    df_cc_raw = _read_optional("gasto_cambio_climatico_clean.csv")

    if df_mant is not None or df_cc_raw is not None:
        print("  [gasto] Procesando datos presupuestales...")
        df_gasto_all = pd.concat(
            [f for f in [df_mant, df_cc_raw] if f is not None], ignore_index=True
        )

        dim_tiempo_ppto = build_dim_tiempo_presupuestal()
        dim_entidad = build_dim_entidad(df_gasto_all)
        dim_presupuesto = build_dim_presupuesto(df_gasto_all)
        dim_programa = build_dim_programa_funcional(df_gasto_all)
        dim_cc_dim = build_dim_cambio_climatico(df_cc_raw) if df_cc_raw is not None else None
        fact_gasto = build_fact_gasto(df_mant, df_cc_raw, dim_geo, dim_tiempo_ppto, dim_entidad, dim_presupuesto, dim_programa, dim_cc_dim)

        dim_tiempo_ppto.to_parquet(MARTS_DIR / "dim_tiempo_presupuestal.parquet", index=False)
        dim_entidad.to_parquet(MARTS_DIR / "dim_entidad.parquet", index=False)
        dim_presupuesto.to_parquet(MARTS_DIR / "dim_presupuesto.parquet", index=False)
        dim_programa.to_parquet(MARTS_DIR / "dim_programa_funcional.parquet", index=False)
        fact_gasto.to_parquet(MARTS_DIR / "fact_gasto.parquet", index=False)

        dim_tiempo_ppto.to_csv(MARTS_DIR / "dim_tiempo_presupuestal.csv", index=False)
        dim_entidad.to_csv(MARTS_DIR / "dim_entidad.csv", index=False)
        dim_presupuesto.to_csv(MARTS_DIR / "dim_presupuesto.csv", index=False)
        dim_programa.to_csv(MARTS_DIR / "dim_programa_funcional.csv", index=False)
        fact_gasto.to_csv(MARTS_DIR / "fact_gasto.csv", index=False)

        if dim_cc_dim is not None:
            dim_cc_dim.to_parquet(MARTS_DIR / "dim_cambio_climatico.parquet", index=False)
            dim_cc_dim.to_csv(MARTS_DIR / "dim_cambio_climatico.csv", index=False)
    else:
        print("  [gasto] Sin datos de gasto disponibles, omitiendo tablas MEF/SIAF.")

    print("  Tablas guardadas en data/marts/")
    return dim_tiempo, dim_geo, dim_municipio, dim_residuo, fact_val, fact_gen


if __name__ == "__main__":
    run()
