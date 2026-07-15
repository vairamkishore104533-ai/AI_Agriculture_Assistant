from flask import Blueprint, render_template, request, jsonify, session
from utils.auth import login_required
from models.fertilizer import Fertilizer
from utils.helpers import get_districts
from datetime import datetime
import traceback

fertilizer_bp = Blueprint("fertilizer", __name__)

SEASONS = [
    {"id": "kuruvai", "en": "Kuruvai", "ta": "குறுவை", "desc_en": "June–September. Short-term paddy cultivation.", "desc_ta": "ஜூன்–செப்டம்பர். குறுகிய கால நெல் சாகுபடி."},
    {"id": "samba", "en": "Samba", "ta": "சம்பா", "desc_en": "August–January. Long-duration paddy season.", "desc_ta": "ஆகஸ்ட்–ஜனவரி. நீண்ட கால நெல் பருவம்."},
    {"id": "thaladi", "en": "Thaladi", "ta": "தாளடி", "desc_en": "September–February. Late paddy season.", "desc_ta": "செப்டம்பர்–பிப்ரவரி. தாமதமான நெல் பருவம்."},
    {"id": "navarai", "en": "Navarai", "ta": "நவரை", "desc_en": "December–March. Summer paddy season.", "desc_ta": "டிசம்பர்–மார்ச். கோடை நெல் பருவம்."},
    {"id": "summer", "en": "Summer", "ta": "கோடை", "desc_en": "March–June. Suitable for vegetables and pulses.", "desc_ta": "மார்ச்–ஜூன். காய்கறிகள் மற்றும் பயறு வகைகளுக்கு ஏற்றது."},
    {"id": "rainy", "en": "Rainy Season", "ta": "மழைக்காலம்", "desc_en": "October–December. North-east monsoon period.", "desc_ta": "அக்டோபர்–டிசம்பர். வடகிழக்கு பருவமழை காலம்."},
    {"id": "winter", "en": "Winter", "ta": "குளிர்காலம்", "desc_en": "January–February. Suitable for cool-season crops.", "desc_ta": "ஜனவரி–பிப்ரவரி. குளிர்கால பயிர்களுக்கு ஏற்றது."},
    {"id": "custom", "en": "Custom Season", "ta": "தனிப்பயன் பருவம்", "desc_en": "Specify your own season.", "desc_ta": "உங்கள் சொந்த பருவத்தைக் குறிப்பிடவும்."},
]

CROPS = [
    "Paddy", "Banana", "Sugarcane", "Cotton", "Groundnut", "Coconut",
    "Turmeric", "Maize", "Tomato", "Brinjal", "Chilli", "Onion",
    "Millets", "Black Gram", "Green Gram", "Mango", "Tapioca",
    "Sunflower", "Sesame", "Horse Gram", "Red Gram", "Cashew",
    "Papaya", "Guava", "Okra", "Cabbage", "Cauliflower", "Carrot",
    "Beans", "Drumstick", "Watermelon", "Pumpkin", "Other"
]

CROPS_TA = [
    "நெல்", "வாழை", "கரும்பு", "பருத்தி", "வேர்க்கடலை", "தேங்காய்",
    "மஞ்சள்", "சோளம்", "தக்காளி", "கத்திரி", "மிளகாய்", "வெங்காயம்",
    "சிறுதானியங்கள்", "உளுந்து", "பச்சைப்பயறு", "மாம்பழம்", "மரவள்ளி",
    "சூரியகாந்தி", "எள்", "கொள்ளு", "துவரை", "முந்திரி",
    "பப்பாளி", "கொய்யா", "வெண்டை", "முட்டைகோஸ்", "காலிஃபிளவர்", "கேரட்",
    "பீன்ஸ்", "முருங்கை", "தர்பூசணி", "பூசணி", "மற்றவை"
]

