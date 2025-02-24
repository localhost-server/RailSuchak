from flask import Flask, request, jsonify, render_template, send_from_directory, url_for, copy_current_request_context
from flask_socketio import SocketIO, emit, disconnect
from datetime import datetime
import os
import sys
import threading
import time
import asyncio

from voice_assistant import VoiceAssistant, kill_process_tree
from utils.constants import STATUS_MESSAGES

# Ensure static folder path is absolute
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'))
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching during development
socketio = SocketIO(app, async_mode='threading', ping_timeout=60, logger=True, cors_allowed_origins="*")

# Global state with thread safety
thread_lock = threading.Lock()
assistants = {}  # Store assistants per session

def cleanup_session(session_id):
    """Clean up resources for a session"""
    with thread_lock:
        if session_id in assistants:
            try:
                print(f"Cleaning up session {session_id}")
                if assistants[session_id].conversation:
                    try:
                        conversation_id = assistants[session_id].conversation.wait_for_session_end()
                        print(f"Conversation ID for session {session_id}: {conversation_id}")
                    except:
                        pass
                assistants[session_id].cleanup()
            except Exception as e:
                print(f"Error cleaning up session: {e}", file=sys.stderr)
            finally:
                try:
                    del assistants[session_id]
                except:
                    pass
                try:
                    kill_process_tree()
                except:
                    pass

@app.route('/')
def index():
    # Force clean start on page load
    try:
        for session_id in list(assistants.keys()):
            cleanup_session(session_id)
    except:
        pass
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@socketio.on('connect')
def handle_connect():
    """Handle new client connection"""
    session_id = request.sid
    print(f'Client connected: {session_id}')
    cleanup_session(session_id)  # Clean up any existing session
    assistants[session_id] = VoiceAssistant()

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    session_id = request.sid
    print(f'Client disconnected: {session_id}')
    cleanup_session(session_id)

# Socket events for conversation status updates
@socketio.on('user_transcript')
def handle_user_transcript(data):
    """Handle user transcript from frontend"""
    print(f"User transcript: {data}")
    emit('transcript', {'type': 'user', 'text': data['text']})

@socketio.on('assistant_response')
def handle_assistant_response(data):
    """Handle assistant response from ElevenLabs"""
    print(f"Assistant response: {data}")
    emit('transcript', {'type': 'assistant', 'text': data['text']})

@socketio.on('start_listening')
def handle_start_listening():
    """Handle start listening request from client"""
    session_id = request.sid
    print(f"Start listening request from {session_id}")
    
    try:
        cleanup_session(session_id)  # Clean up any existing session
        assistants[session_id] = VoiceAssistant()  # Create new assistant
        
        with thread_lock:
            # Get assistant for this session
            assistant = assistants.get(session_id)
            if assistant:
                # Wrap conversation events to ensure they run in the socket context
                @copy_current_request_context
                def emit_status(state, message):
                    print(f"Status update: {state} - {message}")
                    socketio.emit('status', {'state': state, 'message': message}, room=session_id)

                @copy_current_request_context
                def emit_transcript(text, is_user):
                    print(f"Transcript: {'User' if is_user else 'Assistant'} - {text}")
                    socketio.emit('transcript', {
                        'type': 'user' if is_user else 'assistant',
                        'text': text
                    }, room=session_id)

                # Start conversation
                conversation = assistant.start_conversation()
                if conversation:
                    emit_status('listening', 'Listening...')
                    
                        # Start audio interface
                    conversation.start_listening()
                    return

            # If we get here, something went wrong
            cleanup_session(session_id)
            emit_status('error', 'Failed to start conversation')
            
    except Exception as e:
        print(f"Error in start_listening: {str(e)}", file=sys.stderr)
        cleanup_session(session_id)
        emit('status', {'state': 'idle', 'message': 'Click to start'})

@socketio.on('stop_listening')
def handle_stop_listening():
    """Handle stop listening request from client"""
    session_id = request.sid
    print(f"Stop listening request from {session_id}")
    cleanup_session(session_id)
    emit('status', {'state': 'idle', 'message': 'Click to start'})

def cleanup_and_kill():
    """Clean up all resources"""
    print("\nCleaning up resources...")
    try:
        with thread_lock:
            for session_id in list(assistants.keys()):
                cleanup_session(session_id)
    finally:
        kill_process_tree()

if __name__ == '__main__':
    try:
        # Clean start
        cleanup_and_kill()
        
        print("Starting server on http://localhost:5000")
        socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=True, allow_unsafe_werkzeug=True)
    except (KeyboardInterrupt, SystemExit):
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
    finally:
        cleanup_and_kill()
