document.addEventListener('DOMContentLoaded', () => {
    const voiceCircle = document.getElementById('voice-circle');
    const statusText = document.getElementById('status-text');
    const transcript = document.getElementById('transcript');
    
    let socket = io();
    let isListening = false;

    function updateState(state) {
        voiceCircle.classList.remove('listening', 'processing', 'speaking');
        if (state !== 'idle') {
            voiceCircle.classList.add(state);
        }
    }

    function resetUI() {
        isListening = false;
        updateState('idle');
        statusText.textContent = 'Click to start';
        transcript.innerHTML = '';
    }

    function setupSocket() {
        // Always reconnect when setting up socket
        if (socket.connected) {
            socket.disconnect();
        }
        socket.connect();

        socket.on('connect', () => {
            console.log('Connected to server');
            resetUI();
        });

        socket.on('disconnect', () => {
            console.log('Disconnected from server');
            resetUI();
        });

        socket.on('status', (data) => {
            console.log('Status update:', data);
            statusText.textContent = data.message;
            updateState(data.state);
            
            if (data.state === 'listening') {
                isListening = true;
            } else if (data.state === 'idle') {
                isListening = false;
            }
        });

        socket.on('transcript', (data) => {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${data.type}`;
            messageDiv.innerHTML = `<strong>${data.type === 'user' ? 'You' : 'Assistant'}:</strong> ${data.text}`;
            
            // Keep only the last 4 messages
            const messages = transcript.getElementsByClassName('message');
            while (messages.length >= 4) {
                const oldestMessage = messages[0];
                oldestMessage.classList.add('fade-out');
                setTimeout(() => {
                    if (oldestMessage.parentNode === transcript) {
                        transcript.removeChild(oldestMessage);
                    }
                }, 1000);
            }
            
            transcript.appendChild(messageDiv);
            
            // Auto-cleanup after 30 seconds
            setTimeout(() => {
                if (messageDiv.parentNode === transcript) {
                    messageDiv.classList.add('fade-out');
                    setTimeout(() => {
                        if (messageDiv.parentNode === transcript) {
                            transcript.removeChild(messageDiv);
                        }
                    }, 1000);
                }
            }, 30000);
        });

        socket.on('error', (error) => {
            console.error('Error:', error);
            resetUI();
        });
    }

    async function handleClick() {
        try {
            if (isListening) {
                console.log('Stopping current session');
                socket.emit('stop_listening');
                resetUI();
                return;
            }

            console.log('Starting new session');
            socket.emit('start_listening');
            updateState('listening');
            statusText.textContent = 'Listening...';

        } catch (error) {
            console.error('Error handling click:', error);
            resetUI();
        }
    }

    // Initial setup
    voiceCircle.addEventListener('click', handleClick);
    setupSocket();  // Initial socket setup

    // Handle page visibility and reload
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') {
            console.log('Page became visible - reconnecting');
            setupSocket();  // Reconnect and reset when page becomes visible
        }
    });

    window.addEventListener('pageshow', (event) => {
        console.log('Page show event - resetting connection');
        setupSocket();  // Reset connection on page show (including back/forward navigation)
    });

    // Handle page reload through refresh
    window.addEventListener('load', () => {
        console.log('Page loaded - setting up fresh connection');
        setupSocket();
    });

    // Handle page unload
    window.addEventListener('beforeunload', () => {
        socket.emit('stop_listening');
        socket.disconnect();
    });
});
