import os
import signal
import sys
import time
import asyncio
from typing import Callable, Optional
import threading
import atexit
import psutil
import json

from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface

from services.train_service import TrainService
from services.openai_service import extract_query_details, generate_train_response, handle_error_response, format_train_details
from utils.helpers import sanitize_input, is_valid_train_number, is_valid_pnr, is_valid_station_code

AGENT_ID = '0Vbhs0IWORdApcEGENIb'
API_KEY = os.getenv('ELEVEN_LABS_API_KEY')

def kill_process_tree():
    """Kill all child processes including audio processes"""
    try:
        current_process = psutil.Process()
        children = current_process.children(recursive=True)
        for child in children:
            try:
                child.kill()
            except:
                pass
        os.system('pkill -9 -f arecord 2>/dev/null')
        os.system('pkill -9 -f aplay 2>/dev/null')
        time.sleep(0.2)
    except:
        pass

class SafeAudioInterface(DefaultAudioInterface):
    def __init__(self):
        self._stop_event = threading.Event()
        kill_process_tree()
        super().__init__()
    
    def stop(self):
        """Stop audio interface safely"""
        self._stop_event.set()
        try:
            if hasattr(self, '_stream') and self._stream:
                self._stream.stop_stream()
                self._stream.close()
        except:
            pass
        try:
            if hasattr(self, '_audio') and self._audio:
                self._audio.terminate()
        except:
            pass
        kill_process_tree()

