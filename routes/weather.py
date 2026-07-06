from flask import Blueprint, render_template, request, jsonify, session
from utils.auth import login_required
from services.weather_service import WeatherService

weather_bp = Blueprint("weather", __name__)
weather_service = WeatherService()

@weather_bp.route("/weather")
@login_required
def index():
    return render_template("weather.html", lang=session.get("lang", "en"))

@weather_bp.route("/api/weather")
@login_required
def get_weather():
    district = request.args.get("district", "Thanjavur")
    lang = session.get("lang", "en")
    data = weather_service.get_current_weather(district)
    advice = weather_service.get_ai_farming_advice(data, lang)
    return jsonify({"success": True, "weather": data, "advice": advice})
