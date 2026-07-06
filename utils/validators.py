import re

def validate_username(username):
    if not username or len(username) < 4:
        return False, "Username must be at least 4 characters."
    if not re.match("^[a-zA-Z0-9_]+$", username):
        return False, "Username can only contain letters, numbers, and underscores."
    return True, None

def validate_password(password):
    if not password or len(password) < 4:
        return False, "Password must be at least 4 characters."
    return True, None

def validate_crop_data(data):
    required = ["crop_name", "district", "soil_type", "land_size"]
    for field in required:
        if not data.get(field):
            return False, f"{field} is required."
    try:
        size = float(data["land_size"])
        if size <= 0:
            return False, "Land size must be positive."
    except (ValueError, TypeError):
        return False, "Invalid land size."
    return True, None

def validate_expense_data(data):
    required = ["amount", "category"]
    for field in required:
        if not data.get(field):
            return False, f"{field} is required."
    try:
        amount = float(data["amount"])
        if amount <= 0:
            return False, "Amount must be positive."
    except (ValueError, TypeError):
        return False, "Invalid amount."
    return True, None
