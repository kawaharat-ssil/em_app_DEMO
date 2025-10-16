"""
FastAPIのインストール
① 「venvy」という名前の仮想環境を新しく作成する処理
    > python -m venv venvy
    - -m venv
        → Python標準ライブラリの venvモジュール を実行する。
        → venvモジュールは「仮想環境を作るための仕組み」。
    - venvy
        → 作成する仮想環境のディレクトリ名。
        → 実行した場所に venvy/ フォルダが作られ、その中に独立したPython実行環境が展開される。
② プログラムが保存されているpathに移動する。
    > cd C:\Users\kawah\PycharmProjects\setubikanri_DEMO_fastAPI_Ver2.0
③仮想環境を有効化する。
    > venv\Scripts\activate
④fastapi、uvicornをインストールする。（これらは venvy専用の環境 にインストールされる。）
    (venv) ～ > pip install fastapi uvicorn

FastAPIの起動
①仮想環境を有効化でない場合、有効化する。
    > venv\Scripts\activate

①ターミナルで以下を実行し、FastAPI を起動する。
    (venv) ～ > uvicorn api_server.main:app --reload
        - main → ファイル名（main.py）
        - app → FastAPIインスタンス名（app = FastAPI()）
        - --reload → ソースコード保存時に自動リロード

②  http://localhost:8000 でAPIが動作

streamlitの起動
② プログラムが保存されているpathに移動する。
    > cd  C:\Users\kawah\PycharmProjects\setubikanri_DEMO_fastAPI_Ver2.0
③仮想環境を有効化する。
    > venv\Scripts\activate
⑥　FastAPIとは別のターミナルで以下を実行し、streamlitを起動する。
    (venv) ～ > streamlit run frontend/frontend.py

monitor.py を起動
② プログラムが保存されているpathに移動する。
    > cd  C:\Users\kawah\PycharmProjects\setubikanri_DEMO_fastAPI_Ver2.0
③仮想環境を有効化する。
    > venv\Scripts\activate
⑥　新しいターミナルで以下を実行し、monitor.pyを起動する。
    (venv) ～ > python -m monitor.monitor


プログラム停止方法
①FastAPIを起動したターミナルで以下を実行し、FastAPI を停止する。
    (venv) ～ > Ctrl + C
②Streamlitを起動したターミナルで以下を実行し、FastAPI を停止する。
    (venv) ～ > Ctrl + C
"""