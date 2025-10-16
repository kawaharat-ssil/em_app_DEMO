
import matplotlib
import numpy as np
from scipy.stats import linregress
from config import THRESHOLD_VALUE, THRESHOLD_RANGE_exhaust, THRESHOLD_RANGE_cooling, THRESHOLD_SLOPE
from common.patlite_control import activate_patlight_on, activate_patlight_off
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

matplotlib.rcParams['font.family'] = 'Yu Gothic'





# グラフ描画専用関数
def plot_graph(x_time, y_data, slope, intercept, label, start, end,
               figsize, style_params, threshold=None,
               threshold_range: tuple = None,
               slope_threshold: float = None,
               patlight_index: int = 1):

    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    # デフォルト値を設定
    title_fontsize = style_params.get("title_fontsize", 11)
    label_fontsize = style_params.get("label_fontsize", 9)
    tick_fontsize = style_params.get("tick_fontsize", 9)
    legend_fontsize = style_params.get("legend_fontsize", 9)
    legend_loc = style_params.get("legend_loc", "upper center")
    legend_bbox = style_params.get("legend_bbox", (0.5, -0.25))
    legend_ncol = style_params.get("legend_ncol", 3)

    fig, ax = plt.subplots(figsize=figsize)

    # 経過時間（日単位）
    x_elapsed_days = (x_time - x_time.iloc[0]).dt.total_seconds() / (24 * 60 * 60)
    # 近似直線
    y_fit = slope * x_elapsed_days + intercept
    ax.plot(x_time, y_data, 'o', label=label)
    ax.plot(x_time, y_fit, 'r--', label=f"近似直線 (傾き={slope:.4f} [m/s²/日])")

    # 正常範囲の帯
    if threshold_range is not None:
        low, high = threshold_range
        ax.axhspan(low, high, color='green', alpha=0.2,
                   label=f'正常範囲 ({low}–{high})')
        ax.axhline(low, color='green', linestyle='--', linewidth=1)
        ax.axhline(high, color='green', linestyle='--', linewidth=1)

    ax.set_ylim(0, 6)
    ax.set_ylabel("加速度［m/s2］", fontsize=label_fontsize)  # ← 小さめに
    ax.set_title(f"{label}\n{start} ～ {end}", fontsize=title_fontsize)  # ← 小さめに
    ax.tick_params(axis='x', labelsize=tick_fontsize)  # ← X軸ラベル小さめ
    ax.tick_params(axis='y', labelsize=tick_fontsize)  # ← Y軸ラベル小さめ

    ax.grid(True)
    ax.legend(
        loc=legend_loc,
        bbox_to_anchor=legend_bbox,
        ncol=legend_ncol,
        fontsize=legend_fontsize,
        frameon=False
    )
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M"))
    fig.autofmt_xdate()

    return fig




