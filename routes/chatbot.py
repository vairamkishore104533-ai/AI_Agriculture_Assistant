from flask import Blueprint, render_template, request, jsonify, session
from utils.auth import login_required
from services.ai_service import AIService

chatbot_bp = Blueprint("chatbot", __name__)
ai_service = AIService()

@chatbot_bp.route("/ai-chat")
@login_required
def index():
    return render_template("ai_chat.html", lang=session.get("lang", "en"))

@chatbot_bp.route("/api/chat", methods=["POST"])
@login_required
def chat():
    data = request.get_json()
    prompt = data.get("prompt", "").strip()
    lang = session.get("lang", "en")

    if not prompt:
        msg = "Please enter a question." if lang == "en" else "தயவுசெய்து ஒரு கேள்வியை உள்ளிடவும்."
        return jsonify({"success": False, "message": msg})

    if len(prompt) < 3:
        msg = "Question too short. Please be more specific." if lang == "en" else "கேள்வி மிகவும் குறுகியது. மேலும் விவரமாக கேளுங்கள்."
        return jsonify({"success": False, "message": msg})

    response = ai_service.get_response(prompt, lang)

    return jsonify({"success": True, "response": response})
