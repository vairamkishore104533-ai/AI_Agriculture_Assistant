from flask import Blueprint, render_template, session, request
from utils.auth import login_required
from utils.helpers import get_current_season, get_mock_weather, get_season_name
from models.crop import Crop
from models.expense import Expense
from models.notification import Notification
from services.weather_service import WeatherService

dashboard_bp = Blueprint("dashboard", __name__)

DISTRICT_ZONES = {
    "Cauvery Delta Zone": [
        "Ariyalur", "Cuddalore", "Karur", "Mayiladuthurai",
        "Nagapattinam", "Perambalur", "Pudukkottai",
        "Thanjavur", "Tiruchirappalli", "Tiruvarur",
    ],
    "North Eastern Zone": [
        "Chengalpattu", "Chennai", "Kanchipuram", "Kallakurichi",
        "Ranipet", "Tirupathur", "Tiruvallur",
        "Tiruvannamalai", "Vellore", "Viluppuram",
    ],
    "Western Zone": [
        "Coimbatore", "Dharmapuri", "Dindigul", "Erode",
        "Krishnagiri", "Namakkal", "Nilgiris", "Salem", "Tiruppur",
    ],
    "Southern Zone": [
        "Madurai", "Ramanathapuram", "Sivaganga", "Tenkasi",
        "Theni", "Thoothukudi", "Tirunelveli", "Virudhunagar",
    ],
    "High Rainfall Zone": ["Kanyakumari"],
}

