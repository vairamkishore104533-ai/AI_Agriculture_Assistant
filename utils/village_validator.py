import os
import json
import re
import requests
import time
from utils.translations import get_text

class VillageValidator:
    def __init__(self):
        self.dataset_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'tamil_nadu_villages.json')
        self.village_map = {}
        self.loaded = False

    def load_dataset(self):
        if self.loaded:
            return
        
        if os.path.exists(self.dataset_path):
            try:
                with open(self.dataset_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    for record in data:
                        v_name = self.normalize(record.get('village_name', ''))
                        d_name = self.normalize(record.get('district_name', ''))
                        if v_name and d_name:
                            if v_name not in self.village_map:
                                self.village_map[v_name] = set()
                            self.village_map[v_name].add(d_name)
            except Exception as e:
                print(f"[ERROR] Loading village dataset failed: {e}")
        self.loaded = True

    def normalize(self, text):
        if not text:
            return ""
        # Remove extra spaces and convert to lowercase
        text = str(text).lower().strip()
        text = re.sub(r'\s+', ' ', text)
        return text

    def validate(self, village, district, lang="en"):
        if not village or not district:
            return {
                "valid": False,
                "status": "error",
                "message": get_text("village_and_district_required", lang)
            }

        self.load_dataset()
        norm_village = self.normalize(village)
        norm_district = self.normalize(district)

        # 1. Local Dataset Lookup
        if norm_village in self.village_map:
            mapped_districts = self.village_map[norm_village]
            
            # Direct match
            if norm_district in mapped_districts:
                return {
                    "valid": True,
                    "status": "verified",
                    "source": "local",
                    "village": village,
                    "district": district,
                    "message": get_text("village_verified", lang)
                }
            else:
                # Exists locally, but wrong district
                # Get one actual district to show in message
                actual_district = list(mapped_districts)[0].title()
                return {
                    "valid": False,
                    "status": "district_mismatch",
                    "source": "local",
                    "village": village,
                    "selected_district": district,
                    "actual_district": actual_district,
                    "message": get_text("district_mismatch", lang)
                }

        # 2. Nominatim Fallback
        return self._nominatim_fallback(village, district, norm_village, norm_district, lang)

    def _nominatim_fallback(self, village, district, norm_village, norm_district, lang):
        try:
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                "q": f"{village}, Tamil Nadu, India",
                "format": "json",
                "addressdetails": 1,
                "limit": 5,
                "countrycodes": "in"
            }
            headers = {
                "User-Agent": "TN-Agri-Assistant/1.0 (https://github.com/vairamkishore104533-ai/AI_Agriculture_Assistant)"
            }
            
            # Simple rate limiting protection
            time.sleep(1)
            
            response = requests.get(url, params=params, headers=headers, timeout=5)
            
            print(f"[VILLAGE-VALIDATOR] Nominatim status={response.status_code} for village='{village}' district='{district}'")
            
            if response.status_code == 403:
                print("[VILLAGE-VALIDATOR] Nominatim returned 403 Forbidden - likely IP blocked by Nominatim usage policy")
                raise Exception(f"Nominatim 403 Forbidden")
            if response.status_code == 429:
                print("[VILLAGE-VALIDATOR] Nominatim returned 429 Too Many Requests - rate limited")
                raise Exception(f"Nominatim 429 Rate Limited")
            if response.status_code != 200:
                raise Exception(f"Nominatim API error: HTTP {response.status_code}")

            results = response.json()
            if not results:
                return {
                    "valid": False,
                    "status": "not_found",
                    "message": get_text("village_not_found", lang)
                }

            # Filter relevant results
            valid_results = []
            for res in results:
                addr = res.get("address", {})
                country = self.normalize(addr.get("country", ""))
                state = self.normalize(addr.get("state", ""))
                
                if country == "india" and state == "tamil nadu":
                    res_district = self.normalize(addr.get("state_district", addr.get("county", addr.get("city", ""))))
                    # strip 'district' from the nominatim response if present
                    res_district = res_district.replace(" district", "").replace(" district", "").strip()
                    
                    if res_district:
                        valid_results.append(res_district)

            if not valid_results:
                return {
                    "valid": False,
                    "status": "not_found",
                    "message": get_text("village_not_found", lang)
                }

            # Check if any match the user's district
            for res_district in valid_results:
                if res_district == norm_district or norm_district in res_district or res_district in norm_district:
                    return {
                        "valid": True,
                        "status": "verified",
                        "source": "nominatim",
                        "village": village,
                        "district": district,
                        "message": get_text("village_verified", lang)
                    }

            # Check if ambiguous (multiple different districts returned)
            unique_districts = set(valid_results)
            if len(unique_districts) > 1:
                return {
                    "valid": False,
                    "status": "ambiguous",
                    "message": get_text("location_unclear", lang)
                }

            # Otherwise it's a mismatch
            actual_district = list(unique_districts)[0].title()
            return {
                "valid": False,
                "status": "district_mismatch",
                "source": "nominatim",
                "village": village,
                "selected_district": district,
                "actual_district": actual_district,
                "message": get_text("district_mismatch", lang)
            }

        except requests.exceptions.Timeout:
            print(f"[VILLAGE-VALIDATOR] Nominatim TIMEOUT for village='{village}' district='{district}'")
            return {
                "valid": False,
                "status": "error",
                "message": get_text("verification_unavailable", lang)
            }
        except requests.exceptions.ConnectionError as e:
            print(f"[VILLAGE-VALIDATOR] Nominatim CONNECTION ERROR: {e}")
            return {
                "valid": False,
                "status": "error",
                "message": get_text("verification_unavailable", lang)
            }
        except Exception as e:
            print(f"[VILLAGE-VALIDATOR] Nominatim fallback failed: {type(e).__name__}: {e}")
            return {
                "valid": False,
                "status": "error",
                "message": get_text("verification_unavailable", lang)
            }

village_validator = VillageValidator()
