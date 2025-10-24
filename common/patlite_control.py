import serial
import time
import streamlit as st
import config

# ==============================
# パトライト制御  PHC‑D08 制御関数を定義
# ==============================


def control_led_by_status(status: str, muted: bool):
    if "prev_status" not in st.session_state:
        st.session_state.prev_status = None

    prev_status = st.session_state.prev_status

    if status != prev_status:
        if status == "threshold" and not muted:
            set_alarm_led(True)
        else:
            set_alarm_led(False)

    st.session_state.prev_status = status


def get_switch_state() -> list[bool]:
    """
    PHC-D08 の現在の出力状態を取得する
    戻り値: 出力8点のON/OFFをboolリストで返す
    """
    try:
        with serial.Serial(
                port=config.SERIAL_PORT,
                baudrate=config.BAUDRATE,
                timeout=config.TIMEOUT
        ) as ser:
            ser.write(b'Hello\n')
            response = ser.readline().decode('utf-8').strip()
            print(response)

            # 状態取得コマンド（5バイト）
            command = bytearray([0x40, 0x3F, 0x3F, 0x47, 0x21])
            ser.write(command)

            data = bytearray(8)
            index = 0

            for _ in range(10):
                time.sleep(0.2)
                buf = ser.read(8 - index)
                data[index:index + len(buf)] = buf
                index += len(buf)

                if index == 1 and data[0] == 0x15:
                    print("⚠️ 通信エラー（NAK受信）")
                    return [False] * 8
                elif index >= 8:
                    break

            # ON/OFF判定（0x31 = '1' → ON）
            state = [(b == 0x31) for b in data]
            print("✅ 端子状態:", state)
            return state

    except serial.SerialException as e:
        print(f"⚠️ シリアル通信エラー: {e}")
        return [False] * 8


# 異常判定用（既存）
def set_alarm_led(active: bool):
    change_output(index=1, active=active)  # 例: 出力1を異常LEDに割り当て


# 排気（加熱）用
def set_exhaust_led(active: bool):
    change_output(index=3, active=active)  # 例: 出力3を排気LEDに割り当て


# 冷却用
def set_cooling_led(active: bool):
    change_output(index=4, active=active)  # 例: 出力4を冷却LEDに割り当て


# 月報用
def set_report_led(active: bool):
    change_output(index=5, active=active)  # 例: 出力5を冷却LEDに割り当て


def change_output(index: int, active: bool) -> bool:
    """
    PHC-D08 の出力を制御する
    index: 出力番号 (0〜7)
    active: True=ON, False=OFF
    """
    try:
        with serial.Serial(                 # ser.close() は不要（with 文で自動的に閉じられる）
                port=config.SERIAL_PORT,
                baudrate=config.BAUDRATE,
                timeout=config.TIMEOUT
        ) as ser:
            ser.write(b'Hello\n')
            response = ser.readline().decode('utf-8').strip()
            print(response)

            command = bytearray(7)
            command[0] = 0x40
            command[1] = 0x3F
            command[2] = 0x3F
            command[3] = 0x31 if active else 0x30  # '1'=ON, '0'=OFF
            command[4] = 0x30
            command[5] = 0x30
            command[6] = 0x21

            # 出力ビット設定
            if index in [0, 1, 2, 3]:
                command[5] |= 1 << index
            elif index in [4, 5, 6, 7]:
                command[4] |= 1 << (index - 4)
            else:
                print(f"⚠️ 無効なindex: {index}")
                return False

            print("📤 送信コマンド:", [f"0x{b:02X}" for b in command])
            ser.write(command)

            # 応答待ち
            for _ in range(10):
                time.sleep(0.2)
                response = ser.read(1)
                print(f"受信バイト: {response}")
                if response == b'\x06':  # ACK
                    print(f"✅ パトライト index={index} {'ON' if active else 'OFF'} 成功")
                    return True

            print(f"⚠️ パトライト index={index} 応答なし")
            return False

    except serial.SerialException as e:
        print(f"⚠️ シリアル通信エラー: {e}")
        return False


def activate_patlight_on(index: int):
    """指定indexのパトライトを点灯"""
    before = get_switch_state()
    print(f"🚨 パトライト点灯 index={index}（前状態: {'ON' if before[index] else 'OFF'}）")

    success = change_output(index, True)
    after = get_switch_state()
    print(f"✅ index={index} 状態変化: {'ON' if after[index] else 'OFF'}（成功: {success})")


def activate_patlight_off(index: int):
    """指定indexのパトライトを消灯"""
    before = get_switch_state()
    print(f"　　パトライト消灯 index={index}（前状態: {'ON' if before[index] else 'OFF'}）")

    success = change_output(index, False)
    after = get_switch_state()
    print(f"✅ index={index} 状態変化: {'ON' if after[index] else 'OFF'}（成功: {success})")


# def set_alarm_led_test(on: bool):
#     # 実機制御コードに置き換え
#     if on:
#         print("🚨 LED ON")
#     else:
#         print("✅ LED OFF")
#
#
# def control_leds(is_monthly: bool):
#     if is_monthly:
#         set_alarm_led(False)
#         set_exhaust_led(False)
#         set_cooling_led(False)
#         set_report_led(True)
#     else:
#         set_report_led(False)