ZONE_INFO = {
    "Cauvery Delta Zone": {
        "description": "The Cauvery Delta region is the traditional rice bowl of Tamil Nadu, characterized by fertile alluvial soil and an extensive network of irrigation canals fed by the Cauvery River.",
        "ta_description": "காவிரி டெல்டா பகுதி தமிழ்நாட்டின் பாரம்பரிய நெற்களஞ்சியமாகும். வளமான வண்டல் மண் மற்றும் காவிரி ஆற்றின் நீர்ப்பாசன வசதி இங்கு சாகுபடியை வளப்படுத்துகிறது.",
        "soil": "Alluvial soil (clay loam, silty clay loam) — Rich in potash and lime",
        "ta_soil": "வண்டல் மண் (களிமண், மணற்களி) — பொட்டாஷ் மற்றும் சுண்ணாம்பு நிறைந்தது",
        "major_crops": "Paddy (3 seasons), Sugarcane, Banana, Pulses, Groundnut, Cotton",
        "ta_major_crops": "நெல் (3 பருவங்கள்), கரும்பு, வாழை, பயறு வகைகள், நிலக்கடலை, பருத்தி",
        "climate": "Tropical — Hot and humid. Temperature: 25–37°C. Rainfall: 900–1100 mm annually.",
        "ta_climate": "வெப்பமண்டலம் — வெப்பம் மற்றும் ஈரப்பதம். வெப்பநிலை: 25–37°C. மழைப்பொழிவு: 900–1100 மிமீ.",
        "icon": "fas fa-water",
        "color": "#0d9488",
    },
    "North Eastern Zone": {
        "description": "This zone encompasses the northern coastal plains and interior districts, featuring a mix of sandy coastal soils and red loams with diverse agricultural production.",
        "ta_description": "இந்த மண்டலம் வடக்கு கடலோர சமவெளிகள் மற்றும் உள்நாட்டு மாவட்டங்களை உள்ளடக்கியது. மணல் கடலோர மண் மற்றும் சிவப்பு மண் கலந்த வேறுபட்ட விவசாய உற்பத்தியை கொண்டுள்ளது.",
        "soil": "Red sandy loam, Coastal alluvium, Lateritic soils",
        "ta_soil": "சிவப்பு மணற்களி, கடலோர வண்டல் மண், சிகப்பு மண்",
        "major_crops": "Paddy, Sugarcane, Groundnut, Vegetables, Mango, Cashew, Coconut",
        "ta_major_crops": "நெல், கரும்பு, நிலக்கடலை, காய்கறிகள், மாம்பழம், முந்திரி, தேங்காய்",
        "climate": "Sub-tropical — Moderate. Temperature: 22–35°C. Rainfall: 900–1200 mm (NE monsoon).",
        "ta_climate": "துணை வெப்பமண்டலம் — மிதமான. வெப்பநிலை: 22–35°C. மழைப்பொழிவு: 900–1200 மிமீ (வடகிழக்கு பருவமழை).",
        "icon": "fas fa-cloud-sun",
        "color": "#2563eb",
    },
    "Western Zone": {
        "description": "The Western zone covers the rain-shadow region of the Western Ghats with dry conditions, black cotton soils, and a strong focus on cotton, millets, and oilseeds.",
        "ta_description": "மேற்கு மண்டலம் மேற்குத் தொடர்ச்சி மலையின் மழைநிழல் பகுதியை உள்ளடக்கியது. உலர்ந்த நிலைமைகள், கருப்பு பருத்தி மண் மற்றும் பருத்தி, சிறுதானியங்கள், எண்ணெய் வித்துக்கள் மீது கவனம் செலுத்துகிறது.",
        "soil": "Black cotton soil, Red loam, Mixed red and black soil",
        "ta_soil": "கருப்பு பருத்தி மண், சிவப்பு மண், கலந்த சிவப்பு மற்றும் கருப்பு மண்",
        "major_crops": "Cotton, Maize, Sorghum, Turmeric, Coconut, Millets, Tobacco",
        "ta_major_crops": "பருத்தி, மக்காச்சோளம், சோளம், மஞ்சள், தேங்காய், சிறுதானியங்கள், புகையிலை",
        "climate": "Semi-arid tropical — Hot and dry. Temperature: 24–39°C. Rainfall: 600–900 mm annually.",
        "ta_climate": "அரை வறண்ட வெப்பமண்டலம் — வெப்பம் மற்றும் உலர்ந்த. வெப்பநிலை: 24–39°C. மழைப்பொழிவு: 600–900 மிமீ.",
        "icon": "fas fa-sun",
        "color": "#d97706",
    },
    "Southern Zone": {
        "description": "The Southern zone covers the southern plains with red lateritic soils, supporting a mix of rainfed and irrigated crops including cotton, chillies, and paddy.",
        "ta_description": "தெற்கு மண்டலம் சிவப்பு மண் பகுதிகளை உள்ளடக்கியது. மழையைச் சார்ந்த மற்றும் பாசன வசதியுள்ள பயிர்களான பருத்தி, மிளகாய், நெல் ஆகியவை பயிரிடப்படுகின்றன.",
        "soil": "Red lateritic soil, Red sandy loam, Coastal alluvium",
        "ta_soil": "சிவப்பு மண், சிவப்பு மணற்களி, கடலோர வண்டல் மண்",
        "major_crops": "Cotton, Chillies, Paddy, Groundnut, Sugarcane, Mango, Coconut",
        "ta_major_crops": "பருத்தி, மிளகாய், நெல், நிலக்கடலை, கரும்பு, மாம்பழம், தேங்காய்",
        "climate": "Tropical — Hot and moderately humid. Temperature: 25–36°C. Rainfall: 700–1100 mm.",
        "ta_climate": "வெப்பமண்டலம் — வெப்பம் மற்றும் மிதமான ஈரப்பதம். வெப்பநிலை: 25–36°C. மழைப்பொழிவு: 700–1100 மிமீ.",
        "icon": "fas fa-leaf",
        "color": "#059669",
    },
    "High Rainfall Zone": {
        "description": "Kanyakumari district receives the highest rainfall in Tamil Nadu from both Southwest and Northeast monsoons, with lush green vegetation and plantation crops.",
        "ta_description": "கன்னியாகுமரி மாவட்டம் தென்மேற்கு மற்றும் வடகிழக்கு பருவமழை இரண்டிலிருந்தும் அதிக மழைப்பொழிவைப் பெறுகிறது. பசுமையான தாவரங்கள் மற்றும் தோட்டப் பயிர்கள் உள்ளன.",
        "soil": "Lateritic soil, Red loam, Forest soil",
        "ta_soil": "சிகப்பு மண், சிவப்பு மண், காட்டு மண்",
        "major_crops": "Rubber, Coconut, Tapioca, Pepper, Banana, Cloves, Paddy",
        "ta_major_crops": "ரப்பர், தேங்காய், மரவள்ளி, மிளகு, வாழை, கிராம்பு, நெல்",
        "climate": "Tropical — High rainfall. Temperature: 22–33°C. Rainfall: 1500–2500 mm annually.",
        "ta_climate": "வெப்பமண்டலம் — அதிக மழைப்பொழிவு. வெப்பநிலை: 22–33°C. மழைப்பொழிவு: 1500–2500 மிமீ.",
        "icon": "fas fa-umbrella",
        "color": "#0891b2",
    },
}

