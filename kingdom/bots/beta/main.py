#!/usr/bin/env python3
"""
Kingdom Bot Beta
================

Entry point for the Beta bot instance.
Manages VPS Server 2 in the Kingdom infrastructure.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from kingdom.core import KingdomBot, load_config


def main() -> None:
    """Main entry point for Beta bot."""
    # Determine config path
    config_path = Path(__file__).parent / "config.yaml"
    
    # Load configuration
    config = load_config(config_path=config_path, bot_id="beta")
    
    # Create and run bot
    bot = KingdomBot(
        config=config,
        bot_name="Kingdom Beta",
        bot_id="beta",
    )
    
    # Run the bot
    bot.run_bot()


if __name__ == "__main__":
    main()
