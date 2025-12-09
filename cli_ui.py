"""
Professional CLI UI Module - Claude Code Style
"""

import sys
import time
import threading
from typing import Optional
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich.text import Text
from rich.table import Table
from rich.box import ROUNDED, MINIMAL
from rich import print as rprint


class ProfessionalCLI:
    """Claude Code style CLI interface"""
    
    def __init__(self):
        self.console = Console()
        self.processing = False
        
    def clear_screen(self):
        """Clear terminal screen"""
        self.console.clear()
    
    def show_welcome_banner(self):
        """Display professional welcome banner"""
        self.console.print()
        
        welcome_text = """
# 🔭 Autoliv AI Knowledge Assistant
### Smart Document Search & Retrieval System

**Powered by Advanced RAG Pipeline**
"""
        
        welcome_panel = Panel(
            Markdown(welcome_text),
            border_style="cyan",
            box=ROUNDED,
            padding=(1, 2)
        )
        
        self.console.print(welcome_panel)
        self.console.print()
    
    def show_response_modes(self):
        """Display available response modes"""
        modes_table = Table(
            show_header=True,
            header_style="bold cyan",
            border_style="dim",
            box=MINIMAL,
            padding=(0, 1)
        )
        
        modes_table.add_column("Mode", style="yellow", width=15)
        modes_table.add_column("Description", style="white", width=50)
        
        modes_table.add_row(
            "/detail",
            "📘 Comprehensive analysis (400-600 words, ~20s)"
        )
        modes_table.add_row(
            "/normal",
            "📗 Balanced response (150-250 words, ~10s) [DEFAULT]"
        )
        modes_table.add_row(
            "/short",
            "📕 Brief answer (30-80 words, ~4s)"
        )
        
        self.console.print(Panel(
            modes_table,
            title="[bold cyan]📋 Response Modes[/bold cyan]",
            border_style="cyan",
            box=ROUNDED
        ))
        self.console.print()
    
    def show_commands(self):
        """Display available commands"""
        commands_table = Table(
            show_header=True,
            header_style="bold magenta",
            border_style="dim",
            box=MINIMAL,
            padding=(0, 1)
        )
        
        commands_table.add_column("Command", style="green", width=15)
        commands_table.add_column("Description", style="white", width=50)
        
        commands_table.add_row("/clear", "🗑️  Clear current session")
        commands_table.add_row("/sessions", "📋 List all sessions")
        commands_table.add_row("/new", "✨ Create new session")
        commands_table.add_row("/switch ID", "🔄 Switch to session")
        commands_table.add_row("/logs", "📊 Show recent logs")
        commands_table.add_row("/help", "❓ Show this help")
        commands_table.add_row("/quit", "👋 Exit assistant")
        
        self.console.print(Panel(
            commands_table,
            title="[bold magenta]⚙️  Commands[/bold magenta]",
            border_style="magenta",
            box=ROUNDED
        ))
        self.console.print()
    
    def show_help(self):
        """Display help information"""
        self.console.print()
        self.show_response_modes()
        self.show_commands()
    
    def get_user_input(self) -> str:
        """Get user input with styling"""
        self.console.print()
        user_prompt = Text("You: ", style="bold blue")
        self.console.print(user_prompt, end="")
        
        try:
            user_input = input().strip()
            return user_input
        except (KeyboardInterrupt, EOFError):
            return "/quit"
    
    def show_processing_stage(self, stage_name: str, emoji: str = "⚙️"):
        """Show processing stage indicator"""
        stage_text = Text(f"{emoji} {stage_name}", style="dim cyan")
        self.console.print(stage_text)
    
    def show_mode_banner(self, mode: str, config: dict):
        """Display mode banner"""
        self.console.print()
        
        mode_info = f"""**{config['emoji']} MODE: {config['name']}**
📊 Method: {'Two-Stage Analysis' if config['use_two_stage'] else 'Single-Stage (optimized)'}
⏱️  Expected time: {config['expected_time']}"""
        
        mode_panel = Panel(
            Markdown(mode_info),
            border_style="yellow",
            box=ROUNDED,
            padding=(0, 2)
        )
        
        self.console.print(mode_panel)
        self.console.print()
    
    def show_analysis(self, analysis_text: str):
        """Display analysis phase"""
        self.console.print()
        
        analysis_panel = Panel(
            Markdown(analysis_text),
            title="[bold cyan]💭 Analysis Phase[/bold cyan]",
            border_style="cyan",
            box=ROUNDED,
            padding=(1, 2)
        )
        
        self.console.print(analysis_panel)
        self.console.print()
    
    def stream_response(self, response_text: str, delay: float = 0.02):
        """Stream response word by word like Claude Code"""
        self.console.print()
        self.console.print("[bold green]Assistant:[/bold green]")
        self.console.print()
        
        # Split into words but preserve markdown
        words = response_text.split()
        
        current_line = ""
        for word in words:
            current_line += word + " "
            
            # Print word by word
            self.console.print(word, end=" ", style="white")
            time.sleep(delay)
        
        self.console.print("\n")
    
    def show_response_metadata(self, result: dict):
        """Display response metadata (confidence, sources, time)"""
        metadata_table = Table(
            show_header=False,
            border_style="dim",
            box=MINIMAL,
            padding=(0, 1)
        )
        
        metadata_table.add_column("Icon", style="white", width=5)
        metadata_table.add_column("Info", style="dim white", width=60)
        
        # Confidence
        confidence = result.get('confidence', 0)
        if confidence > 0.7:
            confidence_style = "green"
            confidence_emoji = "🟢"
        elif confidence > 0.4:
            confidence_style = "yellow"
            confidence_emoji = "🟡"
        else:
            confidence_style = "red"
            confidence_emoji = "🔴"
        
        metadata_table.add_row(
            confidence_emoji,
            f"Confidence: [{confidence_style}]{confidence*100:.0f}%[/{confidence_style}]"
        )
        
        # Sources
        if result['sources']:
            metadata_table.add_row(
                "📚",
                f"Sources: {result['num_sources']} sections used"
            )
        elif result.get('used_memory'):
            metadata_table.add_row(
                "🧠",
                "Answered from conversation memory"
            )
        
        # Response time
        response_time = result.get('response_time', 0)
        metadata_table.add_row(
            "⏱️",
            f"Response time: {response_time:.1f}s"
        )
        
        self.console.print(metadata_table)
        self.console.print()
    
    def show_sources(self, sources: list, max_display: int = 3):
        """Display source citations"""
        if not sources:
            return
        
        self.console.print()
        self.console.print("[bold cyan]📖 Sources:[/bold cyan]")
        
        for idx, source in enumerate(sources[:max_display], 1):
            source_text = f"**[{idx}]** {source['document']}"
            source_preview = f"_{source['preview']}_"
            
            self.console.print(f"  {source_text}")
            self.console.print(f"     {source_preview}", style="dim")
            self.console.print()
    
    def show_error(self, error_message: str):
        """Display error message"""
        error_panel = Panel(
            f"[bold red]❌ Error:[/bold red] {error_message}",
            border_style="red",
            box=ROUNDED,
            padding=(1, 2)
        )
        
        self.console.print()
        self.console.print(error_panel)
        self.console.print()
    
    def show_success(self, message: str):
        """Display success message"""
        success_text = Text(f"✅ {message}", style="bold green")
        self.console.print()
        self.console.print(success_text)
        self.console.print()
    
    def show_info(self, message: str):
        """Display info message"""
        info_text = Text(f"ℹ️  {message}", style="cyan")
        self.console.print()
        self.console.print(info_text)
        self.console.print()
    
    def show_sessions(self, sessions: list, active_session: str):
        """Display available sessions"""
        self.console.print()
        
        sessions_table = Table(
            show_header=True,
            header_style="bold cyan",
            border_style="cyan",
            box=ROUNDED,
            padding=(0, 2)
        )
        
        sessions_table.add_column("Session ID", style="yellow")
        sessions_table.add_column("Status", style="green")
        
        for session in sessions:
            status = "🟢 Active" if session == active_session else "⚪ Inactive"
            sessions_table.add_row(session, status)
        
        self.console.print(sessions_table)
        self.console.print()
    
    def show_logs(self, logs: list):
        """Display recent logs"""
        self.console.print()
        self.console.print("[bold cyan]📊 Recent Logs:[/bold cyan]")
        self.console.print()
        
        for log in logs:
            query = log.get('query', '')[:60]
            confidence = log.get('confidence', 0)
            
            log_text = f"  **Q:** {query}..."
            confidence_text = f"     Confidence: {confidence*100:.0f}%"
            
            self.console.print(log_text)
            self.console.print(confidence_text, style="dim")
            self.console.print()
    
    def show_goodbye(self):
        """Display goodbye message"""
        self.console.print()
        
        goodbye_text = Text("👋 Goodbye! Thanks for using Autoliv AI Assistant", style="bold cyan")
        self.console.print(goodbye_text)
        
        self.console.print()


class StreamingSpinner:
    """Elegant spinner for processing stages"""
    
    def __init__(self, console: Console, message: str = "Processing"):
        self.console = console
        self.message = message
        self.is_running = False
        self.thread = None
        self.live = None
    
    def start(self):
        """Start spinner"""
        self.is_running = True
        self.thread = threading.Thread(target=self._animate)
        self.thread.start()
    
    def stop(self):
        """Stop spinner"""
        self.is_running = False
        if self.thread:
            self.thread.join()
        if self.live:
            self.live.stop()
    
    def _animate(self):
        """Animate spinner"""
        with Progress(
            SpinnerColumn(spinner_name="dots"),
            TextColumn("[cyan]{task.description}"),
            console=self.console,
            transient=True
        ) as progress:
            self.live = progress
            task = progress.add_task(self.message, total=None)
            
            while self.is_running:
                time.sleep(0.1)
