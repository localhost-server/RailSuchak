import os
from typing import Dict, Any, Optional
from openai import OpenAI
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta
from services.date_service import parse_date_time, is_valid_travel_date

# Load environment variables
load_dotenv()

# Initialize OpenAI client
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

client = OpenAI(api_key=api_key)

def convert_relative_date(date_str: str) -> str:
    """Convert relative dates to YYYY-MM-DD format using robust date parsing"""
    if not date_str:
        return datetime.now().strftime('%Y-%m-%d')
        
    # Use the more robust date parser
    parsed_date = parse_date_time(date_str)
    
    if parsed_date['success']:
        # Check if the date is valid for train booking
        if is_valid_travel_date(parsed_date):
            return parsed_date['formatted']['api_format']
            
        # If date is not valid for booking, default to tomorrow
        tomorrow = datetime.now() + timedelta(days=1)
        return tomorrow.strftime('%Y-%m-%d')
    
    # Fallback to tomorrow if parsing fails
    tomorrow = datetime.now() + timedelta(days=1)
    return tomorrow.strftime('%Y-%m-%d')

def extract_query_details(user_query: str) -> Dict[str, Any]:
    """Extract structured information from user's natural language query"""
    try:
        system_prompt = """You are a helpful train booking assistant. Extract relevant information from user queries about Indian Railways.
        Identify the type of query (train_search, pnr_status, train_schedule, live_status, seat_availability, fare_check) and extract details like:
        - Train numbers (5 digits)
        - Station codes (3-4 letters, e.g., NDLS for New Delhi, CSTM for Mumbai CST)
        - PNR numbers (10 digits)
        - Travel dates - Extract exactly as mentioned by user:
          * If no date mentioned, use "today"
          * For relative dates like "today", "tomorrow", use those exact words
          * For weekdays like "monday" or "next monday", include those exact phrases
          * For dates like "25th", extract as "25"
          * For dates with month like "25th February", extract as "25 february"
        - Class preferences (1A, 2A, 3A, SL, CC, etc.)
        - Number of passengers
        
        For cities without station codes provided, use these mappings:
        - Delhi/New Delhi -> NDLS
        - Mumbai/Bombay -> CSTM
        - Kolkata -> KOAA
        - Chennai -> MAS
        - Bangalore/Bengaluru -> SBC
        
        Format response as JSON with query_type and relevant parameters.
        For dates, preserve the exact way user mentioned them (today, tomorrow, monday, next monday, 25th, etc.)."""

        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Extract information from this query: {user_query}"}
            ],
            response_format={"type": "json_object"}
        )
        
        # Parse the JSON response
        result = json.loads(response.choices[0].message.content)
        
        # Add query type if not present
        if 'query_type' not in result:
            result['query_type'] = 'general'
        
        # Add query type if not present
        query_type = result.get('query_type', 'general')
        
        # Handle dates for train search queries using improved date handling
        if query_type == 'train_search':
            # Extract any date-related field
            date_field = next((field for field in ['travel_date', 'date', 'dateOfJourney'] 
                             if field in result), None)
            
            if date_field:
                # Use robust date parsing for the found date field
                date_value = convert_relative_date(result[date_field])
            else:
                # If no date mentioned, default to tomorrow for better user experience
                date_value = convert_relative_date('tomorrow')
            
            # Update all date fields to maintain consistency
            result['travel_date'] = date_value
            result['date'] = date_value
            result['dateOfJourney'] = date_value
            
            # Add human readable format
            parsed_date = parse_date_time(date_value)
            if parsed_date['success']:
                result['date_display'] = parsed_date['formatted']['display_format']
                result['day_of_week'] = parsed_date['formatted']['day_of_week']
            
        return result
    except Exception as e:
        print(f"Error extracting query details: {str(e)}")
        return {
            'query_type': 'error',
            'error': str(e)
        }

def generate_train_response(train_data: Dict[str, Any], user_query: Optional[str] = None) -> str:
    """Generate natural language response from train data"""
    try:
        # Combine user query and train data for context
        context = {
            "user_query": user_query,
            "train_data": train_data
        }
        
        system_prompt = """You are a helpful Indian Railways assistant. Generate natural, conversational responses about train information.
        For train searches:
        - Mention train numbers, names, and timings
        - Include departure and arrival times
        - Mention available classes
        - Add helpful details about the journey
        
        For PNR status:
        - Clearly state booking status
        - Include passenger details
        - Mention train details
        
        For schedules and live status:
        - List important stations
        - Show arrival/departure times
        - Include any delays or special notices
        
        Keep responses clear, informative, and user-friendly."""
        
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate a natural response for this train data: {json.dumps(context)}"}
            ]
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating response: {str(e)}")
        return "I apologize, but I'm having trouble processing the train information right now. Please try again."

def handle_error_response(error: str) -> str:
    """Generate user-friendly error messages"""
    try:
        system_prompt = """You are a helpful Indian Railways assistant. Generate user-friendly error messages that:
        - Explain the issue clearly
        - Suggest possible solutions
        - Maintain a helpful tone
        - Guide users on next steps
        Keep responses concise and actionable."""
        
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate a user-friendly error message for: {error}"}
            ]
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating error response: {str(e)}")
        return "I apologize, but something went wrong. Please try your request again or rephrase it differently."

def format_train_details(train_data: Dict[str, Any], query_type: str) -> str:
    """Format train details based on query type"""
    try:
        # Format any dates in the train data
        for key in train_data:
            if isinstance(train_data[key], str) and any(date_word in key.lower() for date_word in ['date', 'time', 'departure', 'arrival']):
                parsed_date = parse_date_time(train_data[key])
                if parsed_date['success']:
                    train_data[f"{key}_display"] = parsed_date['formatted']['display_format']
                    if 'time' in key.lower():
                        train_data[f"{key}_display"] = parsed_date['formatted']['full_display']

        system_prompt = f"""Format the following {query_type} information in a clear, organized way.
        - Include relevant details and format times, dates, and statuses clearly
        - Use the provided formatted dates and times (fields ending in _display)
        - Add helpful context like day of week for dates
        - For journey times, include duration when available
        - Highlight any weekend travel dates
        Add helpful context where appropriate."""
        
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Format this train data: {json.dumps(train_data)}"}
            ]
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error formatting train details: {str(e)}")
        return str(train_data)  # Fallback to raw data if formatting fails
