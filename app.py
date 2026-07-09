import os
import sys
import traceback
from dotenv import load_dotenv
from flask import Flask, render_template, session, request, redirect, url_for, jsonify
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

db = None
try:
    from pymongo import MongoClient
    import certifi
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise Exception("MONGO_URI not set in .env")
    print(f"[INFO] Connecting to MongoDB Atlas (10s timeout)...", file=sys.stderr)
    mongo_client = MongoClient(
        mongo_uri,
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=8000,
        tlsCAFile=certifi.where()
    )
    mongo_client.admin.command("ping")
    db = mongo_client["agriculture_assistant"]
    app.config["MONGO"] = db
    app.config["DB_TYPE"] = "mongodb"
    print("[OK] Connected to MongoDB Atlas - agriculture_assistant database", file=sys.stderr)
    if db["users"].count_documents({"username": "admin"}) == 0:
        from utils.auth import hash_password
        db["users"].insert_one({
            "username": "admin",
            "password": hash_password("admin123"),
            "is_admin": True,
            "preferred_language": "en",
            "created_at": datetime.utcnow(),
            "last_login": datetime.utcnow(),
        })
        print("[INFO] Default admin user created (admin/admin123)", file=sys.stderr)
except Exception as e:
    print(f"[ERROR] MongoDB Atlas connection failed:", file=sys.stderr)
    traceback.print_exc()
    print("[WARN] Attempting direct connection fallback...", file=sys.stderr)
    try:
        mongo_client = MongoClient(
            "mongodb://vk:vkdb@ac-mnzj5ki-shard-00-00.rwxd8tx.mongodb.net:27017,ac-mnzj5ki-shard-00-01.rwxd8tx.mongodb.net:27017,ac-mnzj5ki-shard-00-02.rwxd8tx.mongodb.net:27017/?authSource=admin&replicaSet=atlas-jaoq90-shard-0&tls=true&tlsInsecure=true",
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=8000,
        )
        mongo_client.admin.command("ping")
        db = mongo_client["agriculture_assistant"]
        app.config["MONGO"] = db
        app.config["DB_TYPE"] = "mongodb"
        print("[OK] Connected via direct connection fallback", file=sys.stderr)
    except Exception as e2:
        print(f"[ERROR] All MongoDB Atlas connection attempts failed.", file=sys.stderr)
        traceback.print_exc()
        print("[ERROR] Starting with limited functionality (database unavailable)", file=sys.stderr)
        from bcrypt import hashpw, gensalt
        import uuid
        _admin_pw = hashpw("admin123".encode(), gensalt()).decode("utf-8")
        class _MiniColl:
            def __init__(self):
                self._docs = {}
                self._id_counter = 0
            def _gen_id(self):
                self._id_counter += 1
                return str(uuid.uuid4()).replace("-","")[:24]
            def _matches(self, doc, query):
                if not query: return True
                for k, v in query.items():
                    if isinstance(v, dict):
                        for op, val in v.items():
                            if op == "$gte" and doc.get(k,-1) < val: return False
                            elif op == "$regex":
                                import re
                                if not re.search(val, str(doc.get(k,""))): return False
                            elif op == "$in":
                                if doc.get(k) not in val: return False
                    elif doc.get(k) != v: return False
                return True
            def find_one(self, query):
                for d in self._docs.values():
                    if self._matches(d, query): return dict(d)
                return None
            def find(self, query=None):
                return [dict(d) for d in self._docs.values() if self._matches(d, query or {})]
            def count_documents(self, query=None):
                return sum(1 for _ in self.find(query))
            def insert_one(self, data):
                d = dict(data); d["_id"] = self._gen_id()
                self._docs[d.get("username") or d.get("_id")] = d
                class _Result:
                    inserted_id = d["_id"]
                return _Result()
            def update_one(self, query, update):
                for d in self._docs.values():
                    if self._matches(d, query):
                        for op, val in update.items():
                            if op == "$set": d.update(val)
                            elif op == "$push":
                                for k, v in val.items():
                                    if k not in d: d[k] = []
                                    d[k].append(v)
                        return
            def delete_one(self, query):
                for key in list(self._docs.keys()):
                    if self._matches(self._docs[key], query):
                        del self._docs[key]; return
            def aggregate(self, pipeline=None): return []
            def __getitem__(self, name): return self
        class _MiniDB:
            def __init__(self):
                self._colls = {}
            def __getitem__(self, name):
                if name not in self._colls:
                    self._colls[name] = _MiniColl()
                return self._colls[name]
            def __getattr__(self, name):
                if name.startswith("_"):
                    return super().__getattribute__(name)
                return self[name]
        db = _MiniDB()
        db["users"].insert_one({
            "username": "admin", "password": _admin_pw,
            "is_admin": True, "preferred_language": "en",
            "created_at": datetime.utcnow(), "last_login": datetime.utcnow(),
        })
        app.config["MONGO"] = db
        app.config["DB_TYPE"] = "mock"
        print("[INFO] Admin user seeded (admin/admin123) for offline mode", file=sys.stderr)

