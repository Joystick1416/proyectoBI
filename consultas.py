"""
consultas.py
Genera reportes en texto y gráficos PNG en la carpeta reportes/
Uso: python consultas.py
"""

import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from pathlib import Path
from datetime import datetime

DB_PATH    = Path("data/marts/datamart_residuos.duckdb")
OUTPUT_DIR = Path("reportes")
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Estilo global ─────────────────────────────────────────────────────────────
sns.set_theme(style="whitegrid", palette="Set2")
COLORES = sns.color_palette("Set2")

def sep(titulo):
    linea = "=" * 62
    print(f"\n{linea}\n  {titulo}\n{linea}")

def guardar_txt(nombre, contenido):
    path = OUTPUT_DIR / nombre
    path.write_text(contenido, encoding="utf-8")
    print(f"  [guardado] {path}")

def guardar_fig(nombre):
    path = OUTPUT_DIR / nombre
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [guardado] {path}")


# ══════════════════════════════════════════════════════════════════════════════
# 1. EVOLUCIÓN NACIONAL
# ══════════════════════════════════════════════════════════════════════════════
def reporte_evolucion_nacional(con):
    sep("1. EVOLUCIÓN NACIONAL DE VALORIZACIÓN (2019–2024)")
    df = con.execute("""
        SELECT anio, tipo_residuo,
               ROUND(SUM(qresiduos_mun), 1)                                    AS generado_t,
               ROUND(SUM(qresiduos_valorizado), 1)                             AS valorizado_t,
               ROUND(SUM(qresiduos_valorizado)/NULLIF(SUM(qresiduos_mun),0)*100, 2) AS tasa_pct
        FROM fact_valorizacion
        GROUP BY anio, tipo_residuo
        ORDER BY tipo_residuo, anio
    """).df()
    print(df.to_string(index=False))
    guardar_txt("01_evolucion_nacional.txt", df.to_string(index=False))

    # Gráfico: líneas de tasa por tipo
    fig, ax = plt.subplots(figsize=(9, 5))
    for i, tipo in enumerate(["ORGANICO", "INORGANICO"]):
        sub = df[df["tipo_residuo"] == tipo]
        ax.plot(sub["anio"], sub["tasa_pct"], marker="o", linewidth=2.2,
                label=tipo.capitalize(), color=COLORES[i])
        for _, row in sub.iterrows():
            ax.annotate(f'{row["tasa_pct"]}%',
                        xy=(row["anio"], row["tasa_pct"]),
                        xytext=(0, 8), textcoords="offset points",
                        ha="center", fontsize=8)
    ax.set_title("Tasa de valorización nacional (%) 2019–2024", fontsize=13, fontweight="bold")
    ax.set_xlabel("Año"); ax.set_ylabel("Tasa (%)")
    ax.legend(); ax.set_xticks(df["anio"].unique())
    guardar_fig("01_evolucion_nacional.png")

    # Gráfico: barras apiladas toneladas valorizadas
    df_wide = df.pivot(index="anio", columns="tipo_residuo", values="valorizado_t").fillna(0)
    fig, ax = plt.subplots(figsize=(9, 5))
    df_wide.plot(kind="bar", ax=ax, color=[COLORES[0], COLORES[1]], width=0.6)
    ax.set_title("Toneladas valorizadas por tipo (nacional) 2019–2024", fontsize=13, fontweight="bold")
    ax.set_xlabel("Año"); ax.set_ylabel("Toneladas")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.tick_params(axis="x", rotation=0)
    ax.legend(title="Tipo")
    guardar_fig("01_evolucion_toneladas.png")