# グラフ描画専用関数
def make_graph_plotly(df: pd.DataFrame, start, end, col_index: int, label: str,
                      style_params: dict,
                      threshold: float = None,
                      threshold_range: tuple = None,
                      slope_threshold: float = None):

    # データ抽出
    data = df[(df['Timestamp'] >= start) & (df['Timestamp'] <= end)].copy()
    subset = data[['Timestamp', data.columns[col_index]]].dropna()
    if len(subset) < 2:
        return None, None, None

    x_time = subset['Timestamp']
    y_data = subset.iloc[:, 1]

    # 経過時間（日単位）
    x_elapsed_days = (x_time - x_time.iloc[0]).dt.total_seconds() / (24 * 60 * 60)

    # 回帰（傾きは /日 単位になる）
    slope, intercept, _, _, _ = linregress(x_elapsed_days, y_data)

    # 統計値計算
    threshold_for_stats = threshold_range[1] if threshold_range is not None else threshold
    stats = calc_stats(y_data, label, slope=slope, threshold=threshold_for_stats)

    # 判定ロジック
    status = judge_status(
        y_data=y_data,
        slope=slope,
        threshold=threshold,
        threshold_range=threshold_range,
        slope_threshold=slope_threshold
    )

    if threshold_range is not None:
        low, high = threshold_range
        threshold_high = high
        threshold_low = low
    mask = (y_data < threshold_low) | (y_data > threshold_high)

    # --- Plotly グラフ作成 ---
    fig = go.Figure()

    # 正常値
    fig.add_trace(go.Scatter(
        x=x_time[~mask],
        y=y_data[~mask],
        mode="markers",
        marker=dict(color="blue"),
        name="正常値"
    ))

    # 異常値
    fig.add_trace(go.Scatter(
        x=x_time[mask],
        y=y_data[mask],
        mode="markers",
        marker=dict(color="red", size=10, symbol="x"),
        name="異常値"
    ))

    # 近似直線
    y_fit = slope * x_elapsed_days + intercept
    fig.add_trace(go.Scatter(
        x=x_time, y=y_fit,
        mode="lines",
        line=dict(dash="dash", color="red"),
        name=f"近似直線 (傾き={slope:.4f} [m/s²/日])"
    ))

    # 正常範囲の帯
    if threshold_range is not None:
        low, high = threshold_range
        fig.add_hrect(
            y0=low, y1=high,
            fillcolor="green", opacity=0.2,
            line_width=0
        )
        # 凡例用のダミートレースを追加
        fig.add_trace(
            go.Scatter(
                x=[None], y=[None],
                mode="lines",
                line=dict(color="green", width=15),
                name=f"正常範囲 {low}–{high}"
            )
        )

    # レイアウト調整
    fig.update_layout(
        plot_bgcolor="rgb(245,247,249)",
        title=dict(
            text=f"{label}<br>{start} ～ {end}",
            x=0.5,
            xanchor="center",
            font=dict(size=style_params.get("title_fontsize", 12))
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="center",
            x=0.5,
            font=dict(size=style_params.get("legend_fontsize", 10))
        ),
        title_font=dict(size=style_params.get("title_fontsize", 12)),
        yaxis_title="加速度［m/s2］",
        xaxis=dict(
            showline=False,
            zeroline=False,
            gridcolor="lightgray",
            tickfont=dict(size=style_params.get("tick_fontsize", 9))
        ),
        yaxis=dict(
            showline=False,
            zeroline=False,
            gridcolor="lightgray",
            range=[0, 6],
            tickfont=dict(size=style_params.get("tick_fontsize", 9))
        )
    )
    fig.update_xaxes(
        tickformat="%m/%d"
    )

    return fig, stats, status


def render_graph_with_control(df: pd.DataFrame, cfg, style_params):
    """共通のグラフ描画処理"""

    if cfg["type"] == "exhaust":
        threshold_range = THRESHOLD_RANGE_exhaust
    elif cfg["type"] == "cooling":
        threshold_range = THRESHOLD_RANGE_cooling
    else:
        threshold_range = None

    # Plotly グラフ生成
    fig, stats, status = make_graph_plotly(
        df,
        cfg['start'], cfg['end'],
        cfg['column_index'], cfg['label'],
        style_params=style_params,
        threshold=THRESHOLD_VALUE,
        threshold_range=threshold_range,
        slope_threshold=THRESHOLD_SLOPE
    )

    if fig is not None:
        st.session_state.last_fig = fig
        st.session_state.last_stats = stats
        st.session_state.last_status = status

        # パトライト制御
        if status == "threshold":
            activate_patlight_on(index=1)
        # elif status == "slope":
        #     activate_patlight_on(index=1)
        else:
            activate_patlight_off(index=1)

    # 新しいグラフが生成できなくても、前回のグラフを表示
    if "last_fig" in st.session_state:
        st.plotly_chart(st.session_state.last_fig, use_container_width=True)
        return True

    return False

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

def judge_status(y_data: pd.Series,
                 slope: float,
                 threshold: float = None,
                 threshold_range: tuple = None,
                 slope_threshold: float = None) -> str:
    """
    データ系列と傾きから状態を判定する関数

    Parameters
    ----------
    y_data : pd.Series
        計測値
    slope : float
        回帰直線の傾き (/日)
    threshold : float, optional
        単一閾値（これを超えたら異常）
    threshold_range : tuple, optional
        (low, high) の範囲。範囲外なら異常
    slope_threshold : float, optional
        傾きの閾値。これを超えたら異常

    Returns
    -------
    status : str
        "normal" | "threshold" | "slope"
    """

    # 範囲指定がある場合
    if threshold_range is not None:
        low, high = threshold_range
        if (y_data < low).any() or (y_data > high).any():
            return "threshold"

    # 単一閾値
    if threshold is not None and (y_data > threshold).any():
        return "threshold"

    # 傾き判定
    if slope_threshold is not None and slope > slope_threshold:
        return "slope"

    return "normal"