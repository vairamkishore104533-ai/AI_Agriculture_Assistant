from flask import Blueprint, render_template, request, jsonify, session
from utils.auth import login_required
from services.market_service import MarketService

market_bp = Blueprint("market", __name__)
market_service = MarketService()

@market_bp.route("/market")
@login_required
def index():
    return render_template("market.html", lang=session.get("lang", "en"))

@market_bp.route("/api/market")
@login_required
def get_prices():
    district = request.args.get("district", "")
    crop = request.args.get("crop", "")
    prices = market_service.get_prices(district, crop)
    return jsonify({"success": True, "prices": prices})
