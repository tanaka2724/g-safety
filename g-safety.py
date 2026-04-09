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
            # 既存データに結合
            updated_df = pd.concat([df, new_row], ignore_index=True)
            
            # スプレッドシートを更新（サービスアカウント経由で書き込み）
            conn.update(data=updated_df)
            
            st.success("登録しました！")
            st.rerun()
        elif start_date > end_date:
            st.error("下山予定日が入山日より前です")
        else:
            st.error("山域を入力してください")

# --- 6. 状況表示（メトリクス） ---
today_str = str(date.today())
in_mountain = df[df["ステータス"] == "入山中"] if not df.empty else pd.DataFrame()
overdue = in_mountain[in_mountain["下山予定日"] < today_str] if not in_mountain.empty else pd.DataFrame()

m1, m2 = st.columns(2)
m1.metric("現在入山中", f"{len(in_mountain)} 名")
m2.metric("下山遅延", f"{len(overdue)} 名", 
          delta=f"{len(overdue)}名" if not overdue.empty else None, 
          delta_color="inverse")

# --- 7. タブ表示 ---
tab1, tab2 = st.tabs(["📌 現在の入山状況", "📜 全履歴"])

with tab1:
    if not in_mountain.empty:
        # 遅延している行を赤くするスタイル
        def highlight_overdue(s):
            return ['background-color: #ffcccc' if s.下山予定日 < today_str else '' for _ in s]
        
        st.dataframe(in_mountain.style.apply(highlight_overdue, axis=1), use_container_width=True)
        
        # 下山報告機能
        my_active_plans = in_mountain[in_mountain["氏名"] == st.session_state['user_name']]
        if not my_active_plans.empty:
            st.markdown("---")
            st.subheader("✅ 下山報告")
            selected_plan_idx = st.selectbox(
                "報告する計画を選択", 
                my_active_plans.index, 
                format_func=lambda x: f"{df.loc[x, '山域']} ({df.loc[x, '入山日']}〜)"
            )
            if st.button("無事下山しました"):
                # ステータスを更新して書き込み
                df.at[selected_plan_idx, "ステータス"] = "下山済み"
                conn.update(data=df)
                st.balloons()
                st.success("下山報告を完了しました！")
                st.rerun()
    else:
        st.info("現在、入山中のメンバーはいません。")

with tab2:
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.write("履歴はありません。")
