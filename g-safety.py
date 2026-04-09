import streamlit as st
import pandas as pd
from datetime import date

# 1. ユーザー名とパスワードの定義（本来はデータベースで管理しますが、まずはコード内で）
USER_CREDENTIALS = {
    "yamada": "pass123",
    "sato": "mount456",
    "suzuki": "safety789"
}

# 2. ログイン状態の管理
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_name'] = ""

# --- ログイン画面 ---
if not st.session_state['logged_in']:
    st.title("🏔 山岳会 安全管理ログイン")
    user_id = st.text_input("ユーザーID")
    password = st.text_input("パスワード", type="password")

    if st.button("ログイン"):
        if user_id in USER_CREDENTIALS and USER_CREDENTIALS[user_id] == password:
            st.session_state['logged_in'] = True
            st.session_state['user_name'] = user_id
            st.rerun()
        else:
            st.error("IDまたはパスワードが違います")

# --- ログイン後のメイン画面 ---
else:
    st.sidebar.write(f"ログイン中: {st.session_state['user_name']} さん")
    if st.sidebar.button("ログアウト"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.title("🌲 山岳会 動静監視システム")

    # 3. 入力画面（ログインしている人の名前が自動で入る）
    st.sidebar.header("登山計画の登録")
    area = st.sidebar.text_input("山域")
    start_date = st.sidebar.date_input("入山日", date.today())
    end_date = st.sidebar.date_input("下山予定日", date.today())

    if st.sidebar.button("登録"):
        st.sidebar.success(f"{st.session_state['user_name']}さんの計画を受け付けました")

    # 表示用サンプル（本来は保存されたデータを出す）
    st.subheader("現在の入山状況")
    data = {
        "氏名": ["yamada", "sato"],
        "山域": ["北アルプス", "八ヶ岳"],
        "ステータス": ["入山中", "下山完了"]
    }
    st.table(pd.DataFrame(data))
