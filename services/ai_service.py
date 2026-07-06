import os
import json
import requests
from flask import current_app

class AIService:
    def __init__(self):
        self.api_key = os.getenv("AI_API_KEY", "")
        self.api_url = os.getenv("AI_API_URL", "https://api.anthropic.com/v1/messages")
        self.model = os.getenv("AI_MODEL", "claude-3-haiku-20240307")

    def get_response(self, prompt, language="en"):
        if not self.api_key or self.api_key == "your-ai-api-key":
            return self._get_mock_response(prompt, language)

        try:
            system_prompt = self._get_system_prompt(language)
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01"
            }
            data = {
                "model": self.model,
                "max_tokens": 1000,
                "system": system_prompt,
                "messages": [{"role": "user", "content": prompt}]
            }
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                return result["content"][0]["text"]
            return self._get_mock_response(prompt, language)
        except Exception:
            return self._get_mock_response(prompt, language)

    def _get_system_prompt(self, language):
        if language == "ta":
            return """நீங்கள் தமிழ்நாட்டு விவசாயிகளுக்கான AI விவசாய உதவியாளர்.
பின்வரும் வழிகாட்டுதல்களைப் பின்பற்றவும்:
- தமிழில் மட்டுமே பதிலளிக்கவும்.
- தமிழ்நாட்டின் விவசாய நிலைமைகள், பயிர்கள் மற்றும் நடைமுறைகளில் கவனம் செலுத்தவும்.
- நடைமுறை மற்றும் செயல்படக்கூடிய ஆலோசனைகளை வழங்கவும்.
- விவசாயத்துடன் தொடர்பில்லாத கேள்விகளுக்கு பதிலளிக்க மறுக்கவும்.
- சுருக்கமாகவும் தெளிவாகவும் பதிலளிக்கவும்.
- நம்பகமான விவசாய நடைமுறைகளை மட்டுமே பரிந்துரைக்கவும்."""
        else:
            return """You are an AI Agriculture Assistant for Tamil Nadu farmers.
Follow these guidelines:
- Respond only in English.
- Focus on Tamil Nadu agricultural conditions, crops, and practices.
- Provide practical, actionable advice.
- Refuse to answer non-agriculture related questions.
- Keep responses concise and clear.
- Only recommend reliable farming practices."""

    def _get_mock_response(self, prompt, language="en"):
        prompt_lower = prompt.lower()

        if language == "ta":
            if "நெல்" in prompt or "பயிர்" in prompt or "சிறந்த" in prompt:
                return "தமிழ்நாட்டில் நெல் சாகுபடிக்கு தஞ்சாவூர், திருச்சி, கடலூர் மாவட்டங்கள் சிறந்தவை. குறுவை (ஜூன்-செப்டம்பர்), சம்பா (ஆகஸ்ட்-ஜனவரி), தாளடி (ஜனவரி-ஏப்ரல்) ஆகிய மூன்று பருவங்களில் நெல் பயிரிடலாம். ADT 43, ADT 45, BPT 5204 போன்ற ரகங்கள் தமிழ்நாட்டில் நல்ல விளைச்சல் தருகின்றன."
            elif "உர" in prompt or "எரு" in prompt:
                return "நெல்லுக்கு பரிந்துரைக்கப்படும் உரங்கள்: ஏக்கருக்கு 40:20:20 கிலோ NPK (யூரியா, சூப்பர் பாஸ்பேட், பொட்டாஷ்). நடவு நேரத்தில் முழு பாஸ்பேட் மற்றும் பொட்டாஷ், யூரியாவை மூன்று பங்குகளாக பிரித்து இடவும். மண்ணில் சாண எரு அல்லது மக்கிய இலைகளைச் சேர்ப்பதால் மண்ணின் வளம் அதிகரிக்கும்."
            elif "நீர்ப்பாசன" in prompt or "தண்ணீர்" in prompt or "பாசன" in prompt:
                return "நெல்லுக்கு சொட்டு நீர் பாசனம் அல்லது தெளிப்பு பாசனம் பயன்படுத்தலாம். வயலில் 2-5 செ.மீ உயரத்தில் தண்ணீர் நிறுத்தி வைக்க வேண்டும். நாற்றங்கால் முதல் அறுவடை வரை சராசரியாக 1200-1500 மி.மீ தண்ணீர் தேவைப்படுகிறது. மழைநீர் சேகரிப்பு கட்டாயம்."
            elif "நோய்" in prompt or "பூச்சி" in prompt:
                return "நெல்லில் பொதுவான நோய்கள்: இலைக்கருகல் (தாமிர கலவை தெளிப்பு), தண்டழுகல் (கார்பென்டாசிம்), பாக்டீரியல் இலைக்கருகல் (ஸ்ட்ரெப்டோமைசின்). பூச்சிகள்: தண்டு துளைப்பான் (கார்போஃப்யூரான்), இலைப்பேன் (மோனோக்ரோடோபாஸ்). இயற்கை முறையில் வேப்ப எண்ணெய், சூடோமோனாஸ் பாக்டீரியா பயன்படுத்தலாம்."
            elif "அரசு" in prompt or "திட்டம்" in prompt:
                return "தமிழ்நாடு விவசாயிகளுக்கான அரசு திட்டங்கள்: 1. பிரதான் மந்திரி பயிர் காப்பீடு திட்டம் (PMFBY) 2. PM-KISAN (வருடத்திற்கு ரூ.6000) 3. மண் ஆரோக்கிய அட்டை திட்டம் 4. நுண்ணீர் பாசன திட்டம் (80% மானியம்) 5. இயற்கை வேளாண்மை திட்டம். மேலும் விவரங்களுக்கு https://www.tn.gov.in பார்க்கவும்."
            elif "இயற்கை" in prompt or "கரிம" in prompt:
                return "இயற்கை வேளாண்மை குறிப்புகள்: 1. பசுந்தாள் உரங்கள் பயன்படுத்துதல் (தட்டைப்பயறு, கோழிவரகு) 2. மக்கிய சாண எருவினை இடுதல் 3. வேம்பு சார்ந்த பூச்சி விரட்டிகள் 4. பயிர் சுழற்சி முறை கடைப்பிடித்தல் 5. உயிர் உரங்கள் (ரைசோபியம், அசோஸ்பைரில்லம்) பயன்பாடு. தமிழ்நாடு அரசு இயற்கை வேளாண்மைக்கு மானியம் வழங்குகிறது."
            else:
                return "தமிழ்நாட்டில் விவசாயம் பற்றிய உங்கள் கேள்விக்கு நன்றி. பயிர் சாகுபடி, உரங்கள், நீர்ப்பாசனம், நோய் கட்டுப்பாடு, அரசு திட்டங்கள் போன்றவை பற்றி கேட்கலாம். தயவுசெய்து உங்கள் கேள்வியை விவரமாக கேளுங்கள்."
        else:
            if "crop" in prompt_lower or "best" in prompt_lower or "grow" in prompt_lower or "cultivate" in prompt_lower:
                if "district" in prompt_lower or "coimbatore" in prompt_lower or "thanjavur" in prompt_lower:
                    return "For Coimbatore district, the best crops are coconut, turmeric, banana, and vegetables. The region has black and red soil with good irrigation from Bhavani and Noyyal rivers. Coconut farming is especially profitable. For Thanjavur, paddy is the best crop - the 'Rice Bowl of Tamil Nadu' with three seasons: Kuruvai (June-Sept), Samba (Aug-Jan), and Thaladi (Jan-April)."
                return "Tamil Nadu's major crops: Paddy (Thanjavur, Tiruchy, Cuddalore), Coconut (Coimbatore, Pollachi), Sugarcane (Erode, Villupuram), Banana (Namakkal, Tiruchy), Cotton (Salem, Virudhunagar), Groundnut (Tiruppur), Millets (Dharmapuri). Choose crops based on your district's climate and soil conditions."
            elif "fertilizer" in prompt_lower or "manure" in prompt_lower:
                return "For paddy in Tamil Nadu: Apply 40:20:20 kg NPK per acre (Urea, Super Phosphate, Potash). Apply full Phosphate and Potash at transplanting. Split Urea into 3 doses - basal, tillering, and panicle initiation. Add FYM (Farm Yard Manure) 5-7 tons per acre before transplanting. For organic farming, use vermicompost, green manure like daincha, and bio-fertilizers like Azospirillum."
            elif "irrigation" in prompt_lower or "water" in prompt_lower:
                return "For paddy irrigation: Maintain 2-5 cm standing water in the field. Total water requirement: 1200-1500 mm per season. Critical stages: panicle initiation and flowering. Drip irrigation can save 30-40% water. For coconut: 40-60 liters per tree per week. Rainwater harvesting through farm ponds is recommended for Tamil Nadu's variable rainfall."
            elif "disease" in prompt_lower or "pest" in prompt_lower or "treatment" in prompt_lower:
                return "Common paddy diseases in TN: 1. Blast - use Carbendazim or Tricyclazole. 2. Sheath Blight - use Hexaconazole. 3. Bacterial Leaf Blight - use Streptomycin. Organic alternatives: Neem oil spray (3%), Pseudomonas fluorescens, Trichoderma viride. For stem borer: use Carbofuran granules. Always practice crop rotation and resistant varieties."
            elif "scheme" in prompt_lower or "government" in prompt_lower or "subsidy" in prompt_lower:
                return "Tamil Nadu farmer schemes: 1. PM Fasal Bima Yojana (crop insurance) 2. PM-KISAN (Rs.6000/year) 3. TN Organic Farming Policy (subsidy) 4. e-NAM (online trading) 5. Micro Irrigation Scheme (up to 80% subsidy) 6. Soil Health Card Scheme. Apply at nearest Agriculture Department office or online at https://www.tn.gov.in"
            elif "organic" in prompt_lower:
                return "Organic farming tips for Tamil Nadu: 1. Use green manure crops (daincha, cowpea). 2. Apply well-decomposed FYM. 3. Use neem-based pesticides. 4. Practice crop rotation. 5. Use bio-fertilizers (Rhizobium, Azospirillum, Phosphobacteria). Tamil Nadu government provides subsidy for organic certification. Start with 1 acre for trial."
            else:
                return "Thank you for your question about Tamil Nadu agriculture. I can help with: crop selection, fertilizers, irrigation, disease management, government schemes, organic farming, and more. Please provide more details about your specific farming situation for a better recommendation."