GROWTH_STAGES = [
    {"id": "land_prep", "en": "Land Preparation", "ta": "நிலம் தயாரிப்பு"},
    {"id": "seed_treatment", "en": "Seed Treatment", "ta": "விதை நேர்த்தி"},
    {"id": "nursery", "en": "Nursery Stage", "ta": "நாற்றங்கால் நிலை"},
    {"id": "germination", "en": "Germination", "ta": "முளைப்பு"},
    {"id": "seedling", "en": "Seedling", "ta": "நாற்று நிலை"},
    {"id": "vegetative", "en": "Vegetative Stage", "ta": "தாவர வளர்ச்சி நிலை"},
    {"id": "tillering", "en": "Tillering", "ta": "தூர்க்கும் நிலை"},
    {"id": "flowering", "en": "Flowering", "ta": "பூக்கும் நிலை"},
    {"id": "fruiting", "en": "Fruiting", "ta": "காய்க்கும் நிலை"},
    {"id": "grain_filling", "en": "Grain Filling", "ta": "தானிய நிரப்பும் நிலை"},
    {"id": "maturity", "en": "Maturity", "ta": "முதிர்ச்சி நிலை"},
    {"id": "harvest", "en": "Harvest Stage", "ta": "அறுவடை நிலை"},
]

IRRIGATION_METHODS = [
    {"id": "drip", "en": "Drip Irrigation", "ta": "சொட்டு நீர் பாசனம்"},
    {"id": "flood", "en": "Flood Irrigation", "ta": "வெள்ளப் பாசனம்"},
    {"id": "sprinkler", "en": "Sprinkler Irrigation", "ta": "தெளிப்பு பாசனம்"},
    {"id": "rainfed", "en": "Rainfed Farming", "ta": "மழை சார்ந்த விவசாயம்"},
    {"id": "furrow", "en": "Furrow Irrigation", "ta": "சால் பாசனம்"},
    {"id": "basin", "en": "Basin Irrigation", "ta": "குட்டை பாசனம்"},
    {"id": "manual", "en": "Manual Irrigation", "ta": "கைமுறை பாசனம்"},
    {"id": "other", "en": "Other", "ta": "மற்றவை"},
]

@fertilizer_bp.route("/fertilizer", methods=["GET"])
@login_required
def index():
    lang = session.get("lang", "en")
    user_id = session.get("user_id")
    stats = Fertilizer.get_stats(user_id)
    history = Fertilizer.find_by_user(user_id)
    crop_list = []
    for i, c in enumerate(CROPS):
        crop_list.append({"en": c, "ta": CROPS_TA[i] if i < len(CROPS_TA) else c})
    return render_template(
        "fertilizer.html",
        seasons=SEASONS,
        crops=crop_list,
        growth_stages=GROWTH_STAGES,
        irrigation_methods=IRRIGATION_METHODS,
        districts=get_districts(),
        stats=stats,
        history=[h.to_dict() for h in history],
        lang=lang,
    )

@fertilizer_bp.route("/api/fertilizer/seasons", methods=["GET"])
@login_required
def get_seasons():
    return jsonify({"success": True, "seasons": SEASONS})

@fertilizer_bp.route("/api/fertilizer/crops", methods=["GET"])
@login_required
def get_crops():
    lang = session.get("lang", "en")
    crop_list = []
    for i, c in enumerate(CROPS):
        crop_list.append({"en": c, "ta": CROPS_TA[i] if i < len(CROPS_TA) else c})
    return jsonify({"success": True, "crops": crop_list})

@fertilizer_bp.route("/api/fertilizer/growth-stages", methods=["GET"])
@login_required
def get_growth_stages():
    return jsonify({"success": True, "stages": GROWTH_STAGES})

@fertilizer_bp.route("/api/fertilizer/irrigation-methods", methods=["GET"])
@login_required
def get_irrigation_methods():
    return jsonify({"success": True, "methods": IRRIGATION_METHODS})

