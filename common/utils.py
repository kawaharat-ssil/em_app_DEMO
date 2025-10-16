import pandas as pd
import matplotlib
from datetime import datetime, timedelta

matplotlib.rcParams['font.family'] = 'Yu Gothic'


def load_timeseries_data(filepath: str) -> pd.DataFrame:
    df = pd.read_excel(filepath)
    df.columns = df.columns.str.strip()  # 前後の空白を削除
    df.columns = df.columns.str.replace("\n", "", regex=False)  # 改行を削除

    df["[排気] cna-13 AR3D[m/s^2]"] = pd.to_numeric(df["[排気] cna-13 AR3D[m/s^2]"], errors="coerce")
    df["[冷却] cna-13 AR3D[m/s^2]"] = pd.to_numeric(df["[冷却] cna-13 AR3D[m/s^2]"], errors="coerce")
    df["[排気] cna-13 VR3D[mm/s]"] = pd.to_numeric(df["[排気] cna-13 VR3D[mm/s]"], errors="coerce")
    df["[冷却] cna-13 VR3D[mm/s]"] = pd.to_numeric(df["[冷却] cna-13 VR3D[mm/s]"], errors="coerce")

    df['Timestamp'] = pd.to_datetime(df.iloc[:, 2])
    return df


# 今月の範囲を自動計算
def this_month_range():
    """今月の開始日と終了日を返す"""
    today = datetime.today()
    start = datetime(today.year, today.month, 1)
    if today.month == 12:
        end = datetime(today.year+1, 1, 1) - timedelta(seconds=1)
    else:
        end = datetime(today.year, today.month+1, 1) - timedelta(seconds=1)
    return start, end


# 統計値計算専用関数


