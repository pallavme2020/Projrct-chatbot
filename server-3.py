"""
Unified Web Server for TASA AI Knowledge Assistant
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
    <title>TASA AI Knowledge Assistant</title>
    <style>
        :root {
            --primary: #4f46e5;
            --primary-dark: #4338ca;
            --secondary: #06b6d4;
            --accent: #8b5cf6;
            --success: #10b981;
            --warning: #f59e0b;
            --error: #ef4444;
            --bg-primary: #ffffff;
            --bg-secondary: #f8fafc;
            --bg-tertiary: #f1f5f9;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --text-tertiary: #94a3b8;
            --border: #e2e8f0;
            --border-hover: #cbd5e1;
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            --radius: 12px;
            --radius-sm: 8px;
            --transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif;
            background: var(--bg-secondary);
            color: var(--text-primary);
            height: 100vh;
            display: flex;
            flex-direction: column;
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }

        .header {
            background: var(--bg-primary);
            border-bottom: 1px solid var(--border);
            padding: 20px 32px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: var(--shadow-sm);
            z-index: 10;
        }

        .header-left {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .logo {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 700;
            font-size: 18px;
        }

        .header-title h1 {
            font-size: 20px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 2px;
        }

        .header-title p {
            font-size: 13px;
            color: var(--text-secondary);
        }

        .header-status {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 6px 12px;
            background: var(--success);
            color: white;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            background: white;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .container {
            display: flex;
            flex: 1;
            overflow: hidden;
        }

        .sidebar {
            width: 280px;
            background: var(--bg-primary);
            border-right: 1px solid var(--border);
            padding: 24px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 24px;
        }

        .sidebar-section h3 {
            font-size: 11px;
            font-weight: 600;
            color: var(--text-tertiary);
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .mode-option {
            padding: 14px;
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            cursor: pointer;
            transition: var(--transition);
            position: relative;
            overflow: hidden;
        }

        .mode-option::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            bottom: 0;
            width: 3px;
            background: var(--primary);
            transform: translateX(-3px);
            transition: var(--transition);
        }

        .mode-option:hover {
            border-color: var(--primary);
            transform: translateY(-1px);
            box-shadow: var(--shadow);
        }

        .mode-option.active {
            background: var(--primary);
            color: white;
            border-color: var(--primary);
            transform: translateY(-1px);
            box-shadow: var(--shadow);
        }

        .mode-option.active::before {
            transform: translateX(0);
        }

        .mode-option.active .mode-desc {
            color: rgba(255, 255, 255, 0.85);
        }

        .mode-title {
            font-weight: 500;
            font-size: 14px;
            margin-bottom: 4px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .mode-desc {
            font-size: 12px;
            color: var(--text-secondary);
            line-height: 1.4;
        }

        .command-option {
            padding: 12px;
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            cursor: pointer;
            transition: var(--transition);
            font-size: 12px;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .command-option:hover {
            border-color: var(--primary);
            background: var(--primary);
            color: white;
            transform: translateX(4px);
        }

        .command-icon {
            font-size: 14px;
        }

        .chat-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: var(--bg-primary);
            position: relative;
        }

        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 32px;
            display: flex;
            flex-direction: column;
            gap: 24px;
            scroll-behavior: smooth;
        }

        .message {
            display: flex;
            gap: 12px;
            animation: slideIn 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            max-width: 85%;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(12px) scale(0.98);
            }
            to {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }

        .message-avatar {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            flex-shrink: 0;
            margin-top: 2px;
        }

        .user-message {
            align-self: flex-end;
            flex-direction: row-reverse;
        }

        .user-message .message-avatar {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
        }

        .assistant-message .message-avatar {
            background: var(--bg-tertiary);
            color: var(--text-secondary);
        }

        .message-content-wrapper {
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .message-label {
            font-size: 12px;
            font-weight: 500;
            color: var(--text-tertiary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .user-message .message-label {
            text-align: right;
        }

        .message-content {
            padding: 16px 20px;
            border-radius: var(--radius-sm);
            white-space: pre-wrap;
            word-wrap: break-word;
            font-size: 15px;
            line-height: 1.6;
            transition: var(--transition);
        }

        .user-message .message-content {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            border-bottom-right-radius: 4px;
            box-shadow: var(--shadow);
        }

        .assistant-message .message-content {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-bottom-left-radius: 4px;
        }

        .message-content:hover {
            box-shadow: var(--shadow-lg);
        }

        .message-meta {
            display: flex;
            gap: 16px;
            font-size: 11px;
            color: var(--text-tertiary);
            margin-top: 4px;
        }

        .user-message .message-meta {
            justify-content: flex-end;
        }

        .meta-item {
            display: flex;
            align-items: center;
            gap: 4px;
            padding: 2px 6px;
            background: rgba(148, 163, 184, 0.1);
            border-radius: 4px;
        }

        .input-area {
            border-top: 1px solid var(--border);
            padding: 24px 32px;
            background: var(--bg-primary);
            position: sticky;
            bottom: 0;
            z-index: 5;
        }

        .input-wrapper {
            position: relative;
            display: flex;
            gap: 12px;
        }

        #messageInput {
            flex: 1;
            padding: 16px 20px;
            border: 1px solid var(--border);
            border-radius: var(--radius);
            font-size: 15px;
            font-family: inherit;
            background: var(--bg-secondary);
            transition: var(--transition);
            outline: none;
        }

        #messageInput:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.15);
            background: var(--bg-primary);
        }

        #messageInput::placeholder {
            color: var(--text-tertiary);
        }

        #sendButton {
            padding: 16px 28px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            border: none;
            border-radius: var(--radius);
            font-size: 15px;
            font-weight: 500;
            cursor: pointer;
            transition: var(--transition);
            display: flex;
            align-items: center;
            gap: 8px;
            position: relative;
            overflow: hidden;
        }

        #sendButton:hover {
            transform: translateY(-1px);
            box-shadow: var(--shadow-lg);
        }

        #sendButton:active {
            transform: translateY(0);
        }

        #sendButton:disabled {
            background: var(--text-tertiary);
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }

        .send-icon {
            font-size: 16px;
        }

        .autocomplete {
            position: absolute;
            bottom: calc(100% + 8px);
            left: 0;
            right: 100px;
            background: var(--bg-primary);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            box-shadow: var(--shadow-lg);
            display: none;
            max-height: 240px;
            overflow-y: auto;
            z-index: 100;
            backdrop-filter: blur(10px);
        }

        .autocomplete.show {
            display: block;
            animation: fadeInUp 0.2s ease-out;
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(8px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .autocomplete-item {
            padding: 14px 16px;
            cursor: pointer;
            font-size: 13px;
            border-bottom: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            gap: 4px;
            transition: var(--transition);
        }

        .autocomplete-item:last-child {
            border-bottom: none;
        }

        .autocomplete-item:hover,
        .autocomplete-item.selected {
            background: var(--bg-secondary);
            padding-left: 20px;
        }

        .autocomplete-item.selected {
            border-left: 3px solid var(--primary);
        }

        .autocomplete-command {
            font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace;
            font-weight: 600;
            color: var(--text-primary);
            font-size: 13px;
        }

        .autocomplete-desc {
            font-size: 12px;
            color: var(--text-secondary);
        }

        .loading {
            display: none;
            padding: 24px;
            text-align: center;
            color: var(--text-secondary);
            backdrop-filter: blur(4px);
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(255, 255, 255, 0.9);
            border-radius: var(--radius);
            border: 1px solid var(--border);
            box-shadow: var(--shadow-lg);
            z-index: 10;
        }

        .loading.show {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .spinner {
            width: 20px;
            height: 20px;
            border: 2px solid var(--border);
            border-top-color: var(--primary);
            border-radius: 50%;
            animation: spin 0.8s cubic-bezier(0.4, 0, 0.2, 1) infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .welcome {
            text-align: center;
            padding: 80px 32px;
            color: var(--text-secondary);
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 20px;
            max-width: 600px;
            margin: 0 auto;
        }

        .welcome h2 {
            font-size: 28px;
            color: var(--text-primary);
            font-weight: 600;
            margin-bottom: 8px;
        }

        .welcome p {
            font-size: 16px;
            margin-bottom: 24px;
        }

        .quick-commands {
            text-align: left;
            background: var(--bg-secondary);
            padding: 24px;
            border-radius: var(--radius);
            border: 1px solid var(--border);
            width: 100%;
            max-width: 420px;
        }

        .quick-commands h4 {
            font-size: 14px;
            margin-bottom: 16px;
            color: var(--text-primary);
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .quick-commands-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 12px;
        }

        .quick-command-item {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 14px;
            padding: 8px;
            border-radius: var(--radius-sm);
            transition: var(--transition);
        }

        .quick-command-item:hover {
            background: var(--bg-tertiary);
        }

        .command-text {
            font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace;
            background: var(--primary);
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 500;
            font-size: 12px;
        }

        .toast {
            position: fixed;
            bottom: 24px;
            right: 24px;
            background: var(--text-primary);
            color: white;
            padding: 14px 20px;
            border-radius: var(--radius-sm);
            font-size: 14px;
            box-shadow: var(--shadow-lg);
            display: none;
            align-items: center;
            gap: 12px;
            z-index: 1000;
            animation: slideInRight 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .toast.show {
            display: flex;
        }

        @keyframes slideInRight {
            from {
                opacity: 0;
                transform: translateX(100%);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }

        .toast-icon {
            font-size: 18px;
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .sidebar {
                position: absolute;
                top: 0;
                left: 0;
                height: 100%;
                z-index: 20;
                transform: translateX(-100%);
                transition: var(--transition);
            }

            .sidebar.open {
                transform: translateX(0);
                box-shadow: var(--shadow-lg);
            }

            .header {
                padding: 16px 20px;
            }

            .messages {
                padding: 20px;
            }

            .input-area {
                padding: 16px 20px;
            }

            .message {
                max-width: 95%;
            }

            .welcome {
                padding: 60px 20px;
            }

            .welcome h2 {
                font-size: 24px;
            }
        }

        /* Dark mode support */
        @media (prefers-color-scheme: dark) {
            :root {
                --bg-primary: #0f172a;
                --bg-secondary: #1e293b;
                --bg-tertiary: #334155;
                --text-primary: #f1f5f9;
                --text-secondary: #cbd5e1;
                --text-tertiary: #94a3b8;
                --border: #334155;
                --border-hover: #475569;
            }

            .message-content {
                border: 1px solid var(--border);
            }

            .assistant-message .message-content {
                background: var(--bg-secondary);
            }
        }

        /* Scrollbar styling */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: var(--bg-secondary);
        }

        ::-webkit-scrollbar-thumb {
            background: var(--text-tertiary);
            border-radius: 4px;
            border: 2px solid var(--bg-secondary);
        }

        ::-webkit-scrollbar-thumb:hover {
            background: var(--text-secondary);
        }

        /* Focus styles */
        *:focus-visible {
            outline: 2px solid var(--primary);
            outline-offset: 2px;
        }

        /* Selection styles */
        ::selection {
            background: var(--primary);
            color: white;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-left">
            <div class="logo">AI</div>
            <div class="header-title">
                <h1>TASA Knowledge Assistant</h1>
                <p>Intelligent Document Retrieval</p>
            </div>
        </div>
        <div class="header-status">
            <div class="status-dot"></div>
            <span>Online</span>
        </div>
    </div>

    <div class="container">
        <div class="sidebar">
            <div class="sidebar-section">
                <h3>🎨 Response Modes</h3>
                <div class="mode-option active" data-mode="normal">
                    <div class="mode-title">Normal</div>
                    <div class="mode-desc">Balanced response (150-250 words)</div>
                </div>
                <div class="mode-option" data-mode="detail">
                    <div class="mode-title">Detail</div>
                    <div class="mode-desc">Comprehensive analysis (400-600 words)</div>
                </div>
                <div class="mode-option" data-mode="short">
                    <div class="mode-title">Short</div>
                    <div class="mode-desc">Brief answer (30-80 words)</div>
                </div>
            </div>

            <div class="sidebar-section">
                <h3>⌨️ Quick Commands</h3>
                <div class="command-option" onclick="executeCommand('/clear')">
                    <span class="command-icon">🗑️</span>
                    <span>/clear - Clear session</span>
                </div>
                <div class="command-option" onclick="executeCommand('/sessions')">
                    <span class="command-icon">📋</span>
                    <span>/sessions - List sessions</span>
                </div>
                <div class="command-option" onclick="executeCommand('/new')">
                    <span class="command-icon">➕</span>
                    <span>/new - New session</span>
                </div>
                <div class="command-option" onclick="executeCommand('/help')">
                    <span class="command-icon">❓</span>
                    <span>/help - Show help</span>
                </div>
            </div>
        </div>

        <div class="chat-container">
            <div class="messages" id="messages">
                <div class="welcome">
                    <div class="logo" style="width: 64px; height: 64px; font-size: 28px;">AI</div>
                    <h2>Welcome to TASA AI</h2>
                    <p>Your intelligent document assistant is ready to help</p>
                    <div class="quick-commands">
                        <h4>🚀 Quick Start Guide</h4>
                        <div class="quick-commands-grid">
                            <div class="quick-command-item">
                                <span class="command-icon">💬</span>
                                <div>
                                    <span>Type</span> <span class="command-text">/</span> <span>to see all commands</span>
                                </div>
                            </div>
                            <div class="quick-command-item">
                                <span class="command-icon">⌨️</span>
                                <div>
                                    <span>Press</span> <span class="command-text">Tab</span> <span>to autocomplete</span>
                                </div>
                            </div>
                            <div class="quick-command-item">
                                <span class="command-icon">🎨</span>
                                <div>
                                    <span>Choose response mode from sidebar</span>
                                </div>
                            </div>
                            <div class="quick-command-item">
                                <span class="command-icon">⚡</span>
                                <div>
                                    <span>Press</span> <span class="command-text">Enter</span> <span>to send message</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="loading" id="loading">
                <div class="spinner"></div>
                <span>Thinking...</span>
            </div>

            <div class="input-area">
                <div class="input-wrapper">
                    <div class="autocomplete" id="autocomplete"></div>
                    <input 
                        type="text" 
                        id="messageInput" 
                        placeholder="Ask anything about your documents..."
                        autocomplete="off"
                        aria-label="Message input"
                    >
                    <button id="sendButton" aria-label="Send message">
                        <span class="send-icon">➤</span>
                        <span>Send</span>
                    </button>
                </div>
            </div>
        </div>
    </div>

    <div class="toast" id="toast">
        <span class="toast-icon" id="toastIcon">✓</span>
        <span id="toastMessage">Action completed</span>
    </div>

    <script>
        let currentMode = 'normal';
        let selectedAutocompleteIndex = -1;
        let messageHistory = [];
        let historyIndex = -1;

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

        // Mode selection
        document.querySelectorAll('.mode-option').forEach(option => {
            option.addEventListener('click', function() {
                document.querySelectorAll('.mode-option').forEach(o => o.classList.remove('active'));
                this.classList.add('active');
                currentMode = this.dataset.mode;
                showToast('🎨', `Switched to ${this.querySelector('.mode-title').textContent} mode`);
            });
        });

        // Autocomplete functionality
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

        // Keyboard navigation
        messageInput.addEventListener('keydown', function(e) {
            const autocompleteVisible = autocompleteDiv.classList.contains('show');
            const items = autocompleteDiv.querySelectorAll('.autocomplete-item');
            
            // Tab for autocomplete
            if (e.key === 'Tab' && autocompleteVisible && items.length > 0) {
                e.preventDefault();
                const selectedItem = items[selectedAutocompleteIndex >= 0 ? selectedAutocompleteIndex : 0];
                const command = selectedItem.querySelector('.autocomplete-command').textContent;
                messageInput.value = command + ' ';
                hideAutocomplete();
                return;
            }
            
            // Arrow navigation
            if (e.key === 'ArrowDown' && autocompleteVisible) {
                e.preventDefault();
                selectedAutocompleteIndex = Math.min(selectedAutocompleteIndex + 1, items.length - 1);
                updateAutocompleteSelection();
                return;
            }
            
            if (e.key === 'ArrowUp' && autocompleteVisible) {
                e.preventDefault();
                selectedAutocompleteIndex = Math.max(selectedAutocompleteIndex - 1, 0);
                updateAutocompleteSelection();
                return;
            }
            
            // Escape to hide autocomplete
            if (e.key === 'Escape' && autocompleteVisible) {
                hideAutocomplete();
                return;
            }
            
            // Enter to send
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
                return;
            }
            
            // History navigation (arrow up/down when input is empty)
            if (e.key === 'ArrowUp' && messageInput.value === '' && !autocompleteVisible) {
                e.preventDefault();
                if (historyIndex < messageHistory.length - 1) {
                    historyIndex++;
                    messageInput.value = messageHistory[historyIndex];
                }
                return;
            }
            
            if (e.key === 'ArrowDown' && messageInput.value === '' && !autocompleteVisible) {
                e.preventDefault();
                if (historyIndex > 0) {
                    historyIndex--;
                    messageInput.value = messageHistory[historyIndex];
                } else if (historyIndex === 0) {
                    historyIndex--;
                    messageInput.value = '';
                }
                return;
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

        // Send message
        sendButton.addEventListener('click', sendMessage);

        async function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;

            // Add to history
            if (messageHistory[0] !== message) {
                messageHistory.unshift(message);
                if (messageHistory.length > 50) messageHistory.pop();
            }
            historyIndex = -1;

            messageInput.value = '';
            hideAutocomplete();

            addMessage('user', message);
            showLoading(true);

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
                showLoading(false);

                if (data.answer.startsWith('Error:')) {
                    addMessage('assistant', data.answer, null, true);
                } else {
                    addMessage('assistant', data.answer, data.meta);
                }

            } catch (error) {
                showLoading(false);
                addMessage('assistant', '❌ Sorry, an error occurred: ' + error.message, null, true);
                console.error('Error:', error);
            }
        }

        function showLoading(show) {
            loadingDiv.classList.toggle('show', show);
            sendButton.disabled = show;
            
            if (show) {
                messagesDiv.style.filter = 'blur(1px)';
                messagesDiv.style.pointerEvents = 'none';
            } else {
                messagesDiv.style.filter = 'none';
                messagesDiv.style.pointerEvents = 'auto';
            }
        }

        function addMessage(role, content, meta = null, isError = false) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}-message`;
            
            let metaHTML = '';
            if (meta && !isError) {
                metaHTML = `
                    <div class="message-meta">
                        <div class="meta-item">
                            <span>🎯</span>
                            <span>Confidence: ${Math.round(meta.confidence * 100)}%</span>
                        </div>
                        <div class="meta-item">
                            <span>📚</span>
                            <span>Sources: ${meta.sources}</span>
                        </div>
                        <div class="meta-item">
                            <span>⏱️</span>
                            <span>${meta.time}</span>
                        </div>
                    </div>
                `;
            }
            
            const avatarEmoji = role === 'user' ? '👤' : '🤖';
            const avatarClass = isError ? 'error' : '';
            
            messageDiv.innerHTML = `
                <div class="message-avatar ${avatarClass}">${avatarEmoji}</div>
                <div class="message-content-wrapper">
                    <div class="message-label">${role === 'user' ? 'You' : 'Assistant'}</div>
                    <div class="message-content ${isError ? 'error' : ''}">${content}</div>
                    ${metaHTML}
                </div>
            `;
            
            const welcome = messagesDiv.querySelector('.welcome');
            if (welcome) welcome.remove();
            
            messagesDiv.appendChild(messageDiv);
            
            // Auto-scroll
            setTimeout(() => {
                messageDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
            }, 10);
        }

        function executeCommand(command) {
            messageInput.value = command;
            sendMessage();
            showToast('⌨️', `Executed: ${command}`);
        }

        // Toast notifications
        function showToast(icon, message) {
            const toast = document.getElementById('toast');
            const toastIcon = document.getElementById('toastIcon');
            const toastMessage = document.getElementById('toastMessage');
            
            toastIcon.textContent = icon;
            toastMessage.textContent = message;
            toast.classList.add('show');
            
            setTimeout(() => {
                toast.classList.remove('show');
            }, 3000);
        }

        // Focus input on load
        window.addEventListener('load', () => {
            messageInput.focus();
        });

        // Handle window resize for mobile
        let resizeTimer;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(() => {
                if (window.innerWidth > 768) {
                    document.querySelector('.sidebar').classList.remove('open');
                }
            }, 250);
        });

        // Click outside to hide autocomplete
        document.addEventListener('click', (e) => {
            if (!e.target.closest('#messageInput') && !e.target.closest('#autocomplete')) {
                hideAutocomplete();
            }
        });

        // Keyboard shortcut help
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === '/') {
                e.preventDefault();
                showToast('⌨️', 'Ctrl+/: Help | Tab: Autocomplete | Enter: Send | ↑↓: History');
            }
        });
    </script>
</body>
</html>'''


def start_web_server(host='localhost', port=8000, db_path="db/acc.db"):
    """Start the unified web server"""
    
    print("=" * 60)
    print("🚀 TASA AI Knowledge Assistant - Web Server")
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