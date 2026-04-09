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
    st.title("🧗 g登攀計画管理 - ログイン")
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

# SecretsからスプレッドシートURLを取得
try:
    SPREADSHEET_URL = st.secrets["connections"]["gsheets"]["spreadsheet"]
except KeyError:
    st.error("Secretsの設定に 'spreadsheet' URLが見つかりません。")
    st.stop()

# Googleスプレッドシートへの接続
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    # ttl=0 でキャッシュを無効化し、常に最新データを取得
    data = conn.read(spreadsheet=SPREADSHEET_URL, ttl=0)
    return data.dropna(how="all")

df = get_data()

# サイドバー：ユーザー情報とログアウト
st.sidebar.write(f"👤 ログイン中: **{st.session_state['user_name']}** さん")
if st.sidebar.button("ログアウト"):
    st.session_state.update({'logged_in': False, 'user_name': ""})
    st.rerun()

st.title("🧗 登攀計画・入山管理")

# --- 5. 登録処理（サイドバー） ---
st.sidebar.markdown("---")
st.sidebar.header("📝 新規計画の登録")
with st.sidebar:
    area = st.text_input("山域・ルート名")
    start_date = st.date_input("入山日", date.today())
    end_date = st.date_input("下山予定日", date.today())

    if st.button("計画を登録"):
        if area and start_date <= end_date:
            new_row = pd.DataFrame([{
                "氏名": st.session_state['user_name'],
                "山域": area,
                "入山日": str(start_date),
                "下山予定日": str(end_date),
                "ステータス": "入山中"
            }])
            # 既存データと結合
            updated_df = pd.concat([df, new_row], ignore_index=True)
            # スプレッドシートを更新
            conn.update(spreadsheet=SPREADSHEET_URL, data=updated_df)
            st.success("登録完了！")
            st.rerun()
        elif start_date > end_date:
            st.error("下山予定日が入山日より前です")
        else:
            st.error("山域を入力してください")

# --- 6. 状況表示（メトリクス） ---
today_str = str(date.today())
in_mountain = df[df["ステータス"] == "入山中"] if not df.empty else pd.DataFrame()
overdue = in_mountain[in_mountain["下山予定日"] < today_str] if not in_mountain.empty else pd.DataFrame()

col1, col2 = st.columns(2)
col1.metric("現在入山中", f"{len(in_mountain)} 名")
col2.metric("下山遅延", f"{len(overdue)} 名", 
          delta=f"{len(overdue)}名" if not overdue.empty else None, 
          delta_color="inverse")

# --- 7. メイン表示エリア ---
tab1, tab2 = st.tabs(["📌 現在の入山状況", "📜 全履歴"])

with tab1:
    if not in_mountain.empty:
        # 遅延している行を赤くするスタイル
        def highlight_overdue(s):
            return ['background-color: #ffcccc' if s.下山予定日 < today_str else '' for _ in s]
        
        st.subheader("入山中リスト")
        st.dataframe(in_mountain.style.apply(highlight_overdue, axis=1), use_container_width=True)
        
        # 下山報告機能（ログインユーザー本人のデータのみ）
        my_plans = in_mountain[in_mountain["氏名"] == st.session_state['user_name']]
        if not my_plans.empty:
            st.markdown("---")
            st.subheader("✅ 下山報告")
            selected_idx = st.selectbox(
                "報告する計画を選択", 
                my_plans.index, 
                format_func=lambda x: f"{df.loc[x, '山域']} ({df.loc[x, '入山日']}〜)"
            )
            if st.button("無事下山しました"):
                df.at[selected_idx, "ステータス"] = "下山済み"
                conn.update(spreadsheet=SPREADSHEET_URL, data=df)
                st.balloons()
                st.success("下山報告を完了しました！")
                st.rerun()
    else:
        st.info("現在、入山中のメンバーはいません。")

with tab2:
    if not df.empty:
        st.subheader("全データ履歴")
        st.dataframe(df, use_container_width=True)
    else:
        st.write("履歴はありません。")
