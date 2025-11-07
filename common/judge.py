import numpy as np
from scipy.stats import linregress
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
            return "threshold_exceedance"

    # 次点：単一閾値で判定（範囲指定がない場合のみ）
    elif threshold is not None:
        if (y_data > threshold).any():
            return "threshold_exceedance"

    # 傾き判定
    if slope_alert:
        return "slope_violation"

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


def judge_slope_linregress(x_time: pd.Series, y_data: pd.Series, slope_threshold: float, threshold: float):
    """
    時間軸に基づいて傾きを計算し、閾値を超えていれば True（異常）を返す。
    傾きの単位は /日。戻り値は (判定結果, 傾き値)
    """
    if len(x_time) < 2 or len(y_data) < 2:
        return False, 0.0

    # 経過時間（日単位）
    x_elapsed_days = (x_time - x_time.iloc[0]).dt.total_seconds() / (24 * 60 * 60)

    # 線形回帰
    slope, intercept, r_value, p_value, std_err = linregress(x_elapsed_days, y_data)

    # - slope（傾き）
    # - intercept（切片）
    # - r_value（相関係数）
    # - p_value（傾きが統計的に有意かどうかの検定結果）
    # - std_err（傾きの標準誤差）

    # 判定（傾きが正で、閾値を超えていれば異常）
    is_alert = slope > slope_threshold

    if slope <= 0:
        # 上昇傾向でなければ閾値を超えない
        return is_alert, None, slope, intercept

        # 閾値を超えると予測される日数
    x_cross = (threshold - intercept) / slope
    x_now = x_elapsed_days.iloc[-1]

    days_remaining = x_cross - x_now
    if days_remaining < 0:
        days_remaining = 0  # すでに超えている

    return is_alert, days_remaining, slope, intercept
