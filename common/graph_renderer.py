
import matplotlib
from scipy.stats import linregress
import pandas as pd
import plotly.graph_objects as go
from common.judge import judge_status, judge_slope_least_squares
from common.stats_utils import calc_stats

matplotlib.rcParams['font.family'] = 'Yu Gothic'


def make_graph_plotly(df: pd.DataFrame, start, end, col_index: int, label: str,
                      style_params: dict,
                      threshold: float = None,
                      threshold_range: tuple = None,
                      slope_threshold: float = None):
    # 安全な初期化
    threshold_low, threshold_high = None, None
    if threshold_range is not None:
        threshold_low, threshold_high = threshold_range

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
    slope, intercept, r_value, p_value, std_err = linregress(x_elapsed_days, y_data)
    print(slope, intercept, r_value, p_value, std_err)

    # - slope（傾き）
    # - intercept（切片）
    # - r_value（相関係数）
    # - p_value（傾きが統計的に有意かどうかの検定結果）
    # - std_err（傾きの標準誤差）

    days_remaining = None

    if slope > 0:  # 上昇傾向の場合
        if threshold_range is not None:
            _, high = threshold_range
            x_cross = (high - intercept) / slope
        elif threshold is not None:
            x_cross = (threshold - intercept) / slope
        else:
            x_cross = None

        if x_cross is not None:
            x_now = x_elapsed_days.iloc[-1]
            days_remaining = x_cross - x_now
            if days_remaining < 0:
                days_remaining = 0  # すでに超えている

    # 統計値計算
    threshold_for_stats = threshold_range[1] if threshold_range is not None else threshold
    stats = calc_stats(y_data, label, slope=slope, threshold=threshold_for_stats)

    slope_alert = judge_slope_least_squares(
        y_data,
        slope_threshold if slope_threshold is not None else 0.01
    )

    stats["傾き"] = slope
    stats["切片"] = intercept
    if days_remaining is not None:
        stats["予測残り日数（日）"] = round(days_remaining, 1)

    # 判定ロジック
    status = judge_status(
        y_data=y_data,
        slope=slope,
        threshold=threshold,
        threshold_range=threshold_range,
        slope_alert=slope_alert
    )

    if threshold_range is not None:
        low, high = threshold_range
        threshold_high = high
        threshold_low = low

    if threshold_low is not None and threshold_high is not None:
        mask = (y_data < threshold_low) | (y_data > threshold_high)
    else:
        mask = pd.Series(False, index=y_data.index)

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