@fertilizer_bp.route("/api/fertilizer/recommend", methods=["POST"])
@login_required
def recommend():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "Invalid JSON in request body"}), 400

        season_id = data.get("season", "").strip()
        crop = data.get("crop", "").strip()
        growth_stage_id = data.get("growth_stage", "").strip()
        irrigation_id = data.get("irrigation", "").strip()
        lang = session.get("lang", "en")

        print("Recommendation request received")
        print("Request data:", {k: v for k, v in data.items()})
        print("Calling Groq...")

        if not season_id:
            msg = "Please select an agricultural season." if lang == "en" else "தயவுசெய்து ஒரு விவசாய பருவத்தைத் தேர்ந்தெடுக்கவும்."
            return jsonify({"success": False, "error": msg}), 400
        if not crop:
            msg = "Please select a crop." if lang == "en" else "தயவுசெய்து ஒரு பயிரைத் தேர்ந்தெடுக்கவும்."
            return jsonify({"success": False, "error": msg}), 400
        if not growth_stage_id:
            msg = "Please select a growth stage." if lang == "en" else "தயவுசெய்து ஒரு வளர்ச்சி நிலையைத் தேர்ந்தெடுக்கவும்."
            return jsonify({"success": False, "error": msg}), 400
        if not irrigation_id:
            msg = "Please select an irrigation method." if lang == "en" else "தயவுசெய்து ஒரு நீர்ப்பாசன முறையைத் தேர்ந்தெடுக்கவும்."
            return jsonify({"success": False, "error": msg}), 400

        season_name = season_id
        for s in SEASONS:
            if s["id"] == season_id:
                season_name = s["ta"] if lang == "ta" else s["en"]
                break

        stage_name = growth_stage_id
        for s in GROWTH_STAGES:
            if s["id"] == growth_stage_id:
                stage_name = s["ta"] if lang == "ta" else s["en"]
                break

        irrigation_name = irrigation_id
        for m in IRRIGATION_METHODS:
            if m["id"] == irrigation_id:
                irrigation_name = m["ta"] if lang == "ta" else m["en"]
                break

        district = session.get("district", "")
        print(f"[Fertilizer] Calling AI with: {crop}, {season_name}, {stage_name}, {irrigation_name}")

        from services.ai_service import AIService
        ai = AIService()

        if lang == "ta":
            prompt = (
                f"நீங்கள் தமிழ்நாட்டின் முன்னணி உர பரிந்துரை நிபுணர். பின்வரும் தகவல்களின் அடிப்படையில் முழுமையான உர பரிந்துரையை வழங்கவும்.\n\n"
                f"பயிர்: {crop}\n"
                f"விவசாய பருவம்: {season_name}\n"
                f"வளர்ச்சி நிலை: {stage_name}\n"
                f"நீர்ப்பாசன முறை: {irrigation_name}\n"
                f"மாவட்டம்: {district}\n\n"
                f"பின்வரும் பகுதிகளை உள்ளடக்கிய முழுமையான அறிக்கையை உருவாக்கவும். ஒவ்வொரு பகுதியையும் ## தலைப்புடன் தொடங்கவும்:\n\n"
                f"## பயிர் சுருக்கம்\n"
                f"## பரிந்துரைக்கப்பட்ட உரங்கள்\n"
                f"## உர அட்டவணை\n"
                f"## பயன்பாட்டு முறை\n"
                f"## ஊட்டச்சத்து தேவைகள்\n"
                f"## நீர்ப்பாசன அடிப்படையிலான பரிந்துரைகள்\n"
                f"## பருவகால ஆலோசனைகள்\n"
                f"## கரிம மாற்றுகள்\n"
                f"## பொதுவான விவசாயி தவறுகள்\n"
                f"## செலவு மதிப்பீடு\n"
                f"## பாதுகாப்பு வழிகாட்டுதல்கள்\n"
                f"## அரசு பரிந்துரைகள்\n\n"
                f"தமிழ்நாடு விவசாயப் பல்கலைக்கழகம் மற்றும் தமிழ்நாடு வேளாண்மைத் துறை வழிகாட்டுதல்களைப் பின்பற்றவும். தமிழில் மட்டுமே பதிலளிக்கவும்."
            )
        else:
            prompt = (
                f"You are a leading fertilizer recommendation expert for Tamil Nadu agriculture. Generate a complete fertilizer recommendation based on the following details.\n\n"
                f"Crop: {crop}\n"
                f"Agricultural Season: {season_name}\n"
                f"Growth Stage: {stage_name}\n"
                f"Irrigation Method: {irrigation_name}\n"
                f"District: {district}\n\n"
                f"Generate a comprehensive report covering the following sections. Start each section with ## heading:\n\n"
                f"## Crop Summary\n"
                f"## Recommended Fertilizers\n"
                f"## Fertilizer Schedule\n"
                f"## Application Method\n"
                f"## Nutrient Requirements\n"
                f"## Irrigation-Based Recommendations\n"
                f"## Seasonal Advice\n"
                f"## Organic Alternatives\n"
                f"## Common Farmer Mistakes\n"
                f"## Cost Estimation\n"
                f"## Safety Guidelines\n"
                f"## Government Recommendations\n\n"
                f"Follow Tamil Nadu Agricultural University and Tamil Nadu Agriculture Department guidelines. "
                f"Include specific fertilizer names, quantities per acre, timing, and application methods. "
                f"Reply only in English."
            )

        print(f"[Fertilizer] Prompt ({len(prompt)} chars): {prompt[:200]}...")
        response = ai.get_response(prompt, lang)
        print("Recommendation generated")
        print(f"[Fertilizer] AI response ({len(response)} chars): {response[:200]}...")

        return jsonify({
            "success": True,
            "recommendation": response,
            "metadata": {
                "season": season_name,
                "crop": crop,
                "growth_stage": stage_name,
                "irrigation": irrigation_name,
            }
        })

    except Exception as e:
        print(f"[Fertilizer Error] recommend: {traceback.format_exc()}")
        try:
            lang = session.get("lang", "en")
        except Exception:
            lang = "en"
        msg = f"Server error: {type(e).__name__}: {str(e)}"
        return jsonify({"success": False, "error": msg}), 500

