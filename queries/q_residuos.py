"""Queries para Dashboard 2 — Residuos."""
import json
from pathlib import Path
from .db import get_con, GEO_CTE

_GEOJSON_PATH = Path(__file__).parent.parent / "geojson" / "peru-geojson-master" / "peru_distrital_simple.geojson"
_geojson_cache = None

def get_geojson():
    global _geojson_cache
    if _geojson_cache is None:
        with open(_GEOJSON_PATH, encoding="utf-8") as f:
            _geojson_cache = json.load(f)
    return _geojson_cache


def _q(vals):
    return ", ".join(f"'{v}'" for v in vals)


def _where(anios=None, regiones=None, departamentos=None,
           tipos=None, alias_geo="g", alias_fact="fv"):
    clauses = []
    if anios:
        clauses.append(f"{alias_fact}.anio IN ({', '.join(str(a) for a in anios)})")
    if regiones:
        clauses.append(f"{alias_geo}.region_natural IN ({_q(regiones)})")
    if departamentos:
        clauses.append(f"{alias_geo}.departamento IN ({_q(departamentos)})")
    if tipos:
        clauses.append(f"{alias_fact}.tipo_residuo IN ({_q(tipos)})")
    return ("WHERE " + " AND ".join(clauses)) if clauses else ""


# ── KPIs ──────────────────────────────────────────────────────────────────────

def kpi_residuos(anios=None, regiones=None, departamentos=None):
    where_val = _where(anios, regiones, departamentos, tipos=["ORGANICO"])
    where_gen = _where(anios, regiones, departamentos, alias_fact="fg")

    con = get_con()
    row_val = con.execute(f"""
        WITH {GEO_CTE}
        SELECT
            ROUND(SUM(fv.qresiduos_mun) / 1e6, 2)        AS generado_mt,
            ROUND(SUM(fv.qresiduos_valorizado) / 1e3, 1) AS valorizado_kt
        FROM fact_valorizacion fv
        JOIN geo g USING (ubigeo)
        {where_val}
    """).fetchone()

    row_gen = con.execute(f"""
        WITH {GEO_CTE}
        SELECT ROUND(AVG(fg.generacion_per_capita_municipal), 4) AS gpc
        FROM fact_generacion fg
        JOIN geo g USING (ubigeo)
        {where_gen}
    """).fetchone()
    con.close()
    return {
        "generado_mt":   row_val[0] or 0,
        "valorizado_kt": row_val[1] or 0,
        "gpc_municipal": row_gen[0] or 0,
    }


# ── R1: Evolución tasa valorización por tipo ──────────────────────────────────

def evolucion_tasa(anios=None, regiones=None, departamentos=None, tipos=None):
    where = _where(anios, regiones, departamentos, tipos)
    sql = f"""
        WITH {GEO_CTE}
        SELECT fv.anio, fv.tipo_residuo,
               ROUND(SUM(fv.qresiduos_valorizado) /
                     NULLIF(SUM(fv.qresiduos_mun), 0) * 100, 3) AS tasa_pct
        FROM fact_valorizacion fv
        JOIN geo g USING (ubigeo)
        {where}
        GROUP BY fv.anio, fv.tipo_residuo
        ORDER BY fv.tipo_residuo, fv.anio
    """
    con = get_con()
    df = con.execute(sql).df()
    con.close()
    return df


# ── R2: Top 10 distritos por tasa ─────────────────────────────────────────────

def top10_distritos_tasa(anios=None, regiones=None, departamentos=None, tipos=None):
    clauses = ["fv.tasa_valorizacion_pct > 0"]
    if anios:
        clauses.append(f"fv.anio IN ({', '.join(str(a) for a in anios)})")
    if regiones:
        clauses.append(f"g.region_natural IN ({_q(regiones)})")
    if departamentos:
        clauses.append(f"g.departamento IN ({_q(departamentos)})")
    if tipos:
        clauses.append(f"fv.tipo_residuo IN ({_q(tipos)})")
    where = "WHERE " + " AND ".join(clauses)
    sql = f"""
        WITH {GEO_CTE}
        SELECT g.distrito || ' (' || g.departamento || ')' AS lugar,
               ROUND(AVG(fv.tasa_valorizacion_pct), 2) AS tasa_pct
        FROM fact_valorizacion fv
        JOIN geo g USING (ubigeo)
        {where}
        GROUP BY g.distrito, g.departamento
        ORDER BY tasa_pct DESC
        LIMIT 10
    """
    con = get_con()
    df = con.execute(sql).df()
    con.close()
    return df


