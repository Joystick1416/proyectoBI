"""Queries para Dashboard 1 — General."""
from .db import get_con, GEO_CTE


def _q(vals):
    return ", ".join(f"'{v}'" for v in vals)


def _where(anios=None, regiones=None, departamentos=None,
           alias_geo="g", alias_fact="fv"):
    clauses = []
    if anios:
        clauses.append(f"{alias_fact}.anio IN ({', '.join(str(a) for a in anios)})")
    if regiones:
        clauses.append(f"{alias_geo}.region_natural IN ({_q(regiones)})")
    if departamentos:
        clauses.append(f"{alias_geo}.departamento IN ({_q(departamentos)})")
    return ("WHERE " + " AND ".join(clauses)) if clauses else ""


# ── KPIs ──────────────────────────────────────────────────────────────────────

def kpi_general(anios=None, regiones=None, departamentos=None):
    where_gen = _where(anios, regiones, departamentos, alias_fact="fg")
    where_val = _where(anios, regiones, departamentos)
    con = get_con()
    r_gen = con.execute(f"""
        WITH {GEO_CTE}
        SELECT ROUND(SUM(fg.generacion_mun_tanio) / 1e6, 2) AS total_generado_mt
        FROM fact_generacion fg
        JOIN geo g USING (ubigeo)
        {where_gen}
    """).fetchone()
    r_val = con.execute(f"""
        WITH {GEO_CTE}
        SELECT ROUND(
            SUM(fv.qresiduos_valorizado) /
            NULLIF(SUM(CASE WHEN fv.tipo_residuo='ORGANICO'
                           THEN fv.qresiduos_mun END), 0) * 100
        , 2) AS tasa_valorizacion_pct
        FROM fact_valorizacion fv
        JOIN geo g USING (ubigeo)
        {where_val}
    """).fetchone()
    con.close()
    return {
        "total_generado_mt":     r_gen[0] or 0,
        "tasa_valorizacion_pct": r_val[0] or 0,
    }


# ── G1: Evolución tasa valorización nacional ──────────────────────────────────

def evolucion_tasa_nacional(anios=None, regiones=None, departamentos=None):
    where = _where(anios, regiones, departamentos)
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


# ── G2: Top 10 departamentos por toneladas valorizadas ───────────────────────

def top10_deptos_valorizado(anios=None, regiones=None, departamentos=None):
    clauses = ["g.departamento != ''"]
    if anios:
        clauses.append(f"fv.anio IN ({', '.join(str(a) for a in anios)})")
    if regiones:
        clauses.append(f"g.region_natural IN ({_q(regiones)})")
    if departamentos:
        clauses.append(f"g.departamento IN ({_q(departamentos)})")
    where = "WHERE " + " AND ".join(clauses)
    sql = f"""
        WITH {GEO_CTE}
        SELECT g.departamento,
               ROUND(SUM(fv.qresiduos_valorizado), 1) AS valorizado_t
        FROM fact_valorizacion fv
        JOIN geo g USING (ubigeo)
        {where}
        GROUP BY g.departamento
        ORDER BY valorizado_t DESC
        LIMIT 10
    """
    con = get_con()
    df = con.execute(sql).df()
    con.close()
    return df


# ── G3: Distritos sin valorización por región natural ────────────────────────

def sin_valorizacion_por_region(anios=None, departamentos=None):
    clauses = []
    if anios:
        clauses.append(f"fv.anio IN ({', '.join(str(a) for a in anios)})")
    if departamentos:
        clauses.append(f"g.departamento IN ({_q(departamentos)})")
    extra = ("AND " + " AND ".join(clauses)) if clauses else ""
    sql = f"""
        WITH {GEO_CTE}
        SELECT g.region_natural,
               COUNT(DISTINCT fv.ubigeo) AS sin_valorizacion
        FROM fact_valorizacion fv
        JOIN geo g USING (ubigeo)
        WHERE fv.tipo_residuo = 'ORGANICO'
          AND fv.tasa_valorizacion_pct = 0
          {extra}
        GROUP BY g.region_natural
        ORDER BY sin_valorizacion DESC
    """
    con = get_con()
    df = con.execute(sql).df()
    con.close()
    return df


# ── G4: Generación total por año ─────────────────────────────────────────────

def generacion_por_anio(anios=None, regiones=None, departamentos=None):
    where = _where(anios, regiones, departamentos, alias_fact="fg")
    sql = f"""
        WITH {GEO_CTE}
        SELECT fg.anio,
               ROUND(SUM(fg.generacion_mun_tanio) / 1e6, 3) AS generado_mt
        FROM fact_generacion fg
        JOIN geo g USING (ubigeo)
        {where}
        GROUP BY fg.anio
        ORDER BY fg.anio
    """
    con = get_con()
    df = con.execute(sql).df()
    con.close()
    return df


# ── G5: Resumen por región natural ───────────────────────────────────────────

def resumen_por_region(anios=None, departamentos=None):
    clauses = ["fv.tipo_residuo = 'ORGANICO'"]
    if anios:
        clauses.append(f"fv.anio IN ({', '.join(str(a) for a in anios)})")
    if departamentos:
        clauses.append(f"g.departamento IN ({_q(departamentos)})")
    where = "WHERE " + " AND ".join(clauses)
    sql = f"""
        WITH {GEO_CTE}
        SELECT g.region_natural,
               ROUND(SUM(fg.generacion_mun_tanio) / 1e6, 2)               AS generado_mt,
               ROUND(SUM(fv.qresiduos_valorizado) /
                     NULLIF(SUM(fv.qresiduos_mun), 0) * 100, 2)           AS tasa_valorizacion_pct,
               ROUND(AVG(fg.generacion_per_capita_municipal), 3)           AS gpc_municipal
        FROM fact_valorizacion fv
        JOIN geo g USING (ubigeo)
        JOIN fact_generacion fg ON fv.ubigeo = fg.ubigeo AND fv.anio = fg.anio
        {where}
        GROUP BY g.region_natural
        ORDER BY g.region_natural
    """
    con = get_con()
    df = con.execute(sql).df()
    con.close()
    return df


# ── Opciones para dropdowns ───────────────────────────────────────────────────

def opciones_filtros():
    con = get_con()
    anios = [r[0] for r in con.execute(
        "SELECT DISTINCT anio FROM fact_valorizacion ORDER BY anio").fetchall()]
    regiones = [r[0] for r in con.execute(
        f"WITH {GEO_CTE} SELECT DISTINCT region_natural FROM geo ORDER BY 1").fetchall()]
    deptos = [r[0] for r in con.execute(
        f"WITH {GEO_CTE} SELECT DISTINCT departamento FROM geo ORDER BY 1").fetchall()]
    con.close()
    return anios, regiones, deptos
