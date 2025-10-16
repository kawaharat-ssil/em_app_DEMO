import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import time
import requests
import pandas as pd

from common.graph_renderer import make_graph_plotly
from common.patlite_control import activate_patlight_on, activate_patlight_off, set_exhaust_led, set_cooling_led, \
    control_led_by_status, set_report_led, control_leds
from config import key_config,API_BASE, STYLE_PARAMS_MONTHLY
import threading
import monitor.monitor as monitor





st.set_page_config(page_title="振動デモ", layout="wide")
# st.title("振動データデモ表示")

# 画面切り替え
page = st.sidebar.radio("表示する画面を選択", ["月報", "シナリオ選択","グラフ表示"])
st.session_state["page"] = page
print(f"[page] {page}")
st.write("現在時刻:", time.strftime("%H:%M:%S"))

patlight_state = {"ch1": False, "ch2": False}

# def launch_monitor():
#     monitor.start_monitor()
#     threading.Thread(target=monitor.main, daemon=True).start()




def on_press(key):
    """キー入力で制御"""
    global patlight_state
    try:
        key_char = key.char
        if key_char == '9':
            activate_patlight_off(index=1)
            patlight_state["ch1"] = False
    except AttributeError:
        pass


def render_comment():
    """共通のコメント入力欄"""
    st.subheader("コメント入力")
    comment = st.text_area("コメントを入力してください")
    if comment:
        st.write("入力されたコメント:", comment)


# -------------------------------
# 各画面の処理
# -------------------------------
if page == "月報":
    IS_MONTHLY_PAGE = st.session_state.get("page") == "月報"
    if IS_MONTHLY_PAGE:
        control_leds(True)
        requests.post(f"{API_BASE}/stop_monitor")
    else:
        control_leds(False)
        requests.post(f"{API_BASE}/start_monitor")

    st.subheader("月報")

    # FastAPIからデータ取得
    res_data = requests.get(f"{API_BASE}/get_data")
    data_json = res_data.json()
    df = pd.DataFrame(data_json)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])

    # --- ポンプ情報 ---
    st.markdown("### ポンプ情報")
    pump_info = {
        "設置場所": "第3工場",
        "設備名": "モーター直結型ポンプ_V14",
        "メーカー": "ulvac",
        "型番": "VD-40c",
        "運用開始日": "2020-04-01"
    }

    # --- グラフ描画 ---
    stats_list = []

    # 熱処理開始時（排気）
    st.markdown("#### 熱処理開始時（ポンプが排気処理中）")
    fig_exhaust, stats_exhaust, status_exhaust = make_graph_plotly(
        df,
        key_config["4"]["start"], key_config["4"]["end"],
        key_config["4"]["column_index"], key_config["4"]["label"],
        style_params=STYLE_PARAMS_MONTHLY,
        threshold=key_config["4"].get("threshold"),
        threshold_range=key_config["4"].get("range"),
        slope_threshold=key_config["4"].get("slope_threshold")
    )
    if fig_exhaust and stats_exhaust:
        st.plotly_chart(fig_exhaust, use_container_width=True)
        stats_list.append(stats_exhaust)
        if "予測残り日数（日）" in stats_exhaust:
            st.success(f"予測: {stats_exhaust['予測残り日数（日）']} 日後に閾値超過")

    # 熱処理終了後（冷却）
    st.markdown("#### 熱処理終了後（冷却時・ポンプ切離し）")
    fig_cooling, stats_cooling, status_cooling = make_graph_plotly(
        df,
        key_config["5"]["start"], key_config["5"]["end"],
        key_config["5"]["column_index"], key_config["5"]["label"],
        style_params=STYLE_PARAMS_MONTHLY,
        threshold=key_config["5"].get("threshold"),
        threshold_range=key_config["5"].get("range"),
        slope_threshold=key_config["5"].get("slope_threshold")
    )
    if fig_cooling and stats_cooling:
        st.plotly_chart(fig_cooling, use_container_width=True)
        stats_list.append(stats_cooling)
        if "予測残り日数（日）" in stats_cooling:
            st.success(f"予測: {stats_cooling['予測残り日数（日）']} 日後に閾値超過")

    # --- 統計まとめ ---
    if stats_list:
        st.markdown("### 運転特性")
        for stats in stats_list:
            st.markdown(f"#### {stats['ラベル']}")
            df_stats = pd.DataFrame(stats.items(), columns=["項目", "値"]).set_index("項目")
            # 数値は丸めて文字列化
            df_stats["値"] = df_stats["値"].apply(
                lambda x: str(round(x, 1)) if isinstance(x, (int, float)) else str(x)
            )
            st.table(df_stats)

    # --- 設備実績入力 ---
    st.markdown("### 設備実績入力")
    col1, col2, col3 = st.columns(3)
    with col1:
        active = st.number_input("稼働日数［日］", min_value=0, value=20)
    with col2:
        monthly_hours = st.number_input("月次稼働時間［h］", min_value=0, value=1)
    with col3:
        avg_daily_hours = st.number_input("平均日時稼働時間［h］", min_value=0, value=0)

    inspections = st.number_input("点検実施数", min_value=0, value=3)
    failures = st.number_input("故障件数", min_value=0, value=2)
    repairs = st.number_input("修理完了件数", min_value=0, value=1)

    # --- コメント ---
    comment = st.text_area("コメント（特記事項や所感）")
    if comment:
        st.write("コメント:", comment)

    set_cooling_led(False)
    set_exhaust_led(False)
    set_report_led(True)


