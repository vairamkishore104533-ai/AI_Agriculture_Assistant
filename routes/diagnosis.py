from flask import Blueprint, render_template, request, jsonify, session
from utils.auth import login_required
from models.diagnosis import Diagnosis
from utils.helpers import get_districts
from datetime import datetime
import traceback

diagnosis_bp = Blueprint("diagnosis", __name__)

CROPS = [
    "Paddy", "Banana", "Sugarcane", "Cotton", "Groundnut", "Coconut",
    "Turmeric", "Maize", "Tomato", "Brinjal", "Chilli", "Onion",
    "Millets", "Black Gram", "Green Gram", "Mango", "Tapioca",
    "Sunflower", "Sesame", "Horse Gram", "Red Gram", "Cashew",
    "Papaya", "Guava", "Okra", "Cabbage", "Cauliflower", "Carrot",
    "Beans", "Drumstick", "Watermelon", "Pumpkin"
]

CROPS_TA = [
    "நெல்", "வாழை", "கரும்பு", "பருத்தி", "வேர்க்கடலை", "தேங்காய்",
    "மஞ்சள்", "சோளம்", "தக்காளி", "கத்திரி", "மிளகாய்", "வெங்காயம்",
    "சிறுதானியங்கள்", "உளுந்து", "பச்சைப்பயறு", "மாம்பழம்", "மரவள்ளி",
    "சூரியகாந்தி", "எள்", "கொள்ளு", "துவரை", "முந்திரி",
    "பப்பாளி", "கொய்யா", "வெண்டை", "முட்டைகோஸ்", "காலிஃபிளவர்", "கேரட்",
    "பீன்ஸ்", "முருங்கை", "தர்பூசணி", "பூசணி"
]

