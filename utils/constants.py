"""Constants used throughout the application"""

# Train class codes
TRAIN_CLASSES = {
    '1A': 'First AC',
    '2A': 'Second AC',
    '3A': 'Third AC',
    'SL': 'Sleeper',
    'CC': 'Chair Car',
    '2S': 'Second Sitting',
    'EC': 'Executive Chair Car',
    'FC': 'First Class'
}

# Common station codes
MAJOR_STATIONS = {
    'NDLS': 'New Delhi',
    'BCT': 'Mumbai Central',
    'CSTM': 'Mumbai CST',
    'HWH': 'Howrah',
    'MAS': 'Chennai Central',
    'SBC': 'Bengaluru',
    'PUNE': 'Pune Junction',
    'ADI': 'Ahmedabad',
    'CNB': 'Kanpur Central',
    'LKO': 'Lucknow',
}

# API Endpoints
API_ENDPOINTS = {
    'SEARCH_TRAINS': 'api/v3/searchTrain',
    'TRAIN_SCHEDULE': 'api/v1/getTrainSchedule',
    'PNR_STATUS': 'api/v2/pnr-status',
    'SEAT_AVAILABILITY': 'api/v1/checkSeatAvailability',
    'SEARCH_STATION': 'api/v1/searchStation'
}

# OpenAI prompts
TRAIN_QUERY_PROMPT = """You are a helpful train booking assistant. Help users find trains and provide information about Indian Railways services.
Current context: {context}
User query: {query}
"""

ERROR_RESPONSE_PROMPT = """Generate a user-friendly error message for the following error:
Error: {error}
Make it conversational and suggest next steps if applicable.
"""

# Date formats
DATE_FORMATS = {
    'API': 'YYYY-MM-DD',
    'DISPLAY': 'DD MMM YYYY',
    'FULL': 'DD MMM YYYY, hh:mm A'
}

# Status messages
STATUS_MESSAGES = {
    'LISTENING': 'Listening...',
    'PROCESSING': 'Processing your request...',
    'SPEAKING': 'Speaking...',
    'IDLE': 'Click to start',
    'ERROR': 'Something went wrong. Please try again.'
}

# Maximum limits
LIMITS = {
    'MAX_FUTURE_DAYS': 120,  # Maximum days in advance for train booking
    'MAX_RETRY_ATTEMPTS': 3,  # Maximum API retry attempts
    'TIMEOUT_SECONDS': 30,    # API timeout in seconds
}
