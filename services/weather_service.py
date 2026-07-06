import os
import requests
from datetime import datetime
from utils.helpers import get_mock_weather

class WeatherService:
    def __init__(self):
        self.api_key = os.getenv("WEATHER_API_KEY", "")

    def get_current_weather(self, district="Thanjavur"):
        if not self.api_key or self.api_key == "your-weather-api-key":
            return get_mock_weather()

        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={district},IN&appid={self.api_key}&units=metric"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    "temperature": round(data["main"]["temp"]),
                    "humidity": data["main"]["humidity"],
                    "wind_speed": round(data["wind"]["speed"] * 3.6, 1),
                    "rain_probability": data.get("clouds", {}).get("all", 0),
                    "condition": data["weather"][0]["main"].lower(),
                    "forecast": self._get_forecast(district),
                }
            return get_mock_weather()
        except Exception:
            return get_mock_weather()

    def _get_forecast(self, district):
        if not self.api_key or self.api_key == "your-weather-api-key":
            return get_mock_weather()["forecast"]

        try:
            url = f"http://api.openweathermap.org/data/2.5/forecast?q={district},IN&appid={self.api_key}&units=metric"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                forecast = []
                for item in data["list"][:7]:
                    from datetime import datetime
                    day_name = datetime.fromtimestamp(item["dt"]).strftime("%a")
                    forecast.append({
                        "day": day_name,
                        "temp": round(item["main"]["temp"]),
                        "rain": round(item.get("pop", 0) * 100),
                    })
                return forecast
            return get_mock_weather()["forecast"]
        except Exception:
            return get_mock_weather()["forecast"]

    def get_ai_farming_advice(self, weather_data, language="en"):
        temp = weather_data.get("temperature", 30)
        humidity = weather_data.get("humidity", 60)
        rain = weather_data.get("rain_probability", 20)
        wind = weather_data.get("wind_speed", 10)

        if language == "ta":
            if rain > 70:
                return "இன்று அதிக மழை வாய்ப்பு உள்ளது. பயிர்களுக்கு நீர் தேங்காமல் பார்த்துக்கொள்ளவும். நெல் வயலில் தண்ணீர் வெளியேறும் வசதி வேண்டும். பூச்சி மருந்து தெளிக்க வேண்டாம்."
            elif temp > 35:
                return "வெப்பநிலை அதிகமாக உள்ளது. பயிர்களுக்கு போதுமான நீர் பாய்ச்சவும். சொட்டு நீர் பாசனம் மூலம் தண்ணீர் அளிக்கலாம். காலை அல்லது மாலை நேரத்தில் மட்டும் வயலில் வேலை செய்யவும்."
            elif rain > 40:
                return "மழை வாய்ப்பு உள்ளது. உங்கள் வயலில் உரங்களை இடுவதை தவிர்க்கவும். விதைப்பு மற்றும் நடவு பணிகளை திட்டமிடவும்."
            elif wind > 20:
                return "காற்று வேகமாக வீசுகிறது. வாழை, கரும்பு போன்ற பயிர்களுக்கு ஆதரவு அளிக்கவும். தெளிப்பு பாசனம் தவிர்க்கவும்."
            else:
                return "வானிலை விவசாயத்திற்கு சாதகமாக உள்ளது. உங்கள் வழக்கமான விவசாய பணிகளை தொடரலாம். களை எடுத்தல், உரமிடுதல் போன்ற பணிகளை மேற்கொள்ளலாம்."
        else:
            if rain > 70:
                return "Heavy rain expected today. Ensure proper drainage for your crops. Check paddy fields for water stagnation. Avoid pesticide spraying today."
            elif temp > 35:
                return "High temperature detected. Ensure adequate irrigation for your crops. Use drip irrigation to conserve water and protect crops. Work in fields during morning or evening hours only."
            elif rain > 40:
                return "Rain likely today. Avoid applying fertilizers as they may wash away. Good day for planning sowing and transplanting activities."
            elif wind > 20:
                return "Strong winds detected. Provide support for banana and sugarcane crops. Avoid spraying pesticides. Consider wind breaks for sensitive crops."
            else:
                return "Weather conditions are favorable for farming. Continue with regular agricultural activities. Good day for weeding, fertilizing, and general farm maintenance."
