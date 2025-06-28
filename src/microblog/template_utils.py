from datetime import datetime, timedelta, timezone
import os

from fastapi.templating import Jinja2Templates

def format_datetime(dt: datetime) -> str:
    now = datetime.now(timezone.utc)
    delta = now - dt

    if delta < timedelta(minutes=1):
        return "now"
    elif delta < timedelta(hours=1):
        minutes = int(delta.total_seconds() // 60)
        return f"{minutes} min ago"
    elif delta < timedelta(days=1):
        hours = int(delta.total_seconds() // 3600)
        return f"{hours} h ago"
    else:
        return dt.strftime("%a %b %-d, %Y %H:%M")

template_path = os.path.join(
    os.path.dirname(__file__), 'templates'
)
templates = Jinja2Templates(directory=template_path)
templates.env.filters["format_datetime"] = format_datetime