elif page == "シナリオ選択":
    IS_MONTHLY_PAGE = st.session_state.get("page") == "月報"
    if IS_MONTHLY_PAGE:
        control_leds(True)
        requests.post(f"{API_BASE}/stop_monitor")
    else:
        control_leds(False)
        requests.post(f"{API_BASE}/start_monitor")

    st.subheader("読み込みシナリオを選択")
    st.markdown("いずれかのシナリオを選択すると、対応する振動値を計測した状態をシミュレートします。")
    # LED制御
    res_muted = requests.get(f"{API_BASE}/get_alarm_muted")
    alarm_muted = res_muted.json().get("alarm_muted", False)

    col1, col2 = st.columns([1, 3])  # 左右の幅比率を調整

    with col1:
        st.write(f"消灯保持モード: {'ON' if alarm_muted else 'OFF'}")

    with col2:
        if alarm_muted:
            if st.button("消灯保持解除"):
                requests.post(f"{API_BASE}/set_alarm_muted", json={"alarm_muted": False})
                st.rerun()  # ← 強制リフレッシュ
        else:
            if st.button("パトライト消灯"):
                requests.post(f"{API_BASE}/set_alarm_muted", json={"alarm_muted": True})
                st.rerun()  # ← 強制リフレッシュ

    for key in key_config:
        if int(key) in [1, 2, 3]:
            cfg = key_config[key]
            with st.expander(f"シナリオ[{key}]：{cfg['label']}"):
                st.markdown(f"**期間**：{cfg['start'].strftime('%Y-%m-%d %H:%M')} ～ {cfg['end'].strftime('%Y-%m-%d %H:%M')}")
                st.markdown(f"**説明**：{cfg['description']}")

                if st.button(f"このシナリオ [{key}] を選択", key=f"scenario_{key}"):
                    try:
                        requests.post(f"{API_BASE}/set_alarm_muted", json={"alarm_muted": False})
                        res = requests.post(f"http://localhost:8000/set_scenario/{key}")
                        if res.status_code == 200:
                            # 成功メッセージを session_state に保存
                            st.session_state["last_message"] = f"期間 {key} を送信しました"

                            if cfg["type"] == "exhaust":
                                set_exhaust_led(True)
                                set_cooling_led(False)
                            elif cfg["type"] == "cooling":
                                set_exhaust_led(False)
                                set_cooling_led(True)

                            st.rerun()  # ← ここでリフレッシュ
                        else:
                            st.error("送信に失敗しました")
                    except Exception as e:
                        st.error(f"FastAPIとの通信エラー: {e}")

    # --- ページ再描画時にメッセージを表示 ---
    if "last_message" in st.session_state:
        st.success(st.session_state["last_message"])


