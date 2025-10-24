import time
import requests
import pandas as pd
import json

from config import key_config, API_BASE
from common.utils import load_timeseries_data
from common.judge import judge_status, judge_slope_least_squares
from common.patlite_control import change_output,set_exhaust_led,set_cooling_led,set_alarm_led
from common.notify_email import notify_email
from threading import Event

stop_event = Event()
STATE_FILE = "monitor_control.txt"
last_notified = False


def main():
    filepath = r"C:\Users\kawah\PycharmProjects\setubikanri_DEMO_fastAPI_Ver2.0\V14_cna013_forSetubikanri_demo.xlsx"
    global last_notified

    while True:
        check_control_command()
        print(f"[monitor] stop_event.is_set(): {stop_event.is_set()}")

        if stop_event.is_set():
            print("[monitor] 停止中…")
            time.sleep(2)
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
            # print(f"[monitor] y_data count = {len(y_data)}")

            if len(y_data) == 0:
                print("[monitor] No valid data")
                continue

            # 傾き判定（最小二乗法）
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

            # 異常判定による警告LED制御（消灯保持対応）
            # --- LED制御 ---
            if status == "threshold" and not alarm_muted:
                set_alarm_led(True)
                if cfg.get("type") == "exhaust":
                    set_exhaust_led(True)
                    set_cooling_led(False)
                elif cfg.get("type") == "cooling":
                    set_exhaust_led(False)
                    set_cooling_led(True)

                if not last_notified:
                    notify_email(
                        to_addr="kawaharat@ssil.co.jp",
                        subject="🚨 警報通知",
                        body="パトライトが点灯しました。状況を確認してください。"
                    )
                    print("[monitor] 警報メール送信")
                    last_notified = True

            elif slope_alert:
                set_alarm_led(False)  # slope_alert の場合は警告LEDは使わない想定
                if cfg.get("type") == "exhaust":
                    set_exhaust_led(True)
                    set_cooling_led(False)
                elif cfg.get("type") == "cooling":
                    set_exhaust_led(False)
                    set_cooling_led(True)

            else:
                # --- 異常なしの場合は全消灯 ---
                set_alarm_led(False)
                set_exhaust_led(False)
                set_cooling_led(False)
                last_notified = False

            # 6. FastAPIに状態を送信
            try:
                resp = requests.post(f"{API_BASE}/set_status/{status}")
                print(f"[monitor] scenario={selected_key}, status={status}, api={resp.status_code}, col={col}")
            except Exception as e:
                print(f"[monitor] Failed to send status: {e}")

        except Exception as e:
            import traceback
            print(f"[monitor] Error: {e}")
            traceback.print_exc()

        time.sleep(2)


def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def check_control_command():
    try:
        state = load_state()


        # 監視状態
        if state.get("monitor") == "stopped":
            stop_event.set()
            for idx, active in state.get("leds", {}).items():
                change_output(int(idx), active)
        else:
            stop_event.clear()
            change_output(5, False)

        # 消灯保持モード
        if state.get("alarm_muted"):
            set_alarm_led(False)

    except FileNotFoundError:
        pass
    except json.JSONDecodeError as e:
        print(f"[monitor] JSON decode error: {e}")


def stop_monitor():
    print("stop_monitor")
    stop_event.set()


def start_monitor():
    print("start_monitor")
    stop_event.clear()


if __name__ == "__main__":
    main()