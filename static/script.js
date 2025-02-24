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
            // Auto-start listening
            socket.emit('start_listening');
            updateState('listening');
            isListening = true;
        });

        socket.on('disconnect', () => {
            console.log('Disconnected from server');
            resetUI();
        });

        socket.on('status', (data) => {
            console.log('Status update:', data);
            let message = data.state === 'listening' ? 'Listening...' :
                         data.state === 'processing' ? 'Processing...' :
                         data.state === 'speaking' ? 'Speaking...' : '';
            statusText.textContent = message;
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

    // Handle page visibility
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'hidden') {
            console.log('Page hidden - disconnecting');
            socket.emit('stop_listening');
            socket.disconnect();
        }
    });

    // Handle page unload
    window.addEventListener('beforeunload', () => {
        console.log('Page unloading - disconnecting');
        socket.emit('stop_listening');
        socket.disconnect();
    });
});
