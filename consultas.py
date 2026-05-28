"""
consultas.py
Reportes analíticos sobre el datamart de residuos sólidos.
Uso: python consultas.py
"""

import duckdb
from pathlib import Path

DB_PATH = Path("data/marts/datamart_residuos.duckdb")

def separador(titulo: str):
    print("\n" + "=" * 60)
    print(f"  {titulo}")
    print("=" * 60)


def reporte_evolucion_nacional(con):
    separador("1. EVOLUCIÓN NACIONAL DE VALORIZACIÓN (2019–2024)")
    df = con.execute("""
        SELECT
            anio,
            tipo_residuo,
            ROUND(SUM(qresiduos_mun), 1)         AS total_generado_t,
            ROUND(SUM(qresiduos_valorizado), 1)   AS total_valorizado_t,
            ROUND(SUM(qresiduos_valorizado) /
                  NULLIF(SUM(qresiduos_mun), 0) * 100, 2) AS tasa_valorizacion_pct
        FROM fact_valorizacion
        GROUP BY anio, tipo_residuo
        ORDER BY tipo_residuo, anio
    """).df()
    print(df.to_string(index=False))


def reporte_top_distritos_valorizacion(con):
    separador("2. TOP 10 DISTRITOS CON MAYOR TASA DE VALORIZACIÓN (2024)")
    for tipo in ["ORGANICO", "INORGANICO"]:
        print(f"\n  >> {tipo}")
        df = con.execute(f"""
            SELECT
                g.distrito,
                g.provincia,
                g.departamento,
                g.region_natural,
                ROUND(v.qresiduos_valorizado, 2) AS valorizado_t,
                ROUND(v.tasa_valorizacion_pct, 2) AS tasa_pct
            FROM fact_valorizacion v
            JOIN dim_geografica g USING (ubigeo)
            WHERE v.anio = 2024
              AND v.tipo_residuo = '{tipo}'
              AND v.tasa_valorizacion_pct IS NOT NULL
              AND v.qresiduos_valorizado > 0
            ORDER BY v.tasa_valorizacion_pct DESC
            LIMIT 10
        """).df()
        print(df.to_string(index=False))


def reporte_por_region_natural(con):
    separador("3. VALORIZACIÓN POR REGIÓN NATURAL Y AÑO")
    df = con.execute("""
        SELECT
            g.region_natural,
            v.anio,
            v.tipo_residuo,
            ROUND(SUM(v.qresiduos_mun), 1)        AS generado_t,
            ROUND(SUM(v.qresiduos_valorizado), 1)  AS valorizado_t,
            ROUND(SUM(v.qresiduos_valorizado) /
                  NULLIF(SUM(v.qresiduos_mun), 0) * 100, 2) AS tasa_pct
        FROM fact_valorizacion v
        JOIN dim_geografica g USING (ubigeo)
        GROUP BY g.region_natural, v.anio, v.tipo_residuo
        ORDER BY g.region_natural, v.tipo_residuo, v.anio
    """).df()
    print(df.to_string(index=False))


def reporte_ranking_departamentos(con):
    separador("4. RANKING DE DEPARTAMENTOS POR VALORIZACIÓN TOTAL (2024)")
    df = con.execute("""
        SELECT
            g.departamento,
            ROUND(SUM(CASE WHEN v.tipo_residuo = 'ORGANICO'
                          THEN v.qresiduos_valorizado ELSE 0 END), 1) AS organico_t,
            ROUND(SUM(CASE WHEN v.tipo_residuo = 'INORGANICO'
                          THEN v.qresiduos_valorizado ELSE 0 END), 1) AS inorganico_t,
            ROUND(SUM(v.qresiduos_valorizado), 1)                      AS total_valorizado_t,
            ROUND(SUM(v.qresiduos_valorizado) /
                  NULLIF(SUM(v.qresiduos_mun), 0) * 100, 2)           AS tasa_pct
        FROM fact_valorizacion v
        JOIN dim_geografica g USING (ubigeo)
        WHERE v.anio = 2024
        GROUP BY g.departamento
        ORDER BY total_valorizado_t DESC
    """).df()
    df.insert(0, "ranking", range(1, len(df) + 1))
    print(df.to_string(index=False))