# ── R3: Heatmap tasa por región × año ─────────────────────────────────────────

def heatmap_region_anio(tipos=None, departamentos=None):
    clauses = []
    if tipos:
        clauses.append(f"fv.tipo_residuo IN ({_q(tipos)})")
    if departamentos:
        clauses.append(f"g.departamento IN ({_q(departamentos)})")
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = f"""
        WITH {GEO_CTE}
        SELECT g.region_natural, fv.anio,
               ROUND(SUM(fv.qresiduos_valorizado) /
                     NULLIF(SUM(fv.qresiduos_mun), 0) * 100, 3) AS tasa_pct
        FROM fact_valorizacion fv
        JOIN geo g USING (ubigeo)
        {where}
        GROUP BY g.region_natural, fv.anio
        ORDER BY g.region_natural, fv.anio
    """
    con = get_con()
    df = con.execute(sql).df()
    con.close()
    return df


# ── R4: DISTRITAL vs PROVINCIAL ───────────────────────────────────────────────

def por_tipo_municipalidad(anios=None, regiones=None, departamentos=None, tipos=None):
    clauses = ["m.tipo_municipalidad IS NOT NULL"]
    if anios:
        clauses.append(f"fv.anio IN ({', '.join(str(a) for a in anios)})")
    if regiones:
        clauses.append(f"g.region_natural IN ({_q(regiones)})")
    if departamentos:
        clauses.append(f"g.departamento IN ({_q(departamentos)})")
    if tipos:
        clauses.append(f"fv.tipo_residuo IN ({_q(tipos)})")
    where = "WHERE " + " AND ".join(clauses)
    sql = f"""
        WITH {GEO_CTE}
        SELECT m.tipo_municipalidad,
               ROUND(SUM(fv.qresiduos_valorizado), 1)  AS valorizado_t,
               ROUND(AVG(fv.tasa_valorizacion_pct), 2) AS tasa_promedio
        FROM fact_valorizacion fv
        JOIN geo g USING (ubigeo)
        JOIN dim_municipio m USING (ubigeo)
        {where}
        GROUP BY m.tipo_municipalidad
        ORDER BY m.tipo_municipalidad
    """
    con = get_con()
    df = con.execute(sql).df()
    con.close()
    return df


# ── R5: Scatter GPC vs tasa por departamento ──────────────────────────────────

def scatter_gpc_tasa(anios=None, regiones=None, tipos=None):
    tipo_c = f"fv.tipo_residuo IN ({_q(tipos)})" if tipos else "fv.tipo_residuo = 'ORGANICO'"
    clauses = [tipo_c]
    if anios:
        clauses.append(f"fv.anio IN ({', '.join(str(a) for a in anios)})")
    if regiones:
        clauses.append(f"g.region_natural IN ({_q(regiones)})")
    where = "WHERE " + " AND ".join(clauses)
    sql = f"""
        WITH {GEO_CTE}
        SELECT g.departamento, g.region_natural,
               ROUND(AVG(fg.generacion_per_capita_municipal), 4) AS gpc,
               ROUND(SUM(fv.qresiduos_valorizado) /
                     NULLIF(SUM(fv.qresiduos_mun), 0) * 100, 3) AS tasa_pct
        FROM fact_valorizacion fv
        JOIN geo g USING (ubigeo)
        JOIN fact_generacion fg ON fv.ubigeo = fg.ubigeo AND fv.anio = fg.anio
        {where}
        GROUP BY g.departamento, g.region_natural
        ORDER BY g.departamento
    """
    con = get_con()
    df = con.execute(sql).df()
    con.close()
    return df


