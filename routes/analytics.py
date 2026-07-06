from flask import Blueprint, render_template, request, jsonify, session
from utils.auth import login_required
from models.crop import Crop
from models.expense import Expense
from services.weather_service import WeatherService
from datetime import datetime, timedelta

analytics_bp = Blueprint("analytics", __name__)

@analytics_bp.route("/analytics")
@login_required
def index():
    return render_template("analytics.html", lang=session.get("lang", "en"))

@analytics_bp.route("/api/analytics")
@login_required
def get_analytics():
    user_id = session.get("user_id")

    expense_summary = Expense.get_summary(user_id)
    crops = Crop.find_by_user(user_id)
    cat_expenses = Expense.get_category_breakdown(user_id)
    income = expense_summary.get("income", 0)
    expense = expense_summary.get("expense", 0)
    profit = income - expense

    crop_distribution = {}
    for c in crops:
        name = c.crop_name
        crop_distribution[name] = crop_distribution.get(name, 0) + 1

    monthly_data = []
    for i in range(6):
        month = datetime.now().month - i
        year = datetime.now().year
        if month <= 0:
            month += 12
            year -= 1
        month_data = Expense.get_monthly_summary(user_id, year, month)
        inc = 0
        exp = 0
        for m in month_data:
            if m["_id"] == "income":
                inc = m["total"]
            elif m["_id"] == "expense":
                exp = m["total"]
        month_name = datetime(year, month, 1).strftime("%b")
        monthly_data.append({"month": month_name, "income": inc, "expense": exp, "profit": inc - exp})
    monthly_data.reverse()

    weather_service = WeatherService()
    weather = weather_service.get_current_weather()

    return jsonify({
        "success": True,
        "income": income,
        "expenses": expense,
        "profit": profit,
        "crop_count": len(crops),
        "crop_distribution": crop_distribution,
        "category_expenses": cat_expenses,
        "monthly": monthly_data,
        "weather": weather,
    })
