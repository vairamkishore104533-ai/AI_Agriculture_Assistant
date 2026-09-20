from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from models.user import User
from utils.auth import hash_password, check_password, generate_token
from utils.validators import validate_username, validate_password

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    data = request.get_json() or request.form
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    lang = data.get("lang", session.get("lang", "en"))

    if not username or not password:
        return jsonify({"success": False, "message": "Please fill all fields."})

    user = User.find_by_username(username)
    if not user:
        msg = "User not found. Please register first." if lang == "en" else "பயனர் கிடைக்கவில்லை. முதலில் பதிவு செய்யவும்."
        return jsonify({"success": False, "message": msg})

    if not check_password(password, user.password):
        msg = "Incorrect password." if lang == "en" else "தவறான கடவுச்சொல்."
        return jsonify({"success": False, "message": msg})

    token = generate_token(user.id)
    session["token"] = token
    session["user_id"] = user.id
    session["username"] = user.username
    session["is_admin"] = user.is_admin
    session["lang"] = user.preferred_language or lang

    user.update({"last_login": __import__("datetime").datetime.utcnow()})

    msg = "Login successful! Welcome to TN Agriculture Assistant." if lang == "en" else "உள்நுழைவு வெற்றி! TN விவசாய உதவியாளருக்கு வரவேற்கிறோம்."
    return jsonify({"success": True, "message": msg, "redirect": url_for("dashboard.index")})

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    data = request.get_json() or request.form
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    confirm_password = data.get("confirm_password", "").strip()
    lang = data.get("lang", session.get("lang", "en"))

    valid, msg = validate_username(username)
    if not valid:
        return jsonify({"success": False, "message": msg})

    if password != confirm_password:
        msg = "Passwords do not match." if lang == "en" else "கடவுச்சொற்கள் பொருந்தவில்லை."
        return jsonify({"success": False, "message": msg})

    valid, msg = validate_password(password)
    if not valid:
        return jsonify({"success": False, "message": msg})

    if User.find_by_username(username):
        msg = "Username already exists. Please choose another." if lang == "en" else "இந்த பயனர் பெயர் ஏற்கனவே உள்ளது. வேறொன்றைத் தேர்ந்தெடுக்கவும்."
        return jsonify({"success": False, "message": msg})

    user = User()
    user.username = username
    user.password = hash_password(password)
    user.save()

    msg = "Registration successful! Please login." if lang == "en" else "பதிவு வெற்றி! தயவுசெய்து உள்நுழையவும்."
    return jsonify({"success": True, "message": msg, "redirect": url_for("auth.login")})

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))