ALL_DISTRICTS = sorted(d for districts in DISTRICT_ZONES.values() for d in districts)


def get_zone_for_district(district_name):
    for zone, districts in DISTRICT_ZONES.items():
        if district_name in districts:
            return zone
    return None


@dashboard_bp.route("/dashboard")
@login_required
def index():
    user_id = session.get("user_id")
    lang = session.get("lang", "en")
    username = session.get("username", "Farmer")

    selected_district = request.args.get("district", "").strip()
    if selected_district and selected_district not in ALL_DISTRICTS:
        selected_district = ""

    zone = None
    zone_info = None
    if selected_district:
        zone = get_zone_for_district(selected_district)
        zone_info = ZONE_INFO.get(zone)

    season_key = get_current_season()
    season = get_season_name(season_key, lang)

    weather_service = WeatherService()
    weather_data = weather_service.get_current_weather(district=selected_district) if selected_district else {}
    ai_advice = weather_service.get_ai_farming_advice(weather_data, lang) if weather_data else ""

    crop_count = Crop.count_by_user(user_id)
    expense_summary = Expense.get_summary(user_id)
    unread_notifs = Notification.count_unread(user_id)

    tips = {
        "en": [
            "Water your crops early morning or late evening to reduce evaporation.",
            "Monitor soil moisture regularly to avoid over-watering.",
            "Use organic pesticides for healthier crop growth.",
            "Practice crop rotation to maintain soil fertility.",
            "Keep farm equipment clean and well-maintained.",
        ],
        "ta": [
            "ஆவியாவதை குறைக்க காலை அல்லது மாலையில் பயிர்களுக்கு நீர் பாய்ச்சவும்.",
            "அதிக நீர் ஊற்றுவதை தவிர்க்க மண்ணின் ஈரப்பதத்தை தவறாமல் கண்காணிக்கவும்.",
            "ஆரோக்கியமான பயிர் வளர்ச்சிக்கு இயற்கை பூச்சிக்கொல்லிகளைப் பயன்படுத்தவும்.",
            "மண் வளத்தை பராமரிக்க பயிர் சுழற்சியை கடைப்பிடிக்கவும்.",
            "விவசாய கருவிகளை சுத்தமாகவும் பராமரிப்பாகவும் வைத்திருக்கவும்.",
        ],
    }

    if selected_district and zone_info:
        zone_tips_en = [
            f"Your region ({zone}) is ideal for {zone_info.get('major_crops', 'diverse crops')}.",
            f"Predominant soil type: {zone_info.get('soil', 'varied soils')}.",
            "Follow local agricultural extension office recommendations for best results.",
        ]
        zone_tips_ta = [
            f"உங்கள் பகுதி ({zone}) {zone_info.get('ta_major_crops', 'பல்வேறு பயிர்கள்')} சாகுபடிக்கு ஏற்றது.",
            f"முக்கிய மண் வகை: {zone_info.get('ta_soil', 'பல்வேறு மண்')}.",
            "சிறந்த முடிவுகளுக்கு உள்ளூர் வேளாண் விரிவாக்க மைய பரிந்துரைகளை பின்பற்றவும்.",
        ]
        tips["en"] = zone_tips_en + tips["en"]
        tips["ta"] = zone_tips_ta + tips["ta"]

    return render_template(
        "dashboard.html",
        username=username,
        season=season,
        weather=weather_data,
        ai_advice=ai_advice,
        crop_count=crop_count,
        income=expense_summary.get("income", 0),
        expenses=expense_summary.get("expense", 0),
        unread_notifications=unread_notifs,
        unread_count=unread_notifs,
        tips=tips.get(lang, tips["en"]),
        lang=lang,
        selected_district=selected_district,
        zone=zone,
        zone_info=zone_info,
        all_districts=ALL_DISTRICTS,
    )
