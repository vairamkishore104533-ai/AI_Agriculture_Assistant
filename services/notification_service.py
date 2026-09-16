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
        NotificationService._generate_rainfall_notifications(user_id, lang)

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
                hd = datetime.strptime(harvest_date_str, "%Y-%m-%d").date()
                today = datetime.utcnow().date()
                diff = (hd - today).days
                
                if diff == 7:
                    if lang == "ta":
                        title = f"{crop_name} அறுவடை 7 நாட்களில் ({hd.strftime('%d %b')}) உள்ளது"
                        msg = f"{crop_name} அறுவடை 7 நாட்களில் ({hd.strftime('%d %b')}) உள்ளது."
                    else:
                        title = f"{crop_name} harvest is in 7 days ({hd.strftime('%d %b')})"
                        msg = f"{crop_name} harvest is in 7 days ({hd.strftime('%d %b')})."
                        
                    # Check if this exact reminder (by title) was generated recently
                    if NotificationService._exists(user_id, "harvest", title, 24 * 10):
                        continue
                    
                    Notification.create_notification(
                        user_id=user_id, notif_type="harvest",
                        title=title, message=msg,
                        category="crop", priority="high",
                        related_crop=crop_name,
                        related_id=str(c.get("_id", ""))
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
        from datetime import datetime
        db = current_app.config["MONGO"]
        crops = list(db["crops"].find({"user_id": user_id}))
        today = datetime.utcnow().date()
        date_str = today.strftime("%Y-%m-%d")

        for c in crops:
            crop_name = c.get("crop_name", "")
            if not crop_name:
                continue

            pd_str = c.get("planting_date")
            hd_str = c.get("harvest_date")

            if not pd_str or not hd_str:
                continue

            try:
                pd = datetime.strptime(pd_str[:10], "%Y-%m-%d").date()
                hd = datetime.strptime(hd_str[:10], "%Y-%m-%d").date()
            except ValueError:
                continue

            # Must be within cultivation period (inclusive of start/end dates)
            if today < pd or today > hd:
                continue

            if lang == "ta":
                title = f"💧 {crop_name} நீர்ப்பாசன நினைவூட்டல் ({date_str})"
                msg = f"நீர்ப்பாசன நினைவூட்டல்: இன்று உங்கள் {crop_name} பயிருக்கு கவனம் தேவை."
            else:
                title = f"💧 {crop_name} Irrigation Reminder ({date_str})"
                msg = f"Irrigation reminder: Your {crop_name} crop requires attention today."

            # Check if this exact title has already been generated
            existing = db["notifications"].find_one({
                "user_id": user_id,
                "title": title
            })

            if existing:
                continue

            Notification.create_notification(
                user_id=user_id, notif_type="irrigation",
                title=title, message=msg,
                category="irrigation", priority="medium",
                related_crop=crop_name,
                action_link="/irrigation"
            )

    @staticmethod
    def _generate_fertilizer_notifications(user_id, lang):
        from datetime import datetime
        db = current_app.config["MONGO"]
        crops = list(db["crops"].find({"user_id": user_id}))
        now = datetime.utcnow()
        today = now.date()
        
        for c in crops:
            crop_name = c.get("crop_name", "")
            status = c.get("status", "").lower()
            
            # Active crops only
            if not crop_name or status in ("harvested", "completed", "cancelled", "inactive", "planning"):
                continue
                
            pd_str = c.get("planting_date")
            hd_str = c.get("harvest_date") # Wait, in models/crop.py it's harvest_date
            
            if not pd_str or not hd_str:
                continue
                
            try:
                pd = datetime.strptime(pd_str, "%Y-%m-%d").date()
                hd = datetime.strptime(hd_str, "%Y-%m-%d").date()
            except ValueError:
                continue
                
            if today < pd or today > hd:
                continue
                
            # It's an active crop and today is between planting and harvesting.
            # Generate one per calendar day. Use the date in the key to prevent duplicates.
            date_str = today.strftime("%Y-%m-%d")
            
            # Create a unique key per crop per day
            title_en = f"🌱 {crop_name} Fertilizer Reminder ({date_str})"
            title_ta = f"🌱 {crop_name} உர நினைவூட்டல் ({date_str})"
            
            title = title_ta if lang == "ta" else title_en
            
            # Check if this exact title has already been generated
            existing = db["notifications"].find_one({
                "user_id": user_id, 
                "title": title
            })
            
            if existing:
                continue
                
            # Stage calculation
            total_days = (hd - pd).days
            days_passed = (today - pd).days
            
            stage_en = ""
            stage_ta = ""
            if total_days > 0:
                progress = days_passed / total_days
                if progress < 0.2:
                    stage_en = "early growth stage"
                    stage_ta = "ஆரம்ப வளர்ச்சி நிலையில்"
                elif progress < 0.5:
                    stage_en = "active vegetative stage"
                    stage_ta = "தீவிர தாவர வளர்ச்சி நிலையில்"
                elif progress < 0.8:
                    stage_en = "flowering/fruiting stage"
                    stage_ta = "பூக்கும்/காய்க்கும் பருவத்தில்"
                else:
                    stage_en = "maturity stage"
                    stage_ta = "முதிர்ச்சி நிலையில்"
            
            if lang == "ta":
                if stage_ta:
                    msg = f"உங்கள் {crop_name} பயிர் தற்போது {stage_ta} உள்ளது. இன்றைய உரத் தேவையைக் கண்டறிய உர பரிந்துரையை பார்க்கவும்."
                else:
                    msg = f"உங்கள் {crop_name} பயிரின் இன்றைய உரத் தேவையைக் கண்டறியவும்."
            else:
                if stage_en:
                    msg = f"Your {crop_name} crop is currently in the {stage_en}. Check the fertilizer recommendation for today."
                else:
                    msg = f"Check today's fertilizer requirement for your {crop_name} crop."
                
            Notification.create_notification(
                user_id=user_id, notif_type="fertilizer",
                title=title, message=msg,
                category="fertilizer", priority="low",
                related_crop=crop_name,
                action_link="/fertilizer" # This allows clicking the notification if supported
            )

    @staticmethod
    def _generate_rainfall_notifications(user_id, lang):
        from datetime import datetime
        from services.weather_service import WeatherService
        db = current_app.config["MONGO"]
        crops = list(db["crops"].find({"user_id": user_id}))
        today = datetime.utcnow().date()
        date_str = today.strftime("%Y-%m-%d")

        unique_villages = {}
        for c in crops:
            pd_str = c.get("planting_date")
            hd_str = c.get("harvest_date")
            village = c.get("village", "").strip()
            district = c.get("district", "").strip()

            if not village or not district or not pd_str or not hd_str:
                continue

            try:
                pd = datetime.strptime(pd_str[:10], "%Y-%m-%d").date()
                hd = datetime.strptime(hd_str[:10], "%Y-%m-%d").date()
            except ValueError:
                continue

            if today < pd or today > hd:
                continue

            # Store the district for the unique village
            if village not in unique_villages:
                unique_villages[village] = district

        if not unique_villages:
            return

        ws = WeatherService()
        for village, district in unique_villages.items():
            weather_data = ws.fetch_all(district, village)
            if not weather_data or weather_data.get("error"):
                continue

            daily = weather_data.get("daily", [])
            if not daily:
                continue

            rain_chance = daily[0].get("rain", 0)
            try:
                rain_chance = float(rain_chance)
            except (ValueError, TypeError):
                rain_chance = 0

            if rain_chance > 50:
                if lang == "ta":
                    title = f"மழை எச்சரிக்கை: {village} ({date_str})"
                    msg = f"மழை எச்சரிக்கை: இன்று {village} பகுதியில் {rain_chance}% மழை பெய்ய வாய்ப்புள்ளது."
                else:
                    title = f"Rainfall Alert: {village} ({date_str})"
                    msg = f"Rainfall Alert: {rain_chance}% chance of rain is expected in {village} today."

                # Check for duplicates using title
                existing = db["notifications"].find_one({
                    "user_id": user_id,
                    "title": title
                })

                if not existing:
                    Notification.create_notification(
                        user_id=user_id, notif_type="rainfall",
                        title=title, message=msg,
                        category="weather", priority="high",
                        related_id=village,
                        action_link="/weather"
                    )
