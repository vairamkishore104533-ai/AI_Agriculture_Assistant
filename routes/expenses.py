from flask import Blueprint, render_template, request, jsonify, session
from utils.auth import login_required
from models.expense import Expense
from utils.helpers import get_expense_categories

expenses_bp = Blueprint("expenses", __name__)

@expenses_bp.route("/expenses")
@login_required
def index():
    return render_template(
        "expenses.html",
        categories=get_expense_categories(),
        lang=session.get("lang", "en"),
    )

@expenses_bp.route("/api/expenses", methods=["GET"])
@login_required
def get_expenses():
    user_id = session.get("user_id")
    expenses = Expense.find_by_user(user_id)
    summary = Expense.get_summary(user_id)
    cat_breakdown = Expense.get_category_breakdown(user_id)
    return jsonify({
        "success": True,
        "expenses": [e.to_dict() for e in expenses],
        "summary": summary,
        "category_breakdown": cat_breakdown,
    })

@expenses_bp.route("/api/expenses", methods=["POST"])
@login_required
def add_expense():
    data = request.get_json()
    user_id = session.get("user_id")
    lang = session.get("lang", "en")

    if not data.get("amount") or not data.get("category"):
        msg = "Amount and category are required." if lang == "en" else "தொகை மற்றும் வகை தேவை."
        return jsonify({"success": False, "message": msg})

    expense = Expense()
    expense.user_id = user_id
    expense.type = data.get("type", "expense")
    expense.category = data["category"]
    expense.amount = float(data["amount"])
    expense.description = data.get("description", "")
    expense.date = data.get("date", "")
    expense.save()

    msg = "Entry added successfully!" if lang == "en" else "பதிவு வெற்றிகரமாக சேர்க்கப்பட்டது!"
    return jsonify({"success": True, "message": msg})

@expenses_bp.route("/api/expenses/<expense_id>", methods=["DELETE"])
@login_required
def delete_expense(expense_id):
    lang = session.get("lang", "en")
    expense = Expense.find_by_id(expense_id)
    if not expense:
        msg = "Entry not found." if lang == "en" else "பதிவு கிடைக்கவில்லை."
        return jsonify({"success": False, "message": msg})
    expense.delete()
    msg = "Entry deleted successfully!" if lang == "en" else "பதிவு வெற்றிகரமாக நீக்கப்பட்டது!"
    return jsonify({"success": True, "message": msg})

@expenses_bp.route("/api/expenses/summary")
@login_required
def get_summary():
    user_id = session.get("user_id")
    summary = Expense.get_summary(user_id)
    cat_breakdown = Expense.get_category_breakdown(user_id)
    profit = summary.get("income", 0) - summary.get("expense", 0)
    return jsonify({
        "success": True,
        "summary": summary,
        "profit": profit,
        "category_breakdown": cat_breakdown,
    })
