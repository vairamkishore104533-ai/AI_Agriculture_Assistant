from flask import Blueprint, render_template, request, jsonify, session
from utils.auth import login_required
from models.crop import Crop
from utils.helpers import get_crop_list, get_districts, get_soil_types

crops_bp = Blueprint("crops", __name__)

@crops_bp.route("/crops", methods=["GET"])
@login_required
def index():
    user_id = session.get("user_id")
    crops = Crop.find_by_user(user_id)
    return render_template(
        "crops.html",
        crops=[c.to_dict() for c in crops],
        crop_list=get_crop_list(),
        districts=get_districts(),
        soil_types=get_soil_types(),
        lang=session.get("lang", "en"),
    )

@crops_bp.route("/api/crops", methods=["GET"])
@login_required
def get_crops():
    user_id = session.get("user_id")
    crops = Crop.find_by_user(user_id)
    return jsonify({"success": True, "crops": [c.to_dict() for c in crops]})

@crops_bp.route("/api/crops", methods=["POST"])
@login_required
def add_crop():
    data = request.get_json()
    user_id = session.get("user_id")
    lang = session.get("lang", "en")

    required = ["crop_name", "district", "soil_type", "land_size"]
    for field in required:
        if not data.get(field):
            msg = f"{field} is required."
            return jsonify({"success": False, "message": msg})

    crop = Crop()
    crop.user_id = user_id
    crop.crop_name = data["crop_name"]
    crop.district = data["district"]
    crop.village = data.get("village", "")
    crop.soil_type = data["soil_type"]
    crop.land_size = float(data["land_size"])
    crop.planting_date = data.get("planting_date", "")
    crop.harvest_date = data.get("harvest_date", "")
    crop.status = data.get("status", "active")
    crop.save()

    msg = "Crop added successfully!" if lang == "en" else "பயிர் வெற்றிகரமாக சேர்க்கப்பட்டது!"
    return jsonify({"success": True, "message": msg})

@crops_bp.route("/api/crops/<crop_id>", methods=["PUT"])
@login_required
def update_crop(crop_id):
    data = request.get_json()
    lang = session.get("lang", "en")

    crop = Crop.find_by_id(crop_id)
    if not crop:
        msg = "Crop not found." if lang == "en" else "பயிர் கிடைக்கவில்லை."
        return jsonify({"success": False, "message": msg})

    update_data = {}
    for field in ["crop_name", "district", "village", "soil_type", "status", "planting_date", "harvest_date"]:
        if field in data:
            update_data[field] = data[field]
    if "land_size" in data:
        update_data["land_size"] = float(data["land_size"])

    crop.update(update_data)
    msg = "Crop updated successfully!" if lang == "en" else "பயிர் வெற்றிகரமாக புதுப்பிக்கப்பட்டது!"
    return jsonify({"success": True, "message": msg})

@crops_bp.route("/api/crops/<crop_id>", methods=["DELETE"])
@login_required
def delete_crop(crop_id):
    lang = session.get("lang", "en")
    crop = Crop.find_by_id(crop_id)
    if not crop:
        msg = "Crop not found." if lang == "en" else "பயிர் கிடைக்கவில்லை."
        return jsonify({"success": False, "message": msg})
    crop.delete()
    msg = "Crop deleted successfully!" if lang == "en" else "பயிர் வெற்றிகரமாக நீக்கப்பட்டது!"
    return jsonify({"success": True, "message": msg})
