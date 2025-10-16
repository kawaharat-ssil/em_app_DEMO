import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime

# ==============================
# --- CSV / Excel 読み込み CSV/Excel/DB 読み込み関数を定義 ---
# ==============================


def load_from_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path, parse_dates=["Timestamp"])


def load_from_excel(path: str) -> pd.DataFrame:
    df = pd.read_excel(path)  # まずは普通に読む
    # 列名を確認
    print(df.columns)
    return df


# --- CSV 保存（追記モード） ---
def save_to_csv(df: pd.DataFrame, path: str):
    file_exists = Path(path).exists()
    df.to_csv(path, mode="a", header=not file_exists, index=False)


# --- SQLite 保存 ---
def save_to_sqlite(df: pd.DataFrame, db_path: str, table: str = "sensor_data"):
    conn = sqlite3.connect(db_path)
    df.to_sql(table, conn, if_exists="append", index=False)
    conn.close()


def load_from_sqlite(db_path: str, query: str = "SELECT * FROM sensor_data") -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    df = pd.read_sql(query, conn, parse_dates=["Timestamp"])
    conn.close()
    return df


# --- テスト用ダミーデータ生成 ---
def generate_dummy_data(n: int = 10) -> pd.DataFrame:
    now = datetime.now()
    return pd.DataFrame({
        "Timestamp": pd.date_range(now, periods=n, freq="T"),
        "SensorID": ["TEST"] * n,
        "Value": range(n)
    })