SYMPTOMS = {
    "Paddy": [
        "Yellowing of leaves", "Brown spots on leaves", "Wilting seedlings",
        "White earheads", "Empty grains", "Stunted growth",
        "Leaf blast lesions", "Neck blast", "Brown leaf edges",
        "Rotting roots", "Discolored stems", "Leaf curling",
        "Water-soaked lesions", "Orange-colored spores", "Grain discoloration"
    ],
    "Banana": [
        "Yellow leaves", "Black dots on leaves", "Brown leaf edges",
        "Wilting", "Root rot", "Fruit spots",
        "Stem discoloration", "Curling leaves", "Dry leaf margins",
        "Pseudostem splitting", "Leaf freckling", "Bunchy top",
        "Narrow leaves", "Fruit cracking", "Premature ripening"
    ],
    "Sugarcane": [
        "Yellow leaves", "Stunted growth", "Narrow yellow stripes on leaves",
        "Red rotting inside stem", "Wilting leaves", "Pithy stems",
        "White fluffy growth on stems", "Leaf spots", "Poor juice quality",
        "Cracked stems", "Dead hearts", "Gum formation on stems",
        "Chlorotic leaves", "Root stunting", "Leaf drying from tip"
    ],
    "Cotton": [
        "Yellow leaves", "Leaf curling", "Wilting", "Boll rot",
        "Leaf spots", "Stunted growth", "Reddening of leaves",
        "Shedding of squares", "Boll shedding", "Stem cankers",
        "Whitefly infestation", "Pink boll damage", "Leaf crinkling",
        "Necrotic spots", "Root rot"
    ],
    "Groundnut": [
        "Yellow leaves", "Leaf spots", "Wilting", "Stunted growth",
        "Root rot", "Pod rot", "Leaf curling",
        "Chlorosis", "Stem rot", "Necrotic spots",
        "Leaf drying", "Poor pod formation", "Premature defoliation",
        "Bacterial wilt", "Collar rot"
    ],
    "Coconut": [
        "Yellow leaves", "Leaf fall", "Crown rot", "Nut fall",
        "Stunted growth", "Chlorosis", "Wilt",
        "Bud rot", "Stem bleeding", "Leaf blight",
        "Root wilt", "Tapering trunk", "Reduced nut yield",
        "Leaf spot", "Inflorescence drying"
    ],
    "Turmeric": [
        "Yellow leaves", "Leaf curling", "Rhizome rot", "Leaf spots",
        "Stunted growth", "Wilting", "Chlorosis",
        "Leaf blight", "Root rot", "Necrotic lesions",
        "Poor rhizome formation", "Shoot borer damage", "Leaf drying",
        "Bacterial soft rot", "Dry rot"
    ],
    "Maize": [
        "Yellow leaves", "Leaf spots", "Stunted growth", "Ear rot",
        "Wilting", "Chlorosis", "Leaf blight",
        "Stem rot", "Poor grain filling", "Leaf curling",
        "Downy mildew", "Rust pustules", "Cob discoloration",
        "Stalk lodging", "Seed rot"
    ],
    "Tomato": [
        "Yellow leaves", "Leaf spots", "Wilting", "Fruit rot",
        "Blossom end rot", "Leaf curling", "Stunted growth",
        "Blight", "Powdery mildew", "Fruit cracking",
        "Stem cankers", "Root knot", "Leaf yellowing",
        "Necrotic spots", "Bacterial spots"
    ],
    "Brinjal": [
        "Yellow leaves", "Leaf spots", "Fruit rot", "Wilting",
        "Stunted growth", "Leaf curling", "Powdery mildew",
        "Shoot borer damage", "Fruit borer damage", "Root rot",
        "Bacterial wilt", "Necrotic spots", "Mosaic pattern on leaves",
        "Little leaf", "Damping off"
    ],
    "Chilli": [
        "Yellow leaves", "Leaf curling", "Fruit rot", "Powdery mildew",
        "Wilting", "Leaf spots", "Stunted growth",
        "Mosaic pattern", "Fruit discoloration", "Dieback",
        "Anthracnose lesions", "Root rot", "Bacterial leaf spot",
        "Thrips damage", "Mite damage"
    ],
    "Onion": [
        "Yellow leaves", "Bulb rot", "Leaf blight", "Wilting",
        "Stunted growth", "Downy mildew", "Purple blotch",
        "Root rot", "Neck rot", "Leaf curling",
        "Thrips damage", "Bacterial soft rot", "White rot",
        "Necrotic spots", "Poor bulb formation"
    ],
    "Millets": [
        "Yellow leaves", "Leaf spots", "Stunted growth", "Grain discoloration",
        "Wilting", "Chlorosis", "Leaf blight",
        "Head smut", "Ergot", "Rust",
        "Downy mildew", "Leaf drying", "Neck blast",
        "Root rot", "Poor panicle formation"
    ],
    "Black Gram": [
        "Yellow leaves", "Leaf spots", "Wilting", "Root rot",
        "Stunted growth", "Powdery mildew", "Leaf curling",
        "Rust", "Blight", "Mosaic pattern",
        "Necrotic spots", "Pod rot", "Premature defoliation",
        "Collar rot", "Stem necrosis"
    ],
    "Green Gram": [
        "Yellow leaves", "Leaf spots", "Wilting", "Root rot",
        "Stunted growth", "Powdery mildew", "Leaf curling",
        "Yellow mosaic", "Blight", "Pod borer damage",
        "Necrotic spots", "Premature defoliation", "Rust",
        "Cercospora leaf spot", "Stem rot"
    ],
    "Mango": [
        "Yellow leaves", "Leaf spots", "Fruit rot", "Powdery mildew",
        "Anthracnose", "Wilt", "Black spots on fruit",
        "Leaf blight", "Stem cankers", "Dieback",
        "Mango malformation", "Sooty mold", "Bacterial canker",
        "Fruit fly damage", "Hopper damage"
    ],
    "Tapioca": [
        "Yellow leaves", "Leaf spots", "Root rot", "Stunted growth",
        "Wilting", "Mosaic pattern", "Chlorosis",
        "Leaf blight", "Stem rot", "Brown leaf spots",
        "Poor tuber formation", "Cercospora leaf spot", "Bacterial blight",
        "Cassava green mite damage", "Whitefly infestation"
    ],
    "Sunflower": [
        "Yellow leaves", "Leaf spots", "Wilting", "Head rot",
        "Stunted growth", "Powdery mildew", "Rust",
        "Downy mildew", "Stem rot", "Leaf blight",
        "Sclerotinia rot", "Necrotic spots", "Poor seed set",
        "Alternaria blight", "Root rot"
    ],
    "Sesame": [
        "Yellow leaves", "Leaf spots", "Wilting", "Stunted growth",
        "Leaf curling", "Blight", "Capsule rot",
        "Root rot", "Powdery mildew", "Phyllody",
        "Necrotic spots", "Bacterial leaf spot", "Premature defoliation",
        "Stem rot", "Poor seed formation"
    ],
    "Horse Gram": [
        "Yellow leaves", "Leaf spots", "Wilting", "Stunted growth",
        "Powdery mildew", "Root rot", "Leaf curling",
        "Rust", "Blight", "Necrotic spots",
        "Pod rot", "Premature defoliation", "Stem necrosis"
    ],
    "Red Gram": [
        "Yellow leaves", "Leaf spots", "Wilting", "Stunted growth",
        "Pod borer damage", "Powdery mildew", "Leaf curling",
        "Blight", "Sterility mosaic", "Root rot",
        "Necrotic spots", "Alternaria blight", "Phytophthora blight",
        "Cercospora leaf spot", "Stem cankers"
    ],
    "Cashew": [
        "Yellow leaves", "Leaf spots", "Dieback", "Fruit rot",
        "Powdery mildew", "Wilt", "Leaf blight",
        "Stem cankers", "Anthracnose", "Root rot",
        "Tea mosquito damage", "Leaf miner damage", "Nut shedding",
        "Inflorescence blight", "Stem borer damage"
    ],
    "Papaya": [
        "Yellow leaves", "Leaf spots", "Fruit rot", "Wilting",
        "Mosaic pattern", "Ring spot", "Stunted growth",
        "Leaf curling", "Root rot", "Stem cankers",
        "Powdery mildew", "Anthracnose", "Fruit cracking",
        "Papaya mealybug", "Necrotic spots"
    ],
    "Guava": [
        "Yellow leaves", "Leaf spots", "Fruit rot", "Wilt",
        "Powdery mildew", "Anthracnose", "Stem cankers",
        "Bark peeling", "Root rot", "Fruit fly damage",
        "Bacterial canker", "Necrotic spots", "Leaf blight",
        "Algal leaf spot", "Stunted growth"
    ],
    "Okra": [
        "Yellow leaves", "Leaf spots", "Fruit rot", "Wilting",
        "Leaf curling", "Yellow vein mosaic", "Stunted growth",
        "Powdery mildew", "Root rot", "Borer damage",
        "Necrotic spots", "Bacterial leaf spot", "Fruit borer damage",
        "Jassid damage", "Mite damage"
    ],
    "Cabbage": [
        "Yellow leaves", "Leaf spots", "Head rot", "Wilting",
        "Downy mildew", "Black rot", "Club root",
        "Leaf curling", "Stunted growth", "Root rot",
        "Diamondback moth damage", "Aphid infestation", "Necrotic spots",
        "Alternaria leaf spot", "Damping off"
    ],
    "Cauliflower": [
        "Yellow leaves", "Leaf spots", "Curd rot", "Wilting",
        "Downy mildew", "Black rot", "Stunted growth",
        "Leaf curling", "Root rot", "Club root",
        "Diamondback moth damage", "Poor curd formation", "Aphid infestation",
        "Alternaria leaf spot", "Necrotic spots"
    ],
    "Carrot": [
        "Yellow leaves", "Leaf spots", "Root rot", "Wilting",
        "Stunted growth", "Powdery mildew", "Leaf blight",
        "Necrotic spots", "Cavity spot", "Forked roots",
        "Alternaria blight", "Root cracking", "Aphid infestation",
        "Bacterial soft rot", "Damping off"
    ],
    "Beans": [
        "Yellow leaves", "Leaf spots", "Pod rot", "Wilting",
        "Powdery mildew", "Rust", "Stunted growth",
        "Leaf curling", "Root rot", "Blight",
        "Anthracnose", "Necrotic spots", "Mosaic pattern",
        "Bacterial leaf spot", "Premature defoliation"
    ],
    "Drumstick": [
        "Yellow leaves", "Leaf spots", "Wilt", "Stunted growth",
        "Powdery mildew", "Root rot", "Leaf blight",
        "Stem cankers", "Dieback", "Necrotic spots",
        "Fruit rot", "Aphid infestation", "Leaf curling",
        "Bacterial leaf spot", "Caterpillar damage"
    ],
    "Watermelon": [
        "Yellow leaves", "Leaf spots", "Fruit rot", "Wilting",
        "Powdery mildew", "Downy mildew", "Stunted growth",
        "Leaf curling", "Anthracnose", "Root rot",
        "Fusarium wilt", "Gummy stem blight", "Necrotic spots",
        "Blossom end rot", "Aphid infestation"
    ],
    "Pumpkin": [
        "Yellow leaves", "Leaf spots", "Fruit rot", "Wilting",
        "Powdery mildew", "Downy mildew", "Stunted growth",
        "Leaf curling", "Root rot", "Vine borer damage",
        "Anthracnose", "Necrotic spots", "Bacterial wilt",
        "Blossom end rot", "Alternaria leaf spot"
    ],
}


