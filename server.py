"""
Unified Web Server for Autoliv AI Knowledge Assistant
Serves HTML UI and handles API requests
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import webbrowser
import threading
import time
from pathlib import Path

# Import your RAG system
from chat_v2_cleaneroutput import EnhancedChatSystem


class RAGWebServer(BaseHTTPRequestHandler):
    """Handle both UI serving and API requests"""
    
    # Class variable to hold chat system
    chat_system = None
    
    def do_GET(self):
        """Serve the HTML UI"""
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            
            # Send the HTML content
            html_content = self.get_html_content()
            self.wfile.write(html_content.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """Handle API requests"""
        if self.path == '/ask':
            try:
                # Read request data
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                request_data = json.loads(post_data)
                
                # Extract message and mode
                message = request_data.get('message', '')
                mode = request_data.get('mode', 'normal')
                
                # Add mode prefix to message
                if mode == 'detail':
                    message = '/detail ' + message
                elif mode == 'short':
                    message = '/short ' + message
                
                # Call RAG system
                result = self.chat_system.ask(message)
                
                # Prepare response
                response_data = {
                    'answer': result.get('answer', 'No answer generated'),
                    'meta': {
                        'confidence': result.get('confidence', 0),
                        'sources': result.get('num_sources', 0),
                        'time': f"{result.get('response_time', 0):.1f}s"
                    }
                }
                
                # Send response
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode())
                
            except Exception as error:
                # Send error response
                error_response = {
                    'answer': f'Error: {str(error)}',
                    'meta': {'confidence': 0, 'sources': 0, 'time': '0s'}
                }
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(error_response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Custom logging to show requests"""
        if self.path != '/favicon.ico':
            print(f"📡 {self.client_address[0]} - {format % args}")
    
    def get_html_content(self):
        """Return the HTML UI content"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Autoliv AI Knowledge Assistant</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #ffffff;
            color: #333;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }

        .header {
            background: #f8f9fa;
            border-bottom: 2px solid #e0e0e0;
            padding: 20px 30px;
        }

        .header h1 {
            font-size: 24px;
            font-weight: 600;
            color: #1a1a1a;
            margin-bottom: 5px;
        }

        .header p {
            font-size: 14px;
            color: #666;
        }

        .container {
            display: flex;
            flex: 1;
            overflow: hidden;
        }

        .sidebar {
            width: 280px;
            background: #f8f9fa;
            border-right: 1px solid #e0e0e0;
            padding: 20px;
            overflow-y: auto;
        }

        .sidebar h3 {
            font-size: 14px;
            font-weight: 600;
            color: #666;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .mode-option, .command-option {
            padding: 12px 15px;
            margin-bottom: 8px;
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .mode-option:hover, .command-option:hover {
            border-color: #333;
            transform: translateX(2px);
        }

        .mode-option.active {
            background: #333;
            color: white;
            border-color: #333;
        }

        .mode-title {
            font-weight: 600;
            font-size: 13px;
            margin-bottom: 4px;
        }

        .mode-desc {
            font-size: 11px;
            color: #666;
        }

        .mode-option.active .mode-desc {
            color: #ccc;
        }

        .command-option {
            font-size: 13px;
            font-family: 'Courier New', monospace;
        }

        .chat-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: white;
        }

        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 30px;
        }

        .message {
            margin-bottom: 25px;
            animation: fadeIn 0.3s;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .message-label {
            font-size: 12px;
            font-weight: 600;
            color: #666;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .message-content {
            padding: 15px 20px;
            border-radius: 8px;
            line-height: 1.6;
            white-space: pre-wrap;
        }

        .user-message .message-content {
            background: #f8f9fa;
            border: 1px solid #e0e0e0;
        }

        .assistant-message .message-content {
            background: white;
            border: 1px solid #e0e0e0;
        }

        .message-meta {
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #f0f0f0;
            font-size: 12px;
            color: #999;
            display: flex;
            gap: 15px;
        }

        .meta-item {
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .input-area {
            border-top: 1px solid #e0e0e0;
            padding: 20px 30px;
            background: #f8f9fa;
        }

        .input-wrapper {
            position: relative;
            display: flex;
            gap: 10px;
        }

        #messageInput {
            flex: 1;
            padding: 15px 20px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            font-family: inherit;
            background: white;
            transition: border-color 0.2s;
        }

        #messageInput:focus {
            outline: none;
            border-color: #333;
        }

        #sendButton {
            padding: 15px 30px;
            background: #333;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        }

        #sendButton:hover {
            background: #000;
        }

        #sendButton:disabled {
            background: #ccc;
            cursor: not-allowed;
        }

        .autocomplete {
            position: absolute;
            bottom: 100%;
            left: 0;
            right: 80px;
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            margin-bottom: 5px;
            box-shadow: 0 -4px 12px rgba(0,0,0,0.1);
            display: none;
            max-height: 200px;
            overflow-y: auto;
        }

        .autocomplete.show {
            display: block;
        }

        .autocomplete-item {
            padding: 12px 15px;
            cursor: pointer;
            font-size: 13px;
            border-bottom: 1px solid #f0f0f0;
        }

        .autocomplete-item:last-child {
            border-bottom: none;
        }

        .autocomplete-item:hover,
        .autocomplete-item.selected {
            background: #f8f9fa;
        }

        .autocomplete-command {
            font-family: 'Courier New', monospace;
            font-weight: 600;
            color: #333;
            margin-bottom: 3px;
        }

        .autocomplete-desc {
            font-size: 11px;
            color: #666;
        }

        .loading {
            display: none;
            padding: 20px;
            text-align: center;
            color: #666;
        }

        .loading.show {
            display: block;
        }

        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f0f0f0;
            border-top-color: #333;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .welcome {
            text-align: center;
            padding: 60px 30px;
            color: #666;
        }

        .welcome h2 {
            font-size: 28px;
            color: #333;
            margin-bottom: 10px;
        }

        .welcome p {
            font-size: 16px;
            margin-bottom: 30px;
        }

        .quick-commands {
            display: inline-block;
            text-align: left;
            background: #f8f9fa;
            padding: 20px 30px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
        }

        .quick-commands h4 {
            font-size: 14px;
            margin-bottom: 15px;
            color: #333;
        }

        .quick-commands div {
            margin-bottom: 8px;
            font-size: 13px;
        }

        .command-text {
            font-family: 'Courier New', monospace;
            background: white;
            padding: 2px 8px;
            border-radius: 4px;
            border: 1px solid #e0e0e0;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 Autoliv AI Knowledge Assistant</h1>
        <p>Smart Document Search & Retrieval</p>
    </div>

    <div class="container">
        <div class="sidebar">
            <h3>Response Modes</h3>
            <div class="mode-option active" data-mode="normal">
                <div class="mode-title">🟢 Normal</div>
                <div class="mode-desc">Balanced response (150-250 words)</div>
            </div>
            <div class="mode-option" data-mode="detail">
                <div class="mode-title">🔵 Detail</div>
                <div class="mode-desc">Comprehensive analysis (400-600 words)</div>
            </div>
            <div class="mode-option" data-mode="short">
                <div class="mode-title">🟡 Short</div>
                <div class="mode-desc">Brief answer (30-80 words)</div>
            </div>

            <h3 style="margin-top: 30px;">Commands</h3>
            <div class="command-option" onclick="executeCommand('/clear')">
                /clear - Clear session
            </div>
            <div class="command-option" onclick="executeCommand('/sessions')">
                /sessions - List sessions
            </div>
            <div class="command-option" onclick="executeCommand('/new')">
                /new - New session
            </div>
            <div class="command-option" onclick="executeCommand('/help')">
                /help - Show help
            </div>
        </div>

        <div class="chat-container">
            <div class="messages" id="messages">
                <div class="welcome">
                    <h2>Welcome to Autoliv AI Knowledge Assistant</h2>
                    <p>Ask me anything about your documents</p>
                    <div class="quick-commands">
                        <h4>Quick Start:</h4>
                        <div>• Type <span class="command-text">/</span> to see all commands</div>
                        <div>• Press <span class="command-text">Tab</span> to autocomplete</div>
                        <div>• Choose response mode from sidebar</div>
                    </div>
                </div>
            </div>

            <div class="loading" id="loading">
                <div class="spinner"></div>
                <span style="margin-left: 10px;">Processing...</span>
            </div>

            <div class="input-area">
                <div class="input-wrapper">
                    <div class="autocomplete" id="autocomplete"></div>
                    <input 
                        type="text" 
                        id="messageInput" 
                        placeholder="Ask a question or type / for commands..."
                        autocomplete="off"
                    >
                    <button id="sendButton">Send</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentMode = 'normal';
        let selectedAutocompleteIndex = -1;

        const commands = [
            { cmd: '/detail', desc: 'Switch to detailed response mode' },
            { cmd: '/normal', desc: 'Switch to normal response mode' },
            { cmd: '/short', desc: 'Switch to short response mode' },
            { cmd: '/clear', desc: 'Clear current session' },
            { cmd: '/sessions', desc: 'List all sessions' },
            { cmd: '/new', desc: 'Create new session' },
            { cmd: '/help', desc: 'Show help information' }
        ];

        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const messagesDiv = document.getElementById('messages');
        const loadingDiv = document.getElementById('loading');
        const autocompleteDiv = document.getElementById('autocomplete');

        document.querySelectorAll('.mode-option').forEach(option => {
            option.addEventListener('click', function() {
                document.querySelectorAll('.mode-option').forEach(o => o.classList.remove('active'));
                this.classList.add('active');
                currentMode = this.dataset.mode;
            });
        });

        messageInput.addEventListener('input', function(e) {
            const value = this.value;
            
            if (value.startsWith('/')) {
                const search = value.toLowerCase();
                const filtered = commands.filter(c => c.cmd.toLowerCase().startsWith(search));
                
                if (filtered.length > 0) {
                    showAutocomplete(filtered);
                } else {
                    hideAutocomplete();
                }
            } else {
                hideAutocomplete();
            }
        });

        messageInput.addEventListener('keydown', function(e) {
            const autocompleteVisible = autocompleteDiv.classList.contains('show');
            
            if (e.key === 'Tab' && autocompleteVisible) {
                e.preventDefault();
                const items = autocompleteDiv.querySelectorAll('.autocomplete-item');
                if (items.length > 0) {
                    const selectedItem = items[selectedAutocompleteIndex >= 0 ? selectedAutocompleteIndex : 0];
                    const command = selectedItem.querySelector('.autocomplete-command').textContent;
                    messageInput.value = command + ' ';
                    hideAutocomplete();
                }
            } else if (e.key === 'ArrowDown' && autocompleteVisible) {
                e.preventDefault();
                const items = autocompleteDiv.querySelectorAll('.autocomplete-item');
                selectedAutocompleteIndex = Math.min(selectedAutocompleteIndex + 1, items.length - 1);
                updateAutocompleteSelection();
            } else if (e.key === 'ArrowUp' && autocompleteVisible) {
                e.preventDefault();
                selectedAutocompleteIndex = Math.max(selectedAutocompleteIndex - 1, 0);
                updateAutocompleteSelection();
            } else if (e.key === 'Escape' && autocompleteVisible) {
                hideAutocomplete();
            } else if (e.key === 'Enter') {
                e.preventDefault();
                sendMessage();
            }
        });

        function showAutocomplete(items) {
            selectedAutocompleteIndex = 0;
            autocompleteDiv.innerHTML = items.map((item, index) => `
                <div class="autocomplete-item ${index === 0 ? 'selected' : ''}" data-index="${index}">
                    <div class="autocomplete-command">${item.cmd}</div>
                    <div class="autocomplete-desc">${item.desc}</div>
                </div>
            `).join('');
            
            autocompleteDiv.classList.add('show');
            
            autocompleteDiv.querySelectorAll('.autocomplete-item').forEach(item => {
                item.addEventListener('click', function() {
                    const command = this.querySelector('.autocomplete-command').textContent;
                    messageInput.value = command + ' ';
                    hideAutocomplete();
                    messageInput.focus();
                });
            });
        }

        function updateAutocompleteSelection() {
            const items = autocompleteDiv.querySelectorAll('.autocomplete-item');
            items.forEach((item, index) => {
                item.classList.toggle('selected', index === selectedAutocompleteIndex);
            });
        }

        function hideAutocomplete() {
            autocompleteDiv.classList.remove('show');
            selectedAutocompleteIndex = -1;
        }

        sendButton.addEventListener('click', sendMessage);

        async function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;

            messageInput.value = '';
            hideAutocomplete();

            addMessage('user', message);

            loadingDiv.classList.add('show');
            sendButton.disabled = true;

            try {
                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: message,
                        mode: currentMode
                    })
                });

                const data = await response.json();
                
                loadingDiv.classList.remove('show');
                sendButton.disabled = false;

                addMessage('assistant', data.answer, data.meta);

            } catch (error) {
                loadingDiv.classList.remove('show');
                sendButton.disabled = false;
                addMessage('assistant', 'Sorry, an error occurred: ' + error.message);
            }
        }

        function addMessage(role, content, meta = null) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}-message`;
            
            let metaHTML = '';
            if (meta) {
                metaHTML = `
                    <div class="message-meta">
                        <span class="meta-item">📊 Confidence: ${Math.round(meta.confidence * 100)}%</span>
                        <span class="meta-item">📚 Sources: ${meta.sources}</span>
                        <span class="meta-item">⏱️ Time: ${meta.time}</span>
                    </div>
                `;
            }
            
            messageDiv.innerHTML = `
                <div class="message-label">${role === 'user' ? 'You' : 'Autoliv AI Assistant'}</div>
                <div class="message-content">${content}</div>
                ${metaHTML}
            `;
            
            const welcome = messagesDiv.querySelector('.welcome');
            if (welcome) welcome.remove();
            
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function executeCommand(command) {
            messageInput.value = command;
            sendMessage();
        }

        messageInput.focus();
    </script>
</body>
</html>'''


def start_web_server(host='localhost', port=8000, db_path="db/acc.db"):
    """Start the unified web server"""
    
    print("=" * 60)
    print("🚀 Autoliv AI Knowledge Assistant - Web Server")
    print("=" * 60)
    print()
    print("📡 Starting server...")
    
    # Initialize RAG system
    print("🔧 Loading RAG system...")
    RAGWebServer.chat_system = EnhancedChatSystem(db_path)
    print("✅ RAG system ready!")
    print()
    
    # Create server
    server_address = (host, port)
    httpd = HTTPServer(server_address, RAGWebServer)
    
    url = f"http://{host}:{port}"
    print(f"✅ Server running at: {url}")
    print()
    print("📋 Instructions:")
    print(f"   1. Browser will open automatically")
    print(f"   2. If not, visit: {url}")
    print(f"   3. Press Ctrl+C to stop server")
    print()
    print("=" * 60)
    print()
    
    # Open browser after short delay
    def open_browser():
        time.sleep(1.5)
        print(f"🌐 Opening browser...")
        webbrowser.open(url)
    
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Start server
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print()
        print("=" * 60)
        print("🛑 Shutting down server...")
        print("👋 Goodbye!")
        print("=" * 60)
        httpd.shutdown()


if __name__ == "__main__":
    # Start the server
    start_web_server(
        host='localhost',
        port=8000,
        db_path="db/acc.db"
    )