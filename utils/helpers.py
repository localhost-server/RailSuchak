"""Helper functions used throughout the application"""
import re
from typing import Dict, Any, Optional, List
from .constants import MAJOR_STATIONS, TRAIN_CLASSES

def extract_station_code(station_input: str) -> str:
    """
    Extract station code from input string
    Handles both code (NDLS) and name (New Delhi) formats
    """
    # If input is already a valid station code (3-4 uppercase letters)
    if re.match(r'^[A-Z]{3,4}$', station_input):
        return station_input
        
    # Convert to uppercase for comparison
    station_upper = station_input.upper()
    
    # Check if the input matches any known station names
    for code, name in MAJOR_STATIONS.items():
        if name.upper() in station_upper or station_upper in name.upper():
            return code
            
    # If no match found, return the original input cleaned up
    # Remove special characters and take first 4 letters
    cleaned = re.sub(r'[^A-Z]', '', station_upper)[:4]
    return cleaned or station_input

def format_train_class(class_code: str) -> str:
    """Convert class code to full name"""
    return TRAIN_CLASSES.get(class_code.upper(), class_code)

def format_duration(minutes: int) -> str:
    """Format duration in minutes to readable string"""
    hours = minutes // 60
    mins = minutes % 60
    
    if hours == 0:
        return f"{mins}m"
    elif mins == 0:
        return f"{hours}h"
    else:
        return f"{hours}h {mins}m"

def format_fare(fare: float, currency: str = '₹') -> str:
    """Format fare with currency symbol"""
    return f"{currency}{fare:,.2f}"

def format_train_name(train_name: str) -> str:
    """Format train name for display"""
    # Remove extra spaces and standardize separators
    name = re.sub(r'\s+', ' ', train_name).strip()
    
    # Capitalize first letter of each word
    return ' '.join(word.capitalize() for word in name.split())

def extract_pnr_number(text: str) -> Optional[str]:
    """Extract 10-digit PNR number from text"""
    pnr_match = re.search(r'\b\d{10}\b', text)
    return pnr_match.group() if pnr_match else None

def format_train_status(status: Dict[str, Any]) -> Dict[str, Any]:
    """Format train status response for display"""
    formatted = {
        'train_no': status.get('train_number'),
        'train_name': format_train_name(status.get('train_name', '')),
        'from': status.get('from_station'),
        'to': status.get('to_station'),
        'departure': status.get('departure_time'),
        'arrival': status.get('arrival_time'),
        'duration': format_duration(status.get('duration_mins', 0)),
        'status': status.get('running_status', 'No Information'),
        'platform': status.get('platform', 'TBD')
    }
    
    if 'fare' in status:
        formatted['fare'] = format_fare(status['fare'])
        
    return formatted

def chunk_message(message: str, chunk_size: int = 1000) -> List[str]:
    """Split long messages into smaller chunks for API limits"""
    return [message[i:i + chunk_size] for i in range(0, len(message), chunk_size)]

def is_valid_station_code(code: str) -> bool:
    """Check if the station code format is valid"""
    return bool(re.match(r'^[A-Z]{3,4}$', code))

def is_valid_train_number(number: str) -> bool:
    """Check if the train number format is valid"""
    return bool(re.match(r'^\d{5}$', number))

def is_valid_pnr(pnr: str) -> bool:
    """Check if the PNR number format is valid"""
    return bool(re.match(r'^\d{10}$', pnr))

def sanitize_input(text: str) -> str:
    """Clean user input for safe processing"""
    # Remove any potential harmful characters
    cleaned = re.sub(r'[^\w\s\-.,]', '', text)
    # Remove extra whitespace
    cleaned = ' '.join(cleaned.split())
    return cleaned
