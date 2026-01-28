import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import date, time, datetime

# --------------------------------
# Streamlit 設定（最初に書く）
# --------------------------------
st.set_page_config(
    page_title="Daily Schedule & Expense Manager",
    layout="wide"
)

# --------------------------------
# Supabase 設定
# ※ 本当は secrets に移す（あとでやる）
# --------------------------------
SUPABASE_URL = "https://lwemgiikifsdtgmbumkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx3ZW1naWlraWZzZHRnbWJ1bWt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjkxNTA3MDYsImV4cCI6MjA4NDcyNjcwNn0.qrW-LLC858vPOqSG6tS5QrIr4je-2uhyM1ZkI6CFl50"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --------------------------------
# 自動削除（Supabase）
# --------------------------------
now = datetime.now()

# 今日より前の日付は削除
supabase.table("schedules") \
    .delete() \
    .lt("date", now.date().isoformat()) \
    .execute()

# 今日で、終了時刻が過ぎたものを削除
supabase.table("schedules") \
    .delete() \
    .eq("date", now.date().isoformat()) \
    .lt("end_time", now.time().strftime("%H:%M:%S")) \
    .execute()

# --------------------------------
# Sidebar
# --------------------------------
st.sidebar.title("📅 Menu")
page = st.sidebar.radio("Go to", ["Schedule", "Expenses", "Dashboard"])

# --------------------------------
# Schedule Page
# --------------------------------
if page == "Schedule":
    st.title("🗓️ Daily Schedule")

    with st.form("schedule_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            s_date = st.date_input("Date", value=date.today())
        with col2:
            s_start = st.time_input("Start Time", value=time(9, 0))
        with col3:
            s_end = st.time_input("End Time", value=time(10, 0))

        title = st.text_input("Title")
        category = st.selectbox(
            "Category",
            ["Work", "Study", "Private", "Other"]
        )
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

            st.success("Schedule added to database")

    st.subheader("📋 Schedule List")

    response = supabase.table("schedules").select("*").execute()

    if response.data:
        df = pd.DataFrame(response.data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No schedules in database")

# --------------------------------
# Expenses Page（まだローカル）
# --------------------------------
elif page == "Expenses":
    st.title("💰 Daily Expenses")
    st.info("※ Expenses はまだ Supabase 未対応")

# --------------------------------
# Dashboard Page
# --------------------------------
elif page == "Dashboard":
    st.title("📊 Dashboard")
    st.info("※ Dashboard は後で Supabase 対応予定")
