import pandas as pd


def calc_stats(y_data: pd.Series, label: str, slope: float=None, threshold: float=None) -> dict:
    total = len(y_data)
    below = (y_data < threshold).sum() if threshold else None
    above = (y_data >= threshold).sum() if threshold else None

    stats = {
        "ラベル": label,
        "最大値": float(y_data.max()),
        "最小値": float(y_data.min()),
        "平均値": float(y_data.mean()),
        "標準偏差": float(y_data.std()),
    }
    if slope is not None:
        stats["slope"] = float(slope)
    if threshold is not None:
        stats["閾値未満割合[%]"] = round(below / total * 100, 1)
        stats["閾値以上割合[%]"] = round(above / total * 100, 1)

    return stats