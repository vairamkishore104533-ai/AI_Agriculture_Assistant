from flask import Blueprint, render_template, request, jsonify, session
from utils.auth import login_required
from models.notification import Notification

notifications_bp = Blueprint("notifications", __name__)

@notifications_bp.route("/notifications")
@login_required
def index():
    return render_template("notifications.html", lang=session.get("lang", "en"))

@notifications_bp.route("/api/notifications")
@login_required
def get_notifications():
    user_id = session.get("user_id")
    notifs = Notification.find_by_user(user_id)
    unread = Notification.count_unread(user_id)
    return jsonify({
        "success": True,
        "notifications": [n.to_dict() for n in notifs],
        "unread_count": unread,
    })

@notifications_bp.route("/api/notifications/read", methods=["POST"])
@login_required
def mark_read():
    data = request.get_json()
    notif_id = data.get("notification_id")
    if notif_id:
        from models.notification import Notification as N
        notif = N.find_by_id(notif_id) if hasattr(N, 'find_by_id') else None
        if notif:
            notif.mark_read()
    else:
        user_id = session.get("user_id")
        Notification.mark_all_read(user_id)
    return jsonify({"success": True})

@notifications_bp.route("/api/notifications/clear", methods=["POST"])
@login_required
def clear():
    user_id = session.get("user_id")
    Notification.clear_all(user_id)
    return jsonify({"success": True})

@notifications_bp.route("/api/notifications/unread")
@login_required
def unread_count():
    user_id = session.get("user_id")
    count = Notification.count_unread(user_id)
    return jsonify({"success": True, "count": count})