# ══════════════════════════════════════════════════════════════════════════════
# 2. TOP 10 DISTRITOS
# ══════════════════════════════════════════════════════════════════════════════
def reporte_top_distritos(con):
    sep("2. TOP 10 DISTRITOS — MAYOR TASA DE VALORIZACIÓN (2024)")
    for i, tipo in enumerate(["ORGANICO", "INORGANICO"]):
        df = con.execute(f"""
            SELECT g.distrito || ' (' || g.departamento || ')' AS lugar,
                   ROUND(v.qresiduos_valorizado, 1) AS valorizado_t,
                   ROUND(v.tasa_valorizacion_pct, 2) AS tasa_pct
            FROM fact_valorizacion v
            JOIN dim_geografica g USING (ubigeo)
            WHERE v.anio = 2024 AND v.tipo_residuo = '{tipo}'
              AND v.tasa_valorizacion_pct IS NOT NULL
              AND v.qresiduos_valorizado > 0
            GROUP BY lugar, valorizado_t, tasa_pct
            ORDER BY tasa_pct DESC LIMIT 10
        """).df()
        print(f"\n  {tipo}\n{df.to_string(index=False)}")
        guardar_txt(f"02_top10_{tipo.lower()}.txt", df.to_string(index=False))

        fig, ax = plt.subplots(figsize=(10, 5))
        bars = ax.barh(df["lugar"][::-1], df["tasa_pct"][::-1], color=COLORES[i])
        ax.bar_label(bars, fmt="%.1f%%", padding=4, fontsize=8)
        ax.set_title(f"Top 10 distritos — valorización {tipo.lower()} 2024",
                     fontsize=13, fontweight="bold")
        ax.set_xlabel("Tasa de valorización (%)")
        ax.set_xlim(0, df["tasa_pct"].max() * 1.2)
        plt.tight_layout()
        guardar_fig(f"02_top10_{tipo.lower()}.png")


