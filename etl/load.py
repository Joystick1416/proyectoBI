"""
load.py
Carga los marts a DuckDB (base de datos analítica embebida).
Genera también un reporte de validación en data/marts/reporte_calidad.txt
"""

import duckdb
import pandas as pd
from pathlib import Path
from datetime import datetime

MARTS_DIR = Path(__file__).parent.parent / "data" / "marts"
DB_PATH = MARTS_DIR / "datamart_residuos.duckdb"

TABLAS_BASE = [
    "dim_tiempo",
    "dim_geografica",
    "dim_municipio",
    "dim_residuo",
    "fact_valorizacion",
    "fact_generacion",
]

TABLAS_GASTO = [
    "dim_tiempo_presupuestal",
    "dim_entidad",
    "dim_presupuesto",
    "dim_programa_funcional",
    "dim_cambio_climatico",
    "fact_gasto",
]


def load_to_duckdb():
    """Carga todos los parquet disponibles en un archivo DuckDB."""
    if DB_PATH.exists():
        DB_PATH.unlink()  # Recrea siempre desde cero

    tablas = TABLAS_BASE + [t for t in TABLAS_GASTO if (MARTS_DIR / f"{t}.parquet").exists()]

    con = duckdb.connect(str(DB_PATH))
    for tabla in tablas:
        parquet_path = MARTS_DIR / f"{tabla}.parquet"
        con.execute(f"""
            CREATE TABLE {tabla} AS
            SELECT * FROM read_parquet('{parquet_path}')
        """)
        count = con.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
        print(f"  {tabla}: {count:,} filas cargadas en DuckDB")
    con.close()
    print(f"  Base de datos guardada en: {DB_PATH}")


def generate_quality_report():
    """Genera un reporte de calidad básico de los marts."""
    lines = [
        f"# Reporte de Calidad del Datamart",
        f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]
    con = duckdb.connect(str(DB_PATH), read_only=True)
    tablas_cargadas = [r[0] for r in con.execute("SHOW TABLES").fetchall()]

    for tabla in tablas_cargadas:
        df = con.execute(f"SELECT * FROM {tabla}").df()
        lines.append(f"## {tabla}")
        lines.append(f"- Filas: {len(df):,}")
        lines.append(f"- Columnas: {list(df.columns)}")
        nulls = df.isnull().sum()
        null_cols = nulls[nulls > 0]
        if len(null_cols):
            lines.append(f"- Nulos: {null_cols.to_dict()}")
        else:
            lines.append("- Nulos: ninguno")
        lines.append("")

    # Validaciones cruzadas — SIGERSOL
    lines.append("## Validaciones cruzadas")

    r = con.execute("""
        SELECT COUNT(DISTINCT ubigeo) FROM fact_valorizacion
        WHERE ubigeo NOT IN (SELECT ubigeo FROM dim_geografica)
    """).fetchone()[0]
    lines.append(f"- Ubigeos en fact_valorizacion sin match en dim_geografica: {r}")

    r2 = con.execute("""
        SELECT COUNT(DISTINCT ubigeo) FROM fact_generacion
        WHERE ubigeo NOT IN (SELECT ubigeo FROM dim_geografica)
    """).fetchone()[0]
    lines.append(f"- Ubigeos en fact_generacion sin match en dim_geografica: {r2}")

    r3 = con.execute("SELECT MIN(anio), MAX(anio) FROM fact_valorizacion").fetchone()
    lines.append(f"- Rango de años en fact_valorizacion: {r3[0]} – {r3[1]}")

    # Validaciones cruzadas — Gasto (si existe)
    if "fact_gasto" in tablas_cargadas:
        lines.append("")
        lines.append("## Validaciones cruzadas — Gasto (MEF/SIAF)")

        r4 = con.execute("""
            SELECT COUNT(DISTINCT ubigeo) FROM fact_gasto
            WHERE ubigeo NOT IN (SELECT ubigeo FROM dim_geografica)
        """).fetchone()[0]
        lines.append(f"- Ubigeos en fact_gasto sin match en dim_geografica: {r4}")

        r5 = con.execute("""
            SELECT COUNT(DISTINCT anio_id) FROM fact_gasto
            WHERE anio_id NOT IN (SELECT anio_id FROM dim_tiempo)
        """).fetchone()[0]
        lines.append(f"- Años en fact_gasto sin match en dim_tiempo: {r5}")

        r6 = con.execute("SELECT MIN(anio_id), MAX(anio_id) FROM fact_gasto").fetchone()
        lines.append(f"- Rango de años en fact_gasto: {r6[0]} – {r6[1]}")

        r7 = con.execute("SELECT COUNT(*) FROM fact_gasto WHERE ubigeo IS NULL").fetchone()[0]
        lines.append(f"- Registros en fact_gasto sin ubigeo (join geográfico fallido): {r7}")

    con.close()

    report_path = MARTS_DIR / "reporte_calidad.txt"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Reporte guardado en: {report_path}")


def run():
    print("=== CARGA ===")
    load_to_duckdb()
    generate_quality_report()


if __name__ == "__main__":
    run()