@diagnosis_bp.route("/crop-diagnosis", methods=["GET"])
@login_required
def index():
    lang = session.get("lang", "en")
    user_id = session.get("user_id")
    stats = Diagnosis.get_stats(user_id)
    diseases_list = Diagnosis.find_by_user(user_id)
    from models.crop import Crop
    crops_db = Crop.find_by_user(user_id)
    # Consider live crops as ones that aren't harvested or completed/cancelled
    live_crops = [c.to_dict() for c in crops_db if c.status.lower() not in ["harvested", "cancelled", "completed"]]
    
    return render_template(
        "crop_diagnosis.html",
        crops=CROPS,
        live_crops=live_crops,
        districts=get_districts(),
        stats=stats,
        diseases=[d.to_dict() for d in diseases_list],
        lang=lang,
    )


@diagnosis_bp.route("/api/diagnosis/crops", methods=["GET"])
@login_required
def get_crops():
    lang = session.get("lang", "en")
    crops_list = []
    for i, c in enumerate(CROPS):
        crops_list.append({"en": c, "ta": CROPS_TA[i] if i < len(CROPS_TA) else c})
    return jsonify({"success": True, "crops": crops_list})


@diagnosis_bp.route("/api/diagnosis/symptoms/<crop>", methods=["GET"])
@login_required
def get_symptoms(crop):
    lang = session.get("lang", "en")
    symptoms = SYMPTOMS.get(crop, SYMPTOMS.get(crop.title(), []))
    return jsonify({"success": True, "symptoms": symptoms})


