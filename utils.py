from datetime import datetime, timezone
from uuid6 import uuid7

def generate_uuid_v7():
    return str(uuid7())

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def classify_age_group(age: int):
    if age <= 12:
        return "child"
    if 13 <= age <= 19:
        return "teenager"
    if 20 <= age <= 59:
        return "adult"
    return "senior"