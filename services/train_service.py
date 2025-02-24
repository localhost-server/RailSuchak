import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from .date_service import parse_date_time, is_valid_travel_date
from utils.helpers import is_valid_station_code, is_valid_train_number, is_valid_pnr

# Load environment variables
load_dotenv()
DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'

class TrainService:
    def __init__(self):
        self.api_key = os.getenv('RAPIDAPI_KEY')
        self.base_url = "https://irctc1.p.rapidapi.com"
        self.headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": "irctc1.p.rapidapi.com"
        }
        self.debug_mode = DEBUG_MODE

    def format_debug_response(self, query_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Format a debug response explaining what would be sent to the API"""
        
        # Map query types to human readable descriptions
        query_descriptions = {
            'train_search': 'search for trains',
            'pnr_status': 'check PNR status',
            'train_schedule': 'get train schedule',
            'live_status': 'check live train status',
            'seat_availability': 'check seat availability',
            'fare_check': 'check train fare'
        }

        # Build understanding explanation
        understanding = f"I understand you want to {query_descriptions.get(query_type, 'make a query')}.\n\n"
        
        # Add parameter explanations
        if 'fromStationCode' in params and 'toStationCode' in params:
            understanding += f"From: {params['fromStationCode']}\n"
            understanding += f"To: {params['toStationCode']}\n"
        if 'dateOfJourney' in params:
            understanding += f"Date: {params['dateOfJourney']}\n"
        if 'trainNo' in params:
            understanding += f"Train Number: {params['trainNo']}\n"
        if 'pnrNumber' in params:
            understanding += f"PNR Number: {params['pnrNumber']}\n"
        if 'classType' in params:
            understanding += f"Class: {params['classType']}\n"
        if 'query' in params:
            understanding += f"Search Query: {params['query']}\n"
        if 'startDay' in params:
            understanding += f"Start Day: {params['startDay']}\n"
        if 'quota' in params:
            understanding += f"Quota: {params['quota']}\n"
        if 'date' in params:
            understanding += f"Date: {params['date']}\n"
        
        # Add API request details
        understanding += f"\nIn non-debug mode, I would make an API request to:\n"
        understanding += f"Endpoint: {self.base_url}/api/v3/{query_type}\n"
        understanding += f"Parameters: {json.dumps(params, indent=2)}"
        
        return {
            'success': True,
            'debug': True,
            'understanding': understanding,
            'query_type': query_type,
            'params': params
        }

    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make a request to the IRCTC API"""
        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, headers=self.headers, params=params)
            return response.json()
        except Exception as e:
            print(f"API request error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def search_train(self, train_number: str) -> Dict[str, Any]:
        """Search train by number"""
        try:
            if not is_valid_train_number(train_number):
                return {
                    'success': False,
                    'error': 'Invalid train number format'
                }

            params = {"query": train_number}
            
            # If in debug mode, return understanding instead of making API call
            if self.debug_mode:
                return self.format_debug_response('train_search', params)
                
            return self._make_request("api/v1/searchTrain", params)
        except Exception as e:
            return {
                'success': False,
                'error': 'Failed to search train',
                'details': str(e)
            }

    def search_station(self, station_code: str) -> Dict[str, Any]:
        """Search station by code"""
        try:
            params = {"query": station_code.upper()}
            
            # If in debug mode, return understanding instead of making API call
            if self.debug_mode:
                return self.format_debug_response('station_search', params)
                
            return self._make_request("api/v1/searchStation", params)
        except Exception as e:
            return {
                'success': False,
                'error': 'Failed to search station',
                'details': str(e)
            }

    def get_trains_between_stations(self, from_station: str, to_station: str, date_string: Optional[str] = None) -> Dict[str, Any]:
        """Get trains between stations using v3 API"""
        try:
            # Validate station codes
            if not all(is_valid_station_code(code) for code in [from_station, to_station]):
                return {
                    'success': False,
                    'error': 'Invalid station code format'
                }

            # Base params
            params = {
                "fromStationCode": from_station.upper(),
                "toStationCode": to_station.upper()
            }

            # Handle date parameter
            try:
                # If no date provided, use today
                if not date_string:
                    date_string = 'today'
                
                # Convert date to required format (YYYY-MM-DD)
                if isinstance(date_string, str):
                    if date_string.lower() == 'tomorrow':
                        target_date = datetime.now() + timedelta(days=1)
                    elif date_string.lower() == 'today':
                        target_date = datetime.now()
                    else:
                        # Try to parse the provided date
                        target_date = datetime.strptime(date_string, '%Y-%m-%d')
                    
                    params["dateOfJourney"] = target_date.strftime('%Y-%m-%d')
            except Exception as e:
                print(f"Date conversion error: {str(e)}")
                # If date conversion fails, use today's date
                params["dateOfJourney"] = datetime.now().strftime('%Y-%m-%d')

            # If in debug mode, return understanding instead of making API call
            if self.debug_mode:
                return self.format_debug_response('train_search', params)

            print(f"Making API request with params: {json.dumps(params, indent=2)}")
            url = f"{self.base_url}/api/v3/trainBetweenStations"
            response = requests.get(url, headers=self.headers, params=params)
            result = response.json()
            print(f"API response: {json.dumps(result, indent=2)}")
            return result

        except Exception as e:
            error_msg = str(e)
            print(f"Error getting trains between stations: {error_msg}")
            return {
                'success': False,
                'error': 'Failed to get trains between stations',
                'details': error_msg
            }

    def get_live_train_status(self, train_number: str, start_day: str = "1") -> Dict[str, Any]:
        """Get live train status"""
        try:
            if not is_valid_train_number(train_number):
                return {
                    'success': False,
                    'error': 'Invalid train number format'
                }

            params = {
                "trainNo": train_number,
                "startDay": start_day
            }
            
            # If in debug mode, return understanding instead of making API call
            if self.debug_mode:
                return self.format_debug_response('live_status', params)
                
            return self._make_request("api/v1/liveTrainStatus", params)
        except Exception as e:
            return {
                'success': False,
                'error': 'Failed to get live train status',
                'details': str(e)
            }

    def get_train_schedule(self, train_number: str) -> Dict[str, Any]:
        """Get train schedule"""
        try:
            if not is_valid_train_number(train_number):
                return {
                    'success': False,
                    'error': 'Invalid train number format'
                }

            params = {"trainNo": train_number}
            
            # If in debug mode, return understanding instead of making API call
            if self.debug_mode:
                return self.format_debug_response('train_schedule', params)
                
            return self._make_request("api/v1/getTrainSchedule", params)
        except Exception as e:
            return {
                'success': False,
                'error': 'Failed to get train schedule',
                'details': str(e)
            }

    def check_pnr_status(self, pnr_number: str) -> Dict[str, Any]:
        """Check PNR status using v3 API"""
        try:
            if not is_valid_pnr(pnr_number):
                return {
                    'success': False,
                    'error': 'Invalid PNR number format'
                }

            params = {"pnrNumber": pnr_number}
            
            # If in debug mode, return understanding instead of making API call
            if self.debug_mode:
                return self.format_debug_response('pnr_status', params)
                
            return self._make_request("api/v3/getPNRStatus", params)
        except Exception as e:
            return {
                'success': False,
                'error': 'Failed to check PNR status',
                'details': str(e)
            }

    def check_seat_availability(self, train_number: str, from_station: str, 
                              to_station: str, date_string: str, 
                              class_type: str, quota: str = "GN") -> Dict[str, Any]:
        """Check seat availability"""
        try:
            # Validate inputs
            if not is_valid_train_number(train_number):
                return {
                    'success': False,
                    'error': 'Invalid train number format'
                }

            if not all(is_valid_station_code(code) for code in [from_station, to_station]):
                return {
                    'success': False,
                    'error': 'Invalid station code format'
                }

            # Parse and validate date
            date_info = parse_date_time(date_string)
            if not date_info['success'] or not is_valid_travel_date(date_info):
                return {
                    'success': False,
                    'error': 'Invalid date',
                    'details': 'Please provide a valid future date'
                }

            params = {
                "classType": class_type.upper(),
                "fromStationCode": from_station.upper(),
                "quota": quota.upper(),
                "toStationCode": to_station.upper(),
                "trainNo": train_number,
                "date": date_info['formatted']['api_format']
            }
            
            # If in debug mode, return understanding instead of making API call
            if self.debug_mode:
                return self.format_debug_response('seat_availability', params)

            result = self._make_request("api/v1/checkSeatAvailability", params)
            if result.get('success', False):
                result['date_info'] = date_info
            return result

        except Exception as e:
            return {
                'success': False,
                'error': 'Failed to check seat availability',
                'details': str(e)
            }

    def get_train_classes(self, train_number: str) -> Dict[str, Any]:
        """Get available classes for a train"""
        try:
            if not is_valid_train_number(train_number):
                return {
                    'success': False,
                    'error': 'Invalid train number format'
                }

            params = {"trainNo": train_number}
            
            # If in debug mode, return understanding instead of making API call
            if self.debug_mode:
                return self.format_debug_response('train_classes', params)
                
            return self._make_request("api/v1/getTrainClasses", params)
        except Exception as e:
            return {
                'success': False,
                'error': 'Failed to get train classes',
                'details': str(e)
            }

    def get_fare(self, train_number: str, from_station: str, to_station: str) -> Dict[str, Any]:
        """Get fare details using v2 API"""
        try:
            # Validate inputs
            if not is_valid_train_number(train_number):
                return {
                    'success': False,
                    'error': 'Invalid train number format'
                }

            if not all(is_valid_station_code(code) for code in [from_station, to_station]):
                return {
                    'success': False,
                    'error': 'Invalid station code format'
                }

            params = {
                "trainNo": train_number,
                "fromStationCode": from_station.upper(),
                "toStationCode": to_station.upper()
            }
            
            # If in debug mode, return understanding instead of making API call
            if self.debug_mode:
                return self.format_debug_response('fare_check', params)
                
            return self._make_request("api/v2/getFare", params)
        except Exception as e:
            return {
                'success': False,
                'error': 'Failed to get fare details',
                'details': str(e)
            }
