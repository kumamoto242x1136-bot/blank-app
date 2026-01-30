import streamlit as st
import pandas as pd
from datetime import date, time, datetime
from supabase import create_client
import calendar

# -------------------------------
# Page config
# -------------------------------
st.set_page_config(
    page_title="Schedule & Money Manager",
    layout="wide"
)

# -------------------------------
# Supabase connection
# -------------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------------
# Sidebar
# -------------------------------
st.sidebar.title("📅 Menu")
page = st.sidebar.radio(
    "Go to",
    ["Schedule", "Expenses", "Income", "Calendar", "Dashboard"]
)

# ======================================================
# 🗑 Auto delete past schedules
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
# 🗓 Schedule Page
# ======================================================
if page == "Schedule":
    st.title("🗓 Daily Schedule")

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
                "date": s_date.isoformat(),
                "start_time": s_start.isoformat(),
                "end_time": s_end.isoformat(),
                "title": title,
                "category": category,
                "note": note
            }).execute()
            st.success("Schedule added")

    data = supabase.table("schedules").select("*").execute().data
    if data:
        df = pd.DataFrame(data)
        df.rename(columns={
            "date": "Date",
            "start_time": "Start",
            "end_time": "End",
            "title": "Title",
            "category": "Category",
            "note": "Note"
        }, inplace=True)
        st.dataframe(df, use_container_width=True)

# ======================================================
# 💰 Expenses Page
# ======================================================
elif page == "Expenses":
    st.title("💰 Expenses")

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
                "date": e_date.isoformat(),
                "item": item,
                "category": category,
                "amount": int(amount),
                "note": note
            }).execute()
            st.success("Expense added")

    data = supabase.table("expenses").select("*").execute().data
    if data:
        df = pd.DataFrame(data)
        df.rename(columns={
            "date": "Date",
            "item": "Item",
            "category": "Category",
            "amount": "Amount",
            "note": "Note"
        }, inplace=True)
        st.dataframe(df, use_container_width=True)

# ======================================================
# 💵 Income Page
# ======================================================
elif page == "Income":
    st.title("💵 Income")

    with st.form("income_form"):
        col1, col2 = st.columns(2)
        with col1:
            i_date = st.date_input("Date", value=date.today())
        with col2:
            amount = st.number_input("Amount (¥)", min_value=0, step=100)

        source = st.text_input("Source")
        category = st.selectbox("Category", ["Salary", "Allowance", "Other"])
        note = st.text_area("Note")
        submitted = st.form_submit_button("Add Income")

        if submitted:
            supabase.table("income").insert({
                "date": i_date.isoformat(),
                "source": source,
                "category": category,
                "amount": int(amount),
                "note": note
            }).execute()
            st.success("Income added")

    data = supabase.table("income").select("*").execute().data
    if data:
        df = pd.DataFrame(data)
        df.rename(columns={
            "date": "Date",
            "source": "Source",
            "category": "Category",
            "amount": "Amount",
            "note": "Note"
        }, inplace=True)
        st.dataframe(df, use_container_width=True)

# ======================================================
# 📅 Calendar Page
# ======================================================
elif page == "Calendar":
    st.title("📅 Calendar")

    col1, col2 = st.columns(2)
    with col1:
        year = st.selectbox("Year", range(2023, 2031), index=3)
    with col2:
        month = st.selectbox("Month", range(1, 13), index=date.today().month - 1)

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
        f"<h3>{year}年 {month}月 収支：<span style='color:{color}'>¥{monthly_balance:+,}</span></h3>",
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
                        <b>{day}</b><br>
                        🗓 {s_count}件<br>
                        <span style="color:{c}; font-weight:bold">💰 {bal:+,}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    st.subheader("📊 Category Breakdown")

    if not expenses.empty:
        st.write("💸 Expenses")
        st.pyplot(expenses.groupby("category")["amount"].sum().plot.pie(autopct="%1.1f%%").figure)

    if not income.empty:
        st.write("💵 Income")
        st.pyplot(income.groupby("category")["amount"].sum().plot.pie(autopct="%1.1f%%").figure)

# ======================================================
# 📊 Dashboard
# ======================================================
elif page == "Dashboard":
    st.title("📊 Dashboard")

    expenses = supabase.table("expenses").select("*").execute().data
    income = supabase.table("income").select("*").execute().data

    total_exp = sum(e["amount"] for e in expenses) if expenses else 0
    total_inc = sum(i["amount"] for i in income) if income else 0
    balance = total_inc - total_exp

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Income", f"¥{total_inc:,}")
    col2.metric("Total Expense", f"¥{total_exp:,}")
    col3.metric("Balance", f"¥{balance:+,}")
