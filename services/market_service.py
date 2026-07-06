from utils.helpers import get_mock_market_prices

class MarketService:
    def __init__(self):
        pass

    def get_prices(self, district=None, crop=None):
        prices = get_mock_market_prices()
        if district:
            prices = [p for p in prices if p["district"].lower() == district.lower()]
        if crop:
            prices = [p for p in prices if crop.lower() in p["crop"].lower()]
        return prices

    def get_nearby_markets(self, district):
        all_markets = [
            {"name": "Thanjavur Regulated Market", "district": "Thanjavur", "distance": "0 km"},
            {"name": "Kumbakonam Market", "district": "Thanjavur", "distance": "40 km"},
            {"name": "Tiruchy Market", "district": "Tiruchirappalli", "distance": "55 km"},
            {"name": "Pollachi Market", "district": "Coimbatore", "distance": "0 km"},
            {"name": "Coimbatore Market", "district": "Coimbatore", "distance": "35 km"},
            {"name": "Erode Market", "district": "Erode", "distance": "0 km"},
            {"name": "Salem Market", "district": "Salem", "distance": "0 km"},
            {"name": "Madurai Market", "district": "Madurai", "distance": "0 km"},
            {"name": "Virudhunagar Market", "district": "Virudhunagar", "distance": "0 km"},
            {"name": "Rasipuram Market", "district": "Namakkal", "distance": "0 km"},
            {"name": "Thally Market", "district": "Krishnagiri", "distance": "0 km"},
            {"name": "Tiruppur Market", "district": "Tiruppur", "distance": "0 km"},
        ]
        return [m for m in all_markets if m["district"].lower() == district.lower()] or all_markets[:3]