@fertilizer_bp.route("/api/fertilizer/save", methods=["POST"])
@login_required
def save():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "Invalid JSON"}), 400

        user_id = session.get("user_id")
        lang = session.get("lang", "en")

        f = Fertilizer()
        f.user_id = user_id
        f.season = data.get("season", "")
        f.crop = data.get("crop", "")
        f.growth_stage = data.get("growth_stage", "")
        f.irrigation_method = data.get("irrigation_method", "")
        f.recommendation = data.get("recommendation", "")
        f.language = data.get("language", lang)
        f.district = data.get("district", session.get("district", ""))
        f.save()

        print("Saved to MongoDB")
        msg = "Recommendation saved successfully!" if lang == "en" else "பரிந்துரை வெற்றிகரமாக சேமிக்கப்பட்டது!"
        return jsonify({"success": True, "message": msg})

    except Exception as e:
        print(f"[Fertilizer Error] save: {traceback.format_exc()}")
        return jsonify({"success": False, "error": "Failed to save recommendation"}), 500

@fertilizer_bp.route("/api/fertilizer/history", methods=["GET"])
@login_required
def get_history():
    try:
        user_id = session.get("user_id")
        search_q = request.args.get("search", "").strip()
        season_filter = request.args.get("season", "").strip()
        if search_q:
            items = Fertilizer.search_by_user(user_id, search_q)
        elif season_filter:
            items = Fertilizer.find_by_season(user_id, season_filter)
        else:
            items = Fertilizer.find_by_user(user_id)
        return jsonify({"success": True, "history": [h.to_dict() for h in items]})
    except Exception as e:
        print(f"[Fertilizer Error] history: {traceback.format_exc()}")
        return jsonify({"success": False, "error": "Failed to load history"}), 500

@fertilizer_bp.route("/api/fertilizer/<rec_id>", methods=["DELETE"])
@login_required
def delete(rec_id):
    try:
        lang = session.get("lang", "en")
        f = Fertilizer.find_by_id(rec_id)
        if not f:
            msg = "Recommendation not found." if lang == "en" else "பரிந்துரை கிடைக்கவில்லை."
            return jsonify({"success": False, "error": msg})
        f.delete()
        stats = Fertilizer.get_stats(session.get("user_id"))
        msg = "Recommendation deleted successfully!" if lang == "en" else "பரிந்துரை வெற்றிகரமாக நீக்கப்பட்டது!"
        return jsonify({"success": True, "message": msg, "stats": stats})
    except Exception as e:
        print(f"[Fertilizer Error] delete: {traceback.format_exc()}")
        return jsonify({"success": False, "error": "Failed to delete"}), 500

