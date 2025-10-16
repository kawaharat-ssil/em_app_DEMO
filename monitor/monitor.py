import time
import requests
import pandas as pd
from config import key_config, API_BASE
from common.utils import load_timeseries_data
from common.judge import judge_status, judge_slope_least_squares
from common.patlite_control import change_output,set_exhaust_led,set_cooling_led,set_alarm_led

from threading import Event

stop_event = Event()


def main():
    filepath = r"C:\Users\kawah\PycharmProjects\setubikanri_DEMO_fastAPI_Ver2.0\V14_cna013_forSetubikanri_demo.xlsx"

    while True:
        check_control_command()
        print(f"[monitor] stop_event.is_set(): {stop_event.is_set()}")

        if stop_event.is_set():
            print("[monitor] 停止中…")
            time.sleep(5)
            continue  # 監視処理をスキップ

        print("[monitor] 監視ループ実行中")

        try:
            # 1. FastAPIから現在のシナリオを取得
            res = requests.get(f"{API_BASE}/get_period")
            selected_key = res.json().get("selected", "2")
            cfg = key_config[selected_key]

            # 2. データ読み込み
            df = load_timeseries_data(filepath)
            df["Timestamp"] = pd.to_datetime(df["Timestamp"])
            col = cfg["label"]

            if col not in df.columns:
                print(f"[monitor] Column '{col}' not found")
                continue

            # 3. 判定対象のデータ抽出
            start = cfg["start"]
            end = cfg["end"]
            df_period = df[(df["Timestamp"] >= start) & (df["Timestamp"] <= end)].copy()
            y_data = df_period[col].dropna()

            print("[monitor] y_data max =", y_data.max())
            print(f"[monitor] y_data count = {len(y_data)}")

            if len(y_data) == 0:
                print("[monitor] No valid data")
                continue

            # 傾き判定（最小二乗法）
            # slope_alert = judge_slope_least_squares(y_data.tail(5), cfg.get("slope_threshold", 0.01))
            slope_alert = judge_slope_least_squares(y_data, cfg.get("slope_threshold", 0.01))

            # 総合判定
            status = judge_status(
                y_data=y_data,
                slope=0,  # 差分ベースは使わない場合は 0
                threshold=cfg.get("threshold"),
                threshold_range=cfg.get("range"),
                slope_alert=slope_alert
            )

            # 5. パトライト制御
            res_muted = requests.get(f"{API_BASE}/get_alarm_muted")
            alarm_muted = res_muted.json().get("alarm_muted", False)

            if cfg.get("type") == "exhaust":
                set_exhaust_led(True)
            elif cfg.get("type") == "cooling":
                set_cooling_led(True)

            # 異常判定による警告LED制御（消灯保持対応）
            if status == "threshold" and not alarm_muted:
                set_alarm_led(True)
            else:
                set_alarm_led(False)

            # 6. FastAPIに状態を送信
            resp = requests.post(f"{API_BASE}/set_status/{status}")
            print(f"[monitor] scenario={selected_key}, status={status}, api={resp.status_code}, col={col}")

        except Exception as e:
            import traceback
            print(f"[monitor] Error: {e}")
            traceback.print_exc()

        time.sleep(5)


def check_control_command():
    print("check_control_command")
    try:
        with open("monitor_control.txt", "r") as f:
            cmd = f.read().strip()
        if cmd == "stop":
            stop_event.set()
        elif cmd == "start":
            stop_event.clear()
    except FileNotFoundError:
        pass


def stop_monitor():
    print("stop_monitor")
    stop_event.set()


def start_monitor():
    print("start_monitor")
    stop_event.clear()


if __name__ == "__main__":
    main()