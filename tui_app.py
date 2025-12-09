"""
Professional TUI Interface using Textual Framework
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Input, Static, Button, Markdown
from textual.binding import Binding
from textual.reactive import reactive
from textual import events
from rich.text import Text
from rich.markdown import Markdown as RichMarkdown
import asyncio


class ChatMessage(Static):
    """A single chat message widget"""
    
    def __init__(self, content: str, is_user: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.content = content
        self.is_user = is_user
    
    def compose(self) -> ComposeResult:
        """Create message layout"""
        if self.is_user:
            # User message - right aligned, blue
            yield Static(f"[bold blue]You:[/bold blue]\n{self.content}", classes="user-message")
        else:
            # Assistant message - left aligned, green with markdown
            yield Markdown(f"**🟣 Assistant:**\n\n{self.content}", classes="assistant-message")


class StatusBar(Static):
    """Status bar showing current mode and info"""
    
    status_text = reactive("Ready")
    
    def render(self) -> str:
        return f"[dim cyan]ℹ️  {self.status_text}[/dim cyan]"


class ChatHistory(ScrollableContainer):
    """Scrollable chat history container"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.can_focus = False


class ModeBanner(Static):
    """Display current response mode"""
    
    current_mode = reactive("normal")
    
    def render(self) -> str:
        mode_info = {
            "detail": "📘 DETAIL MODE - Comprehensive (400-600 words, ~20s)",
            "normal": "📗 NORMAL MODE - Balanced (150-250 words, ~10s) [ACTIVE]",
            "short": "📕 SHORT MODE - Brief (30-80 words, ~4s)"
        }
        return f"[bold yellow]{mode_info.get(self.current_mode, mode_info['normal'])}[/bold yellow]"


class AutolivTUI(App):
    """Professional TUI for Autoliv AI Knowledge Assistant"""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #main-container {
        height: 100%;
        background: $surface;
    }
    
    #header-section {
        height: auto;
        background: $primary;
        padding: 1;
        border: solid $accent;
    }
    
    #title {
        text-align: center;
        text-style: bold;
        color: $accent;
    }
    
    #mode-banner {
        height: 3;
        padding: 1;
        background: $panel;
        border: solid $secondary;
        margin: 1 0;
    }
    
    #chat-history {
        height: 1fr;
        background: $surface;
        border: solid $primary;
        padding: 1;
        margin: 0 1;
    }
    
    .user-message {
        background: $primary-background;
        color: $primary;
        padding: 1 2;
        margin: 1 0;
        border: solid $primary;
        width: 80%;
        align: right top;
    }
    
    .assistant-message {
        background: $success-darken-1;
        color: $text;
        padding: 1 2;
        margin: 1 0;
        border: solid $success;
        width: 85%;
        align: left top;
    }
    
    #status-bar {
        height: 3;
        padding: 1;
        background: $panel;
        border: solid $secondary;
        margin: 0 1;
    }
    
    #input-section {
        height: auto;
        background: $panel;
        padding: 1;
        border: solid $accent;
        margin: 0 1 1 1;
    }
    
    #input-box {
        width: 1fr;
        border: solid $accent;
    }
    
    #help-text {
        text-align: center;
        color: $text-muted;
        padding: 0 1;
        margin-top: 1;
    }
    
    .processing {
        text-align: center;
        color: $warning;
        text-style: bold;
        padding: 1;
        background: $warning-darken-3;
        border: solid $warning;
        margin: 1;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True),
        Binding("ctrl+l", "clear", "Clear Chat", show=True),
        Binding("ctrl+h", "help", "Help", show=True),
        Binding("ctrl+n", "new_session", "New Session", show=False),
    ]
    
    TITLE = "🔭 Autoliv AI Knowledge Assistant"
    SUB_TITLE = "Smart Document Search & Retrieval System"
    
    def __init__(self, chat_system):
        super().__init__()
        self.chat_system = chat_system
        self.processing = False
    
    def compose(self) -> ComposeResult:
        """Create the TUI layout"""
        yield Header(show_clock=True)
        
        with Container(id="main-container"):
            # Title section
            with Vertical(id="header-section"):
                yield Static("🔭 [bold cyan]Autoliv AI Knowledge Assistant[/bold cyan]", id="title")
                yield Static("[dim]Smart Document Search & Retrieval System[/dim]", id="subtitle")
            
            # Mode banner
            yield ModeBanner(id="mode-banner")
            
            # Chat history
            yield ChatHistory(id="chat-history")
            
            # Status bar
            yield StatusBar(id="status-bar")
            
            # Input section
            with Vertical(id="input-section"):
                yield Input(
                    placeholder="Ask me anything... (Type /help for commands)",
                    id="input-box"
                )
                yield Static(
                    "[dim]💡 Commands: /detail, /normal, /short, /clear, /help, /quit[/dim]",
                    id="help-text"
                )
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when app starts"""
        self.query_one("#input-box").focus()
        self.add_welcome_message()
    
    def add_welcome_message(self) -> None:
        """Add welcome message to chat"""
        welcome_text = """Welcome! I'm your AI Knowledge Assistant.

