from flask import Blueprint, request, jsonify, session
from utils.village_validator import village_validator

validation_bp = Blueprint("validation", __name__)

@validation_bp.route("/api/validate-village", methods=["POST"])
def validate_village():
    data = request.get_json()
    if not data:
        return jsonify({
            "valid": False,
            "status": "error",
            "message": "Invalid JSON"
        }), 400

    village = data.get("village", "").strip()
    district = data.get("district", "").strip()
    lang = session.get("lang", "en")

    # The validator handles its own checking, normalization, and fallback.
    result = village_validator.validate(village, district, lang=lang)
    
    return jsonify(result)