app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads")

from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.chatbot import chatbot_bp
from routes.crops import crops_bp
from routes.weather import weather_bp
from routes.market import market_bp
from routes.schemes import schemes_bp
from routes.expenses import expenses_bp
from routes.analytics import analytics_bp
from routes.notifications import notifications_bp
from routes.profile import profile_bp
from routes.admin import admin_bp

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(chatbot_bp)
app.register_blueprint(crops_bp)
app.register_blueprint(weather_bp)
app.register_blueprint(market_bp)
app.register_blueprint(schemes_bp)
app.register_blueprint(expenses_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(notifications_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(admin_bp)

from utils.translations import TRANSLATIONS
from models.notification import Notification

@app.context_processor
def inject_globals():
    lang = session.get("lang", "en")
    unread_count = 0
    if "user_id" in session:
        unread_count = Notification.count_unread(session["user_id"])
    return {
        "lang": lang,
        "t": lambda key: TRANSLATIONS.get(lang, {}).get(key, TRANSLATIONS["en"].get(key, key)),
        "current_year": datetime.now().year,
        "unread_count": unread_count,
        "username": session.get("username", ""),
        "is_admin": session.get("is_admin", False),
    }

@app.route("/")
def index():
    return render_template("index.html", lang=session.get("lang", "en"))

@app.route("/set-language", methods=["POST"])
def set_language():
    data = request.get_json()
    lang = data.get("lang", "en")
    if lang in ["en", "ta"]:
        session["lang"] = lang
    return jsonify({"success": True})

@app.route("/crops")
@app.route("/crop-diagnosis")
@app.route("/fertilizer")
@app.route("/irrigation")
def feature_pages():
    route_map = {
        "/crops": "crops.html",
        "/crop-diagnosis": "crop_diagnosis.html",
        "/fertilizer": "fertilizer.html",
        "/irrigation": "irrigation.html",
    }
    template = route_map.get(request.path, "index.html")
    return render_template(template, lang=session.get("lang", "en"))

@app.route("/api/crop-diagnosis", methods=["POST"])
def crop_diagnosis():
    data = request.get_json()
    crop = data.get("crop", "")
    symptoms = data.get("symptoms", "")
    lang = session.get("lang", "en")

    if not crop or not symptoms:
        msg = "Please select crop and describe symptoms." if lang == "en" else "தயவுசெய்து பயிரைத் தேர்ந்தெடுத்து அறிகுறிகளை விவரிக்கவும்."
        return jsonify({"success": False, "message": msg})

    from services.ai_service import AIService
    ai = AIService()
    if lang == "ta":
        prompt = f"பயிர்: {crop}\nஅறிகுறிகள்: {symptoms}\n\nதயவுசெய்து இந்த அறிகுறிகளின் அடிப்படையில் சாத்தியமான நோய், காரணம், சிகிச்சை, தடுப்பு மற்றும் இயற்கை மாற்றுகளை பின்வரும் வடிவத்தில் வழங்கவும்:\n\nநோய்: \nகாரணம்: \nசிகிச்சை: \nதடுப்பு: \nஇயற்கை மாற்றுகள்:"
    else:
        prompt = f"Crop: {crop}\nSymptoms: {symptoms}\n\nBased on these symptoms, provide the possible disease, cause, treatment, prevention, and organic alternatives in the following format:\n\nDisease: \nCause: \nTreatment: \nPrevention: \nOrganic Alternatives:"

    response = ai.get_response(prompt, lang)

    result = {}
    sections = response.split("\n")
    current_key = None
    for line in sections:
        line = line.strip()
        if not line:
            continue
        for key in ["Disease", "Cause", "Treatment", "Prevention", "Organic", "நோய்", "காரணம்", "சிகிச்சை", "தடுப்பு", "இயற்கை"]:
            if line.startswith(key + ":") or line.startswith(key + " :") or line.startswith(key + " -"):
                colon_idx = line.find(":")
                if colon_idx == -1:
                    colon_idx = line.find(" -")
                if colon_idx > 0:
                    val = line[colon_idx+1:].strip()
                    if lang == "ta":
                        map_key = {"நோய்": "disease", "காரணம்": "cause", "சிகிச்சை": "treatment", "தடுப்பு": "prevention", "இயற்கை": "organic"}.get(key, key.lower())
                    else:
                        map_key = key.lower()
                    result[map_key] = val
                break

    if not result:
        result = {
            "disease": "Analysis based on symptoms",
            "cause": "Further analysis needed",
            "treatment": "Consult local agriculture officer",
            "prevention": "Practice good farm hygiene",
            "organic": "Use neem-based products",
        } if lang == "en" else {
            "disease": "அறிகுறிகளின் அடிப்படையில் பகுப்பாய்வு",
            "cause": "மேலும் பகுப்பாய்வு தேவை",
            "treatment": "உள்ளூர் விவசாய அலுவலரை அணுகவும்",
            "prevention": "நல்ல விவசாய சுகாதாரத்தை கடைப்பிடிக்கவும்",
            "organic": "வேம்பு சார்ந்த பொருட்களைப் பயன்படுத்தவும்",
        }

    return jsonify({"success": True, "result": result})

@app.route("/api/fertilizer", methods=["POST"])
def fertilizer_recommend():
    data = request.get_json()
    crop = data.get("crop", "")
    soil = data.get("soil", "")
    season = data.get("season", "")
    lang = session.get("lang", "en")

    if not crop or not soil:
        msg = "Please select crop and soil type." if lang == "en" else "தயவுசெய்து பயிர் மற்றும் மண் வகையைத் தேர்ந்தெடுக்கவும்."
        return jsonify({"success": False, "message": msg})

    from services.ai_service import AIService
    ai = AIService()

    if lang == "ta":
        prompt = f"பயிர்: {crop}, மண்: {soil}, பருவம்: {season}\n\nஇந்த தகவல்களின் அடிப்படையில் NPK விகிதம், கரிம உரங்கள், உயிர் உரங்கள் மற்றும் பயன்பாட்டு அட்டவணையை வழங்கவும்."
    else:
        prompt = f"Crop: {crop}, Soil: {soil}, Season: {season}\n\nBased on this information, provide NPK ratio, organic fertilizers, bio fertilizers, and application schedule."

    response = ai.get_response(prompt, lang)

    result = {}
    sections = response.split("\n")
    current_lines = []
    current_key = None
    for line in sections:
        line = line.strip()
        lower = line.lower()
        if any(k in lower for k in ["npk", "organic", "bio fertilizer", "application", "schedule", "கரிம", "உயிர்", "பயன்பாடு"]) and ":" in line:
            if current_key and current_lines:
                result[current_key] = "\n".join(current_lines)
            idx = line.find(":")
            key = line[:idx].strip().lower()
            current_key = key
            current_lines = [line[idx+1:].strip()]
        elif current_key:
            current_lines.append(line)
    if current_key and current_lines:
        result[current_key] = "\n".join(current_lines)

    if not result:
        result = {
            "npk": "20:10:10 (N:P:K)",
            "organic": "FYM 5 tons/acre, Vermicompost 2 tons/acre",
            "bio": "Azospirillum, Phosphobacteria, Rhizobium",
            "schedule": "Basal: Full P&K + 1/3 N | Tillering: 1/3 N | Panicle: 1/3 N",
        } if lang == "en" else {
            "npk": "20:10:10 (N:P:K)",
            "organic": "சாண எரு 5 டன்/ஏக்கர், மண்புழு உரம் 2 டன்/ஏக்கர்",
            "bio": "அசோஸ்பைரில்லம், பாஸ்போபாக்டீரியா, ரைசோபியம்",
            "schedule": "அடி உரம்: முழு P&K + 1/3 N | தூர்க்கும் நேரம்: 1/3 N | கதிர் விடும் நேரம்: 1/3 N",
        }

    return jsonify({"success": True, "result": result})

@app.route("/api/irrigation", methods=["POST"])
def irrigation_plan():
    data = request.get_json()
    crop = data.get("crop", "")
    soil = data.get("soil", "")
    lang = session.get("lang", "en")

    if not crop or not soil:
        msg = "Please select crop and soil type." if lang == "en" else "தயவுசெய்து பயிர் மற்றும் மண் வகையைத் தேர்ந்தெடுக்கவும்."
        return jsonify({"success": False, "message": msg})

    from services.ai_service import AIService
    ai = AIService()

    irrigation_data = {
        "paddy": {"water": "1200-1500 mm/season", "frequency": "Every 2-3 days", "method": "Flood irrigation / Drip", "rainwater": "Build farm ponds for rainwater harvesting"},
        "coconut": {"water": "40-60 liters/tree/week", "frequency": "Twice a week", "method": "Drip irrigation", "rainwater": "Create ring basins around trees"},
        "banana": {"water": "30-50 liters/plant/week", "frequency": "Every 3-4 days", "method": "Drip irrigation", "rainwater": "Use drip irrigation with rainwater harvesting"},
        "sugarcane": {"water": "2000-2500 mm/season", "frequency": "Every 5-7 days", "method": "Furrow irrigation / Drip", "rainwater": "Construct farm ponds"},
        "default": {"water": "Depends on crop and soil", "frequency": "Monitor soil moisture", "method": "Drip irrigation recommended", "rainwater": "Implement rainwater harvesting structures"},
    }

    crop_key = crop.lower() if crop.lower() in irrigation_data else "default"
    plan = irrigation_data[crop_key]

    if lang == "ta":
        plan = {
            "water": f"நீர் தேவை: {plan['water']}",
            "frequency": f"நீர்ப்பாசன அதிர்வெண்: {plan['frequency']}",
            "method": f"பரிந்துரைக்கப்பட்ட முறை: {plan['method']}",
            "rainwater": f"மழைநீர் சேகரிப்பு: {plan['rainwater']}",
        }
    else:
        plan = {
            "water": f"Water Requirement: {plan['water']}",
            "frequency": f"Irrigation Frequency: {plan['frequency']}",
            "method": f"Recommended Method: {plan['method']}",
            "rainwater": f"Rainwater Harvesting: {plan['rainwater']}",
        }

    return jsonify({"success": True, "result": plan})

@app.route("/api/contact", methods=["POST"])
def contact():
    data = request.get_json()
    lang = session.get("lang", "en")
    msg = "Message sent successfully! We will get back to you soon." if lang == "en" else "செய்தி வெற்றிகரமாக அனுப்பப்பட்டது! நாங்கள் விரைவில் உங்களை தொடர்பு கொள்வோம்."
    return jsonify({"success": True, "message": msg})

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
