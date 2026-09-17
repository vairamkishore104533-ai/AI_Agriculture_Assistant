from flask import current_app
from datetime import datetime, timedelta
from models.notification import Notification
from services.scheme_service import SchemeService
from services.weather_service import WeatherService
from services.market_service import market_service
import traceback

class NotificationService:
    @staticmethod
    def generate_all(user_id, lang="en"):
        try:
            NotificationService._generate_crop_added_notifications(user_id, lang)
            NotificationService._generate_harvest_notifications(user_id, lang)
            NotificationService._generate_diagnosis_notifications(user_id, lang)
            NotificationService._generate_fertilizer_notifications(user_id, lang)
            NotificationService._generate_irrigation_notifications(user_id, lang)
            NotificationService._generate_weather_notifications(user_id, lang)
            NotificationService._generate_market_notifications(user_id, lang)
            NotificationService._generate_scheme_notifications(user_id, lang)
        except Exception as e:
            print(f"[NotificationService] generate_all error: {traceback.format_exc()}")

    @staticmethod
    def _exists(user_id, unique_key):
        db = current_app.config["MONGO"]
        state = db["user_notification_state"].find_one({"user_id": user_id})
        if state and unique_key in state.get("generated_keys", []):
            return True
        return False

    @staticmethod
    def _create(user_id, n_type, title, message, category, priority, related_crop, unique_key):
        if NotificationService._exists(user_id, unique_key):
            return
            
        Notification.create_notification(
            user_id=user_id, notif_type=n_type,
            title=title, message=message,
            category=category, priority=priority,
            related_crop=related_crop, related_id=unique_key
        )
        
        # Log that this notification was generated so we don't recreate it if the user clears it
        db = current_app.config["MONGO"]
        db["user_notification_state"].update_one(
            {"user_id": user_id},
            {"$addToSet": {"generated_keys": unique_key}},
            upsert=True
        )

    @staticmethod
    def _generate_crop_added_notifications(user_id, lang):
        db = current_app.config["MONGO"]
        crops = list(db["crops"].find({"user_id": user_id}))
        for c in crops:
            crop_name = c.get("crop_name", "Unknown Crop")
            cid = str(c.get("_id", ""))
            unique_key = f"crop_added_{cid}"
            
            if lang == "ta":
                title = f"புதிய பயிர் சேர்க்கப்பட்டது: {crop_name}"
                msg = f"புதிய பயிர் சேர்க்கப்பட்டது: {crop_name} உங்கள் பயிர்களில் சேர்க்கப்பட்டுள்ளது."
            else:
                title = f"New crop added: {crop_name}"
                msg = f"New crop added: {crop_name} has been added to your crops."
                
            NotificationService._create(
                user_id, "crop_added", title, msg, "crop", "low", crop_name, unique_key
            )

    @staticmethod
    def _generate_harvest_notifications(user_id, lang):
        db = current_app.config["MONGO"]
        crops = list(db["crops"].find({"user_id": user_id}))
        today = datetime.utcnow().date()
        
        for c in crops:
            status = c.get("status", "").lower()
            if status in ["harvested", "cancelled", "completed"]:
                continue
            crop_name = c.get("crop_name", "")
            hd_str = c.get("harvest_date", "")
            cid = str(c.get("_id", ""))
            
            if not hd_str or not crop_name:
                continue
                
            try:
                hd = datetime.strptime(hd_str[:10], "%Y-%m-%d").date()
            except ValueError:
                continue
                
            diff_days = (hd - today).days
            
            # The user must receive a harvesting notification for each of the 7 days before the harvesting date.
            if 1 <= diff_days <= 7:
                unique_key = f"harvest_reminder_{cid}_{diff_days}"
                
                if lang == "ta":
                    title = f"அறுவடை நினைவூட்டல்: {crop_name}"
                    if diff_days == 1:
                        msg = f"அறுவடை நினைவூட்டல்: {crop_name} அறுவடை நாளை."
                    else:
                        msg = f"அறுவடை நினைவூட்டல்: {crop_name} அறுவடை இன்னும் {diff_days} நாட்களில் உள்ளது."
                else:
                    title = f"Harvesting reminder: {crop_name}"
                    if diff_days == 1:
                        msg = f"Harvesting reminder: {crop_name} harvest is tomorrow."
                    else:
                        msg = f"Harvesting reminder: {crop_name} harvest is in {diff_days} days."
                        
                NotificationService._create(
                    user_id, "harvest_reminder", title, msg, "crop", "high", crop_name, unique_key
                )

    @staticmethod
    def _generate_diagnosis_notifications(user_id, lang):
        db = current_app.config["MONGO"]
        diagnoses = list(db["diagnoses"].find({"user_id": user_id}))
        
        for d in diagnoses:
            severity = d.get("severity", "")
            if severity == "Highly Critical":
                crop_name = d.get("crop", "Crop")
                did = str(d.get("_id", ""))
                unique_key = f"critical_diagnosis_{did}"
                
                if lang == "ta":
                    title = f"மிகவும் தீவிரமான பாதிப்பு: {crop_name}"
                    msg = f"{crop_name} பயிரில் மிகவும் தீவிரமான பாதிப்பு கண்டறியப்பட்டுள்ளது. உடனடி கவனம் தேவைப்படலாம்."
                else:
                    title = f"Highly Critical Diagnosis: {crop_name}"
                    msg = f"Highly critical diagnosis detected for {crop_name}. Immediate attention may be required."
                    
                NotificationService._create(
                    user_id, "critical_diagnosis", title, msg, "diagnosis", "high", crop_name, unique_key
                )

    @staticmethod
    def _generate_fertilizer_notifications(user_id, lang):
        db = current_app.config["MONGO"]
        ferts = list(db["fertilizer"].find({"user_id": user_id}))
        crops = list(db["crops"].find({"user_id": user_id}))
        
        today = datetime.utcnow().date()
        today_str = today.strftime("%Y-%m-%d")
        
        for f in ferts:
            crop_name = f.get("crop", "")
            fid = str(f.get("_id", ""))
            if not crop_name:
                continue
                
            # Find matching crop to get planting & harvest dates
            matching_crop = next((c for c in crops if c.get("crop_name") == crop_name), None)
            if not matching_crop:
                continue
                
            status = matching_crop.get("status", "").lower()
            if status in ["harvested", "cancelled", "completed"]:
                continue
                
            pd_str = matching_crop.get("planting_date", "")
            hd_str = matching_crop.get("harvest_date", "")
            if not pd_str or not hd_str:
                continue
                
            try:
                pd = datetime.strptime(pd_str[:10], "%Y-%m-%d").date()
                hd = datetime.strptime(hd_str[:10], "%Y-%m-%d").date()
            except ValueError:
                continue
                
            if pd <= today <= hd:
                unique_key = f"fertilizer_{fid}_{today_str}"
                if lang == "ta":
                    title = f"உர நினைவூட்டல்: {crop_name}"
                    msg = f"உர நினைவூட்டல்: {crop_name} பயிருக்கான உரப் பரிந்துரைகளை சரிபார்க்கவும்."
                else:
                    title = f"Fertilizer reminder: {crop_name}"
                    msg = f"Fertilizer reminder: Check the recommended fertilizer requirements for {crop_name}."
                    
                NotificationService._create(
                    user_id, "fertilizer", title, msg, "fertilizer", "medium", crop_name, unique_key
                )

    @staticmethod
    def _generate_irrigation_notifications(user_id, lang):
        db = current_app.config["MONGO"]
        irrs = list(db["irrigation"].find({"user_id": user_id}))
        crops = list(db["crops"].find({"user_id": user_id}))
        
        today = datetime.utcnow().date()
        today_str = today.strftime("%Y-%m-%d")
        
        for irr in irrs:
            crop_name = irr.get("crop", "")
            iid = str(irr.get("_id", ""))
            if not crop_name:
                continue
                
            # Find matching crop
            matching_crop = next((c for c in crops if c.get("crop_name") == crop_name), None)
            if not matching_crop:
                continue
                
            status = matching_crop.get("status", "").lower()
            if status in ["harvested", "cancelled", "completed"]:
                continue
                
            pd_str = matching_crop.get("planting_date", "")
            hd_str = matching_crop.get("harvest_date", "")
            if not pd_str or not hd_str:
                continue
                
            try:
                pd = datetime.strptime(pd_str[:10], "%Y-%m-%d").date()
                hd = datetime.strptime(hd_str[:10], "%Y-%m-%d").date()
            except ValueError:
                continue
                
            if pd <= today <= hd:
                unique_key = f"irrigation_{iid}_{today_str}"
                if lang == "ta":
                    title = f"நீர்ப்பாசன நினைவூட்டல்: {crop_name}"
                    msg = f"நீர்ப்பாசன நினைவூட்டல்: {crop_name} பயிருக்கான நீர்ப்பாசன தேவைகளை சரிபார்க்கவும்."
                else:
                    title = f"Irrigation reminder: {crop_name}"
                    msg = f"Irrigation reminder: Check the irrigation requirements for {crop_name}."
                    
                NotificationService._create(
                    user_id, "irrigation", title, msg, "irrigation", "medium", crop_name, unique_key
                )

    @staticmethod
    def _generate_weather_notifications(user_id, lang):
        db = current_app.config["MONGO"]
        fav_locs = list(db["weather_favorites"].find({"user_id": user_id}))
        history_locs = list(db["weather_history"].find({"user_id": user_id}))
        
        # Combine unique locations
        locations = {}
        for loc in fav_locs + history_locs:
            district = loc.get("district", "")
            town = loc.get("town", "")
            if district or town:
                locations[f"{district}_{town}"] = (district, town)
                
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        ws = WeatherService()
        
        for key, (district, town) in locations.items():
            loc_name = town if town else district
            weather_data = ws.fetch_all(district, town)
            if not weather_data or weather_data.get("error"):
                continue
                
            daily = weather_data.get("daily", [])
            if not daily:
                continue
                
            try:
                rain_prob = float(daily[0].get("rain", 0))
            except (ValueError, TypeError):
                rain_prob = 0
                
            if rain_prob > 50:
                unique_key = f"rainfall_{loc_name}_{today_str}"
                if lang == "ta":
                    title = f"மழை எச்சரிக்கை: {loc_name}"
                    msg = f"மழை எச்சரிக்கை: {loc_name} பகுதியில் {rain_prob:.0f}% மழை பெய்ய வாய்ப்புள்ளது."
                else:
                    title = f"Rain alert: {loc_name}"
                    msg = f"Rain alert: {loc_name} has a {rain_prob:.0f}% probability of rainfall."
                    
                NotificationService._create(
                    user_id, "rainfall", title, msg, "weather", "medium", "", unique_key
                )

    @staticmethod
    def _generate_market_notifications(user_id, lang):
        db = current_app.config["MONGO"]
        history = list(db["market_history"].find({"user_id": user_id}))
        favorites = list(db["market_favorites"].find({"user_id": user_id}))
        
        crops_to_check = set()
        for r in history:
            if r.get("crop"): crops_to_check.add(r.get("crop"))
        for f in favorites:
            if f.get("crop"): crops_to_check.add(f.get("crop"))
            
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        
        for crop in crops_to_check:
            # We can use the MarketPrices API to get the current trend or rely on existing records.
            # We'll check the market service directly.
            results = market_service.compare_markets(crop)
            if not results:
                continue
                
            # Take the best market or average trend
            best_market = results[0]
            trend = best_market.get("trend", "stable")
            
            if trend in ["up", "down"]:
                unique_key = f"market_{crop}_{trend}_{today_str}"
                
                if trend == "up":
                    if lang == "ta":
                        title = f"சந்தை நிலவரம்: {crop}"
                        msg = f"சந்தை நிலவரம்: {crop} விலை மேல்நோக்கி செல்கிறது."
                    else:
                        title = f"Market update: {crop}"
                        msg = f"Market update: {crop} prices are trending upward."
                else:
                    if lang == "ta":
                        title = f"சந்தை நிலவரம்: {crop}"
                        msg = f"சந்தை நிலவரம்: {crop} விலை கீழ்நோக்கி செல்கிறது."
                    else:
                        title = f"Market update: {crop}"
                        msg = f"Market update: {crop} prices are trending downward."
                        
                NotificationService._create(
                    user_id, "market_trend", title, msg, "market", "medium", crop, unique_key
                )

    @staticmethod
    def _generate_scheme_notifications(user_id, lang):
        db = current_app.config["MONGO"]
        
        # Get current state from user_scheme_state
        state_doc = db["user_scheme_state"].find_one({"user_id": user_id})
        previously_seen = state_doc.get("seen_scheme_ids", []) if state_doc else []
        
        # Get all schemes from the app
        current_schemes = SchemeService().get_all_schemes()
        current_scheme_ids = [s.get("id") for s in current_schemes if s.get("id")]
        
        if not state_doc:
            # First time, don't spam the user with 100 new scheme notifications.
            # Just save the current state and return.
            db["user_scheme_state"].insert_one({
                "user_id": user_id,
                "seen_scheme_ids": current_scheme_ids,
                "updated_at": datetime.utcnow()
            })
            return
            
        # Detect NEW schemes
        new_schemes = [sid for sid in current_scheme_ids if sid not in previously_seen]
        for sid in new_schemes:
            scheme = next((s for s in current_schemes if s.get("id") == sid), None)
            if not scheme: continue
            
            title_en = scheme.get("title_en", scheme.get("title", ""))
            title_ta = scheme.get("title_ta", title_en)
            
            unique_key = f"scheme_new_{sid}"
            if lang == "ta":
                title = f"புதிய திட்டம்"
                msg = f"புதிய அரசு திட்டம் கிடைக்கிறது: {title_ta}."
            else:
                title = f"New scheme available"
                msg = f"New government scheme available: {title_en}."
                
            NotificationService._create(
                user_id, "scheme_new", title, msg, "scheme", "medium", "", unique_key
            )
            
        # Detect REMOVED schemes
        removed_schemes = [sid for sid in previously_seen if sid not in current_scheme_ids]
        for sid in removed_schemes:
            # We don't have the scheme object anymore, just notify generically or by ID if we don't have the title
            unique_key = f"scheme_removed_{sid}"
            if lang == "ta":
                title = f"திட்டம் நீக்கப்பட்டது"
                msg = f"அரசு திட்ட புதுப்பிப்பு: ஒரு திட்டம் (ID: {sid}) இனி கிடைக்காது."
            else:
                title = f"Scheme removed"
                msg = f"Government scheme update: A scheme (ID: {sid}) is no longer available."
                
            NotificationService._create(
                user_id, "scheme_removed", title, msg, "scheme", "medium", "", unique_key
            )
            
        # Update state if changes occurred
        if new_schemes or removed_schemes:
            db["user_scheme_state"].update_one(
                {"user_id": user_id},
                {"$set": {"seen_scheme_ids": current_scheme_ids, "updated_at": datetime.utcnow()}}
            )
