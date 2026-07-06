import os
import json
import re
import time

class AIService:
    def __init__(self):
        self.api_key = os.getenv("AI_API_KEY", "")
        self.api_url = os.getenv("AI_API_URL", "https://api.anthropic.com/v1/messages")
        self.model = os.getenv("AI_MODEL", "claude-3-haiku-20240307")
        self.provider = os.getenv("AI_PROVIDER", "mock")

    def get_response(self, prompt, language="en", district="", history=None):
        if not self.api_key or self.api_key in ("", "your-ai-api-key"):
            return self._get_mock_response(prompt, language, district)
        try:
            system_prompt = self._build_system_prompt(language, district, history)
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01"
            }
            messages = []
            if history:
                for msg in history[-10:]:
                    messages.append({"role": msg["role"], "content": msg["content"]})
            messages.append({"role": "user", "content": prompt})
            data = {
                "model": self.model,
                "max_tokens": 2000,
                "system": system_prompt,
                "messages": messages,
            }
            import requests
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                return result["content"][0]["text"]
            return self._get_mock_response(prompt, language, district)
        except Exception:
            return self._get_mock_response(prompt, language, district)

    def stream_response(self, prompt, language="en", district="", history=None):
        if not self.api_key or self.api_key in ("", "your-ai-api-key"):
            full = self._get_mock_response(prompt, language, district)
            for i in range(0, len(full), 3):
                yield full[i:i+3]
                time.sleep(0.02)
            return
        try:
            system_prompt = self._build_system_prompt(language, district, history)
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01"
            }
            messages = []
            if history:
                for msg in history[-10:]:
                    messages.append({"role": msg["role"], "content": msg["content"]})
            messages.append({"role": "user", "content": prompt})
            data = {
                "model": self.model,
                "max_tokens": 2000,
                "system": system_prompt,
                "messages": messages,
                "stream": True,
            }
            import requests
            with requests.post(self.api_url, headers=headers, json=data, stream=True, timeout=60) as resp:
                if resp.status_code != 200:
                    full = self._get_mock_response(prompt, language, district)
                    for i in range(0, len(full), 3):
                        yield full[i:i+3]
                        time.sleep(0.02)
                    return
                for line in resp.iter_lines():
                    if line:
                        decoded = line.decode("utf-8")
                        if decoded.startswith("data: "):
                            try:
                                chunk = json.loads(decoded[6:])
                                if chunk.get("type") == "content_block_delta":
                                    text = chunk.get("delta", {}).get("text", "")
                                    if text:
                                        yield text
                            except json.JSONDecodeError:
                                continue
        except Exception:
            full = self._get_mock_response(prompt, language, district)
            for i in range(0, len(full), 3):
                yield full[i:i+3]
                time.sleep(0.02)

    def _build_system_prompt(self, language, district="", history=None):
        lang_instruction = (
            "Respond only in Tamil language. Use Tamil agricultural terminology."
            if language == "ta"
            else "Respond only in English."
        )
        district_context = ""
        if district:
            from routes.dashboard import ZONE_INFO, get_zone_for_district
            zone = get_zone_for_district(district)
            if zone and zone in ZONE_INFO:
                info = ZONE_INFO[zone]
                major_crops_tn = ", ".join(info.get("crops", []))
                soil_tn = info.get("soil", "")
                climate_tn = info.get("climate", "")
                zone_name_tn = info.get("name_ta", zone) if language == "ta" else zone
                if language == "ta":
                    district_context = (
                        f"பயனர் {district} மாவட்டத்தைச் சேர்ந்தவர். "
                        f"இந்த மாவட்டம் {zone_name_tn} மண்டலத்தில் உள்ளது. "
                        f"இங்கு மண் வகை: {soil_tn}, காலநிலை: {climate_tn}, முக்கிய பயிர்கள்: {major_crops_tn}. "
                        f"இந்த சூழலுக்கு ஏற்ப ஆலோசனைகளை வழங்கவும்."
                    )
                else:
                    district_context = (
                        f"The user is from {district} district. "
                        f"This district belongs to the {zone_name_tn} agro-climatic zone. "
                        f"Soil type: {soil_tn}. Climate: {climate_tn}. Major crops: {major_crops_tn}. "
                        f"Tailor your advice to this context."
                    )
        system = f"""You are an AI Agriculture Assistant for Tamil Nadu farmers.

{lang_instruction}
- Focus on Tamil Nadu agricultural conditions, crops, and practices.
- Provide practical, actionable advice.
- If the user asks about non-agriculture topics (politics, entertainment, technology, etc.), politely refuse and redirect to farming topics.
- Keep responses concise and clear.
- Only recommend reliable farming practices.
- Use Markdown formatting for structure: **bold** for emphasis, bullet points for lists, headings for sections.
- Always answer in complete, helpful paragraphs.

{district_context}"""
        return system

    def _detect_off_topic(self, prompt):
        agriculture_keywords_en = [
            "crop", "farm", "soil", "seed", "fertilizer", "pesticide", "harvest",
            "plant", "grow", "irrigation", "weather", "rain", "market", "price",
            "scheme", "subsidy", "organic", "disease", "pest", "weed", "yield",
            "paddy", "rice", "wheat", "coconut", "sugarcane", "banana", "cotton",
            "vegetable", "fruit", "livestock", "cattle", "goat", "chicken",
            "tamil nadu", "agriculture", "farming", "farmer", "cultivation",
            "manure", "compost", "nursery", "sprout", "tillage", "plough",
            "water", "drainage", "greenhouse", "mulch", "prune", "graft",
        ]
        agriculture_keywords_ta = [
            "விவசாய", "பயிர்", "நெல்", "மண்", "விதை", "உரம்", "பூச்சி",
            "அறுவடை", "நடவு", "சாகுபடி", "பாசன", "நீர்ப்பாசன", "வானிலை",
            "மழை", "சந்தை", "விலை", "திட்டம்", "மானியம்", "இயற்கை",
            "நோய்", "களை", "விளைச்ச", "தேங்காய்", "கரும்பு", "வாழை",
            "பருத்தி", "காய்கறி", "கால்நடை", "ஆடு", "மாடு", "கோழி",
            "தமிழ்நாடு", "வேளாண்", "உழவர்", "விவசாயி", "பண்ணை",
            "தோட்டம்", "நாற்று", "நீர்", "வடிகால்", "சாணம்", "எரு",
            "பசளை", "வேப்ப", "மிளகாய்", "தக்காளி", "மஞ்சள்",
        ]
        prompt_lower = prompt.lower()
        keywords = agriculture_keywords_en + agriculture_keywords_ta
        matches = sum(1 for kw in keywords if kw in prompt_lower)
        if matches == 0 and len(prompt.split()) > 3:
            return True
        return False

    def _get_mock_response(self, prompt, language="en", district=""):
        if self._detect_off_topic(prompt) and language == "en":
            return "I'm designed to answer **agriculture-related questions** for Tamil Nadu farmers. I can help with crops, fertilizers, irrigation, disease management, government schemes, organic farming, and more. Please ask a farming-related question!"
        if self._detect_off_topic(prompt) and language == "ta":
            return "நான் **தமிழ்நாடு விவசாயிகள்**க்கான AI உதவியாளர். பயிர்கள், உரங்கள், நீர்ப்பாசனம், நோய் மேலாண்மை, அரசு திட்டங்கள், இயற்கை விவசாயம் போன்றவற்றில் உதவ முடியும். தயவுசெய்து விவசாயம் சார்ந்த கேள்வியைக் கேளுங்கள்."

        prompt_lower = prompt.lower()
        district_lower = district.lower() if district else ""

        if language == "ta":
            if district_lower and ("நெல்" in prompt or "பயிர்" in prompt):
                return f"**{district} மாவட்டத்தில் நெல் சாகுபடி**\n\nதஞ்சாவூர், திருச்சி, கடலூர் மாவட்டங்கள் நெல் சாகுபடிக்கு சிறந்தவை. குறுவை (ஜூன்-செப்டம்பர்), சம்பா (ஆகஸ்ட்-ஜனவரி), தாளடி (ஜனவரி-ஏப்ரல்) ஆகிய மூன்று பருவங்களில் நெல் பயிரிடலாம்.\n\n**பரிந்துரைக்கப்பட்ட ரகங்கள்:** ADT 43, ADT 45, BPT 5204\n\n**மகசூல்:** ஏக்கருக்கு 5-6 டன் வரை பெறலாம்."
            if district_lower and "உர" in prompt:
                return f"**{district} மாவட்டத்தில் உர பரிந்துரை**\n\nநெல்லுக்கு பரிந்துரைக்கப்படும் உரங்கள்: ஏக்கருக்கு **40:20:20 கிலோ NPK** (யூரியா, சூப்பர் பாஸ்பேட், பொட்டாஷ்).\n\n**பயன்பாட்டு முறை:**\n- அடி உரமாக: முழு பாஸ்பேட் மற்றும் பொட்டாஷ்\n- யூரியாவை 3 பங்குகளாகப் பிரித்து இடவும்\n- மண்ணில் சாண எரு அல்லது மக்கிய இலைகளைச் சேர்க்கவும்"
            if "நெல்" in prompt or "பயிர்" in prompt or "சிறந்த" in prompt:
                return "தமிழ்நாட்டில் நெல் சாகுபடிக்கு **தஞ்சாவூர், திருச்சி, கடலூர்** மாவட்டங்கள் சிறந்தவை. குறுவை (ஜூன்-செப்டம்பர்), சம்பா (ஆகஸ்ட்-ஜனவரி), தாளடி (ஜனவரி-ஏப்ரல்) ஆகிய மூன்று பருவங்களில் நெல் பயிரிடலாம். ADT 43, ADT 45, BPT 5204 போன்ற ரகங்கள் தமிழ்நாட்டில் நல்ல விளைச்சல் தருகின்றன."
            if "உர" in prompt or "எரு" in prompt:
                return "நெல்லுக்கு பரிந்துரைக்கப்படும் உரங்கள்: ஏக்கருக்கு **40:20:20 கிலோ NPK** (யூரியா, சூப்பர் பாஸ்பேட், பொட்டாஷ்). நடவு நேரத்தில் முழு பாஸ்பேட் மற்றும் பொட்டாஷ், யூரியாவை மூன்று பங்குகளாக பிரித்து இடவும். மண்ணில் சாண எரு அல்லது மக்கிய இலைகளைச் சேர்ப்பதால் மண்ணின் வளம் அதிகரிக்கும்."
            if "நீர்ப்பாசன" in prompt or "தண்ணீர்" in prompt or "பாசன" in prompt:
                return "நெல்லுக்கு **சொட்டு நீர் பாசனம்** அல்லது தெளிப்பு பாசனம் பயன்படுத்தலாம். வயலில் 2-5 செ.மீ உயரத்தில் தண்ணீர் நிறுத்தி வைக்க வேண்டும். நாற்றங்கால் முதல் அறுவடை வரை சராசரியாக **1200-1500 மி.மீ** தண்ணீர் தேவைப்படுகிறது. மழைநீர் சேகரிப்பு கட்டாயம்."
            if "நோய்" in prompt or "பூச்சி" in prompt:
                return "**நெல்லில் பொதுவான நோய்கள்:**\n\n**இலைக்கருகல்:** தாமிர கலவை தெளிப்பு\n**தண்டழுகல்:** கார்பென்டாசிம்\n**பாக்டீரியல் இலைக்கருகல்:** ஸ்ட்ரெப்டோமைசின்\n\n**பூச்சிகள்:**\n- தண்டு துளைப்பான்: கார்போஃப்யூரான்\n- இலைப்பேன்: மோனோக்ரோடோபாஸ்\n\n**இயற்கை முறை:** வேப்ப எண்ணெய், சூடோமோனாஸ் பாக்டீரியா"
            if "அரசு" in prompt or "திட்டம்" in prompt:
                return "**தமிழ்நாடு விவசாயிகளுக்கான அரசு திட்டங்கள்:**\n\n1. **பிரதான் மந்திரி பயிர் காப்பீடு திட்டம் (PMFBY)**\n2. **PM-KISAN** - வருடத்திற்கு ரூ.6000\n3. மண் ஆரோக்கிய அட்டை திட்டம்\n4. நுண்ணீர் பாசன திட்டம் (80% மானியம்)\n5. இயற்கை வேளாண்மை திட்டம்\n\nமேலும் விவரங்களுக்கு https://www.tn.gov.in பார்க்கவும்."
            if "இயற்கை" in prompt or "கரிம" in prompt:
                return "**இயற்கை வேளாண்மை குறிப்புகள்:**\n\n1. பசுந்தாள் உரங்கள் பயன்படுத்துதல் (தட்டைப்பயறு, கோழிவரகு)\n2. மக்கிய சாண எருவினை இடுதல்\n3. வேம்பு சார்ந்த பூச்சி விரட்டிகள்\n4. பயிர் சுழற்சி முறை கடைப்பிடித்தல்\n5. உயிர் உரங்கள் (ரைசோபியம், அசோஸ்பைரில்லம்) பயன்பாடு\n\nதமிழ்நாடு அரசு இயற்கை வேளாண்மைக்கு மானியம் வழங்குகிறது."
            return "தமிழ்நாட்டில் விவசாயம் பற்றிய உங்கள் கேள்விக்கு நன்றி. **பயிர் சாகுபடி, உரங்கள், நீர்ப்பாசனம், நோய் கட்டுப்பாடு, அரசு திட்டங்கள்** போன்றவை பற்றி கேட்கலாம். தயவுசெய்து உங்கள் கேள்வியை விவரமாக கேளுங்கள்."
        else:
            if district_lower and ("crop" in prompt_lower or "best" in prompt_lower or "grow" in prompt_lower):
                return f"### Best Crops for {district}\n\nBased on {district}'s agro-climatic zone, here are the recommended crops:\n\n- **Paddy** - Main season crop with 3 seasons (Kuruvai, Samba, Thaladi)\n- **Coconut** - Suitable for most soil types\n- **Sugarcane** - 12-month crop with good returns\n- **Banana** - High-value fruit crop\n- **Vegetables** - Tomato, brinjal, chilli for local markets\n\nWould you like specific fertilizer or irrigation advice for any of these crops?"
            if "crop" in prompt_lower or "best" in prompt_lower or "grow" in prompt_lower or "cultivate" in prompt_lower:
                if district_lower:
                    return f"### Crops for {district}\n\nTamil Nadu's major crops include **Paddy, Coconut, Sugarcane, Banana, Cotton, Groundnut, and Millets**. Your district's specific recommendations depend on local soil and climate conditions. Would you like to tell me your district for personalized advice?"
                return "**Tamil Nadu's Major Crops:**\n\n- **Paddy** - Thanjavur, Tiruchy, Cuddalore\n- **Coconut** - Coimbatore, Pollachi\n- **Sugarcane** - Erode, Villupuram\n- **Banana** - Namakkal, Tiruchy\n- **Cotton** - Salem, Virudhunagar\n- **Groundnut** - Tiruppur\n- **Millets** - Dharmapuri\n\nChoose crops based on your district's climate and soil conditions."
            elif "fertilizer" in prompt_lower or "manure" in prompt_lower:
                return "### Fertilizer Recommendation for Paddy\n\nApply **40:20:20 kg NPK per acre** (Urea, Super Phosphate, Potash).\n\n**Application Schedule:**\n- **Basal**: Full Phosphate and Potash + 1/3 Nitrogen\n- **Tillering**: 1/3 Nitrogen\n- **Panicle Initiation**: 1/3 Nitrogen\n\nAdd **FYM 5-7 tons per acre** before transplanting. For organic farming, use vermicompost, green manure (daincha), and bio-fertilizers (Azospirillum)."
            elif "irrigation" in prompt_lower or "water" in prompt_lower:
                return "### Irrigation Guide\n\nFor **paddy**: Maintain **2-5 cm standing water**. Total water requirement: **1200-1500 mm/season**.\n\n**Critical stages:** Panicle initiation and flowering.\n\n**Drip irrigation** can save 30-40% water.\n\nFor **coconut**: 40-60 liters/tree/week.\n\n**Rainwater harvesting** through farm ponds is highly recommended for Tamil Nadu's variable rainfall."
            elif "disease" in prompt_lower or "pest" in prompt_lower or "treatment" in prompt_lower:
                return "### Common Paddy Diseases & Treatment\n\n**1. Blast** - Use Carbendazim or Tricyclazole\n**2. Sheath Blight** - Use Hexaconazole\n**3. Bacterial Leaf Blight** - Use Streptomycin\n\n**Organic Alternatives:**\n- Neem oil spray (3%)\n- Pseudomonas fluorescens\n- Trichoderma viride\n\nAlways practice **crop rotation** and use **resistant varieties**."
            elif "scheme" in prompt_lower or "government" in prompt_lower or "subsidy" in prompt_lower:
                return "### Government Schemes for Tamil Nadu Farmers\n\n1. **PM Fasal Bima Yojana** - Crop insurance\n2. **PM-KISAN** - Rs.6,000/year income support\n3. **TN Organic Farming Policy** - Subsidy for organic certification\n4. **e-NAM** - Online trading platform\n5. **Micro Irrigation Scheme** - Up to 80% subsidy\n\nApply at your nearest Agriculture Department office."
            elif "organic" in prompt_lower:
                return "### Organic Farming Tips for Tamil Nadu\n\n1. Use **green manure** crops (daincha, cowpea)\n2. Apply **well-decomposed FYM**\n3. Use **neem-based pesticides**\n4. Practice **crop rotation**\n5. Use **bio-fertilizers** (Rhizobium, Azospirillum, Phosphobacteria)\n\nTamil Nadu government provides subsidy for organic certification. Start with 1 acre for trial."
            else:
                return "Thank you for your question about Tamil Nadu agriculture! I can help with:\n\n- **Crop selection** for your district\n- **Fertilizer** recommendations (NPK, organic, bio)\n- **Irrigation** planning and water management\n- **Disease & pest** control (chemical + organic)\n- **Government schemes** and subsidies\n- **Organic farming** practices\n\nPlease provide more details about your specific farming situation!"