@diagnosis_bp.route("/api/diagnosis/analyze", methods=["POST"])
@login_required
def analyze():
    try:
        data = request.get_json(silent=True)
        if not data:
            print("[Diagnosis] ERROR: Invalid JSON in request body")
            return jsonify({"success": False, "error": "Invalid JSON in request body", "message": "Request must be valid JSON."}), 400

        crop = data.get("crop", "").strip()
        symptoms = data.get("symptoms", [])
        district = data.get("district", session.get("district", ""))
        lang = session.get("lang", "en")

        print(f"[Diagnosis] Received diagnosis request — crop: '{crop}', symptoms: {len(symptoms)}, district: '{district}', lang: '{lang}'")

        if not crop:
            msg = "Please select a crop." if lang == "en" else "தயவுசெய்து ஒரு பயிரைத் தேர்ந்தெடுக்கவும்."
            print(f"[Diagnosis] Validation error: no crop")
            return jsonify({"success": False, "error": msg, "message": msg}), 400

        if not symptoms or len(symptoms) == 0:
            msg = "Please select at least one symptom." if lang == "en" else "தயவுசெய்து குறைந்தது ஒரு அறிகுறியையாவது தேர்ந்தெடுக்கவும்."
            print(f"[Diagnosis] Validation error: no symptoms")
            return jsonify({"success": False, "error": msg, "message": msg}), 400

        print(f"[Diagnosis] Validated input — calling Groq API...")

        from services.ai_service import AIService
        import json
        import re

        def get_prompt(missing_keys=None, previous_response=None):
            req_format = """{
  "disease": "",
  "confidence": "High/Medium/Low",
  "description": "",
  "severity": "Low/Medium/High/Critical",
  "causes": "",
  "spread": "",
  "treatment_immediate": "",
  "treatment_organic": "",
  "treatment_chemical": "",
  "prevention": "",
  "emergency": "",
  "related_diseases": "",
  "recovery_time": "",
  "success_rate": ""
}"""
            if lang == "ta":
                base = (
                    f"நீங்கள் தமிழ்நாட்டின் முன்னணி விவசாய நோய் கண்டறியும் நிபுணர்.\n\n"
                    f"பயிர்: {crop}\n"
                    f"தேர்ந்தெடுக்கப்பட்ட அறிகுறிகள்: {', '.join(symptoms)}\n"
                    f"மாவட்டம்: {district}\n\n"
                    f"கண்டிப்பான விதி: நீங்கள் ஒரு சரியான JSON வடிவத்தில் மட்டுமே பதிலளிக்க வேண்டும். எந்தவொரு markdown குறிச்சொற்களையும் (```json) பயன்படுத்த வேண்டாம்.\n"
                    f"அனைத்து புலங்களும் கட்டாயமானவை. எந்த புலத்தையும் காலியாக விடக்கூடாது. உண்மையான, பயிர் சார்ந்த தகவல்களை வழங்கவும்.\n"
                    f"JSON வடிவம் இதோ:\n{req_format}\n"
                )
            else:
                base = (
                    f"You are a leading agricultural crop disease diagnosis expert for Tamil Nadu, India.\n\n"
                    f"Crop: {crop}\n"
                    f"Selected Symptoms: {', '.join(symptoms)}\n"
                    f"District: {district}\n\n"
                    f"STRICT RULE: You MUST respond ONLY with valid JSON. Do NOT wrap the JSON in markdown blocks like ```json.\n"
                    f"EVERY field is mandatory. Never return null, empty string, or placeholder values. Provide actual, disease-specific information for every field.\n"
                    f"Use this exact JSON schema:\n{req_format}\n"
                )
            
            if missing_keys and previous_response:
                retry_msg = f"\n\nYour previous response was incomplete. The following fields were missing or empty: {', '.join(missing_keys)}.\nPlease provide a complete JSON response filling in ALL fields including the missing ones. Here was your previous response:\n{previous_response}"
                return base + retry_msg
            return base

        ai = AIService()
        max_retries = 2
        
        required_keys = [
            "disease", "confidence", "description", "severity",
            "causes", "spread", "treatment_immediate", "treatment_organic",
            "treatment_chemical", "prevention", "emergency", "related_diseases",
            "recovery_time", "success_rate"
        ]
        
        result = None
        raw_response = ""
        
        for attempt in range(max_retries + 1):
            if attempt == 0:
                prompt = get_prompt()
            else:
                prompt = get_prompt(missing_keys, raw_response)
                
            print(f"[Diagnosis] Calling Groq (Attempt {attempt+1}/{max_retries+1})...")
            response = ai.get_response(prompt, lang)
            raw_response = response
            
            # Try to parse JSON
            try:
                # Strip markdown json blocks if AI included them despite instructions
                json_str = response.strip()
                if json_str.startswith("```json"):
                    json_str = json_str[7:]
                if json_str.startswith("```"):
                    json_str = json_str[3:]
                if json_str.endswith("```"):
                    json_str = json_str[:-3]
                json_str = json_str.strip()
                
                # Extract json object if there's leading/trailing text
                start_brace = json_str.find('{')
                end_brace = json_str.rfind('}')
                if start_brace != -1 and end_brace != -1:
                    json_str = json_str[start_brace:end_brace+1]
                
                parsed_json = json.loads(json_str)
                
                missing_keys = []
                for k in required_keys:
                    val = parsed_json.get(k)
                    if val is None or str(val).strip() in ["", "[]", "null", "None", "-", "N/A"]:
                        if k != "emergency": # Allow emergency to be empty if they really want
                            missing_keys.append(k)
                
                if not missing_keys:
                    # Success!
                    result = parsed_json
                    break
                else:
                    print(f"[Diagnosis] Attempt {attempt+1} missing keys: {missing_keys}")
                    if attempt == max_retries:
                        result = parsed_json
                        break
            except Exception as e:
                print(f"[Diagnosis] JSON parse failed on attempt {attempt+1}: {e}")
                if attempt == max_retries:
                    # Fallback on final failure
                    pass
        
        if not result or not result.get("disease"):
            print(f"[Diagnosis] No disease parsed from Groq response, using fallback.")
            return jsonify({
                "success": True,
                "result": None,
                "diagnosis": raw_response,
                "fallback": False,
            })
            
        # Clean up values to ensure no '-' or empty strings in final result
        for k in required_keys:
            if not result.get(k) or str(result[k]).strip() in ["", "-", "N/A", "None", "null", "[]"]:
                if k == "emergency":
                    result[k] = ""
                else:
                    result[k] = "Specific information unavailable, consult local agricultural extension officer."
                
        # Handle stringification for UI
        for k in required_keys:
            if isinstance(result[k], list):
                result[k] = ", ".join(result[k])

        print(f"[Diagnosis] Parsed result — disease: '{result.get('disease')}', severity: '{result.get('severity')}', confidence: '{result.get('confidence')}'")

        return jsonify({"success": True, "result": result, "diagnosis": raw_response, "fallback": False})

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"[Diagnosis Error] analyze EXCEPTION: {tb}")
        try:
            lang = session.get("lang", "en")
        except Exception:
            lang = "en"
        msg = f"Server error: {type(e).__name__}: {str(e)}"
        return jsonify({"success": False, "error": msg, "message": msg}), 500


