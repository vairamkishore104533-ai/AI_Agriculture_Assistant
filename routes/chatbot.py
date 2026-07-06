from flask import Blueprint, render_template, request, jsonify, session, Response, stream_with_context
from utils.auth import login_required
from services.ai_service import AIService
from models.chat import ChatConversation
from datetime import datetime
import json

chatbot_bp = Blueprint("chatbot", __name__)
ai_service = AIService()

@chatbot_bp.route("/ai-chat")
@login_required
def index():
    conv_id = request.args.get("conv", "")
    user_id = session["user_id"]
    conversations = ChatConversation.find_by_user(user_id)
    convs_data = [c.to_dict() for c in conversations]

    current_conv = None
    if conv_id:
        current_conv = ChatConversation.find_by_id(conv_id)
        if current_conv and current_conv.user_id != user_id:
            current_conv = None

    if not current_conv and convs_data:
        current_conv = conversations[0]
    elif not current_conv:
        current_conv = ChatConversation({
            "user_id": user_id,
            "title": "New Chat",
            "district": session.get("district", ""),
            "messages": [],
        })
        current_conv.save()

    return render_template(
        "ai_chat.html",
        lang=session.get("lang", "en"),
        conversations=convs_data,
        current_conv=current_conv.to_dict() if current_conv else None,
        selected_district=session.get("district", ""),
    )

@chatbot_bp.route("/api/chat", methods=["POST"])
@login_required
def chat():
    data = request.get_json()
    prompt = data.get("prompt", "").strip()
    lang = session.get("lang", "en")
    district = session.get("district", "")
    conv_id = data.get("conv_id", "")
    user_id = session["user_id"]

    if not prompt:
        msg = "Please enter a question." if lang == "en" else "தயவுசெய்து ஒரு கேள்வியை உள்ளிடவும்."
        return jsonify({"success": False, "message": msg})

    if len(prompt) < 3:
        msg = "Question too short. Please be more specific." if lang == "en" else "கேள்வி மிகவும் குறுகியது. மேலும் விவரமாக கேளுங்கள்."
        return jsonify({"success": False, "message": msg})

    conv = None
    history = []
    if conv_id:
        conv = ChatConversation.find_by_id(conv_id)
        if conv and conv.user_id == user_id:
            history = [{"role": m["role"], "content": m["content"]} for m in conv.messages]

    response = ai_service.get_response(prompt, lang, district, history)

    if not conv:
        conv = ChatConversation({
            "user_id": user_id,
            "title": prompt[:60] + ("..." if len(prompt) > 60 else ""),
            "district": district,
            "messages": [],
        })
        conv.save()
        conv.add_message("user", prompt)
        conv.add_message("assistant", response)
        title = prompt[:60] + ("..." if len(prompt) > 60 else "")
        conv.update({"title": title})
    else:
        conv.add_message("user", prompt)
        conv.add_message("assistant", response)

    return jsonify({
        "success": True,
        "response": response,
        "conv_id": conv.id,
        "title": conv.title,
    })

@chatbot_bp.route("/api/chat/stream", methods=["POST"])
@login_required
def chat_stream():
    data = request.get_json()
    prompt = data.get("prompt", "").strip()
    lang = session.get("lang", "en")
    district = session.get("district", "")
    conv_id = data.get("conv_id", "")
    user_id = session["user_id"]

    if not prompt:
        msg = "Please enter a question." if lang == "en" else "தயவுசெய்து ஒரு கேள்வியை உள்ளிடவும்."
        return jsonify({"success": False, "message": msg})

    conv = None
    history = []
    if conv_id:
        conv = ChatConversation.find_by_id(conv_id)
        if conv and conv.user_id == user_id:
            history = [{"role": m["role"], "content": m["content"]} for m in conv.messages]

    def generate():
        full_response = ""
        for chunk in ai_service.stream_response(prompt, lang, district, history):
            full_response += chunk
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"

        if not conv:
            conv = ChatConversation({
                "user_id": user_id,
                "title": prompt[:60] + ("..." if len(prompt) > 60 else ""),
                "district": district,
                "messages": [],
            })
            conv.save()
            conv.add_message("user", prompt)
            conv.add_message("assistant", full_response)
            title = prompt[:60] + ("..." if len(prompt) > 60 else "")
            conv.update({"title": title})
        else:
            conv.add_message("user", prompt)
            conv.add_message("assistant", full_response)

        yield f"data: {json.dumps({'done': True, 'conv_id': conv.id, 'title': conv.title})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

@chatbot_bp.route("/api/chat/conversations", methods=["GET"])
@login_required
def list_conversations():
    user_id = session["user_id"]
    conversations = ChatConversation.find_by_user(user_id)
    return jsonify({"success": True, "conversations": [c.to_dict() for c in conversations]})

@chatbot_bp.route("/api/chat/conversation/<conv_id>", methods=["GET"])
@login_required
def get_conversation(conv_id):
    user_id = session["user_id"]
    conv = ChatConversation.find_by_id(conv_id)
    if not conv or conv.user_id != user_id:
        lang = session.get("lang", "en")
        msg = "Conversation not found." if lang == "en" else "உரையாடல் கிடைக்கவில்லை."
        return jsonify({"success": False, "message": msg})
    return jsonify({"success": True, "conversation": conv.to_dict()})

@chatbot_bp.route("/api/chat/conversation/<conv_id>", methods=["DELETE"])
@login_required
def delete_conversation(conv_id):
    user_id = session["user_id"]
    conv = ChatConversation.find_by_id(conv_id)
    if not conv or conv.user_id != user_id:
        lang = session.get("lang", "en")
        msg = "Conversation not found." if lang == "en" else "உரையாடல் கிடைக்கவில்லை."
        return jsonify({"success": False, "message": msg})
    ChatConversation.delete_by_id(conv_id)
    return jsonify({"success": True})

@chatbot_bp.route("/api/chat/new", methods=["POST"])
@login_required
def new_conversation():
    user_id = session["user_id"]
    district = session.get("district", "")
    conv = ChatConversation({
        "user_id": user_id,
        "title": "New Chat",
        "district": district,
        "messages": [],
    })
    conv.save()
    return jsonify({"success": True, "conversation": conv.to_dict()})

@chatbot_bp.route("/api/chat/export", methods=["POST"])
@login_required
def export_chat():
    data = request.get_json()
    conv_id = data.get("conv_id", "")
    export_format = data.get("format", "txt")
    user_id = session["user_id"]
    lang = session.get("lang", "en")

    conv = ChatConversation.find_by_id(conv_id)
    if not conv or conv.user_id != user_id:
        msg = "Conversation not found." if lang == "en" else "உரையாடல் கிடைக்கவில்லை."
        return jsonify({"success": False, "message": msg})

    lines = []
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    header = f"AI Agriculture Assistant - Chat Export\nDate: {now}\nDistrict: {conv.district or 'Not set'}\nLanguage: {'Tamil' if lang == 'ta' else 'English'}\n"
    header += "=" * 50 + "\n\n"
    lines.append(header)

    for msg in conv.messages:
        role = "You" if msg["role"] == "user" else "AI Assistant"
        content = msg["content"]
        lines.append(f"[{role}]\n{content}\n\n")

    text_content = "".join(lines)

    if export_format == "txt":
        return jsonify({
            "success": True,
            "export": text_content,
            "filename": f"chat_{conv_id}.txt",
            "mime": "text/plain",
        })
    else:
        return jsonify({
            "success": True,
            "export": text_content,
            "filename": f"chat_{conv_id}.txt",
            "mime": "text/plain",
        })
