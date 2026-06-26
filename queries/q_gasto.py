"""Queries para Dashboard 3 — Gasto Presupuestal."""
from .db import get_con


def _q(vals):
    return ", ".join(f"'{v}'" for v in vals)


_CALLAO_RAW = 'PROVINCIA CONSTITUCIONAL DEL CALLAO'


def _norm_depto(d):
    return 'CALLAO' if d == _CALLAO_RAW else d


def _where(anios=None, niveles=None, deptos=None, funciones=None, programas=None, meses=None):
    clauses = ["departamento != ' '"]
    if anios:
        clauses.append(f"anio IN ({', '.join(str(a) for a in anios)})")
    if meses:
        clauses.append(f"mes IN ({', '.join(str(m) for m in meses)})")
    if niveles:
        clauses.append(f"nivel_gobierno IN ({_q(niveles)})")
    if deptos:
        # Expande 'CALLAO' para incluir su nombre largo en fact_gasto
        expanded = list(deptos)
        if 'CALLAO' in deptos:
            expanded.append(_CALLAO_RAW)
        clauses.append(f"departamento IN ({_q(expanded)})")
    if funciones:
        clauses.append(f"funcion IN ({_q(funciones)})")
    if programas:
        clauses.append(f"programa IN ({_q(programas)})")
    return "WHERE " + " AND ".join(clauses)


def opciones_gasto():
    con = get_con()
    anios = [r[0] for r in con.execute(
        "SELECT DISTINCT anio FROM fact_gasto WHERE anio IS NOT NULL ORDER BY anio"
    ).fetchall()]
    niveles = [r[0] for r in con.execute(
        "SELECT DISTINCT nivel_gobierno FROM fact_gasto WHERE nivel_gobierno IS NOT NULL ORDER BY 1"
    ).fetchall()]
    # Normaliza Callao y excluye EXTERIOR del dropdown
    deptos = sorted(set(
        _norm_depto(r[0]) for r in con.execute(
            "SELECT DISTINCT departamento FROM fact_gasto "
            "WHERE departamento IS NOT NULL AND departamento != ' ' AND departamento != 'EXTERIOR' ORDER BY 1"
        ).fetchall()
    ))
    funcs = [r[0] for r in con.execute(
        "SELECT DISTINCT funcion FROM fact_gasto WHERE funcion IS NOT NULL ORDER BY 1"
    ).fetchall()]
    progs = [r[0] for r in con.execute(
        "SELECT DISTINCT programa FROM fact_gasto WHERE programa IS NOT NULL ORDER BY 1"
    ).fetchall()]
    meses = [r[0] for r in con.execute(
        "SELECT DISTINCT mes FROM fact_gasto WHERE mes IS NOT NULL ORDER BY 1"
    ).fetchall()]
    con.close()
    return anios, niveles, deptos, funcs, progs, meses


def kpi_gasto(anios=None, niveles=None, deptos=None, funciones=None, programas=None, meses=None):
    where = _where(anios, niveles, deptos, funciones, programas, meses)
    con = get_con()
    row = con.execute(f"""
        SELECT
            ROUND(SUM(monto_pim)    / 1e9, 2),
            ROUND(SUM(monto_girado) / 1e9, 2),
            COUNT(DISTINCT departamento)
        FROM fact_gasto {where}
    """).fetchone()
    con.close()
    return {"pim": row[0] or 0, "girado": row[1] or 0, "deptos": row[2] or 0}


def evolucion_anual(anios=None, niveles=None, deptos=None, funciones=None, programas=None, meses=None):
    where = _where(anios, niveles, deptos, funciones, programas, meses)
    con = get_con()
    df = con.execute(f"""
        SELECT anio,
               ROUND(SUM(monto_pim)       / 1e9, 2) AS pim,
               ROUND(SUM(monto_devengado) / 1e9, 2) AS devengado
        FROM fact_gasto {where}
        GROUP BY anio ORDER BY anio
    """).df()
    con.close()
    return df


def top_deptos(anios=None, niveles=None, deptos=None, funciones=None, programas=None, meses=None):
    where = _where(anios, niveles, deptos, funciones, programas, meses)
    con = get_con()
    df = con.execute(f"""
        SELECT CASE WHEN departamento = '{_CALLAO_RAW}' THEN 'CALLAO' ELSE departamento END AS departamento,
               ROUND(SUM(monto_pim)       / 1e9, 3) AS pim,
               ROUND(SUM(monto_devengado) / 1e9, 3) AS devengado,
               ROUND(SUM(monto_devengado) / NULLIF(SUM(monto_pim), 0) * 100, 1) AS tasa_ejec
        FROM fact_gasto {where}
        GROUP BY 1
        ORDER BY devengado DESC
        LIMIT 15
    """).df()
    con.close()
    return df


def gasto_por_funcion(anios=None, niveles=None, deptos=None, funciones=None, programas=None, meses=None):
    where = _where(anios, niveles, deptos, funciones, programas, meses)
    con = get_con()
    df = con.execute(f"""
        SELECT funcion,
               ROUND(SUM(monto_devengado) / 1e9, 2) AS devengado
        FROM fact_gasto {where}
        GROUP BY funcion
        ORDER BY devengado DESC
        LIMIT 12
    """).df()
    con.close()
    return df


def gasto_por_fuente(anios=None, niveles=None, deptos=None, funciones=None, programas=None, meses=None):
    where = _where(anios, niveles, deptos, funciones, programas, meses)
    con = get_con()
    df = con.execute(f"""
        SELECT fuente_financiamiento,
               ROUND(SUM(monto_devengado) / 1e9, 2) AS devengado
        FROM fact_gasto {where}
        GROUP BY fuente_financiamiento
        ORDER BY devengado DESC
    """).df()
    con.close()
    return df


def gasto_por_nivel(anios=None, deptos=None, funciones=None, programas=None, meses=None):
    where = _where(anios, None, deptos, funciones, programas, meses)
    con = get_con()
    df = con.execute(f"""
        SELECT nivel_gobierno,
               ROUND(SUM(monto_pim)       / 1e9, 2) AS pim,
               ROUND(SUM(monto_devengado) / 1e9, 2) AS devengado
        FROM fact_gasto {where}
        GROUP BY nivel_gobierno
        ORDER BY devengado DESC
    """).df()
    con.close()
    return df


def heatmap_mensual(anios=None, niveles=None, deptos=None, funciones=None, programas=None, meses=None):
    where = _where(anios, niveles, deptos, funciones, programas, meses)
    con = get_con()
    df = con.execute(f"""
        SELECT anio, mes,
               ROUND(SUM(monto_devengado) / 1e6, 1) AS devengado_mill
        FROM fact_gasto {where}
        GROUP BY anio, mes
        ORDER BY anio, mes
    """).df()
    con.close()
    return df