@fertilizer_bp.route("/api/fertilizer/stats", methods=["GET"])
@login_required
def get_stats():
    user_id = session.get("user_id")
    stats = Fertilizer.get_stats(user_id)
    return jsonify({"success": True, "stats": stats})

@fertilizer_bp.route("/api/fertilizer/export/<rec_id>", methods=["GET"])
@login_required
def export(rec_id):
    try:
        lang = session.get("lang", "en")
        f = Fertilizer.find_by_id(rec_id)
        if not f:
            msg = "Recommendation not found." if lang == "en" else "பரிந்துரை கிடைக்கவில்லை."
            return jsonify({"success": False, "error": msg})

        fmt = request.args.get("format", "txt")
        username = session.get("username", "Farmer")
        lines = []
        lines.append("=" * 50)
        lines.append("FERTILIZER RECOMMENDATION REPORT" if lang == "en" else "உர பரிந்துரை அறிக்கை")
        lines.append("=" * 50)
        lines.append(f"Farmer: {username}" if lang == "en" else f"விவசாயி: {username}")
        lines.append(f"Crop: {f.crop}" if lang == "en" else f"பயிர்: {f.crop}")
        lines.append(f"Season: {f.season}" if lang == "en" else f"பருவம்: {f.season}")
        lines.append(f"Growth Stage: {f.growth_stage}" if lang == "en" else f"வளர்ச்சி நிலை: {f.growth_stage}")
        lines.append(f"Irrigation: {f.irrigation_method}" if lang == "en" else f"நீர்ப்பாசனம்: {f.irrigation_method}")
        lines.append(f"Date: {f.created_at.strftime('%Y-%m-%d %H:%M')}" if lang == "en" else f"தேதி: {f.created_at.strftime('%Y-%m-%d %H:%M')}")
        lines.append("")
        lines.append(f.recommendation)

        text_content = "\n".join(lines)

        if fmt == "csv":
            csv_lines = [
                "Field,Value",
                f"Crop,{f.crop}",
                f"Season,{f.season}",
                f"Growth Stage,{f.growth_stage}",
                f"Irrigation Method,{f.irrigation_method}",
                f"Date,{f.created_at.strftime('%Y-%m-%d %H:%M')}",
            ]
            return jsonify({
                "success": True,
                "export": "\n".join(csv_lines),
                "filename": f"fertilizer_{rec_id[:8]}.csv",
                "mime": "text/csv",
            })

        if fmt == "pdf":
            from fpdf import FPDF
            from fpdf.enums import XPos, YPos
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_font("Arial", "", r"C:\Windows\Fonts\arial.ttf")
            pdf.add_font("Arial", "B", r"C:\Windows\Fonts\arialbd.ttf")
            pdf.set_font("Arial", "B", 16)
            title = "Fertilizer Recommendation Report" if lang == "en" else "உர பரிந்துரை அறிக்கை"
            pdf.cell(0, 10, text=title, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
            pdf.set_font("Arial", "", 10)
            for line in text_content.split("\n"):
                pdf.set_x(pdf.l_margin)
                if line.startswith("=") or line.startswith("-"):
                    pdf.set_font("Arial", "", 10)
                elif any(line.startswith(x) for x in ["CROP", "FERTILIZER", "பயிர்", "உர"]):
                    pdf.set_font("Arial", "B", 11)
                else:
                    pdf.set_font("Arial", "", 10)
                w = pdf.get_string_width(line) + 2
                if w > 190:
                    pdf.multi_cell(0, 5, text=line)
                else:
                    pdf.cell(0, 5, text=line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            import base64
            output = bytes(pdf.output())
            return jsonify({
                "success": True,
                "export": base64.b64encode(output).decode("ascii"),
                "filename": f"fertilizer_{rec_id[:8]}.pdf",
                "mime": "application/pdf",
                "encoding": "base64",
            })

        return jsonify({
            "success": True,
            "export": text_content,
            "filename": f"fertilizer_{rec_id[:8]}.txt",
            "mime": "text/plain",
        })

    except Exception as e:
        print(f"[Fertilizer Error] export: {traceback.format_exc()}")
        return jsonify({"success": False, "error": "Failed to export"}), 500