# ── R6: Top 10 mejora primer → último año ────────────────────────────────────

def top10_mejora(regiones=None, departamentos=None, tipos=None):
    tipo_f = f"AND fv.tipo_residuo IN ({_q(tipos)})" if tipos else "AND fv.tipo_residuo = 'ORGANICO'"
    geo_f = ""
    if regiones:
        geo_f += f" AND g.region_natural IN ({_q(regiones)})"
    if departamentos:
        geo_f += f" AND g.departamento IN ({_q(departamentos)})"
    sql = f"""
        WITH {GEO_CTE},
        anio_min AS (SELECT MIN(anio) AS a FROM fact_valorizacion),
        anio_max AS (SELECT MAX(anio) AS a FROM fact_valorizacion),
        base AS (
            SELECT fv.ubigeo,
                   g.distrito || ' (' || g.departamento || ')' AS lugar,
                   fv.anio,
                   AVG(fv.tasa_valorizacion_pct) AS tasa
            FROM fact_valorizacion fv
            JOIN geo g USING (ubigeo)
            WHERE fv.anio IN ((SELECT a FROM anio_min), (SELECT a FROM anio_max))
              {tipo_f} {geo_f}
            GROUP BY fv.ubigeo, g.distrito, g.departamento, fv.anio
        )
        SELECT b1.lugar,
               ROUND(b1.tasa, 2) AS tasa_inicio,
               ROUND(b2.tasa, 2) AS tasa_fin,
               ROUND(b2.tasa - b1.tasa, 2) AS mejora
        FROM base b1
        JOIN base b2 ON b1.ubigeo = b2.ubigeo
        CROSS JOIN anio_min, anio_max
        WHERE b1.anio = anio_min.a AND b2.anio = anio_max.a
          AND b2.tasa > b1.tasa
        ORDER BY mejora DESC
        LIMIT 10
    """
    con = get_con()
    df = con.execute(sql).df()
    con.close()
    return df


# ── Mapa: generación por distrito ────────────────────────────────────────────

def mapa_generacion(anios=None, regiones=None, departamentos=None):
    clauses = []
    if anios:
        clauses.append(f"fg.anio IN ({', '.join(str(a) for a in anios)})")
    if regiones:
        clauses.append(f"g.region_natural IN ({_q(regiones)})")
    if departamentos:
        clauses.append(f"g.departamento IN ({_q(departamentos)})")
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = f"""
        WITH {GEO_CTE}
        SELECT LPAD(CAST(fg.ubigeo AS VARCHAR), 6, '0') AS ubigeo_str,
               g.distrito, g.departamento, g.region_natural,
               ROUND(SUM(fg.generacion_mun_tanio), 1)              AS generado_t,
               ROUND(AVG(fg.generacion_per_capita_municipal), 4)   AS gpc
        FROM fact_generacion fg
        JOIN geo g USING (ubigeo)
        {where}
        GROUP BY fg.ubigeo, g.distrito, g.departamento, g.region_natural
        ORDER BY generado_t DESC
    """
    con = get_con()
    df = con.execute(sql).df()
    con.close()
    return df


# ── R7: Treemap generación por departamento ───────────────────────────────────

def treemap_generacion(anios=None, regiones=None, departamentos=None):
    clauses = []
    if anios:
        clauses.append(f"fg.anio IN ({', '.join(str(a) for a in anios)})")
    if regiones:
        clauses.append(f"g.region_natural IN ({_q(regiones)})")
    if departamentos:
        clauses.append(f"g.departamento IN ({_q(departamentos)})")
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = f"""
        WITH {GEO_CTE}
        SELECT g.region_natural, g.departamento,
               ROUND(SUM(fg.generacion_mun_tanio) / 1e3, 1) AS generado_kt
        FROM fact_generacion fg
        JOIN geo g USING (ubigeo)
        {where}
        GROUP BY g.region_natural, g.departamento
        ORDER BY g.region_natural, generado_kt DESC
    """
    con = get_con()
    df = con.execute(sql).df()
    con.close()
    return df
