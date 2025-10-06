from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import List
from pydantic import BaseModel
import db_helper

# Import auth router and token verification
from auth import router as auth_router, verify_token


class Expense(BaseModel):
    amount: float
    category: str
    notes: str
    user_id: int


app = FastAPI(title="Expense Tracker API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication routes
app.include_router(auth_router)


@app.get('/')
def root():
    return {"message": "Expense Tracker API is running", "version": "3.0"}


# PROTECTED EXPENSE ENDPOINTS

@app.get('/expenses/{user_id}/{expense_date}')
def get_expenses(user_id: int, expense_date: str, token_user_id: int = Depends(verify_token)):
    if token_user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this user's data")

    try:
        date_obj = datetime.strptime(expense_date, "%Y-%m-%d").date()
        print(f"Fetching expenses for user_id={user_id}, date={date_obj}")
        expenses = db_helper.fetch_expenses_for_date(date_obj, user_id)

        if expenses is None or len(expenses) == 0:
            print("No expenses found, returning empty list")
            return []

        print(f"Found {len(expenses)} expenses")
        return expenses

    except ValueError as ve:
        print(f"Invalid date format: {expense_date}")
        raise HTTPException(status_code=400, detail=f"Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        print(f"Error fetching expenses: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching expenses: {str(e)}")


@app.post('/expenses/{expense_date}')
def add_or_update_expense(expense_date: str, expenses: List[Expense], token_user_id: int = Depends(verify_token)):
    try:
        date_obj = datetime.strptime(expense_date, "%Y-%m-%d").date()

        if not expenses:
            raise HTTPException(status_code=400, detail="No expenses provided")

        user_id = expenses[0].user_id

        if token_user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to modify this user's data")

        print(f"Deleting expenses for user_id={user_id}, date={date_obj}")
        db_helper.delete_expenses_for_date(date_obj, user_id)

        for expense in expenses:
            if expense.user_id != token_user_id:
                raise HTTPException(status_code=403, detail="Not authorized to create expenses for other users")

            print(f"Inserting: {expense.amount} - {expense.category}")
            db_helper.insert_expense(
                date_obj,
                expense.amount,
                expense.category,
                expense.notes,
                expense.user_id
            )

        print(f"Successfully inserted {len(expenses)} expenses")
        return {"message": "Expenses updated successfully", "count": len(expenses)}

    except ValueError as ve:
        print(f"Invalid date format: {expense_date}")
        raise HTTPException(status_code=400, detail=f"Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        print(f"Error updating expenses: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error updating expenses: {str(e)}")


@app.get('/analytics_by_category/{user_id}')
def get_analytics_by_category(user_id: int, start_date: str, end_date: str, token_user_id: int = Depends(verify_token)):
    if token_user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this user's data")

    try:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()

        print(f"Fetching analytics for user_id={user_id}, from {start_date_obj} to {end_date_obj}")

        summary = db_helper.fetch_expense_summary_by_catrgory(start_date_obj, end_date_obj, user_id)

        if summary is None or len(summary) == 0:
            print("No analytics data found, returning empty list")
            return []

        print(f"Found analytics for {len(summary)} categories")
        return summary

    except ValueError as ve:
        print(f"Invalid date format: {start_date} or {end_date}")
        raise HTTPException(status_code=400, detail=f"Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        print(f"Error fetching analytics: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching analytics: {str(e)}")


@app.get('/analytics_by_months/{user_id}')
def get_analytics_by_months(user_id: int, token_user_id: int = Depends(verify_token)):
    if token_user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this user's data")

    try:
        print(f"Fetching monthly summary for user_id={user_id}")

        summary = db_helper.fetch_expense_summary_by_month(user_id)

        if summary is None or len(summary) == 0:
            print("No monthly summary found, returning empty list")
            return []

        print(f"Found summary for {len(summary)} months")
        return summary

    except Exception as e:
        print(f"Error fetching monthly summary: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching monthly summary: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    print("Starting Expense Tracker API on port 8000...")
    uvicorn.run(app, host="127.0.0.1", port=8000)