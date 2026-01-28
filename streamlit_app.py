import streamlit as st
from supabase import create_client

# Supabase情報
SUPABASE_URL = "https://lwemgiikifsdtgmbumkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx3ZW1naWlraWZzZHRnbWJ1bWt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjkxNTA3MDYsImV4cCI6MjA4NDcyNjcwNn0.qrW-LLC858vPOqSG6tS5QrIr4je-2uhyM1ZkI6CFl50"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("Todoリスト管理アプリ")
import pandas as pd
from datetime import date, time
# -------------------------------
# Auto-delete past schedules (Supabase)
# -------------------------------
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


st.set_page_config(page_title="Daily Schedule & Expense Manager", layout="wide")

# -------------------------------
# Initialize session state
# -------------------------------
if "schedules" not in st.session_state:
    st.session_state.schedules = pd.DataFrame(columns=[
        "Date", "Start", "End", "Title", "Category", "Note"
    ])

if "expenses" not in st.session_state:
    st.session_state.expenses = pd.DataFrame(columns=[
        "Date", "Item", "Category", "Amount", "Note"
    ])

# -------------------------------
# Sidebar
# -------------------------------
st.sidebar.title("📅 Menu")
page = st.sidebar.radio("Go to", ["Schedule", "Expenses", "Dashboard"])

# -------------------------------
# Schedule Page
# -------------------------------
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

    st.success("Schedule added to database")
    st.subheader("📋 Schedule List")
    st.dataframe(st.session_state.schedules, use_container_width=True)

# -------------------------------
# Expenses Page
# -------------------------------
elif page == "Expenses":
    st.title("💰 Daily Expenses")

    with st.form("expense_form"):
        col1, col2 = st.columns(2)
        with col1:
            e_date = st.date_input("Date", value=date.today(), key="expense_date")
        with col2:
            amount = st.number_input("Amount (¥)", min_value=0, step=100)

        item = st.text_input("Item")
        category = st.selectbox("Category", ["Food", "Transport", "Shopping", "Other"])
        note = st.text_area("Note", key="expense_note")
        submitted = st.form_submit_button("Add Expense")

        if submitted:
            new_row = pd.DataFrame([[e_date, item, category, amount, note]],
                                   columns=st.session_state.expenses.columns)
            st.session_state.expenses = pd.concat([
                st.session_state.expenses, new_row
            ], ignore_index=True)
            st.success("Expense added")

    st.subheader("📋 Expense List")
    st.dataframe(st.session_state.expenses, use_container_width=True)

# -------------------------------
# Dashboard Page
# -------------------------------
elif page == "Dashboard":
    st.title("📊 Dashboard")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Total Expense by Category")
        if not st.session_state.expenses.empty:
            summary = st.session_state.expenses.groupby("Category")["Amount"].sum()
            st.bar_chart(summary)
        else:
            st.info("No expense data")

    with col2:
        st.subheader("Today's Schedule")
        today = date.today()
        today_schedule = st.session_state.schedules[
            st.session_state.schedules["Date"] == today
        ]
        if not today_schedule.empty:
            st.dataframe(today_schedule, use_container_width=True)
        else:
            st.info("No schedules for today")

    st.subheader("💡 Tips")
    st.write("You can deploy this app directly on Streamlit Community Cloud. For persistence, consider using CSV files or a database (SQLite).")
