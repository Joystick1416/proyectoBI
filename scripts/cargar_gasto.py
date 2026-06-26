"""Carga fact_gasto desde los ZIP anuales de Gasto Mantenimiento al DuckDB."""
import zipfile
from pathlib import Path
import pandas as pd
import duckdb

RAW_DIR = Path(__file__).parent.parent / "data" / "raw" / "Gasto_mantenimiento"
DB_PATH  = Path(__file__).parent.parent / "data" / "marts" / "datamart_residuos.duckdb"

COLS = [
    "ANO_EJE",
    "MES_EJE",
    "NIVEL_GOBIERNO_NOMBRE",
    "SECTOR_NOMBRE",
    "DEPARTAMENTO_META_NOMBRE",
    "FUNCION_NOMBRE",
    "PROGRAMA_PPTO_NOMBRE",
    "CATEGORIA_GASTO_NOMBRE",
    "FUENTE_FINANCIAMIENTO_NOMBRE",
    "GENERICA_NOMBRE",
    "MONTO_PIM",
    "MONTO_DEVENGADO",
    "MONTO_GIRADO",
]

RENAME = {
    "ANO_EJE":                    "anio",
    "MES_EJE":                    "mes",
    "NIVEL_GOBIERNO_NOMBRE":      "nivel_gobierno",
    "SECTOR_NOMBRE":              "sector",
    "DEPARTAMENTO_META_NOMBRE":   "departamento",
    "FUNCION_NOMBRE":             "funcion",
    "PROGRAMA_PPTO_NOMBRE":       "programa",
    "CATEGORIA_GASTO_NOMBRE":     "categoria_gasto",
    "FUENTE_FINANCIAMIENTO_NOMBRE": "fuente_financiamiento",
    "GENERICA_NOMBRE":            "generica",
    "MONTO_PIM":                  "monto_pim",
    "MONTO_DEVENGADO":            "monto_devengado",
    "MONTO_GIRADO":               "monto_girado",
}

def leer_zip(zip_path: Path) -> pd.DataFrame:
    csv_name = zip_path.stem + ".csv"
    with zipfile.ZipFile(zip_path) as z:
        with z.open(csv_name) as f:
            df = pd.read_csv(f, encoding="latin-1", usecols=COLS, low_memory=False)
    df = df.rename(columns=RENAME)
    df["monto_pim"]       = pd.to_numeric(df["monto_pim"],       errors="coerce").fillna(0)
    df["monto_devengado"] = pd.to_numeric(df["monto_devengado"], errors="coerce").fillna(0)
    df["monto_girado"]    = pd.to_numeric(df["monto_girado"],    errors="coerce").fillna(0)
    return df


def main():
    zips = sorted(RAW_DIR.glob("*.zip"))
    if not zips:
        print("No se encontraron archivos ZIP en", RAW_DIR)
        return

    frames = []
    for z in zips:
        print(f"  Leyendo {z.name}…", end=" ", flush=True)
        df = leer_zip(z)
        print(f"{len(df):,} filas")
        frames.append(df)

    print("Concatenando…")
    gasto = pd.concat(frames, ignore_index=True)
    print(f"Total: {len(gasto):,} filas · {len(gasto.columns)} columnas")

    print("Cargando en DuckDB…")
    con = duckdb.connect(str(DB_PATH))
    con.execute("DROP TABLE IF EXISTS fact_gasto")
    con.execute("CREATE TABLE fact_gasto AS SELECT * FROM gasto")
    total = con.execute("SELECT COUNT(*) FROM fact_gasto").fetchone()[0]
    con.close()
    print(f"fact_gasto creada: {total:,} filas en {DB_PATH.name}")


if __name__ == "__main__":
    main()
