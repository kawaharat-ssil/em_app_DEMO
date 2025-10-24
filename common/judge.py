import numpy as np
import pandas as pd


def judge_status(y_data: pd.Series,
                 slope: float,
                 threshold: float = None,
                 threshold_range: tuple = None,
                 slope_alert: bool = False) -> str:

    # 優先：範囲指定がある場合はそれで判定
    if threshold_range is not None:
        low, high = threshold_range
        if (y_data < low).any() or (y_data > high).any():
            return "threshold"

    # 次点：単一閾値で判定（範囲指定がない場合のみ）
    elif threshold is not None:
        if (y_data > threshold).any():
            return "threshold"

    # 傾き判定
    if slope_alert:
        return "slope"

    return "normal"



def judge_slope_least_squares(y_data: pd.Series, slope_threshold: float) -> bool:
    """
    最小二乗法で傾きを計算し、傾きが閾値を超えていれば True（異常）を返す
    """
    if len(y_data) < 2:
        return False

    x = np.arange(len(y_data))
    y = y_data.values
    slope = np.polyfit(x, y, 1)[0]  # 1次回帰の傾き

    return slope > slope_threshold
