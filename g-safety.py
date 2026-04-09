import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- 1. ユーザー定義（ログイン情報） ---
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
            uid = user_id.strip()
            if USER_CREDENTIALS.get(uid) == password:
                st.session_state.update({'logged_in': True, 'user_name': uid})
                st.rerun()
            else:
                st.error("IDまたはパスワードが正しくありません")
    st.stop()

# --- 4. メイン画面（ログイン後） ---

# 接続の確立
# Streamlit CloudのSecretsにある [connections.gsheets] セクションを自動参照します
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    # ttl=0 で常に最新のスプレッドシート情報を取得
    return conn.read(ttl=0)

try:
    df = get_data()
except Exception as e:
    st.error("スプレッドシートへの接続に失敗しました。Secretsの設定を確認してください。")
    st.info("ヒント: private_key の改行が正しく設定されていない可能性があります。")
    st.stop()

# サイドバー：ユーザー情報とログアウト
st.sidebar.markdown(f"### 👤 ログイン: **{st.session_state['user_name']}**")
if st.sidebar.button("ログアウト"):
    st.session_state.update({'logged_in': False, 'user_name': ""})
    st.rerun()

st.title("🧗 登攀計画・入山管理")

# --- 5. 登録処理 ---
with st.sidebar.expander("📝 新規計画を登録する", expanded=True):
    area = st.text_input("山域・ルート名")
    start_date = st.date_input("入山日", date.today())
    end_date = st.date_input("下山予定日", date.today())
    
    if st.button("計画を送信"):
        if area and start_date <= end_date:
            new_row = pd.DataFrame([{
                "氏名": st.session_state['user_name'],
                "山域": area,
                "入山日": str(start_date),
                "下山予定日": str(end_date),
                "ステータス": "入山中"
            }])
            # 既存データに新しい行を結合
            updated_df = pd.concat([df, new_row], ignore_index=True)
            
            # スプレッドシートを更新
            conn.update(data=updated_df)
            
            st.success("登録しました！")
            st.rerun()
        elif start_date > end_date:
            st.error("下山予定日が入山日より前です")
        else:
            st.error("山域を入力してください")

# --- 6. 状況表示（メトリクス） ---
today_str = str(date.today())
if df.empty:
    in_mountain = pd.DataFrame()
    overdue = pd.DataFrame()
else:
    in_mountain = df[df["ステータス"] == "入山中"]
    overdue = in_mountain[in_mountain["下山予定日"] < today_str]

m1, m2 = st.columns(2)
m1.metric("現在入山中",