@diagnosis_bp.route("/api/diagnosis/save", methods=["POST"])
@login_required
def save_diagnosis():
    try:
        data = request.get_json()
        user_id = session.get("user_id")
        lang = session.get("lang", "en")

        d = Diagnosis()
        d.user_id = user_id
        d.crop = data.get("crop", "")
        d.symptoms = data.get("symptoms", [])
        d.disease = data.get("disease", "")
        d.severity = data.get("severity", "Medium")
        d.confidence = data.get("confidence", "Medium")
        d.description = data.get("description", "")
        d.causes = data.get("causes", "")
        d.spread = data.get("spread", "")
        d.treatment_immediate = data.get("treatment_immediate", "")
        d.treatment_organic = data.get("treatment_organic", "")
        d.treatment_chemical = data.get("treatment_chemical", "")
        d.prevention = data.get("prevention", "")
        d.emergency = data.get("emergency", "")
        d.related_diseases = data.get("related_diseases", "")
        d.recovery_time = data.get("recovery_time", "")
        d.success_rate = data.get("success_rate", "")
        d.district = data.get("district", session.get("district", ""))
        d.diagnosis = data.get("diagnosis", "")
        d.save()

        msg = "Diagnosis saved successfully!" if lang == "en" else "நோய் கண்டறிதல் வெற்றிகரமாக சேமிக்கப்பட்டது!"
        return jsonify({"success": True, "message": msg})
    except Exception as e:
        print(f"[Diagnosis Error] save: {traceback.format_exc()}")
        return jsonify({"success": False, "message": "Failed to save diagnosis"}), 500


