from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import pandas as pd
import numpy as np
import datetime

from common.utils import load_timeseries_data

app = FastAPI()

scenario = {"selected": "2"}
status = {"current": "normal"}

current_status = "normal"

# 状態を保持する変数（本番ではDBや状態管理に置き換え）
alarm_muted = False
class AlarmMutedRequest(BaseModel):
    alarm_muted: bool


# 既存のエンドポイント
@app.post("/set_scenario/{key}")
def set_scenario(key: str):
    scenario["selected"] = key
    return {"status": "ok", "selected": key}


@app.get("/get_period")
def get_period():
    return scenario


@app.post("/set_status/{status}")
def set_status(status: str):
    global current_status
    current_status = status
    return {"result": "ok"}


@app.get("/get_status")
def get_status():
    return {"status": current_status}


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

    # Timestamp や datetime.time を文字列に変換
    def safe_convert(x):
        if isinstance(x, (pd.Timestamp, pd.Timedelta)):
            return str(x)
        elif isinstance(x, (datetime.datetime, datetime.date, datetime.time)):
            return x.isoformat()
        else:
            return x

    df = df.applymap(safe_convert)

    # NaN を None に変換
    df = df.astype(object).where(pd.notnull(df), None)

    return df


@app.post("/set_alarm_muted")
def set_alarm_muted(req: AlarmMutedRequest):
    global alarm_muted
    alarm_muted = req.alarm_muted
    return {"alarm_muted": alarm_muted}

@app.get("/get_alarm_muted")
def get_alarm_muted():
    return {"alarm_muted": alarm_muted}


# FastAPI側
@app.post("/stop_monitor")
def stop_monitor():
    # ここでは monitor.stop_monitor() は効かない
    # 代わりに、monitor.py 側がこのAPIをポーリングする必要がある
    with open("monitor_control.txt", "w") as f:
        f.write("stop")
    return {"status": "stop command written"}


@app.post("/start_monitor")
def start_monitor():
    with open("monitor_control.txt", "w") as f:
        f.write("start")
    return {"status": "start command written"}