def reporte_mejora_valorizacion(con):
    separador("5. TOP 10 DISTRITOS QUE MÁS MEJORARON SU TASA (2019 → 2024)")
    for tipo in ["ORGANICO", "INORGANICO"]:
        print(f"\n  >> {tipo}")
        df = con.execute(f"""
            WITH base AS (
                SELECT ubigeo,
                       MAX(CASE WHEN anio = 2019 THEN tasa_valorizacion_pct END) AS tasa_2019,
                       MAX(CASE WHEN anio = 2024 THEN tasa_valorizacion_pct END) AS tasa_2024
                FROM fact_valorizacion
                WHERE tipo_residuo = '{tipo}'
                GROUP BY ubigeo
            )
            SELECT
                g.distrito,
                g.departamento,
                ROUND(b.tasa_2019, 2) AS tasa_2019_pct,
                ROUND(b.tasa_2024, 2) AS tasa_2024_pct,
                ROUND(b.tasa_2024 - b.tasa_2019, 2) AS mejora_pct
            FROM base b
            JOIN dim_geografica g USING (ubigeo)
            WHERE b.tasa_2019 IS NOT NULL AND b.tasa_2024 IS NOT NULL
              AND b.tasa_2024 > b.tasa_2019
            ORDER BY mejora_pct DESC
            LIMIT 10
        """).df()
        print(df.to_string(index=False))


def reporte_generacion_per_capita(con):
    separador("6. GENERACIÓN PER CÁPITA MUNICIPAL PROMEDIO POR DEPARTAMENTO (2024)")
    df = con.execute("""
        SELECT
            g.departamento,
            ROUND(AVG(f.generacion_per_capita_municipal), 4) AS gpc_municipal_kg_hab_dia,
            ROUND(AVG(f.generacion_per_capita_dom), 4)       AS gpc_domiciliario_kg_hab_dia,
            ROUND(SUM(f.generacion_mun_tanio), 1)            AS total_generado_t_anio,
            COUNT(DISTINCT f.ubigeo)                          AS n_distritos
        FROM fact_generacion f
        JOIN dim_geografica g USING (ubigeo)
        WHERE f.anio = 2024
        GROUP BY g.departamento
        ORDER BY gpc_municipal_kg_hab_dia DESC
    """).df()
    print(df.to_string(index=False))


def reporte_distritos_sin_valorizacion(con):
    separador("7. DISTRITOS SIN VALORIZACIÓN EN 2024 (oportunidad de mejora)")
    df = con.execute("""
        SELECT
            g.region_natural,
            COUNT(DISTINCT g.ubigeo) AS distritos_sin_valorizacion
        FROM fact_valorizacion v
        JOIN dim_geografica g USING (ubigeo)
        WHERE v.anio = 2024
          AND v.qresiduos_valorizado = 0
        GROUP BY g.region_natural
        ORDER BY distritos_sin_valorizacion DESC
    """).df()
    print(df.to_string(index=False))

    total = con.execute("""
        SELECT COUNT(DISTINCT ubigeo) FROM fact_valorizacion
        WHERE anio = 2024 AND qresiduos_valorizado = 0
    """).fetchone()[0]
    print(f"\n  Total distritos sin ningún tipo de valorización en 2024: {total}")


def reporte_tipo_municipalidad(con):
    separador("8. VALORIZACIÓN SEGÚN TIPO DE MUNICIPALIDAD (2024)")
    df = con.execute("""
        SELECT
            m.tipo_municipalidad,
            v.tipo_residuo,
            COUNT(DISTINCT v.ubigeo)                          AS n_distritos,
            ROUND(SUM(v.qresiduos_valorizado), 1)             AS total_valorizado_t,
            ROUND(AVG(v.tasa_valorizacion_pct), 2)            AS tasa_promedio_pct
        FROM fact_valorizacion v
        JOIN dim_municipio m USING (ubigeo)
        WHERE v.anio = 2024
        GROUP BY m.tipo_municipalidad, v.tipo_residuo
        ORDER BY m.tipo_municipalidad, v.tipo_residuo
    """).df()
    print(df.to_string(index=False))


def main():
    if not DB_PATH.exists():
        print(f"[ERROR] No se encontró la base de datos en {DB_PATH}")
        print("Ejecuta primero:  python run_pipeline.py")
        return

    con = duckdb.connect(str(DB_PATH), read_only=True)
    print("\n" + "=" * 60)
    print("  REPORTES — Datamart Residuos Sólidos Perú 2019–2024")
    print("=" * 60)

    reporte_evolucion_nacional(con)
    reporte_top_distritos_valorizacion(con)
    reporte_por_region_natural(con)
    reporte_ranking_departamentos(con)
    reporte_mejora_valorizacion(con)
    reporte_generacion_per_capita(con)
    reporte_distritos_sin_valorizacion(con)
    reporte_tipo_municipalidad(con)

    con.close()
    print("\n" + "=" * 60)
    print("  Fin de reportes")
    print("=" * 60)


if __name__ == "__main__":
    main()