class VoiceAssistant:
    def __init__(self):
        self.conversation = None
        self.client = ElevenLabs(api_key=API_KEY)
        self.audio_interface = None
        self._shutdown = threading.Event()
        self.train_service = TrainService()
        self.conversation_context = {}

    def force_cleanup(self):
        """Force cleanup of all resources"""
        print("Performing force cleanup...")
        try:
            self._shutdown.set()
            
            # Stop audio interface first
            if self.audio_interface:
                self.audio_interface.stop()
                self.audio_interface = None

            # End conversation if active
            if self.conversation:
                try:
                    self.conversation.end_session()
                except:
                    pass
                try:
                    del self.conversation
                except:
                    pass
                self.conversation = None

            # Reset context
            self.conversation_context = {}

            # Kill any remaining processes
            kill_process_tree()
                
            # Force garbage collection
            import gc
            gc.collect()
            
            time.sleep(0.5)  # Wait for cleanup to complete
            
        except Exception as e:
            print(f"Force cleanup error: {str(e)}", file=sys.stderr)
        finally:
            self.conversation = None
            self.audio_interface = None
            print("Force cleanup completed")

    def cleanup(self):
        """Safely cleanup the current conversation"""
        print("Starting cleanup...")
        try:
            if self.conversation:
                try:
                    conversation_id = self.conversation.wait_for_session_end()
                    print(f"Conversation ID: {conversation_id}")
                except:
                    pass
            self.force_cleanup()
        except Exception as e:
            print(f"Cleanup error: {str(e)}", file=sys.stderr)
            try:
                kill_process_tree()  # Last resort cleanup
            except:
                pass
        finally:
            self.conversation = None
            self.audio_interface = None
            print("Cleanup completed")

    async def process_train_query(self, query: str) -> str:
        """Process train-related queries"""
        try:
            print("\n=== Processing Train Query ===")
            print(f"Original query: {query}")
            
            # Clean the input
            clean_query = sanitize_input(query)
            print(f"Cleaned query: {clean_query}")
            
            # Extract query details using OpenAI
            print("Calling OpenAI to extract query details...")
            query_details = extract_query_details(clean_query)
            print(f"OpenAI response: {json.dumps(query_details, indent=2)}")
            
            if not query_details or query_details.get('query_type') == 'error':
                print("Error in query details")
                return "I'm having trouble understanding your query. Could you please rephrase it?"
            
            # Update conversation context
            self.conversation_context.update(query_details)
            print(f"Updated context: {json.dumps(self.conversation_context, indent=2)}")
            
            # Handle different types of queries
            result = None
            query_type = query_details.get('query_type')
            print(f"Query type: {query_type}")

            if query_type == 'train_search':
                print("Processing train search query...")
                if 'train_number' in query_details:
                    print(f"Searching for train number: {query_details['train_number']}")
                    result = self.train_service.search_train(query_details['train_number'])
                elif all(k in query_details for k in ['from_station', 'to_station']):
                    print(f"Searching trains between stations: {query_details['from_station']} to {query_details['to_station']}")
                    result = self.train_service.get_trains_between_stations(
                        query_details['from_station'],
                        query_details['to_station'],
                        query_details.get('travel_date', 'tomorrow')
                    )

            elif query_type == 'pnr_status' and 'pnr_number' in query_details:
                print(f"Checking PNR status: {query_details['pnr_number']}")
                result = self.train_service.check_pnr_status(query_details['pnr_number'])

            elif query_type == 'train_schedule' and 'train_number' in query_details:
                print(f"Getting train schedule: {query_details['train_number']}")
                result = self.train_service.get_train_schedule(query_details['train_number'])

            elif query_type == 'live_status' and 'train_number' in query_details:
                print(f"Getting live status: {query_details['train_number']}")
                result = self.train_service.get_live_train_status(query_details['train_number'])

            elif query_type == 'seat_availability' and all(k in query_details for k in ['train_number', 'from_station', 'to_station', 'class_type']):
                print(f"Checking seat availability: Train {query_details['train_number']}, {query_details['from_station']} to {query_details['to_station']}, Class {query_details['class_type']}")
                result = self.train_service.check_seat_availability(
                    query_details['train_number'],
                    query_details['from_station'],
                    query_details['to_station'],
                    query_details.get('travel_date', 'tomorrow'),
                    query_details['class_type']
                )

            elif query_type == 'fare_check' and all(k in query_details for k in ['train_number', 'from_station', 'to_station']):
                print(f"Checking fare: Train {query_details['train_number']}, {query_details['from_station']} to {query_details['to_station']}")
                result = self.train_service.get_fare(
                    query_details['train_number'],
                    query_details['from_station'],
                    query_details['to_station']
                )

            print(f"API Result: {json.dumps(result, indent=2) if result else 'No result'}")

            if not result:
                print("No result returned")
                return "I need more information to help you. Could you provide more details about your request?"

            # Handle debug mode response
            if result.get('debug', False):
                print("Debug mode: Returning understanding explanation")
                understanding = result['understanding']
                
                # Format response for voice
                if "what" in query.lower() and any(x in query.lower() for x in ["can you", "things", "help", "share"]):
                    return """I can help you with several things:
1. Finding trains between stations
2. Checking PNR status
3. Getting train schedules
4. Checking live train status
5. Checking seat availability
6. Getting fare information

Just ask me naturally, for example 'Find trains from Delhi to Mumbai' or 'Check PNR status 1234567890'."""
                else:
                    # Convert technical response to natural language
                    params = result['params']
                    if 'fromStationCode' in params and 'toStationCode' in params:
                        date = params.get('dateOfJourney', 'today')
                        return f"I'll help you find trains from {params['fromStationCode']} to {params['toStationCode']} for {date}. In debug mode, I'm showing you what I understood, but normally I would fetch the actual train information for you."
                    elif 'pnrNumber' in params:
                        return f"I'll check the status of PNR number {params['pnrNumber']} for you. In debug mode, I'm just confirming what I understood."
                    elif 'trainNo' in params:
                        return f"I'll get the information for train number {params['trainNo']} for you. In debug mode, I'm just confirming what I understood."
                    
                    return "I understand your request. In debug mode, I'm showing you what I understood, but normally I would fetch the actual information for you."

            if not result.get('success', False):
                error_msg = result.get('error', 'Unknown error occurred')
                print(f"Error in result: {error_msg}")
                return handle_error_response(error_msg)

            # Format the response based on query type
            print("Formatting train details...")
            formatted_data = format_train_details(result, query_type)
            print(f"Formatted data: {formatted_data}")
            
            # Generate natural language response
            print("Generating natural language response...")
            response = generate_train_response(formatted_data, clean_query)
            print(f"Final response: {response}")
            
            return response
            
        except Exception as e:
            error_msg = str(e)
            print(f"Error processing train query: {error_msg}", file=sys.stderr)
            print("Stack trace:", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return handle_error_response(error_msg)

    def start_conversation(self) -> Optional[Conversation]:
        """Start a new conversation session with webhook processing"""
        print("Starting new conversation session...")
        self._shutdown.clear()
        
        try:
            # Ensure clean slate
            self.cleanup()
            time.sleep(0.5)  # Wait for cleanup to complete
            
            print("Creating new audio interface...")
            self.audio_interface = SafeAudioInterface()
            time.sleep(0.2)  # Wait for audio interface to initialize
            
            print("Creating new conversation instance...")
            # Initialize conversation exactly like the demo
            if not API_KEY:
                raise ValueError("ElevenLabs API key not found")

            # Minimal initialization - let server handle greetings and events
            self.conversation = Conversation(
                self.client,
                AGENT_ID,
                audio_interface=self.audio_interface,
                requires_auth=bool(API_KEY),
                webhook=lambda transcript: self._handle_webhook(transcript)
            )
            
            # Start session
            self.conversation.start_session()
            signal.signal(signal.SIGINT, lambda sig, frame: self.conversation.end_session())
            print("Conversation started successfully")
            return self.conversation
            
        except Exception as e:
            print(f"Error starting conversation: {str(e)}", file=sys.stderr)
            self.cleanup()
            return None

    def is_active(self) -> bool:
        """Check if conversation is active"""
        return self.conversation is not None and not self._shutdown.is_set()

    def _handle_webhook(self, transcript: str):
        """Handle webhook callbacks safely"""
        try:
            if not self.is_active():
                print("Webhook called but conversation is not active")
                return
                
            response = asyncio.run(self.process_train_query(transcript))
            if response and self.conversation:
                print("Sending response:", response[:100] + "..." if len(response) > 100 else response)
                self.conversation.say(response)
            else:
                print("No response generated or conversation ended")
                
        except Exception as e:
            print(f"Error in webhook handler: {str(e)}", file=sys.stderr)
            error_msg = "I apologize, but I encountered an error. Could you please try again?"
            if self.conversation:
                self.conversation.say(error_msg)

# Register cleanup on process exit
atexit.register(kill_process_tree)

if __name__ == "__main__":
    assistant = VoiceAssistant()
    
    # Basic signal handling for graceful shutdown
    def cleanup(sig=None, frame=None):
        print("\nShutting down...")
        assistant.cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    # Simple test conversation
    try:
        conversation = assistant.start_conversation()
        if conversation:
            conversation_id = conversation.wait_for_session_end()
            print(f"Conversation ended with ID: {conversation_id}")
        else:
            print("Failed to start conversation", file=sys.stderr)
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nStopped by user")
        cleanup()
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        cleanup()
