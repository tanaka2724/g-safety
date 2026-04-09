import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- 1. ユーザー定義 ---
USER_CREDENTIALS = {
    "yamada": "pass123",
    "sato": "mount456",
    "suzuki": "safety789",
    "a": "a"
}

# --- 2. セッション状態の初期化 ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user_name': ""})

# --- 3. ログイン画面 ---
if not st.session_state['logged_in']:
    st.title("g登攀計画管理")
    with st.form("login_form"):
        user_id = st.text_input("ユーザーID")
        password = st.text_input("パスワード", type="password")
        if st.form_submit_button("ログイン"):
            if USER_CREDENTIALS.get(user_id) == password:
                st.session_state.update({'logged_in': True, 'user_name': user_id})
                st.rerun()
            else:
                st.error("IDまたはパスワードが正しくありません")
    st.stop()

# --- 4. メイン画面（ログイン後） ---

# Googleスプレッドシートへの接続
# secrets.toml の [connections.gsheets] 設定を自動的に使用します
conn = st.connection("gsheets", type=GSheetsConnection)

# データの読み込み
def get_data():
    # 引数を空にすることで secrets.toml の spreadsheet URL を使用し、
    # かつサービスアカウント認証で読み込みます
    data = conn.read(ttl=0)
    return data.dropna(how="all")

df = get_data()

# サイドバー：ユーザー情報とログアウト
st.sidebar.markdown(f"### 👤 ログイン: **{st.session
