from flask import Blueprint, render_template, request, jsonify, session
from utils.auth import login_required, admin_required
from services.scheme_service import SchemeService

schemes_bp = Blueprint("schemes", __name__)
scheme_service = SchemeService()

@schemes_bp.route("/schemes")
@login_required
def index():
    return render_template("schemes.html", lang=session.get("lang", "en"))

@schemes_bp.route("/api/schemes")
@login_required
def get_schemes():
    schemes = scheme_service.get_all_schemes()
    return jsonify({"success": True, "schemes": schemes})