elif page == "グラフ表示":  # ← 遠隔制御モード
    if "page" not in st.session_state:
        st.session_state["page"] = "ダッシュボード"

    IS_MONTHLY_PAGE = st.session_state.get("page") == "月報"
    if IS_MONTHLY_PAGE:
        control_leds(True)
        requests.post(f"{API_BASE}/stop_monitor")
    else:
        control_leds(False)
        requests.post(f"{API_BASE}/start_monitor")

    print(f"[page] {page}")
    st.subheader("グラフ表示")
    st_autorefresh(interval=10000, limit=None, key="refresh")

    if "alarm_muted_key" not in st.session_state:
        st.session_state.alarm_muted_key = None
    if "alarm_muted" not in st.session_state:
        st.session_state.alarm_muted = False

    try:
        # 現在のシナリオを取得
        res = requests.get(f"{API_BASE}/get_period")
        selected_key = res.json().get("selected", "2")
        cfg = key_config[selected_key]

        # FastAPIからデータ取得
        res_data = requests.get(f"{API_BASE}/get_data")
        data_json = res_data.json()
        df = pd.DataFrame(data_json)
        df["Timestamp"] = pd.to_datetime(df["Timestamp"])

        msg_area = st.empty()
        # FastAPIから判定結果を取得
        status = requests.get(f"{API_BASE}/get_status").json().get("status", "normal")
        print(f"[monitor] POST status to {API_BASE}/set_status/{status}")
        print(f"[frontend] scenario={selected_key}, status={status}")





        # グラフ描画
        fig, stats, status_local = make_graph_plotly(
            df,
            cfg["start"], cfg["end"],
            cfg["column_index"], cfg["label"],
            style_params=STYLE_PARAMS_MONTHLY,
            threshold=cfg.get("threshold"),
            threshold_range=cfg.get("range"),
            slope_threshold=cfg.get("slope_threshold")
        )
        days_left = stats.get("予測残り日数（日）")
        EXHAUST_ALERT_HTML = f"""
        <div style="background-color:#cc0000; padding:15px; border-radius:5px; width:100%; height:400px; margin:auto;
                                            display:flex;
                                            flex-direction:column;   /* 縦方向に並べる */
                                            align-items:center;      /* 横中央 */
                                            justify-content:center;  /* 縦中央 */
                                            text-align:center;">
           <p style="font-size:84px; font-weight:bold; margin:0; color:white; text-align:center;">🚨 不適切運転警報 🚨</p>
           <p style="font-size:32px; color:white; margin:0; text-align:center;">ポンプの過負荷が発生しています。</p>
           <p style="font-size:32px; color:white; margin:0; text-align:center;">運転条件、炉の異常等を点検してください。</p>
        </div>
        """

        COOLING_ALERT_HTML = f"""
        <div style="background-color:#f8d7da; padding:15px; border-radius:5px; width:100%; height:250px; margin:auto;
                    display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center;">
            <p style="font-size:32px; font-weight:bold; margin:0; color:red;">🚨 不適切運転警報！</p>
            <p style="font-size:20px; margin:0;">ポンプの異常が発生しています。</p>
            <p style="font-size:20px; margin:0;">できるだけ早く点検してください。</p>
        </div>
        """

        SLOPE_ALERT_HTML = f"""
         <div style="background-color:#fff3cd; padding:15px; border-radius:5px; width:100%; height:226px; margin:auto;
                display:flex;
                flex-direction:column;
                align-items:center;
                justify-content:center;
                text-align:center;
                border:1px solid #ffeeba;">
        <p style="font-size:32px; font-weight:bold; margin:0; color:#856404;">⚠️ 振動警報️ ⚠️</p>
        <p style="font-size:26px; margin:0; color:#856404;">振動が増加傾向にあります。</p>
        <p style="font-size:26px; margin:0; color:#856404;text-align:center;">{days_left}日程で基準値を超える見込みです。数日中に点検してください。</p>
        </div>
        """
        # 警告メッセージ表示
        if status == "threshold":
            if cfg["type"] == "exhaust":
                msg_area.markdown(EXHAUST_ALERT_HTML, unsafe_allow_html=True)
            elif cfg["type"] == "cooling":
                msg_area.markdown(COOLING_ALERT_HTML, unsafe_allow_html=True)
        elif status == "slope":
            msg_area.markdown(SLOPE_ALERT_HTML, unsafe_allow_html=True)
        else:
            msg_area.info("異常なし")

        # if stats:
        #     if "予測残り日数（日）" in stats:
        #         st.success(f"予測: {stats['予測残り日数（日）']} 日後に閾値超過")

        if fig:
            st.plotly_chart(fig, use_container_width=True)
            st.write("判定結果:", status_local)
            if stats:
                # stats を DataFrame に変換
                stats_df = pd.DataFrame([stats])

                # object型の列を float に変換できるものは変換
                for col in stats_df.columns:
                    if stats_df[col].dtype == object:
                        try:
                            stats_df[col] = stats_df[col].astype(float)
                        except ValueError:
                            pass  # 変換できない列はそのまま

                st.dataframe(stats_df)

        # コメント欄
        render_comment()

        # グラフ切り替え時の消灯保持リセット
        if st.session_state.alarm_muted_key is None:
            st.session_state.alarm_muted_key = selected_key
        elif st.session_state.alarm_muted_key != selected_key:
            st.session_state.alarm_muted = False
            st.session_state.alarm_muted_key = selected_key

        # LED制御（必要なら）
        res_muted = requests.get(f"{API_BASE}/get_alarm_muted")
        alarm_muted = res_muted.json().get("alarm_muted", False)

        col1, col2 = st.columns([1, 3])  # 左右の幅比率を調整

        with col1:
            st.write(f"消灯保持モード: {'ON' if alarm_muted else 'OFF'}")

        with col2:
            if alarm_muted:
                if st.button("消灯保持解除"):
                    requests.post(f"{API_BASE}/set_alarm_muted", json={"alarm_muted": False})
                    st.rerun()  # ← 強制リフレッシュ
            else:
                if st.button("パトライト消灯"):
                    requests.post(f"{API_BASE}/set_alarm_muted", json={"alarm_muted": True})
                    st.rerun()  # ← 強制リフレッシュ

    except Exception as e:
        st.error(f"FastAPIとの通信エラー: {e}")

