import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import date, time, datetime

# -------------------------------
# ページ設定
# -------------------------------
st.set_page_config(page_title="スケジュール・家計簿アプリ", layout="wide")

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
st.title("スケジュール・家計簿アプリ")

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
    ["スケジュール管理", "収入・支出管理", "カレンダー", "ダッシュボード"]
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
elif page == "カレンダー":
    st.header("カレンダー（予定・収支一覧）")

    # 表示する年月を選択
    col1, col2 = st.columns(2)
    with col1:
        year = st.number_input("年", value=date.today().year, step=1)
    with col2:
        month = st.number_input("月", value=date.today().month, min_value=1, max_value=12)

    # Supabaseからデータ取得
    schedules = supabase.table("schedules").select("*").execute().data
    transactions = supabase.table("transactions").select("*").execute().data

    df_s = pd.DataFrame(schedules)
    df_t = pd.DataFrame(transactions)

    if df_s.empty and df_t.empty:
        st.info("データがありません")
    else:
        if not df_s.empty:
            df_s["date"] = pd.to_datetime(df_s["date"]).dt.date

        if not df_t.empty:
            df_t["date"] = pd.to_datetime(df_t["date"]).dt.date
            df_t["signed_amount"] = df_t.apply(
                lambda x: x["amount"] if x["type"] == "収入" else -x["amount"],
                axis=1
            )

        # 月で絞り込み
        start_date = date(int(year), int(month), 1)
        if month == 12:
            end_date = date(int(year) + 1, 1, 1)
        else:
            end_date = date(int(year), int(month) + 1, 1)

        df_s_month = df_s[(df_s["date"] >= start_date) & (df_s["date"] < end_date)] if not df_s.empty else pd.DataFrame()
        df_t_month = df_t[(df_t["date"] >= start_date) & (df_t["date"] < end_date)] if not df_t.empty else pd.DataFrame()

        # 日別収支
        daily_balance = {}
        if not df_t_month.empty:
            daily_balance = df_t_month.groupby("date")["signed_amount"].sum().to_dict()

        # 月間収支
        monthly_total = df_t_month["signed_amount"].sum() if not df_t_month.empty else 0

        st.subheader("月間収支合計")
        st.metric(label="合計（円）", value=f"{monthly_total:+,}")

        st.divider()
        st.subheader("日別一覧")

        # 日付ごとに表示（カレンダー風）
        current = start_date
        while current < end_date:
            st.markdown(f"### {current}")

            # 予定
            day_schedules = df_s_month[df_s_month["date"] == current]
            if not day_schedules.empty:
                st.write("【予定】")
                st.dataframe(
                    day_schedules[["start_time", "end_time", "title", "category"]],
                    use_container_width=True
                )
            else:
                st.write("予定なし")

            # 収支
            balance = daily_balance.get(current, 0)
            st.write(f"【当日の収支】 {balance:+,} 円")

            st.divider()
            current += pd.Timedelta(days=1)
