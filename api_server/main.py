import json
import datetime
import numpy as np
import pandas as pd
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from common.utils import load_timeseries_data

app = FastAPI()
STATE_FILE = "monitor_control.txt"


def load_state():
    """状態ファイルを読み込む。存在しない場合は初期状態を返す"""
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "monitor": "running",        # "running" or "stopped"
            "scenario": "1",             # 現在のシナリオ
            "leds": {"1": False, "3": False, "4": False, "5": False},
            "alarm_muted": False,        # 消灯保持
            "status": "normal"           # 最新の判定結果
        }


# --- 状態確認用 ---
@app.get("/get_state")
def get_state():
    return load_state()


def save_state(state: dict):
    """状態ファイルを保存する"""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# -------------------------
# --- データ取得API ---
# -------------------------
@app.get("/get_data")
def get_data():
    try:
        filepath = r"C:\Users\kawah\PycharmProjects\setubikanri_DEMO_fastAPI_Ver2.0\V14_cna013_forSetubikanri_demo.xlsx"
        df = load_timeseries_data(filepath)
        df = sanitize_dataframe_for_json(df)
        return JSONResponse(content=df.to_dict(orient="records"))
    except Exception as e:
        return JSONResponse(content={"error": str(e)})


def sanitize_dataframe_for_json(df: pd.DataFrame) -> pd.DataFrame:
    # inf を NaN に変換
    df = df.replace([np.inf, -np.inf], np.nan)

    # Timestamp や datetime を文字列に変換
    def safe_convert(x):
        if isinstance(x, (pd.Timestamp, pd.Timedelta)):
            return str(x)
        elif isinstance(x, (datetime.datetime, datetime.date, datetime.time)):
            return x.isoformat()
        else:
            return x

    df = df.applymap(safe_convert)
    df = df.astype(object).where(pd.notnull(df), None)
    return df


# -------------------------
# --- 監視制御API ---
# -------------------------
@app.post("/start_monitor")
def start_monitor():
    state = load_state()
    state["monitor"] = "running"
    save_state(state)
    return {"status": "monitor started", "state": state}


@app.post("/stop_monitor")
def stop_monitor():
    state = load_state()
    state["monitor"] = "stopped"
    save_state(state)
    return {"status": "monitor stopped", "state": state}


# -------------------------
# --- LED制御API ---
# -------------------------
@app.post("/set_led")
def set_led(index: int, active: bool):
    state = load_state()
    state["leds"][str(index)] = active
    save_state(state)
    return {"status": "ok", "state": state}


# -------------------------
# 消灯保持モード
# -------------------------
class AlarmMutedRequest(BaseModel):
    alarm_muted: bool


@app.post("/set_alarm_muted")
def set_alarm_muted(req: AlarmMutedRequest):
    state = load_state()
    state["alarm_muted"] = req.alarm_muted
    save_state(state)
    return {"alarm_muted": state["alarm_muted"]}


@app.get("/get_alarm_muted")
def get_alarm_muted():
    state = load_state()
    return {"alarm_muted": state.get("alarm_muted", False)}


# -------------------------
# モード切替
# -------------------------

@app.post("/set_monthly_mode")
def set_monthly_mode():
    state = load_state()
    state["monitor"] = "stopped"  # ← monitorを停止
    state["leds"] = {"1": True, "3": False, "4": False, "5": True}  # ← LED状態を固定
    state["alarm_muted"] = False  # ← 消灯保持はOFF
    save_state(state)
    return {"status": "monthly mode set", "state": state}


@app.post("/set_normal_mode")
def set_normal_mode():
    state = load_state()
    state["monitor"] = "running"
    state["leds"] = {"1": False, "3": False, "4": False, "5": False}  # ← LED5を確実にOFF
    state["alarm_muted"] = False
    save_state(state)
    return {"status": "normal mode set", "state": state}


# -------------------------
# シナリオ管理
# -------------------------
@app.post("/set_scenario/{key}")
def set_scenario(key: str):
    state = load_state()
    state["scenario"] = key
    save_state(state)
    return {"status": "ok", "selected": key}


@app.get("/get_period")
def get_period():
    state = load_state()
    return {"selected": state.get("scenario", "2")}


# -------------------------
# 判定ステータス管理
# -------------------------

@app.post("/set_status/{status}")
def set_status(status: str):
    state = load_state()
    state["status"] = status
    save_state(state)
    return {"result": "ok"}


@app.get("/get_status")
def get_status():
    state = load_state()
    return {"status": state.get("status", "normal")}
