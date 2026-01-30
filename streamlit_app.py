import streamlit as st
import pandas as pd
from datetime import date, time, datetime
from supabase import create_client
import calendar

# -------------------------------
# ページ設定
# -------------------------------
st.set_page_config(
    page_title="スケジュール＆家計管理アプリ",
    layout="wide"
)

# -------------------------------
# Supabase 接続
# -------------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------------
# サイドバー
# -------------------------------
st.sidebar.title("メニュー")
page = st.sidebar.radio(
    "ページ選択",
    ["予定管理", "支出管理", "収入管理", "カレンダー", "ダッシュボード"]
)

# ======================================================
# 過去の予定を自動削除
# ======================================================
now = datetime.now()
schedules_data = supabase.table("schedules").select("*").execute().data

for s in schedules_data:
    end_dt = datetime.combine(
        datetime.fromisoformat(s["date"]).date(),
        datetime.fromisoformat(f"2000-01-01T{s['end_time']}").time()
    )
    if end_dt < now:
        supabase.table("schedules").delete().eq("id", s["id"]).execute()

# ======================================================
# 予定管理ページ
# ======================================================
if page == "予定管理":
    st.title("予定管理")

    with st.form("schedule_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            s_date = st.date_input("日付", value=date.today())
        with col2:
            s_start = st.time_input("開始時刻", value=time(9, 0))
        with col3:
            s_end = st.time_input("終了時刻", value=time(10, 0))

        title = st.text_input("予定名")
        category = st.selectbox("カテゴリ", ["仕事", "勉強", "プライベート", "その他"])
        note = st.text_area("メモ")
        submitted = st.form_submit_button("予定を追加")

        if submitted:
            supabase.table("schedules").insert({
                "date": s_date.isoformat(),
                "start_time": s_start.isoformat(),
                "end_time": s_end.isoformat(),
                "title": title,
                "category": category,
                "note": note
            }).execute()
            st.success("予定を追加しました")

    data = supabase.table("schedules").select("*").execute().data
    if data:
        df = pd.DataFrame(data)
        df.rename(columns={
            "date": "日付",
            "start_time": "開始",
            "end_time": "終了",
            "title": "予定名",
            "category": "カテゴリ",
            "note": "メモ"
        }, inplace=True)
        st.dataframe(df, use_container_width=True)

# ======================================================
# 支出管理ページ
# ======================================================
elif page == "支出管理":
    st.title("支出管理")

    with st.form("expense_form"):
        col1, col2 = st.columns(2)
        with col1:
            e_date = st.date_input("日付", value=date.today())
        with col2:
            amount = st.number_input("金額（円）", min_value=0, step=100)

        item = st.text_input("内容")
        category = st.selectbox("カテゴリ", ["食費", "交通費", "買い物", "その他"])
        note = st.text_area("メモ")
        submitted = st.form_submit_button("支出を追加")

        if submitted:
            supabase.table("expenses").insert({
                "date": e_date.isoformat(),
                "item": item,
                "category": category,
                "amount": int(amount),
                "note": note
            }).execute()
            st.success("支出を追加しました")

    data = supabase.table("expenses").select("*").execute().data
    if data:
        df = pd.DataFrame(data)
        df.rename(columns={
            "date": "日付",
            "item": "内容",
            "category": "カテゴリ",
            "amount": "金額",
            "note": "メモ"
        }, inplace=True)
        st.dataframe(df, use_container_width=True)

# ======================================================
# 収入管理ページ
# ======================================================
elif page == "収入管理":
    st.title("収入管理")

    with st.form("income_form"):
        col1, col2 = st.columns(2)
        with col1:
            i_date = st.date_input("日付", value=date.today())
        with col2:
            amount = st.number_input("金額（円）", min_value=0, step=100)

        source = st.text_input("収入源")
        category = st.selectbox("カテゴリ", ["給料", "お小遣い", "その他"])
        note = st.text_area("メモ")
        submitted = st.form_submit_button("収入を追加")

        if submitted:
            supabase.table("income").insert({
                "date": i_date.isoformat(),
                "source": source,
                "category": category,
                "amount": int(amount),
                "note": note
            }).execute()
            st.success("収入を追加しました")

    data = supabase.table("income").select("*").execute().data
    if data:
        df = pd.DataFrame(data)
        df.rename(columns={
            "date": "日付",
            "source": "収入源",
            "category": "カテゴリ",
            "amount": "金額",
            "note": "メモ"
        }, inplace=True)
        st.dataframe(df, use_container_width=True)

# ======================================================
# カレンダーページ
# ======================================================
elif page == "カレンダー":
    st.title("カレンダー（月別予定・収支）")

    col1, col2 = st.columns(2)
    with col1:
        year = st.selectbox("年", range(2023, 2031), index=3)
    with col2:
        month = st.selectbox("月", range(1, 13), index=date.today().month - 1)

    schedules = pd.DataFrame(supabase.table("schedules").select("*").execute().data)
    expenses = pd.DataFrame(supabase.table("expenses").select("*").execute().data)
    income = pd.DataFrame(supabase.table("income").select("*").execute().data)

    for df in [schedules, expenses, income]:
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"]).dt.date

    month_start = date(year, month, 1)
    month_end = date(year + (month == 12), (month % 12) + 1, 1)

    monthly_exp = expenses[(expenses["date"] >= month_start) & (expenses["date"] < month_end)]["amount"].sum() if not expenses.empty else 0
    monthly_inc = income[(income["date"] >= month_start) & (income["date"] < month_end)]["amount"].sum() if not income.empty else 0
    monthly_balance = monthly_inc - monthly_exp

    color = "green" if monthly_balance >= 0 else "red"

    st.markdown(
        f"<h3>{year}年 {month}月の収支：<span style='color:{color}'>¥{monthly_balance:+,}</span></h3>",
        unsafe_allow_html=True
    )

    cal = calendar.monthcalendar(year, month)

    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write("")
            else:
                d = date(year, month, day)
                s_count = schedules[schedules["date"] == d].shape[0] if not schedules.empty else 0
                exp = expenses[expenses["date"] == d]["amount"].sum() if not expenses.empty else 0
                inc = income[income["date"] == d]["amount"].sum() if not income.empty else 0
                bal = inc - exp
                c = "green" if bal >= 0 else "red"

                cols[i].markdown(
                    f"""
                <div style="border:1px solid #ddd; padding:6px; border-radius:6px">
                    <b>{day}日</b><br>
                    予定：{s_count}件<br>
                    <span style="color:{c}; font-weight:bold">収支 {bal:+,} 円</span>
                </div>
                """,
                    unsafe_allow_html=True
                )


# ======================================================
# ダッシュボード
# ======================================================
elif page == "ダッシュボード":
    st.title("ダッシュボード（累計）")

    expenses = supabase.table("expenses").select("*").execute().data
    income = supabase.table("income").select("*").execute().data

    total_exp = sum(e["amount"] for e in expenses) if expenses else 0
    total_inc = sum(i["amount"] for i in income) if income else 0
    balance = total_inc - total_exp

    col1, col2, col3 = st.columns(3)
    col1.metric("総収入", f"¥{total_inc:,}")
    col2.metric("総支出", f"¥{total_exp:,}")
    col3.metric("差引残高", f"¥{balance:+,}")