@diagnosis_bp.route("/api/diagnosis/history", methods=["GET"])
@login_required
def get_history():
    try:
        user_id = session.get("user_id")
        search_q = request.args.get("search", "").strip()
        if search_q:
            diseases = Diagnosis.search_by_user(user_id, search_q)
        else:
            diseases = Diagnosis.find_by_user(user_id)
        return jsonify({"success": True, "diagnoses": [d.to_dict() for d in diseases]})
    except Exception as e:
        print(f"[Diagnosis Error] history: {traceback.format_exc()}")
        return jsonify({"success": False, "message": "Failed to load history"}), 500


@diagnosis_bp.route("/api/diagnosis/<diag_id>", methods=["DELETE"])
@login_required
def delete_diagnosis(diag_id):
    try:
        lang = session.get("lang", "en")
        d = Diagnosis.find_by_id(diag_id)
        if not d:
            msg = "Diagnosis not found." if lang == "en" else "நோய் கண்டறிதல் கிடைக்கவில்லை."
            return jsonify({"success": False, "message": msg})
        d.delete()
        stats = Diagnosis.get_stats(session.get("user_id"))
        msg = "Diagnosis deleted successfully!" if lang == "en" else "நோய் கண்டறிதல் வெற்றிகரமாக நீக்கப்பட்டது!"
        return jsonify({"success": True, "message": msg, "stats": stats})
    except Exception as e:
        print(f"[Diagnosis Error] delete: {traceback.format_exc()}")
        return jsonify({"success": False, "message": "Failed to delete"}), 500


