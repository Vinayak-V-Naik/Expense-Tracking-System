import mysql.connector
from contextlib import contextmanager
from logging_setup import setup_logger
import os

logger = setup_logger('db_helper')


# Database connection context manager
@contextmanager
def get_db_cursor(commit=False):
    connection=mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "root"),
        database=os.getenv("DB_NAME", "expense_manager"),
        port=int(os.getenv("DB_PORT", "3306"))
    )
    cursor = connection.cursor(dictionary=True)
    yield cursor
    if commit:
        connection.commit()
    cursor.close()
    connection.close()


# User functions
def create_user(actual_name, username, password):
    """Create a new user (plain text password)"""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "INSERT INTO users (actual_name, username, password_hash) VALUES (%s, %s, %s)",
            (actual_name, username, password)
        )


def get_user_by_username(username):
    """Fetch user details by username"""
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        return cursor.fetchone()


def verify_password(plain_password, stored_password):
    """Verify password against stored plain text password"""
    return plain_password == stored_password


# Expense functions
def fetch_expenses_for_date(expense_date, user_id):
    logger.info(f"fetch_expenses_for_date called with {expense_date}, user_id={user_id}")
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT amount, category, notes, user_id FROM expenses WHERE expense_date = %s AND user_id = %s",
            (expense_date, user_id)
        )
        return cursor.fetchall()


def delete_expenses_for_date(expense_date, user_id):
    logger.info(f"delete_expenses_for_date called with {expense_date}, user_id={user_id}")
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "DELETE FROM expenses WHERE expense_date = %s AND user_id = %s",
            (expense_date, user_id)
        )


def insert_expense(expense_date, amount, category, notes, user_id):
    logger.info(
        f"insert_expense called with date: {expense_date}, amount: {amount}, category: {category}, user_id={user_id}")
    # Capitalize category for consistency
    category = category.capitalize()
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "INSERT INTO expenses (expense_date, amount, category, notes, user_id) VALUES (%s, %s, %s, %s, %s)",
            (expense_date, amount, category, notes, user_id)
        )


def fetch_expense_summary_by_catrgory(start_date, end_date, user_id):
    logger.info(f"fetch_expense_summary called with start: {start_date}, end: {end_date}, user_id={user_id}")
    with get_db_cursor() as cursor:
        cursor.execute(
            '''SELECT category, SUM(amount) as total
               FROM expenses
               WHERE expense_date BETWEEN %s AND %s
                 AND user_id = %s
               GROUP BY category;''',
            (start_date, end_date, user_id)
        )
        return cursor.fetchall()


def fetch_expense_summary_by_month(user_id):
    """
    Fetch total expenses grouped by month for a specific user.
    Returns list of dicts with expense_month, month_name, expense_year, and total.
    """
    logger.info(f"fetch_expense_summary_by_month called with user_id={user_id}")
    with get_db_cursor() as cursor:
        # Simple query - fetch all expenses
        query = """
                SELECT
                    MONTH (expense_date) as expense_month, YEAR (expense_date) as expense_year, amount
                FROM expenses
                WHERE user_id = %s \
                """

        try:
            cursor.execute(query, (user_id,))
            results = cursor.fetchall()

            if not results:
                return []

            # Group and sum in Python
            from collections import defaultdict
            import calendar

            monthly_totals = defaultdict(float)

            for row in results:
                key = (row['expense_year'], row['expense_month'])
                monthly_totals[key] += float(row['amount'])

            # Convert to list of dicts with proper format
            final_results = []
            for (year, month), total in monthly_totals.items():
                month_name = calendar.month_name[month]
                final_results.append({
                    'expense_month': month,
                    'expense_year': year,
                    'month_name': f"{month_name} {year}",
                    'total': total
                })

            # Sort by year and month descending
            final_results.sort(key=lambda x: (x['expense_year'], x['expense_month']), reverse=True)

            return final_results

        except Exception as e:
            logger.error(f"Error in fetch_expense_summary_by_month: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise

# Test section

if __name__ == "__main__":
    user_id = 1  # Replace with actual user_id from your users table

    print("=== Testing fetch_expenses_for_date ===")
    expenses = fetch_expenses_for_date("2024-09-30", user_id)
    print(expenses)

    print("\n=== Testing fetch_expense_summary ===")
    summary = fetch_expense_summary("2024-08-01", "2024-08-05", user_id)
    for record in summary:
        print(record)

    print("\n=== Testing fetch_monthly_summary ===")
    monthly = fetch_monthly_summary(user_id)
    for record in monthly:
        print(record)