**Available Commands:**
- `/detail` - Comprehensive analysis (400-600 words)
- `/normal` - Balanced response (150-250 words) [DEFAULT]
- `/short` - Brief answer (30-80 words)
- `/clear` - Clear chat history
- `/help` - Show help
- `/quit` - Exit application

**Ask me anything about your documents!**"""
        
        chat_history = self.query_one("#chat-history")
        chat_history.mount(ChatMessage(welcome_text, is_user=False))
        chat_history.scroll_end(animate=False)
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user input submission"""
        user_input = event.value.strip()
        
        if not user_input:
            return
        
        # Clear input
        input_box = self.query_one("#input-box")
        input_box.value = ""
        
        # Add user message
        chat_history = self.query_one("#chat-history")
        chat_history.mount(ChatMessage(user_input, is_user=True))
        chat_history.scroll_end(animate=True)
        
        # Handle commands
        if user_input == "/quit":
            self.exit()
            return
        
        elif user_input == "/clear":
            await self.action_clear()
            return
        
        elif user_input == "/help":
            self.show_help_message()
            return
        
        elif user_input.startswith("/detail"):
            self.update_mode("detail")
            if len(user_input) > 7:
                user_input = user_input[7:].strip()
            else:
                return
        
        elif user_input.startswith("/normal"):
            self.update_mode("normal")
            if len(user_input) > 7:
                user_input = user_input[7:].strip()
            else:
                return
        
        elif user_input.startswith("/short"):
            self.update_mode("short")
            if len(user_input) > 6:
                user_input = user_input[6:].strip()
            else:
                return
        
        # Process query
        await self.process_query(user_input)
    
    def update_mode(self, mode: str) -> None:
        """Update response mode"""
        mode_banner = self.query_one(ModeBanner)
        mode_banner.current_mode = mode
        
        status_bar = self.query_one(StatusBar)
        status_bar.status_text = f"Mode changed to: {mode.upper()}"
    
    def show_help_message(self) -> None:
        """Show help information"""
        help_text = """**📋 Available Commands:**

**Response Modes:**
- `/detail` - Comprehensive analysis (400-600 words, ~20 seconds)
- `/normal` - Balanced response (150-250 words, ~10 seconds)
- `/short` - Brief answer (30-80 words, ~4 seconds)

**Session Commands:**
- `/clear` - Clear current chat history
- `/help` - Show this help message
- `/quit` - Exit the application

**Keyboard Shortcuts:**
- `Ctrl+C` - Quit application
- `Ctrl+L` - Clear chat history
- `Ctrl+H` - Show help

**How to use:**
Just type your question and press Enter!"""
        
        chat_history = self.query_one("#chat-history")
        chat_history.mount(ChatMessage(help_text, is_user=False))
        chat_history.scroll_end(animate=True)
    
    async def process_query(self, query: str) -> None:
        """Process user query and show response"""
        if self.processing:
            return
        
        self.processing = True
        status_bar = self.query_one(StatusBar)
        chat_history = self.query_one("#chat-history")
        
        # Show processing indicator
        processing_msg = Static("⚙️ Processing your query...", classes="processing")
        chat_history.mount(processing_msg)
        chat_history.scroll_end(animate=True)
        
        try:
            # Update status
            status_bar.status_text = "🔍 Searching documents..."
            
            # Process in background
            result = await asyncio.to_thread(self.chat_system.ask, query)
            
            # Remove processing indicator
            processing_msg.remove()
            
            # Add assistant response
            answer = result.get('answer', 'No response generated.')
            
            # Add metadata to answer
            confidence = result.get('confidence', 0)
            num_sources = result.get('num_sources', 0)
            response_time = result.get('response_time', 0)
            
            metadata = f"\n\n---\n**Confidence:** {confidence*100:.0f}% | **Sources:** {num_sources} | **Time:** {response_time:.1f}s"
            full_answer = answer + metadata
            
            chat_history.mount(ChatMessage(full_answer, is_user=False))
            chat_history.scroll_end(animate=True)
            
            # Update status
            status_bar.status_text = f"✅ Response generated ({response_time:.1f}s)"
        
        except Exception as error:
            # Remove processing indicator
            processing_msg.remove()
            
            # Show error
            error_msg = f"**❌ Error:**\n{str(error)}"
            chat_history.mount(ChatMessage(error_msg, is_user=False))
            chat_history.scroll_end(animate=True)
            
            status_bar.status_text = "❌ Error processing query"
        
        finally:
            self.processing = False
    
    async def action_clear(self) -> None:
        """Clear chat history"""
        chat_history = self.query_one("#chat-history")
        await chat_history.remove_children()
        
        self.chat_system.session_manager.clear_session()
        
        self.add_welcome_message()
        
        status_bar = self.query_one(StatusBar)
        status_bar.status_text = "🗑️ Chat history cleared"
    
    async def action_help(self) -> None:
        """Show help"""
        self.show_help_message()
    
    async def action_new_session(self) -> None:
        """Create new session"""
        new_id = self.chat_system.session_manager.create_session()
        
        status_bar = self.query_one(StatusBar)
        status_bar.status_text = f"✨ New session created: {new_id}"


def run_tui(chat_system):
    """Run the TUI application"""
    app = AutolivTUI(chat_system)
    app.run()
