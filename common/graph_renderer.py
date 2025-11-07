import numpy as np
import matplotlib
from scipy.stats import linregress
import pandas as pd
import plotly.graph_objects as go
from common.judge import judge_status, judge_slope_least_squares
from common.stats_utils import calc_stats

matplotlib.rcParams['font.family'] = 'Yu Gothic'


def make_graph_plotly(
    df: pd.DataFrame, start, end, col_index: int, label: str,
    style_params: dict,
    threshold: float = None,
    threshold_range: tuple = None,
    slope_threshold: float = None,
    use_sigma_band: bool = True,        # ★ 追加: ±kσ帯を使うか
    sigma_mult: float = 2.0,            # ★ 追加: k（既定=2）
    robust: bool = False                # ★ 追加: 外れ値に強い推定（MAD）を使うか
):
    # データ抽出
    data = df[(df['Timestamp'] >= start) & (df['Timestamp'] <= end)].copy()
    subset = data[['Timestamp', data.columns[col_index]]].dropna()
    if len(subset) < 2:
        return None, None, None

    x_time = subset['Timestamp']
    y_data = subset.iloc[:, 1]

    # 経過時間（日単位）
    x_elapsed_days = (x_time - x_time.iloc[0]).dt.total_seconds() / (24 * 60 * 60)

    # 回帰（傾きは /日）
    slope, intercept, r_value, p_value, std_err = linregress(x_elapsed_days, y_data)
    print(slope, intercept, r_value, p_value, std_err)

    # ---- 正常範囲（帯）の決定：平均±kσ（既定は±2σ） ----
    # robust=True の場合は MAD から近似σ=1.4826*MAD を使用（外れ値耐性）
    if use_sigma_band:
        mu = float(y_data.mean())
        if robust:
            med = float(y_data.median())
            mad = float((y_data - med).abs().median())
            sigma = 1.4826 * mad
        else:
            # pandas std は既定 ddof=1（標本標準偏差）
            sigma = float(y_data.std(ddof=1))

        # σ が NaN や 0 に近い場合のガード
        if not np.isfinite(sigma) or sigma < 1e-12:
            band_low, band_high = mu - 1e-6, mu + 1e-6  # 最小帯幅を確保
            sigma_info = "σ≈0（最小帯幅）"
        else:
            band_low = mu - sigma_mult * sigma
            band_high = mu + sigma_mult * sigma
            sigma_info = f"μ={mu:.3f}, σ={sigma:.3f}, ±{sigma_mult}σ"
        # この後のロジックは band_low/band_high を既定として扱う
        tr_low, tr_high = band_low, band_high
    else:
        # 既存の threshold / threshold_range を使う従来動作
        if threshold_range is not None:
            tr_low, tr_high = threshold_range
        elif threshold is not None:
            tr_low, tr_high = None, threshold  # 上限のみのケース
        else:
            tr_low, tr_high = None, None
        sigma_info = None

    # 交差予測（残り日数）
    days_remaining = None
    if slope != 0:
        # 傾きの符号で見る閾を切替：上昇なら上限、下降なら下限
        x_cross = None
        if use_sigma_band and (tr_low is not None and tr_high is not None):
            target = tr_high if slope > 0 else tr_low
            x_cross = (target - intercept) / slope
        elif threshold is not None and slope > 0:
            x_cross = (threshold - intercept) / slope

        if x_cross is not None and np.isfinite(x_cross):
            x_now = x_elapsed_days.iloc[-1]
            days_remaining = max(0.0, float(x_cross - x_now))

    # 統計値（レポート用）
    # stats の threshold は「上限側」を渡す仕様に合わせる
    threshold_for_stats = None
    if use_sigma_band and (tr_low is not None and tr_high is not None):
        threshold_for_stats = tr_high
    elif threshold is not None:
        threshold_for_stats = threshold

    stats = calc_stats(y_data, label, slope=slope, threshold=threshold_for_stats)
    stats["傾き"] = slope
    stats["切片"] = intercept
    if days_remaining is not None:
        stats["予測残り日数（日）"] = round(days_remaining, 1)
    if use_sigma_band and sigma_info is not None:
        stats["正常範囲(±σ)"] = sigma_info
        stats["下限(帯)"] = tr_low
        stats["上限(帯)"] = tr_high

    # 傾きの判定
    slope_alert = judge_slope_least_squares(
        y_data,
        slope_threshold if slope_threshold is not None else 0.01
    )

    # 総合判定
    status = judge_status(
        y_data=y_data,
        slope=slope,
        threshold=threshold if not use_sigma_band else None,
        threshold_range=(tr_low, tr_high) if (tr_low is not None and tr_high is not None) else None,
        slope_alert=slope_alert
    )

    # 異常値マスク
    if tr_low is not None and tr_high is not None:
        mask = (y_data < tr_low) | (y_data > tr_high)
    elif tr_high is not None:
        mask = (y_data > tr_high)
    elif tr_low is not None:
        mask = (y_data < tr_low)
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

    # 正常範囲の帯（±kσ もしくは従来の threshold_range）
    if (tr_low is not None) and (tr_high is not None):
        fig.add_hrect(
            y0=tr_low, y1=tr_high,
            fillcolor="green", opacity=0.2,
            line_width=0
        )
        legend_name = (
            f"±{sigma_mult}σ帯 {tr_low:.3f}–{tr_high:.3f}"
            if use_sigma_band else f"正常範囲 {tr_low}–{tr_high}"
        )
        # 凡例用ダミー
        fig.add_trace(
            go.Scatter(
                x=[None], y=[None],
                mode="lines",
                line=dict(color="green", width=15),
                name=legend_name
            )
        )

    # レイアウト
    fig.update_layout(
        plot_bgcolor="rgb(245,247,249)",
        title=dict(
            text=f"{label}<br>{start} ～ {end}",
            x=0.5, xanchor="center",
            font=dict(size=style_params.get("title_fontsize", 12))
        ),
        legend=dict(
            orientation="h",
            yanchor="top", y=-0.2,
            xanchor="center", x=0.5,
            font=dict(size=style_params.get("legend_fontsize", 10))
        ),
        title_font=dict(size=style_params.get("title_fontsize", 12)),
        yaxis_title="加速度［m/s²］",
        xaxis=dict(
            showline=False, zeroline=False,
            gridcolor="lightgray",
            tickfont=dict(size=style_params.get("tick_fontsize", 9))
        ),
        yaxis=dict(
            showline=False, zeroline=False,
            gridcolor="lightgray",
            range=[0, 6],
            tickfont=dict(size=style_params.get("tick_fontsize", 9))
        )
    )
    fig.update_xaxes(tickformat="%m/%d")

    return fig, stats, status