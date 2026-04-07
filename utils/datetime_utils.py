from datetime import datetime, timedelta
from typing import Dict


def get_utc_now() -> datetime:
    """Get current UTC datetime - centralized for consistent timestamps"""
    return datetime.utcnow()


def format_timestamp(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime to consistent display string"""
    if dt is None:
        return ""
    return dt.strftime(fmt)


def get_date_range(days: int = 7) -> Dict[str, datetime]:
    """Get date range from now going back N days
    
    Returns:
        {'start': datetime, 'end': datetime}
    """
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    return {'start': start, 'end': end}