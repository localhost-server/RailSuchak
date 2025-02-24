import os
import json
import time
import argparse
from datetime import datetime
from dotenv import load_dotenv
from services.train_service import TrainService
from services.openai_service import extract_query_details, generate_train_response
from services.date_service import parse_date_time

# Load environment variables
load_dotenv()

# Define test data
TEST_DATA = {
    'train_number': '12936',  # Intercity Express
    'station_code': 'NDLS',   # New Delhi
    'from_station': 'BVI',    # Bhavnagar
    'to_station': 'NDLS',     # New Delhi
    'date': '2025-02-26',
    'class_type': '3A',       # 2-tier AC
    'quota': 'GN'            # General Quota
}

# Define available endpoints
ENDPOINTS = {
    'search_train': 'Search train by number',
    'search_station': 'Search station by code',
    'trains_between': 'Find trains between stations',
    'live_status': 'Get live train status',
    'train_schedule': 'Get train schedule',
    'pnr_status': 'Check PNR status',
    'seat_availability': 'Check seat availability',
    'train_classes': 'Get available train classes',
    'fare': 'Get fare details',
    'test_dates': 'Test date handling'  # New endpoint for testing date handling
}

def pretty_print_json(data):
    """Print JSON data in a readable format"""
    print(json.dumps(data, indent=2, ensure_ascii=False))

def run_test(name, func, *args):
    """Run a test case and measure execution time"""
    print(f"\n{'='*80}")
    print(f"Testing: {name}")
    print(f"Arguments: {args}")
    print(f"{'='*80}")
    
    start_time = time.time()
    try:
        result = func(*args)
        execution_time = time.time() - start_time
        print(f"\nResult:")
        pretty_print_json(result)
        print(f"\nExecution time: {execution_time:.2f} seconds")
        return result
    except Exception as e:
        print(f"\nError: {str(e)}")
        return None

def test_pnr_status(train_service, pnr=None):
    """Test PNR status"""
    if pnr:
        return run_test(
            f"PNR Status Check - {pnr}",
            train_service.check_pnr_status,
            pnr
        )
    
    # If no PNR provided, read from file
    try:
        with open('pnrs.txt', 'r') as f:
            pnr = f.readline().strip()  # Get first PNR
            return run_test(
                f"PNR Status Check - {pnr}",
                train_service.check_pnr_status,
                pnr
            )
    except Exception as e:
        print(f"\nError reading PNR: {str(e)}")
        return None

def test_date_handling():
    """Test date handling with various formats"""
    print("\nTesting Date Handling")
    print("="*80)
    
    test_queries = [
        "Find trains from Delhi to Mumbai tomorrow",
        "Show trains from Delhi to Mumbai on Monday",
        "Get trains from Delhi to Mumbai next Monday",
        "Check trains from Delhi to Mumbai on 25th",
        "Find trains from Delhi to Mumbai today",
        "Show me trains running between Delhi and Mumbai on 25th February",
        "Get trains from Delhi to Mumbai next week Monday"
    ]
    
    for query in test_queries:
        print(f"\nTesting query: {query}")
        details = extract_query_details(query)
        print("Extracted details:")
        pretty_print_json(details)
        print("-"*40)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test Indian Railways API endpoints')
    parser.add_argument('endpoint', choices=ENDPOINTS.keys(), help='Endpoint to test')
    parser.add_argument('--train', help='Train number')
    parser.add_argument('--station', help='Station code')
    parser.add_argument('--from-station', help='From station code')
    parser.add_argument('--to-station', help='To station code')
    parser.add_argument('--date', help='Date (YYYY-MM-DD)')
    parser.add_argument('--class', dest='class_type', help='Class type (e.g., 2A, 3A, SL)')
    parser.add_argument('--pnr', help='PNR number')
    args = parser.parse_args()

    # Initialize service
    train_service = TrainService()
    
    print("\nStarting API Test")
    print(f"Timestamp: {datetime.now()}")
    print(f"Testing endpoint: {args.endpoint} ({ENDPOINTS[args.endpoint]})")

    # Special case for date handling test
    if args.endpoint == 'test_dates':
        test_date_handling()
        return

    # Run the requested test
    if args.endpoint == 'search_train':
        run_test(
            "Train Search",
            train_service.search_train,
            args.train or TEST_DATA['train_number']
        )

    elif args.endpoint == 'search_station':
        run_test(
            "Station Search",
            train_service.search_station,
            args.station or TEST_DATA['station_code']
        )

    elif args.endpoint == 'trains_between':
        params = [
            args.from_station or TEST_DATA['from_station'],
            args.to_station or TEST_DATA['to_station']
        ]
        if args.date:
            params.append(args.date)
        run_test(
            "Trains Between Stations",
            train_service.get_trains_between_stations,
            *params
        )

    elif args.endpoint == 'live_status':
        run_test(
            "Live Train Status",
            train_service.get_live_train_status,
            args.train or TEST_DATA['train_number']
        )

    elif args.endpoint == 'train_schedule':
        run_test(
            "Train Schedule",
            train_service.get_train_schedule,
            args.train or TEST_DATA['train_number']
        )

    elif args.endpoint == 'pnr_status':
        test_pnr_status(train_service, args.pnr)

    elif args.endpoint == 'seat_availability':
        run_test(
            "Seat Availability",
            train_service.check_seat_availability,
            args.train or TEST_DATA['train_number'],
            args.from_station or TEST_DATA['from_station'],
            args.to_station or TEST_DATA['to_station'],
            args.date or TEST_DATA['date'],
            args.class_type or TEST_DATA['class_type']
        )

    elif args.endpoint == 'train_classes':
        run_test(
            "Train Classes",
            train_service.get_train_classes,
            args.train or TEST_DATA['train_number']
        )

    elif args.endpoint == 'fare':
        run_test(
            "Fare Check",
            train_service.get_fare,
            args.train or TEST_DATA['train_number'],
            args.from_station or TEST_DATA['from_station'],
            args.to_station or TEST_DATA['to_station']
        )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nTesting interrupted by user")
    except Exception as e:
        print(f"\nError during testing: {str(e)}")
    finally:
        print("\nTesting completed")

# Example usage:
# python test_integration.py search_train --train 12936
# python test_integration.py trains_between --from-station BVI --to-station NDLS --date 2025-02-24
# python test_integration.py pnr_status --pnr 1234567890
# python test_integration.py test_dates  # Test date handling
