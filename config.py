from datetime import datetime

API_BASE = "http://127.0.0.1:8000"


# ==============================
# キー入力に対応する設定
# ==============================
key_config = {
    '1': {
        'start': datetime(2025, 2, 10, 10, 0),
        'end': datetime(2025, 3, 10, 10, 0),
        'column_index': 4,  # E列（[排気] cna-13 AR3D[m/s^2]）
        'label': '[排気] cna-13 AR3D[m/s^2]',
        'type': 'exhaust',
        'description': '粗びき時に正常範囲外の振動を計測。粗びき時の不適切な運転に対するアラームを発報します。',
        'threshold': 4.2,
        'range': (2.0, 4.2),
        'slope_threshold': 0.01
    },
    '2': {
        'start': datetime(2025, 4, 1, 0, 0),
        'end': datetime(2025, 5, 1, 0, 0),
        'column_index': 5,  # E列（[排気] cna-13 AR3D[m/s^2]）
        'label': '[冷却] cna-13 AR3D[m/s^2]',
        'type': 'cooling',  # 排気データ
        'description': '冷却時の計測値が徐々に上昇してきている。短期的にポンプ異常が発生する場合のアラームを発報します。',
        'threshold': 5.0,
        'range': (3.0, 5.0),
        'slope_threshold': 0.01
    },
    '3': {
        'start': datetime(2025, 6, 1, 0, 0),
        'end': datetime(2025, 7, 1, 0, 0),
        'column_index': 5,  # F列（[冷却] cna-13 AR3D[m/s^2]）
        'label': '[冷却] cna-13 AR3D[m/s^2]',
        'type': 'cooling',   # 冷却データ
        'description': '正常状態',
        'threshold': 5.0,
        'range': (3.0, 5.0),
        'slope_threshold': 0.01
    },
    '4': {
        'start': datetime(2025, 8, 1, 0, 0),
        'end': datetime(2025, 9, 1, 0, 0),
        'column_index': 4,  # E列（[排気] cna-13 AR3D[m/s^2]）
        'label': '[排気] cna-13 AR3D[m/s^2]',
        'type': 'exhaust',   # 排気データ
        'description': '2025年8月排気時',
        'threshold': 4.2,
        'range': (2.0, 4.2),
        'slope_threshold': 0.01
    },
    '5': {
        'start': datetime(2025, 8, 1, 0, 0),
        'end': datetime(2025, 9, 1, 0, 0),
        'column_index': 5,  # F列（[冷却] cna-13 AR3D[m/s^2]）
        'label': '[冷却] cna-13 AR3D[m/s^2]',
        'type': 'cooling',   # 冷却データ
        'description':'2025年8月冷却時',
        'threshold': 5.0,
        'range': (3.0, 5.0),
        'slope_threshold': 0.01
    }
}

# ==============================
# 閾値設定
# ==============================
# 閾値設定
THRESHOLD_VALUE = 4.2
THRESHOLD_RANGE_exhaust = (2.0, 4.2)
THRESHOLD_RANGE_cooling = (3.0, 5.0)
THRESHOLD_SLOPE = 0.01    # 単位（m/s2）/日　傾きの閾値

# ==============================
# パトライト制御設定
# ==============================
SERIAL_PORT = "COM3"       # 接続ポート（環境に合わせて変更）
BAUDRATE = 9600            # 通信速度
TIMEOUT = 1                # タイムアウト秒数

# ==============================
# グラフ関連設定
# ==============================
# グラフのデフォルトサイズ
DEFAULT_FIGSIZE = (10, 4)
MONTHLY_FIGSIZE = (10, 2)
TABLE_HEADER_COLOR = "#4CAF50"
PUMP_INFO_HEADER_COLOR = "#1f77b4"

# グラフ描画用のスタイル設定
STYLE_PARAMS_DEFAULT = {
    "title_fontsize": 25,
    "label_fontsize": 18,
    "tick_fontsize": 18,
    "legend_fontsize": 16,
    "legend_loc": "upper center",
    "legend_bbox": (0.5, -0.25),
    "legend_ncol": 3,
}

STYLE_PARAMS_MONTHLY = {
    "title_fontsize": 18,
    "label_fontsize": 15,
    "tick_fontsize": 15,
    "legend_fontsize": 16,
    "legend_loc": "upper center",
    "legend_bbox": (0.5, -0.37),
    "legend_ncol": 3,
}

STYLE_PARAMS_DEFAULT_matplotlib = {
    "title_fontsize": 12,
    "label_fontsize": 10,
    "tick_fontsize": 10,
    "legend_fontsize": 10,
    "legend_loc": "upper center",
    "legend_bbox": (0.5, -0.25),
    "legend_ncol": 3,
}

STYLE_PARAMS_MONTHLY_matplotlib = {
    "title_fontsize": 11,
    "label_fontsize": 9,
    "tick_fontsize": 9,
    "legend_fontsize": 9,
    "legend_loc": "upper center",
    "legend_bbox": (0.5, -0.37),
    "legend_ncol": 3,
}
