import os
import json
import requests

class AIService:
    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")
        self.openai_key = os.getenv("OPENAI_API_KEY", "")
        self.provider = os.getenv("AI_PROVIDER", "gemini")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def get_response(self, message, language="en", district="", history=None):
        system_prompt = self._build_system_prompt(language, district)
        messages = self._build_messages(history)
        messages.append({"role": "user", "content": message})

        if self.provider == "openai" and self.openai_key:
            return self._call_openai(system_prompt, messages, language)
        elif self.provider == "gemini" and self.gemini_key:
            return self._call_gemini(system_prompt, messages, language)
        elif self.gemini_key:
            return self._call_gemini(system_prompt, messages, language)
        elif self.openai_key:
            return self._call_openai(system_prompt, messages, language)
        else:
            return "Unable to contact the AI service at the moment. Please set the GEMINI_API_KEY or OPENAI_API_KEY environment variable and try again."

    def _call_gemini(self, system_prompt, messages, language):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={self.gemini_key}"

            contents = []
            for msg in messages:
                role = "model" if msg["role"] == "assistant" else "user"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}]
                })

            payload = {
                "system_instruction": {
                    "parts": [{"text": system_prompt}]
                },
                "contents": contents,
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 2048,
                    "topK": 40,
                    "topP": 0.95,
                },
                "safetySettings": [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]
            }

            resp = requests.post(url, json=payload, timeout=60)
            resp.raise_for_status()
            result = resp.json()

            candidates = result.get("candidates", [])
            if not candidates:
                print(f"[Gemini] No candidates in response: {json.dumps(result)[:200]}")
                return "I received an empty response from the AI service. Please try rephrasing your question."

            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                finish_reason = candidates[0].get("finishReason", "UNKNOWN")
                if finish_reason == "SAFETY":
                    return "Your question was blocked by safety filters. Please ask an agriculture-related question."
                print(f"[Gemini] No parts, finishReason={finish_reason}")
                return "The AI service could not generate a response. Please try a different question."

            text = parts[0].get("text", "")
            if not text.strip():
                return "The AI service returned an empty response. Please try again."

            return text.strip()

        except requests.exceptions.Timeout:
            print("[Gemini] Request timed out after 60s")
            return "The AI service is taking too long to respond. Please try again later."
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if hasattr(e, 'response') else 0
            print(f"[Gemini] HTTP {status}: {str(e)[:200]}")
            if status == 400:
                return "The AI service received an invalid request. You may have exceeded the message length limit."
            if status == 429:
                return "The AI service is currently overloaded. Please wait a moment and try again."
            if status == 403 or status == 401:
                return "The AI service is not properly configured. Please check your API key."
            return "Unable to contact the AI service at the moment. Please try again later."
        except requests.exceptions.ConnectionError:
            print("[Gemini] Connection error")
            return "Unable to reach the AI service. Please check your internet connection."
        except Exception as e:
            print(f"[Gemini] Unexpected error: {type(e).__name__}: {str(e)[:200]}")
            return "Unable to contact the AI service at the moment. Please try again later."

    def _call_openai(self, system_prompt, messages, language):
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.openai_key}",
                "Content-Type": "application/json",
            }

            openai_messages = [{"role": "system", "content": system_prompt}]
            for msg in messages:
                role = "assistant" if msg["role"] == "assistant" else "user"
                openai_messages.append({"role": role, "content": msg["content"]})

            payload = {
                "model": self.openai_model,
                "messages": openai_messages,
                "temperature": 0.7,
                "max_tokens": 2048,
            }

            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            result = resp.json()

            choice = result.get("choices", [{}])[0]
            text = choice.get("message", {}).get("content", "")
            if not text.strip():
                finish = choice.get("finish_reason", "UNKNOWN")
                print(f"[OpenAI] Empty response, finish_reason={finish}")
                return "The AI service returned an empty response. Please try again."

            return text.strip()

        except requests.exceptions.Timeout:
            print("[OpenAI] Request timed out")
            return "The AI service is taking too long. Please try again later."
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if hasattr(e, 'response') else 0
            print(f"[OpenAI] HTTP {status}: {str(e)[:200]}")
            if status == 429:
                return "The AI service is currently overloaded. Please wait and try again."
            if status in (401, 403):
                return "The AI service is not properly configured. Please check your API key."
            return "Unable to contact the AI service. Please try again later."
        except Exception as e:
            print(f"[OpenAI] Error: {type(e).__name__}: {str(e)[:200]}")
            return "Unable to contact the AI service at the moment. Please try again later."

    def _build_system_prompt(self, language, district=""):
        lang_instruction = (
            "Reply only in Tamil language. Use Tamil agricultural terminology."
            if language == "ta"
            else "Reply only in English."
        )

        district_context = ""
        if district:
            zone, info = self._get_zone_info(district)
            if info:
                crops = ", ".join(info.get("crops", info.get("major_crops", "").split(",")[:3]))
                crops = crops[:200]
                soil = info.get("soil", "")
                climate = info.get("climate", "")
                name_ta = info.get("name_ta", zone)
                zone_name = name_ta if language == "ta" else zone

                if language == "ta":
                    district_context = (
                        f"பயனர் {district} மாவட்டத்தைச் சேர்ந்தவர். "
                        f"இந்த மாவட்டம் {zone_name} மண்டலத்தில் உள்ளது. "
                        f"மண் வகை: {soil}. காலநிலை: {climate}. முக்கிய பயிர்கள்: {crops}. "
                        f"இந்த சூழலுக்கு ஏற்ப ஆலோசனைகளை வழங்கவும்."
                    )
                else:
                    district_context = (
                        f"The user is from {district} district ({zone_name} zone). "
                        f"Soil: {soil}. Climate: {climate}. Major crops: {crops}. "
                        f"Tailor your advice to this context."
                    )

        return (
            f"You are an expert AI Agriculture Assistant specialized in Tamil Nadu farming.\n\n"
            f"{lang_instruction}\n\n"
            f"Guidelines:\n"
            f"- Answer ONLY agriculture and farming related questions.\n"
            f"- If the user asks about non-agriculture topics (politics, entertainment, technology, general news, etc.), "
            f"politely refuse by saying you are designed only for agriculture assistance.\n"
            f"- Use the user's district and agro-climatic zone whenever relevant.\n"
            f"- Be practical, farmer-friendly and accurate.\n"
            f"- Use Markdown formatting for clarity: **bold** for emphasis, bullet points for lists, "
            f"headings for sections, and code blocks where appropriate.\n"
            f"- Keep responses well-structured but concise.\n"
            f"{district_context}"
        )

    def _get_zone_info(self, district):
        ZONE_INFO = {
            "Cauvery Delta Zone": {"soil": "Alluvial, Clay", "climate": "Tropical, 25-37°C, 900-1100mm rain", "crops": ["Paddy", "Sugarcane", "Banana", "Coconut"]},
            "North Eastern Zone": {"soil": "Red Sandy Loam, Clay Loam", "climate": "Sub-tropical, 22-35°C, 900-1200mm rain", "crops": ["Paddy", "Groundnut", "Sugarcane", "Vegetables", "Mango"]},
            "Western Zone": {"soil": "Red Loam, Black Soil", "climate": "Semi-arid, 20-38°C, 600-800mm rain", "crops": ["Coconut", "Cotton", "Turmeric", "Banana", "Vegetables"]},
            "Southern Zone": {"soil": "Red Sandy, Black, Coastal Alluvium", "climate": "Semi-arid to Dry, 22-36°C, 700-900mm rain", "crops": ["Cotton", "Paddy", "Groundnut", "Chilli", "Pulses"]},
            "Hilly Zone": {"soil": "Red Loamy, Laterite, Forest Soil", "climate": "Cool, 12-25°C, 1200-2000mm rain", "crops": ["Tea", "Coffee", "Spices", "Vegetables", "Fruits"]},
            "High Rainfall Zone": {"soil": "Deep Red Loam, Coastal Alluvium", "climate": "Tropical, 24-34°C, 1500-2500mm rain", "crops": ["Coconut", "Rubber", "Pepper", "Cloves", "Banana"]},
        }
        DISTRICT_ZONES = {
            "Cauvery Delta Zone": ["Thanjavur", "Tiruvarur", "Nagapattinam", "Mayiladuthurai"],
            "North Eastern Zone": ["Chennai", "Chengalpattu", "Kancheepuram", "Tiruvallur", "Cuddalore", "Villupuram", "Kallakurichi", "Vellore", "Ranipet", "Tirupattur", "Tiruvannamalai"],
            "Western Zone": ["Coimbatore", "Tiruppur", "Erode", "Karur", "Namakkal", "Dindigul", "Theni"],
            "Southern Zone": ["Madurai", "Virudhunagar", "Thoothukudi", "Tirunelveli", "Tenkasi", "Sivaganga", "Ramanathapuram", "Pudukkottai"],
            "Hilly Zone": ["Nilgiris"],
            "High Rainfall Zone": ["Kanniyakumari"],
        }
        ALL_DISTRICTS = [
            "Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore",
            "Dharmapuri", "Dindigul", "Erode", "Kallakurichi", "Kancheepuram",
            "Kanniyakumari", "Karur", "Krishnagiri", "Madurai", "Mayiladuthurai",
            "Nagapattinam", "Namakkal", "Nilgiris", "Perambalur", "Pudukkottai",
            "Ramanathapuram", "Ranipet", "Salem", "Sivaganga", "Tenkasi",
            "Thanjavur", "Theni", "Thoothukudi", "Tiruchirappalli", "Tirunelveli",
            "Tirupathur", "Tiruppur", "Tiruvallur", "Tiruvannamalai", "Tiruvarur",
            "Vellore", "Villupuram", "Virudhunagar",
        ]

        if district not in ALL_DISTRICTS:
            return None, None

        for zone, districts in DISTRICT_ZONES.items():
            if district in districts:
                return zone, ZONE_INFO.get(zone)

        for zone, districts in {
            "Cauvery Delta Zone": ["Ariyalur", "Perambalur", "Tiruchirappalli"],
            "North Eastern Zone": ["Dharmapuri", "Krishnagiri", "Salem"],
            "Southern Zone": ["Thoothukudi", "Tirunelveli"],
        }.items():
            if district in districts:
                return zone, ZONE_INFO.get(zone)

        return None, None

    def _build_messages(self, history=None):
        messages = []
        if history:
            for msg in history[-20:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
        return messages
