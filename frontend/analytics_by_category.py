import streamlit as st
from datetime import datetime, timedelta
import requests
import pandas as pd
import plotly.express as px

API_URL = "http://localhost:8000"


def analytics_category_tab(user_id, token):
    st.title("Expense Analytics By Category")

    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=30),
            key="analytics_start_date"
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.now(),
            key="analytics_end_date"
        )

    # Validate date range
    if start_date > end_date:
        st.error("Start date must be before end date!")
        return

    # Convert dates to strings
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")

    # Fetch analytics data
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{API_URL}/analytics_by_category/{user_id}",
            params={"start_date": start_date_str, "end_date": end_date_str},
            headers=headers
        )

        if response.status_code == 404:
            st.info("No expense data found for the selected date range.")
            return

        if response.status_code != 200:
            st.error(f"Failed to retrieve analytics: {response.text}")
            return

        analytics_data = response.json()

        if not analytics_data or len(analytics_data) == 0:
            st.info("No expenses found in the selected date range. Add some expenses to see analytics!")
            return

        # Create DataFrame
        df = pd.DataFrame(analytics_data)

        # Check if required columns exist
        if 'category' not in df.columns or 'total' not in df.columns:
            st.error("Invalid data format from API")
            return

        # Sort by total (highest first)
        df_sorted = df.sort_values(by='total', ascending=False)

        # Display summary metrics
        total_expenses = df_sorted['total'].sum()
        num_categories = len(df_sorted)
        highest_category = df_sorted.iloc[0]['category'] if num_categories > 0 else "N/A"
        highest_amount = df_sorted.iloc[0]['total'] if num_categories > 0 else 0

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Spent", f"₹{total_expenses:.2f}")
        with col2:
            st.metric("Categories", num_categories)
        with col3:
            st.metric("Highest Category", highest_category, f"₹{highest_amount:.2f}")

        st.divider()

        # Display bar chart
        st.subheader("Spending by Category")
        df_chart = df_sorted.set_index('category')
        st.bar_chart(
            data=df_chart['total'],
            use_container_width=True,
            height=400
        )

        st.divider()

        # PIE CHART: Category Distribution
        st.subheader("Category Distribution (Pie Chart)")

        # Calculate percentage
        df_sorted['percentage'] = (df_sorted['total'] / total_expenses * 100).round(2)

        # Create pie chart
        fig = px.pie(
            df_sorted,
            names='category',
            values='total',
            title="Expense Distribution by Category",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )

        # Show percentage labels
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label'
        )

        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # Text-based breakdown
        st.subheader("Detailed Breakdown by Category")

        # Display table
        df_display = df_sorted.copy()
        df_display['total'] = df_display['total'].map("₹{:.2f}".format)
        df_display['percentage'] = df_display['percentage'].map("{:.1f}%".format)
        df_display.columns = ['Category', 'Total Amount', 'Percentage']
        df_display.index = range(1, len(df_display) + 1)

        st.table(df_display)

    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to the API. Make sure the FastAPI server is running.")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        import traceback
        st.code(traceback.format_exc())