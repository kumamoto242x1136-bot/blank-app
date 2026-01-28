import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime, date, time

# -------------------------------
# Streamlit設定
# -------------------------------
st.set_page_config(page_title="Daily Schedule & Expense Manager", layout="wide")
st.title("📅 Schedule & Expense Manager")

# -------------------------------
# Supabase設定
# -------------------------------
SUPABASE_URL = "https://lwemgiikifsdtgmbumkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx3ZW1naWlraWZzZHRnbWJ1bWt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjkxNTA3MDYsImV4cCI6MjA4NDcyNjcwNn0.qrW-LLC858vPOqSG6tS5QrIr4je-2uhyM1ZkI6CFl50"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------------
# 自動削除（スケジュール）
# -------------------------------
now = datetime.now()

# 過去日付のスケジュールを削除
supabase.table("schedules").delete().lt("date", now.date().isoformat()).execute()
# 今日で終了時間を過ぎたスケジュールを削除
supabase.table("schedules").delete().eq("date", now.date().isoformat()).lt("end_time", now.time().strftime("%H:%M:%S")).execute()

# -------------------------------
# Sidebar
# -------------------------------
st.sidebar.title("📂 Menu")
page = st.sidebar.radio("Go to", ["Schedule", "Expenses", "Dashboard"])

# -------------------------------
# Schedule Page
# -------------------------------
if page == "Schedule":
    st.header("🗓 Daily Schedule")

    # 入力フォーム
    with st.form("schedule_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            s_date = st.date_input("Date", value=date.today())
        with col2:
            s_start = st.time_input("Start Time", value=time(9,0))
        with col3:
            s_end = st.time_input("End Time", value=time(10,0))

        title = st.text_input("Title")
        category = st.selectbox("Category", ["Work", "Study", "Private", "Other"])
        note = st.text_area("Note")

        submitted = st.form_submit_button("Add Schedule")

        if submitted:
            supabase.table("schedules").insert({
                "date": str(s_date),
                "start_time": str(s_start),
                "end_time": str(s_end),
                "title": title,
                "category": category,
                "note": note
            }).execute()
            st.success("Schedule added!")

    # 表示部分
    st.subheader("📌 Upcoming Schedules")
    response = supabase.table("schedules").select("*").execute()
    if response.data:
        df = pd.DataFrame(response.data)
        # 終了時間が過ぎたものは表示しない
        upcoming = []
        now = datetime.now()
        for _, row in df.iterrows():
            end_dt = datetime.combine(pd.to_datetime(row["date"]).date(), pd.to_datetime(row["end_time"]).time())
            if end_dt >= now:
                upcoming.append(row)
        if upcoming:
            st.dataframe(pd.DataFrame(upcoming), use_container_width=True)
        else:
            st.info("No upcoming schedules!")
    else:
        st.info("No schedules in database.")

# -------------------------------
# Expenses Page
# -------------------------------
elif page == "Expenses":
    st.header("💰 Daily Expenses")

    # 入力フォーム
    with st.form("expense_form"):
        col1, col2 = st.columns(2)
        with col1:
            e_date = st.date_input("Date", value=date.today())
        with col2:
            amount = st.number_input("Amount (¥)", min_value=0, step=100)

        item = st.text_input("Item")
        category = st.selectbox("Category", ["Food", "Transport", "Shopping", "Other"])
        note = st.text_area("Note")

        submitted = st.form_submit_button("Add Expense")

        if submitted:
            supabase.table("expenses").insert({
                "date": str(e_date),
                "item": item,
                "category": category,
                "amount": amount,
                "note": note
            }).execute()
            st.success("Expense added!")

    # 表示部分
    st.subheader("📋 Expense List")
    response = supabase.table("expenses").select("*").execute()
    if response.data:
        df = pd.DataFrame(response.data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No expenses in database.")

# -------------------------------
# Dashboard Page
# -------------------------------
elif page == "Dashboard":
    st.header("📊 Dashboard")

    # 合計支出
    st.subheader("Total Expense by Category")
    response = supabase.table("expenses").select("*").execute()
    if response.data:
        df = pd.DataFrame(response.data)
        if not df.empty:
            summary = df.groupby("category")["amount"].sum()
            st.bar_chart(summary)
        else:
            st.info("No expense data")
    else:
        st.info("No expense data")

    # 今日のスケジュール
    st.subheader("Today's Schedule")
    response = supabase.table("schedules").select("*").eq("date", str(date.today())).execute()
    if response.data:
        df = pd.DataFrame(response.data)
        # 終了時間が過ぎたものは非表示
        now = datetime.now()
        upcoming = []
        for _, row in df.iterrows():
            end_dt = datetime.combine(pd.to_datetime(row["date"]).date(), pd.to_datetime(row["end_time"]).time())
            if end_dt >= now:
                upcoming.append(row)
        if upcoming:
            st.dataframe(pd.DataFrame(upcoming), use_container_width=True)
        else:
            st.info("No upcoming schedules for today")
    else:
        st.info("No schedules for today")