# ══════════════════════════════════════════════════════════════════════════════
# 3. REGIÓN NATURAL
# ══════════════════════════════════════════════════════════════════════════════
def reporte_region_natural(con):
    sep("3. VALORIZACIÓN POR REGIÓN NATURAL Y AÑO")
    df = con.execute("""
        SELECT g.region_natural, v.anio, v.tipo_residuo,
               ROUND(SUM(v.qresiduos_valorizado)/NULLIF(SUM(v.qresiduos_mun),0)*100, 2) AS tasa_pct
        FROM fact_valorizacion v
        JOIN dim_geografica g USING (ubigeo)
        WHERE g.region_natural NOT LIKE '%LIMA%'   -- evita duplicados Lima/Callao
        GROUP BY g.region_natural, v.anio, v.tipo_residuo
        ORDER BY g.region_natural, v.tipo_residuo, v.anio
    """).df()
    print(df.to_string(index=False))
    guardar_txt("03_region_natural.txt", df.to_string(index=False))

    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=False)
    for idx, tipo in enumerate(["ORGANICO", "INORGANICO"]):
        ax = axes[idx]
        sub = df[df["tipo_residuo"] == tipo]
        for j, region in enumerate(sub["region_natural"].unique()):
            r = sub[sub["region_natural"] == region]
            ax.plot(r["anio"], r["tasa_pct"], marker="o", linewidth=2,
                    label=region, color=COLORES[j])
        ax.set_title(f"Tasa valorización {tipo.lower()}\npor región natural",
                     fontsize=11, fontweight="bold")
        ax.set_xlabel("Año"); ax.set_ylabel("Tasa (%)")
        ax.legend(fontsize=8); ax.set_xticks(df["anio"].unique())
    fig.suptitle("Evolución por región natural 2019–2024", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    guardar_fig("03_region_natural.png")


# ══════════════════════════════════════════════════════════════════════════════
# 4. RANKING DEPARTAMENTOS
# ══════════════════════════════════════════════════════════════════════════════
def reporte_ranking_departamentos(con):
    sep("4. RANKING DE DEPARTAMENTOS — VALORIZACIÓN TOTAL (2024)")
    df = con.execute("""
        SELECT g.departamento,
               ROUND(SUM(CASE WHEN v.tipo_residuo='ORGANICO'   THEN v.qresiduos_valorizado ELSE 0 END),1) AS organico_t,
               ROUND(SUM(CASE WHEN v.tipo_residuo='INORGANICO' THEN v.qresiduos_valorizado ELSE 0 END),1) AS inorganico_t,
               ROUND(SUM(v.qresiduos_valorizado),1) AS total_t,
               ROUND(SUM(v.qresiduos_valorizado)/NULLIF(SUM(v.qresiduos_mun),0)*100,2) AS tasa_pct
        FROM fact_valorizacion v
        JOIN dim_geografica g USING (ubigeo)
        WHERE v.anio = 2024
        GROUP BY g.departamento
        ORDER BY total_t DESC
        LIMIT 15
    """).df()
    print(df.to_string(index=False))
    guardar_txt("04_ranking_departamentos.txt", df.to_string(index=False))

    fig, ax = plt.subplots(figsize=(11, 6))
    x = range(len(df))
    ax.bar(x, df["organico_t"],   label="Orgánico",    color=COLORES[0])
    ax.bar(x, df["inorganico_t"], bottom=df["organico_t"], label="Inorgánico", color=COLORES[1])
    ax.set_xticks(x); ax.set_xticklabels(df["departamento"], rotation=35, ha="right", fontsize=9)
    ax.set_title("Top 15 departamentos — toneladas valorizadas (2024)",
                 fontsize=13, fontweight="bold")
    ax.set_ylabel("Toneladas")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.legend()
    plt.tight_layout()
    guardar_fig("04_ranking_departamentos.png")


# ══════════════════════════════════════════════════════════════════════════════
# 5. MEJORA 2019 → 2024
# ══════════════════════════════════════════════════════════════════════════════
def reporte_mejora(con):
    sep("5. TOP 10 DISTRITOS QUE MÁS MEJORARON (2019 → 2024)")
    for i, tipo in enumerate(["ORGANICO", "INORGANICO"]):
        df = con.execute(f"""
            WITH base AS (
                SELECT ubigeo,
                       MAX(CASE WHEN anio=2019 THEN tasa_valorizacion_pct END) AS t2019,
                       MAX(CASE WHEN anio=2024 THEN tasa_valorizacion_pct END) AS t2024
                FROM fact_valorizacion WHERE tipo_residuo='{tipo}' GROUP BY ubigeo
            )
            SELECT g.distrito || ' (' || g.departamento || ')' AS lugar,
                   ROUND(b.t2019,2) AS tasa_2019, ROUND(b.t2024,2) AS tasa_2024,
                   ROUND(b.t2024-b.t2019,2) AS mejora
            FROM base b JOIN dim_geografica g USING (ubigeo)
            WHERE b.t2019 IS NOT NULL AND b.t2024 > b.t2019
            GROUP BY lugar, b.t2019, b.t2024, mejora
            ORDER BY mejora DESC LIMIT 10
        """).df()
        print(f"\n  {tipo}\n{df.to_string(index=False)}")
        guardar_txt(f"05_mejora_{tipo.lower()}.txt", df.to_string(index=False))

        fig, ax = plt.subplots(figsize=(10, 5))
        y = range(len(df))
        ax.barh(list(y), df["tasa_2019"][::-1], color="#c9d6df", label="2019")
        ax.barh(list(y), (df["tasa_2024"] - df["tasa_2019"])[::-1],
                left=df["tasa_2019"][::-1], color=COLORES[i], label="Mejora → 2024")
        ax.set_yticks(list(y)); ax.set_yticklabels(df["lugar"][::-1], fontsize=8)
        ax.set_title(f"Top 10 mejora en valorización {tipo.lower()} (2019→2024)",
                     fontsize=12, fontweight="bold")
        ax.set_xlabel("Tasa (%)"); ax.legend()
        plt.tight_layout()
        guardar_fig(f"05_mejora_{tipo.lower()}.png")


# ══════════════════════════════════════════════════════════════════════════════
# 6. GENERACIÓN PER CÁPITA
# ══════════════════════════════════════════════════════════════════════════════
def reporte_per_capita(con):
    sep("6. GENERACIÓN PER CÁPITA MUNICIPAL POR DEPARTAMENTO (2024)")
    df = con.execute("""
        SELECT g.departamento,
               ROUND(AVG(f.generacion_per_capita_municipal),4) AS gpc_municipal,
               ROUND(AVG(f.generacion_per_capita_dom),4)       AS gpc_domiciliario
        FROM fact_generacion f JOIN dim_geografica g USING (ubigeo)
        WHERE f.anio=2024
        GROUP BY g.departamento
        ORDER BY gpc_municipal DESC
        LIMIT 20
    """).df()
    print(df.to_string(index=False))
    guardar_txt("06_per_capita.txt", df.to_string(index=False))

    fig, ax = plt.subplots(figsize=(11, 6))
    x = range(len(df))
    ax.bar(x, df["gpc_municipal"],    label="Municipal",    color=COLORES[2])
    ax.bar(x, df["gpc_domiciliario"], label="Domiciliario", color=COLORES[3], alpha=0.8)
    ax.set_xticks(x); ax.set_xticklabels(df["departamento"], rotation=35, ha="right", fontsize=9)
    ax.set_title("Generación per cápita kg/hab/día por departamento (2024)",
                 fontsize=12, fontweight="bold")
    ax.set_ylabel("kg / hab / día"); ax.legend()
    plt.tight_layout()
    guardar_fig("06_per_capita.png")


# ══════════════════════════════════════════════════════════════════════════════
# 7. DISTRITOS SIN VALORIZACIÓN
# ══════════════════════════════════════════════════════════════════════════════
def reporte_sin_valorizacion(con):
    sep("7. DISTRITOS SIN VALORIZACIÓN EN 2024")
    df = con.execute("""
        SELECT g.region_natural,
               COUNT(DISTINCT g.ubigeo) AS sin_valorizacion
        FROM fact_valorizacion v JOIN dim_geografica g USING (ubigeo)
        WHERE v.anio=2024 AND v.qresiduos_valorizado=0
          AND g.region_natural NOT LIKE '%LIMA%'
        GROUP BY g.region_natural ORDER BY sin_valorizacion DESC
    """).df()
    print(df.to_string(index=False))
    guardar_txt("07_sin_valorizacion.txt", df.to_string(index=False))

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.pie(df["sin_valorizacion"], labels=df["region_natural"],
           autopct="%1.1f%%", colors=COLORES[:len(df)],
           startangle=90, wedgeprops=dict(edgecolor="white", linewidth=1.5))
    ax.set_title("Distribución de distritos sin valorización\npor región natural (2024)",
                 fontsize=12, fontweight="bold")
    guardar_fig("07_sin_valorizacion.png")


# ══════════════════════════════════════════════════════════════════════════════
# 8. TIPO DE MUNICIPALIDAD
# ══════════════════════════════════════════════════════════════════════════════
def reporte_tipo_municipalidad(con):
    sep("8. VALORIZACIÓN SEGÚN TIPO DE MUNICIPALIDAD (2024)")
    df = con.execute("""
        SELECT m.tipo_municipalidad, v.tipo_residuo,
               COUNT(DISTINCT v.ubigeo)            AS n_distritos,
               ROUND(SUM(v.qresiduos_valorizado),1) AS total_t,
               ROUND(AVG(v.tasa_valorizacion_pct),2) AS tasa_promedio
        FROM fact_valorizacion v JOIN dim_municipio m USING (ubigeo)
        WHERE v.anio=2024
        GROUP BY m.tipo_municipalidad, v.tipo_residuo
        ORDER BY m.tipo_municipalidad, v.tipo_residuo
    """).df()
    print(df.to_string(index=False))
    guardar_txt("08_tipo_municipalidad.txt", df.to_string(index=False))

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for idx, metrica in enumerate([("total_t", "Toneladas valorizadas"),
                                    ("tasa_promedio", "Tasa promedio (%)")]):
        col, label = metrica
        ax = axes[idx]
        ancho = 0.35
        tipos_mun  = df["tipo_municipalidad"].unique()
        tipos_res  = df["tipo_residuo"].unique()
        x = range(len(tipos_mun))
        for j, tr in enumerate(tipos_res):
            vals = [df[(df["tipo_municipalidad"]==tm) & (df["tipo_residuo"]==tr)][col].values[0]
                    for tm in tipos_mun]
            ax.bar([xi + j*ancho for xi in x], vals, ancho, label=tr, color=COLORES[j])
        ax.set_xticks([xi + ancho/2 for xi in x])
        ax.set_xticklabels(tipos_mun, fontsize=10)
        ax.set_title(label, fontsize=11, fontweight="bold")
        ax.set_ylabel(label); ax.legend()
    fig.suptitle("Valorización por tipo de municipalidad (2024)", fontsize=13, fontweight="bold")
    plt.tight_layout()
    guardar_fig("08_tipo_municipalidad.png")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    if not DB_PATH.exists():
        print(f"[ERROR] No se encontró {DB_PATH}\nEjecuta primero: python run_pipeline.py")
        return

    con = duckdb.connect(str(DB_PATH), read_only=True)
    ts  = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"\n{'='*62}")
    print(f"  REPORTES — Datamart Residuos Sólidos Perú 2019–2024")
    print(f"  Generado: {ts}")
    print(f"{'='*62}")

    reporte_evolucion_nacional(con)
    reporte_top_distritos(con)
    reporte_region_natural(con)
    reporte_ranking_departamentos(con)
    reporte_mejora(con)
    reporte_per_capita(con)
    reporte_sin_valorizacion(con)
    reporte_tipo_municipalidad(con)

    con.close()
    print(f"\n{'='*62}")
    print(f"  Listo. Archivos guardados en: {OUTPUT_DIR.resolve()}")
    print(f"{'='*62}\n")


if __name__ == "__main__":
    main()
