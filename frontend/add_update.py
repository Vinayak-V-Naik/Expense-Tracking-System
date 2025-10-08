import streamlit as st
from datetime import datetime
import requests
import os
API_URL = os.getenv("API_URL", "https://expense-tracking-system-app.onrender.com")



def add_update_tab(user_id, token):
    selected_date = st.date_input("Enter Date", datetime(2024, 8, 1), label_visibility="collapsed")
    selected_date_str = selected_date.strftime("%Y-%m-%d")

    # Create a unique key based on date to force form reset when date changes
    form_key = f"expense_form_{selected_date_str}"

    # GET expenses for the logged-in user
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{API_URL}/expenses/{user_id}/{selected_date_str}",
            headers=headers
        )

        if response.status_code == 200:
            existing_expenses = response.json()
            st.write(f"There are {len(existing_expenses)} expenses on this date")
        else:
            st.warning(f"No expenses found for this date (Status: {response.status_code})")
            existing_expenses = []
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        existing_expenses = []

    categories = ["Rent", "Food", "Shopping", "Entertainment", "Other"]

    with st.form(key=form_key):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.text("Amount")
        with col2:
            st.text("Category")
        with col3:
            st.text("Notes")

        expenses = []
        for i in range(5):
            if i < len(existing_expenses):
                amount = existing_expenses[i]['amount']
                category = existing_expenses[i]["category"]
                notes = existing_expenses[i]["notes"]
            else:
                amount = 0.0
                category = "Shopping"
                notes = ""

            col1, col2, col3 = st.columns(3)
            with col1:
                amount_input = st.number_input(
                    label="Amount", min_value=0.0, step=1.0, value=amount,
                    key=f"amount_{i}_{selected_date_str}",
                    label_visibility="collapsed"
                )
            with col2:
                # Handle case-insensitive category matching
                try:
                    category_index = categories.index(category)
                except ValueError:
                    # If category not found, try case-insensitive match
                    category_lower = category.lower()
                    category_index = next(
                        (i for i, cat in enumerate(categories) if cat.lower() == category_lower),
                        2  # Default to "Shopping" (index 2) if not found
                    )

                category_input = st.selectbox(
                    label="Category", options=categories, index=category_index,
                    key=f"category_{i}_{selected_date_str}", label_visibility="collapsed"
                )
            with col3:
                notes_input = st.text_input(
                    label="Notes", value=notes,
                    key=f"notes_{i}_{selected_date_str}",
                    label_visibility="collapsed"
                )

            expenses.append({
                'amount': amount_input,
                'category': category_input,
                'notes': notes_input,
                'user_id': user_id
            })

        submit_button = st.form_submit_button("Save Expenses")
        if submit_button:
            # Filter out empty expenses (only keep rows with amount > 0)
            filtered_expenses = [expense for expense in expenses if expense['amount'] > 0]

            if len(filtered_expenses) == 0:
                st.warning("No expenses to save. Please enter at least one expense with amount > 0.")
            else:
                # Send expenses with authorization header
                headers = {"Authorization": f"Bearer {token}"}
                response = requests.post(
                    f"{API_URL}/expenses/{selected_date_str}",
                    json=filtered_expenses,
                    headers=headers
                )
                if response.status_code == 200:
                    st.success(f"Successfully saved {len(filtered_expenses)} expense(s)!")
                    st.rerun()
                else:
                    st.error(f"Failed to update expenses: {response.text}")

