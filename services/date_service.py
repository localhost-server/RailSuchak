import arrow
import dateparser
from typing import Optional, Dict, Any
from datetime import datetime
import pytz

# Indian timezone
INDIA_TZ = 'Asia/Kolkata'

def parse_date_time(date_string: str, reference_date: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Parse date and time from natural language input
    Returns a dictionary with parsed date information
    """
    try:
        # Use dateparser for initial parsing with Indian context
        settings = {
            'PREFER_DATES_FROM': 'future',
            'TIMEZONE': INDIA_TZ,
            'RETURN_AS_TIMEZONE_AWARE': True,
            'PREFER_DAY_OF_MONTH': 'first',
            'DATE_ORDER': 'DMY'  # Indian date format
        }
        
        if reference_date:
            settings['RELATIVE_BASE'] = reference_date
            
        parsed_date = dateparser.parse(
            date_string,
            settings=settings,
            languages=['en', 'hi']  # Support both English and Hindi
        )
        
        if not parsed_date:
            return {
                'success': False,
                'error': 'Could not parse date',
                'input': date_string
            }
            
        # Convert to Arrow for easier manipulation
        arr = arrow.get(parsed_date)
        
        # Format for different uses
        return {
            'success': True,
            'date': arr.date(),
            'datetime': arr.datetime,
            'timestamp': int(arr.timestamp()),
            'formatted': {
                'api_format': arr.format('YYYY-MM-DD'),
                'display_format': arr.format('DD MMM YYYY'),
                'full_display': arr.format('DD MMM YYYY, hh:mm A'),
                'day_of_week': arr.format('dddd')
            },
            'is_weekend': arr.weekday() in [5, 6],  # 5 = Saturday, 6 = Sunday
            'relative': arr.humanize(locale='en_in'),
            'timezone': INDIA_TZ
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'input': date_string
        }

def is_valid_travel_date(date_dict: Dict[str, Any]) -> bool:
    """Check if the parsed date is valid for train booking"""
    if not date_dict.get('success', False):
        return False
        
    try:
        date = arrow.get(date_dict['date'])
        now = arrow.now(INDIA_TZ)
        
        # Check if date is not in the past
        if date < now:
            return False
            
        # Check if date is not too far in the future (usually 120 days for Indian Railways)
        max_future = now.shift(days=120)
        if date > max_future:
            return False
            
        return True
        
    except Exception:
        return False

def get_date_range(start_date_dict: Dict[str, Any], days: int = 7) -> list:
    """Get a range of dates starting from the parsed date"""
    if not start_date_dict.get('success', False):
        return []
        
    try:
        start = arrow.get(start_date_dict['date'])
        dates = []
        
        for i in range(days):
            current = start.shift(days=i)
            dates.append({
                'date': current.format('YYYY-MM-DD'),
                'display': current.format('DD MMM YYYY'),
                'day': current.format('dddd'),
                'is_weekend': current.weekday() in [5, 6]
            })
            
        return dates
        
    except Exception:
        return []

def format_duration(minutes: int) -> str:
    """Format duration in minutes to human readable string"""
    try:
        hours = minutes // 60
        mins = minutes % 60
        
        if hours == 0:
            return f"{mins} minutes"
        elif mins == 0:
            return f"{hours} hours"
        else:
            return f"{hours} hours {mins} minutes"
            
    except Exception:
        return str(minutes) + " minutes"
