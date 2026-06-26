import duckdb
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "marts" / "datamart_residuos.duckdb"

def get_con():
    return duckdb.connect(str(DB_PATH), read_only=True)

# CTE que deduplica dim_geografica (hay ubigeos con trailing-space en departamento)
GEO_CTE = """
    geo AS (
        SELECT DISTINCT
               ubigeo,
               TRIM(departamento)  AS departamento,
               TRIM(provincia)     AS provincia,
               TRIM(distrito)      AS distrito,
               region_natural
        FROM dim_geografica
        QUALIFY ROW_NUMBER() OVER (PARTITION BY ubigeo ORDER BY LENGTH(departamento)) = 1
    )
"""
