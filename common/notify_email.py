import smtplib
from email.mime.text import MIMEText


def notify_email(to_addr, subject, body):
    from_addr = "kawaharat@ssil.co.jp"
    smtp_host = "air.secure.ne.jp"   # CPIのSMTPサーバー
    smtp_port = 465                # STARTTLSの場合
    smtp_user = "kawaharat@ssil.co.jp"
    smtp_pass = "tomoya2025-0620++A"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr

    with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)


if __name__ == "__main__":
    # テスト用の宛先（まずは自分のメールアドレスで確認）
    to_addr = "kawaharat@ssil.co.jp"
    subject = "テスト送信"
    body = "これは Python から送ったテストメールです。"

    notify_email(to_addr, subject, body)
    print("送信完了")

