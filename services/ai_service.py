import os
from google import genai
from google.genai import types
from google.genai.errors import APIError, ClientError, ServerError

class AIService:
    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")
        self.openai_key = os.getenv("OPENAI_API_KEY", "")
        self.provider = os.getenv("AI_PROVIDER", "gemini")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self._client = None

    def _get_client(self):
        if self._client is None:
            key = self.gemini_key
            if not key:
                key = self.openai_key
            self._client = genai.Client(api_key=key)
        return self._client

    def get_response(self, message, language="en", district="", history=None):
        if not self.gemini_key:
            return "AI service is not configured. Please set GEMINI_API_KEY in .env file."

        system_prompt = self._build_system_prompt(language, district)

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.7,
            max_output_tokens=2048,
            top_p=0.95,
            top_k=40,
        )

        try:
            client = self._get_client()

            if history and len(history) > 0:
                chat_history = []
                for msg in history[-20:]:
                    role = "model" if msg["role"] == "assistant" else "user"
                    chat_history.append(
                        types.Content(
                            role=role,
                            parts=[types.Part(text=msg["content"])]
                        )
                    )

                chat = client.chats.create(
                    model=self.gemini_model,
                    history=chat_history,
                    config=config,
                )
                response = chat.send_message(message)
                result = response.text
            else:
                response = client.models.generate_content(
                    model=self.gemini_model,
                    contents=message,
                    config=config,
                )
                result = response.text

            if not result or not result.strip():
                return "The AI service returned an empty response. Please try again."

            return result.strip()

        except ServerError as e:
            status = e.code if hasattr(e, 'code') else 0
            print(f"[Gemini] Server error {status}: {str(e)[:200]}")
            if status == 429:
                return "The AI service is currently overloaded. Please wait a moment and try again."
            if status in (403, 401):
                return "The AI service is not properly configured. Please check your API key."
            return "Unable to contact the AI service at the moment. Please try again later."
        except ClientError as e:
            err_str = str(e)
            print(f"[Gemini] Client error: {err_str[:200]}")
            if "UNAUTHENTICATED" in err_str or "API_KEY" in err_str:
                return "The AI service is not properly configured. Please check your Gemini API key."
            return "The AI service received an invalid request. Please try rephrasing your question."
        except APIError as e:
            print(f"[Gemini] API error: {str(e)[:200]}")
            return "Unable to contact the AI service at the moment. Please try again later."
        except Exception as e:
            print(f"[Gemini] Unexpected error: {type(e).__name__}: {str(e)[:200]}")
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
