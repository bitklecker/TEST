import datetime

def format_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        return None

def truncate(text, max_length=50):
    return (text[:max_length] + "...") if text and len(text) > max_length else text
