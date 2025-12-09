"""
Main Entry Point for Textual TUI Interface
"""

from chat_v2_cleaneroutput import EnhancedChatSystem
from tui_app import run_tui


def main():
    """Initialize and run TUI"""
    print("🔧 Initializing Autoliv AI Knowledge Assistant...")
    
    # Initialize chat system
    chat_system = EnhancedChatSystem(
        db_path="db/acc.db",
        model_name="granite4:micro-h"
    )
    
    print("✅ System ready! Launching TUI...\n")
    
    # Run TUI
    run_tui(chat_system)


if __name__ == "__main__":
    main()