@diagnosis_bp.route("/api/diagnosis/stats", methods=["GET"])
@login_required
def get_stats():
    user_id = session.get("user_id")
    stats = Diagnosis.get_stats(user_id)
    return jsonify({"success": True, "stats": stats})


@diagnosis_bp.route("/api/diagnosis/export/<diag_id>", methods=["GET"])
@login_required
def export_diagnosis(diag_id):
    try:
        lang = session.get("lang", "en")
        d = Diagnosis.find_by_id(diag_id)
        if not d:
            msg = "Diagnosis not found." if lang == "en" else "நோய் கண்டறிதல் கிடைக்கவில்லை."
            return jsonify({"success": False, "message": msg})
        fmt = request.args.get("format", "txt")
        username = session.get("username", "Farmer")

        lines = []
        if lang == "en":
            lines.append("CROP DIAGNOSIS REPORT")
            lines.append("=" * 50)
            lines.append(f"Farmer: {username}")
            lines.append(f"Crop: {d.crop}")
            lines.append(f"District: {d.district or 'N/A'}")
            lines.append(f"Date: {d.created_at.strftime('%Y-%m-%d %H:%M')}")
            lines.append(f"Symptoms: {', '.join(d.symptoms)}")
            lines.append("")
            lines.append(f"Disease: {d.disease}")
            lines.append(f"Confidence: {d.confidence}")
            lines.append(f"Severity: {d.severity}")
            lines.append(f"Description: {d.description}")
            lines.append(f"Causes: {d.causes}")
            lines.append(f"Spread: {d.spread}")
            lines.append("")
            lines.append("TREATMENT")
            lines.append("-" * 50)
            lines.append(f"Immediate Actions: {d.treatment_immediate}")
            lines.append(f"Organic Treatment: {d.treatment_organic}")
            lines.append(f"Chemical Treatment: {d.treatment_chemical}")
            lines.append(f"Prevention: {d.prevention}")
            lines.append("")
            lines.append("EMERGENCY ACTIONS")
            lines.append("-" * 50)
            lines.append(d.emergency or "None")
            lines.append("")
            lines.append(f"Related Diseases: {d.related_diseases}")
            lines.append(f"Recovery Time: {d.recovery_time}")
            lines.append(f"Success Rate: {d.success_rate}")
        else:
            lines.append("பயிர் நோய் கண்டறிதல் அறிக்கை")
            lines.append("=" * 50)
            lines.append(f"விவசாயி: {username}")
            lines.append(f"பயிர்: {d.crop}")
            lines.append(f"மாவட்டம்: {d.district or 'இல்லை'}")
            lines.append(f"தேதி: {d.created_at.strftime('%Y-%m-%d %H:%M')}")
            lines.append(f"அறிகுறிகள்: {', '.join(d.symptoms)}")
            lines.append("")
            lines.append(f"நோய்: {d.disease}")
            lines.append(f"நம்பிக்கை: {d.confidence}")
            lines.append(f"தீவிரம்: {d.severity}")
            lines.append(f"விளக்கம்: {d.description}")
            lines.append(f"காரணங்கள்: {d.causes}")
            lines.append(f"பரவல்: {d.spread}")
            lines.append("")
            lines.append("சிகிச்சை")
            lines.append("-" * 50)
            lines.append(f"உடனடி நடவடிக்கைகள்: {d.treatment_immediate}")
            lines.append(f"இயற்கை சிகிச்சை: {d.treatment_organic}")
            lines.append(f"இரசாயன சிகிச்சை: {d.treatment_chemical}")
            lines.append(f"தடுப்பு: {d.prevention}")
            lines.append("")
            lines.append("அவசர நடவடிக்கைகள்")
            lines.append("-" * 50)
            lines.append(d.emergency or "எதுவும் இல்லை")
            lines.append("")
            lines.append(f"தொடர்புடைய நோய்கள்: {d.related_diseases}")
            lines.append(f"மீட்பு நேரம்: {d.recovery_time}")
            lines.append(f"வெற்றி விகிதம்: {d.success_rate}")

        text_content = "\n".join(lines)

        if fmt == "pdf":
            from fpdf import FPDF
            from fpdf.enums import XPos, YPos
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_font("Arial", "", r"C:\Windows\Fonts\arial.ttf")
            pdf.add_font("Arial", "B", r"C:\Windows\Fonts\arialbd.ttf")
            pdf.set_font("Arial", "B", 16)
            title = "Crop Diagnosis Report" if lang == "en" else "பயிர் நோய் கண்டறிதல் அறிக்கை"
            pdf.cell(0, 10, text=title, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
            pdf.set_font("Arial", "", 10)
            for line in text_content.split("\n"):
                pdf.set_x(pdf.l_margin)
                if line.startswith("=") or line.startswith("-"):
                    pdf.set_font("Arial", "", 10)
                elif any(line.startswith(x) for x in ["CROP", "பயிர்", "TREATMENT", "EMERGENCY", "சிகிச்சை", "அவசர"]):
                    pdf.set_font("Arial", "B", 11)
                else:
                    pdf.set_font("Arial", "", 10)
                w = pdf.get_string_width(line) + 2
                if w > 190:
                    pdf.multi_cell(0, 5, text=line)
                else:
                    pdf.cell(0, 5, text=line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            output = bytes(pdf.output())
            import base64
            return jsonify({
                "success": True,
                "export": base64.b64encode(output).decode("ascii"),
                "filename": f"diagnosis_{diag_id[:8]}.pdf",
                "mime": "application/pdf",
                "encoding": "base64",
            })
        else:
            return jsonify({
                "success": True,
                "export": text_content,
                "filename": f"diagnosis_{diag_id[:8]}.txt",
                "mime": "text/plain",
            })
    except Exception as e:
        print(f"[Diagnosis Error] export: {traceback.format_exc()}")
        return jsonify({"success": False, "message": "Failed to export"}), 500
