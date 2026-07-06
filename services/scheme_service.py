from utils.helpers import get_mock_schemes

class SchemeService:
    def __init__(self):
        pass

    def get_all_schemes(self):
        return get_mock_schemes()

    def get_scheme_by_name(self, name):
        schemes = get_mock_schemes()
        for s in schemes:
            if name.lower() in s["name"].lower():
                return s
        return None
