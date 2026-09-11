from flask import current_app
from datetime import datetime, timedelta
from models.notification import Notification
from services.scheme_service import SchemeService
from services.ai_service import AIService


class NotificationService:
    @staticmethod
    def generate_all(user_id, lang="en"):
        NotificationService._generate_scheme_notifications(user_id, lang)
        NotificationService._generate_market_notifications(user_id, lang)
        NotificationService._generate_irrigation_notifications(user_id, lang)
        NotificationService._generate_fertilizer_notifications(user_id, lang)
        NotificationService._generate_harvest_notifications(user_id, lang)
        NotificationService._generate_watering_notifications(user_id, lang)

    @staticmethod
    def _exists(user_id, notif_type, title, hours=24):
        since = datetime.utcnow() - timedelta(hours=hours)
        existing = Notification.get_collection().find_one({
            "user_id": user_id, "type": notif_type, "title": title,
            "created_at": {"$gte": since}
        })
        return existing is not None

    @staticmethod
    def _generate_scheme_notifications(user_id, lang):
        db = current_app.config["MONGO"]
        crops = list(db["crops"].find({"user_id": user_id}))
        user_districts = list(set(c.get("district", "") for c in crops if c.get("district")))
        schemes = SchemeService.get_all_schemes(lang)[:5]
        for s in schemes:
            title = s.get("title_en" if lang == "en" else "title_ta", "")
            deadline = s.get("deadline", "")
            if not title:
                continue
            
            if deadline:
                key = f"scheme_end_{title}"
                if NotificationService._exists(user_id, "scheme_ending", key, 168):
                    continue
                if lang == "ta":
                    msg = f"{title} திட்டம் முடிவடையும் தேதி நெருங்குகிறது: {deadline}. உடனே விண்ணப்பிக்கவும்."
                    t_title = f"முடிவடைகிறது: {title}"
                else:
                    msg = f"{title} scheme is ending soon (Deadline: {deadline}). Apply now."
                    t_title = f"Ending Soon: {title}"
                Notification.create_notification(
                    user_id=user_id, notif_type="scheme_ending",
                    title=t_title, message=msg, category="scheme", priority="high",
                    related_id=s.get("id", ""),
                )
            else:
                key = f"scheme_new_{title}"
                if NotificationService._exists(user_id, "scheme_new", key, 168):
                    continue
                if lang == "ta":
                    msg = f"புதிய திட்டம்: {title} திட்டம் இப்போது உள்ளது. விவரங்களை பார்க்கவும்."
                    t_title = "புதிய திட்டம்"
                else:
                    msg = f"New scheme available: {title}. Check details."
                    t_title = "New Scheme"
                Notification.create_notification(
                    user_id=user_id, notif_type="scheme_new",
                    title=t_title, message=msg, category="scheme", priority="medium",
                    related_id=s.get("id", ""),
                )

        saved = list(db["saved_schemes"].find({"user_id": user_id}))
        for s in saved:
            sd = s.get("scheme_data", {})
            title = sd.get("title_en" if lang == "en" else "title_ta", "") or sd.get("title", "")
            if not title:
                continue
            key = f"update_{title}"
            if NotificationService._exists(user_id, "scheme_update", key, 168):
                continue
            if lang == "ta":
                msg = f"நீங்கள் சேமித்த {title} திட்டத்தில் புதிய புதுப்பிப்பு உள்ளது."
            else:
                msg = f"New update available for your saved scheme: {title}"
            Notification.create_notification(
                user_id=user_id, notif_type="scheme_update",
                title=title, message=msg,
                category="scheme", priority="medium",
                related_id=str(s.get("_id", "")),
            )


    @staticmethod
    def _generate_harvest_notifications(user_id, lang):
        db = current_app.config["MONGO"]
        crops = list(db["crops"].find({"user_id": user_id}))
        for c in crops:
            crop_name = c.get("crop_name", "")
            status = c.get("status", "").lower()
            harvest_date_str = c.get("harvest_date", "")
            if not crop_name or status == "harvested" or not harvest_date_str:
                continue
            
            try:
                hd = datetime.strptime(harvest_date_str, "%Y-%m-%d")
                today = datetime.utcnow()
                diff = (hd - today).days
                if 0 <= diff <= 3:
                    key = f"harvest_{crop_name}_{user_id[:8]}"
                    if NotificationService._exists(user_id, "harvest", key, 24):
                        continue
                    if lang == "ta":
                        title = f"{crop_name} அறுவடை நேரம்"
                        msg = f"{crop_name} அறுவடைக்கு இன்னும் {diff} நாட்களே உள்ளன! தேவையான முன்னேற்பாடுகளை செய்யவும்."
                    else:
                        title = f"{crop_name} Harvest Reminder"
                        msg = f"Your {crop_name} is near harvest in {diff} days! Prepare accordingly."
                    
                    Notification.create_notification(
                        user_id=user_id, notif_type="harvest",
                        title=title, message=msg,
                        category="crop", priority="high",
                        related_crop=crop_name,
                    )
            except Exception:
                pass

    @staticmethod
    def _generate_watering_notifications(user_id, lang):
        db = current_app.config["MONGO"]
        crops = list(db["crops"].find({"user_id": user_id}))
        live_crops = [c.get("crop_name", "") for c in crops if c.get("status", "").title() in ["Seeded", "Growing", "Flowering", "Harvest Ready"] and c.get("crop_name")]
        
        if not live_crops:
            return
            
        key = f"water_crops_{user_id[:8]}"
        if NotificationService._exists(user_id, "watering", key, 24):
            return
            
        crop_names = ", ".join(live_crops[:3])
        if len(live_crops) > 3:
            crop_names += f" and {len(live_crops) - 3} others"
            
        if lang == "ta":
            title = "பயிர்களுக்கு நீர் பாய்ச்ச நினைவூட்டல்"
            msg = f"உங்கள் நேரடி பயிர்களுக்கு (live crops - {crop_names}) நீர் பாய்ச்ச மறக்க வேண்டாம்."
        else:
            title = "Watering Reminder"
            msg = f"Don't forget to water all your live crops: {crop_names}."
            
        Notification.create_notification(
            user_id=user_id, notif_type="watering",
            title=title, message=msg,
            category="irrigation", priority="medium",
        )

    @staticmethod
    def _generate_market_notifications(user_id, lang):
        db = current_app.config["MONGO"]
        crops = list(db["crops"].find({"user_id": user_id}))
        user_crops = list(set(c.get("crop_name", "").lower() for c in crops if c.get("crop_name")))
        market_history = list(db["market_history"].find({"user_id": user_id}).sort("created_at", -1).limit(50))
        for crop_name in user_crops:
            crop_records = [m for m in market_history if m.get("crop", "").lower() == crop_name]
            if len(crop_records) < 2:
                continue
            latest = crop_records[0]
            prev = crop_records[1]
            try:
                curr_price = float(latest.get("price", 0))
                prev_price = float(prev.get("price", 1))
                pct_change = ((curr_price - prev_price) / prev_price) * 100
            except (ValueError, TypeError):
                continue
            market_name = latest.get("market", "local")
            crop_display = crop_name.title()

            if abs(pct_change) < 5:
                continue

            if pct_change > 0:
                key = f"price_up_{crop_name}_{market_name}"
                if NotificationService._exists(user_id, "price_up", key, 72):
                    continue
                if lang == "ta":
                    title = f"{crop_display} விலை அதிகரிப்பு"
                    msg = f"{crop_display} விலை {market_name} சந்தையில் {pct_change:.0f}% அதிகரித்துள்ளது. விற்பனை செய்ய ஏற்ற நேரம்."
                else:
                    title = f"{crop_display} Price Up"
                    msg = f"{crop_display} price increased by {pct_change:.0f}% in {market_name}. Good time to sell."
                Notification.create_notification(
                    user_id=user_id, notif_type="price_up",
                    title=title, message=msg,
                    category="market", priority="high" if pct_change > 15 else "medium",
                    related_crop=crop_display,
                )
            else:
                key = f"price_down_{crop_name}_{market_name}"
                if NotificationService._exists(user_id, "price_down", key, 72):
                    continue
                if lang == "ta":
                    title = f"{crop_display} விலை குறைவு"
                    msg = f"{crop_display} விலை {market_name} சந்தையில் {abs(pct_change):.0f}% குறைந்துள்ளது."
                else:
                    title = f"{crop_display} Price Drop"
                    msg = f"{crop_display} price dropped by {abs(pct_change):.0f}% in {market_name}."
                Notification.create_notification(
                    user_id=user_id, notif_type="price_down",
                    title=title, message=msg,
                    category="market", priority="high" if abs(pct_change) > 15 else "medium",
                    related_crop=crop_display,
                )

    @staticmethod
    def _generate_irrigation_notifications(user_id, lang):
        db = current_app.config["MONGO"]
        crops = list(db["crops"].find({"user_id": user_id}))
        for c in crops:
            crop_name = c.get("crop_name", "")
            status = c.get("status", "").lower()
            if not crop_name or status in ("harvested", "planning"):
                continue
            key = f"irr_{crop_name}_{user_id[:8]}"
            if NotificationService._exists(user_id, "irrigation", key, 48):
                continue
            if lang == "ta":
                title = f"{crop_name} நீர்ப்பாசன நினைவூட்டல்"
                msg = f"{crop_name} பயிருக்கு நீர்ப்பாசனம் தேவைப்படலாம். வானிலை மற்றும் மண்ணின் ஈரப்பதத்தை சரிபார்க்கவும்."
            else:
                title = f"{crop_name} Irrigation Reminder"
                msg = f"{crop_name} may need irrigation soon. Check weather and soil moisture."
            Notification.create_notification(
                user_id=user_id, notif_type="irrigation",
                title=title, message=msg,
                category="irrigation", priority="medium",
                related_crop=crop_name,
            )

    @staticmethod
    def _generate_fertilizer_notifications(user_id, lang):
        db = current_app.config["MONGO"]
        crops = list(db["crops"].find({"user_id": user_id}))
        for c in crops:
            crop_name = c.get("crop_name", "")
            status = c.get("status", "").lower()
            if not crop_name or status in ("harvested", "planning"):
                continue
            fert_records = list(db["fertilizer"].find({"user_id": user_id, "crop": crop_name}).sort("created_at", -1).limit(1))
            if not fert_records:
                continue
            key = f"fert_{crop_name}_{user_id[:8]}"
            if NotificationService._exists(user_id, "fertilizer", key, 72):
                continue
            if lang == "ta":
                title = f"{crop_name} உர நினைவூட்டல்"
                msg = f"{crop_name} பயிருக்கு உரம் இட வேண்டிய நேரம். உங்கள் உர பரிந்துரையை பார்க்கவும்."
            else:
                title = f"{crop_name} Fertilizer Reminder"
                msg = f"Time to apply fertilizer for {crop_name}. Check your fertilizer recommendation."
            Notification.create_notification(
                user_id=user_id, notif_type="fertilizer",
                title=title, message=msg,
                category="fertilizer", priority="low",
                related_crop=crop_name,
            )
