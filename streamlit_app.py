import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import date, time, datetime

# -------------------------------
# ページ設定
# -------------------------------
st.set_page_config(page_title="スケジュール・家計管理アプリ", layout="wide")

# -------------------------------
# Supabase 接続
# -------------------------------
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# -------------------------------
# タイトル
# -------------------------------
st.title("スケジュール・家計管理アプリ")

# -------------------------------
# セッション初期化
# -------------------------------
if "schedules" not in st.session_state:
    st.session_state.schedules = pd.DataFrame()

if "transactions" not in st.session_state:
    st.session_state.transactions = pd.DataFrame()

# -------------------------------
# サイドバー
# -------------------------------
st.sidebar.title("メニュー")
page = st.sidebar.radio(
    "画面選択",
    ["スケジュール管理", "収入・支出管理", "ダッシュボード"]
)

# -------------------------------
# スケジュール自動削除（終了時刻を過ぎたもの）
# -------------------------------
now = datetime.now()

try:
    schedules = supabase.table("schedules").select("*").execute().data
    df_schedules = pd.DataFrame(schedules)

    if not df_schedules.empty:
        df_schedules["end_datetime"] = pd.to_datetime(
            df_schedules["date"] + " " + df_schedules["end_time"]
        )

        expired = df_schedules[df_schedules["end_datetime"] < now]

        for _, row in expired.iterrows():
            supabase.table("schedules").delete().eq("id", row["id"]).execute()

except Exception:
    pass

# -------------------------------
# スケジュール管理
# -------------------------------
if page == "スケジュール管理":
    st.header("スケジュール管理")

    with st.form("schedule_form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            s_date = st.date_input("日付", value=date.today())
        with col2:
            s_start = st.time_input("開始時刻", value=time(9, 0))
        with col3:
            s_end = st.time_input("終了時刻", value=time(10, 0))

        title = st.text_input("予定名")
        category = st.selectbox("分類", ["仕事", "勉強", "私用", "その他"])
        note = st.text_area("メモ")

        submitted = st.form_submit_button("予定を追加")

        if submitted:
            supabase.table("schedules").insert({
                "date": str(s_date),
                "start_time": str(s_start),
                "end_time": str(s_end),
                "title": title,
                "category": category,
                "note": note
            }).execute()
            st.success("予定を追加しました")

    data = supabase.table("schedules").select("*").execute().data
    st.dataframe(pd.DataFrame(data), use_container_width=True)

# -------------------------------
# 収入・支出管理
# -------------------------------
elif page == "収入・支出管理":
    st.header("収入・支出管理")

    with st.form("money_form"):
        col1, col2 = st.columns(2)

        with col1:
            t_date = st.date_input("日付", value=date.today(), key="money_date")
        with col2:
            amount = st.number_input("金額（円）", step=100)

        t_type = st.selectbox("種別", ["収入", "支出"])
        category = st.text_input("項目（例：食費、給料）")
        note = st.text_area("メモ", key="money_note")

        submitted = st.form_submit_button("登録")

        if submitted:
            supabase.table("transactions").insert({
                "date": str(t_date),
                "type": t_type,
                "category": category,
                "amount": amount,
                "note": note
            }).execute()
            st.success("登録しました")

    data = supabase.table("transactions").select("*").execute().data
    st.dataframe(pd.DataFrame(data), use_container_width=True)

# -------------------------------
# ダッシュボード
# -------------------------------
elif page == "ダッシュボード":
    st.header("ダッシュボード")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("収支合計")
        data = supabase.table("transactions").select("*").execute().data
        df = pd.DataFrame(data)

        if not df.empty:
            summary = df.groupby("type")["amount"].sum()
            st.bar_chart(summary)
        else:
            st.info("データがありません")

    with col2:
        st.subheader("本日の予定")
        today = str(date.today())
        data = supabase.table("schedules").select("*").eq("date", today).execute().data

        if data:
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        else:
            st.info("本日の予定はありません")
