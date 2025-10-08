import streamlit as st
from datetime import datetime
import requests
import pandas as pd
import os
API_URL = os.getenv("API_URL", "https://expense-tracking-system-app.onrender.com")


def analytics_months_tab(user_id, token):
    st.title("Expense Breakdown By Months")

    # GET monthly summary for the logged-in user
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{API_URL}/analytics_by_months/{user_id}",
            headers=headers
        )

        if response.status_code == 404:
            st.info("No monthly data available. Start by adding some expenses!")
            return

        if response.status_code != 200:
            st.error(f"Failed to retrieve monthly summary: {response.text}")
            return

        monthly_summary = response.json()

        if not monthly_summary or len(monthly_summary) == 0:
            st.info("No expense data available yet. Add some expenses to see analytics!")
            return

        # Create DataFrame
        df = pd.DataFrame(monthly_summary)

        # Check required columns exist
        required_columns = ["expense_month", "month_name", "total"]
        if not all(col in df.columns for col in required_columns):
            st.error(f"Invalid data format from API. Expected: {required_columns}, Got: {df.columns.tolist()}")
            return

        # Handle expense_year if it exists for proper sorting
        if 'expense_year' in df.columns:
            df_sorted = df.sort_values(by=["expense_year", "expense_month"], ascending=False)
            df_chart = df.sort_values(by=["expense_year", "expense_month"], ascending=True)
        else:
            df_sorted = df.sort_values(by="expense_month", ascending=False)
            df_chart = df.sort_values(by="expense_month", ascending=True)

        # Display summary statistics at top
        total_expenses = df['total'].sum()
        num_months = len(df)
        avg_per_month = df['total'].mean()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Months", num_months)
        with col2:
            st.metric("Total Spent", f"₹{total_expenses:.2f}")
        with col3:
            st.metric("Average/Month", f"₹{avg_per_month:.2f}")

        st.divider()

        # Display bar chart
        st.subheader("Monthly Expenses Chart")
        df_chart_indexed = df_chart.set_index("month_name")
        st.bar_chart(
            data=df_chart_indexed['total'],
            use_container_width=True,
            height=400
        )

        st.divider()

        # Display table
        st.subheader("Monthly Summary Table")
        df_display = df_sorted.copy()
        df_display["total"] = df_display["total"].map("₹{:.2f}".format)
        df_display = df_display[["month_name", "total"]]
        df_display.columns = ["Month", "Total Amount"]
        df_display.index = range(1, len(df_display) + 1)
        st.table(df_display)

    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to the API. Make sure the FastAPI server is running.")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

