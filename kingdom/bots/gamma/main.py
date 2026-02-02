#!/usr/bin/env python3
"""
Kingdom Bot Gamma
=================

Entry point for the Gamma bot instance.
Manages VPS Server 3 in the Kingdom infrastructure.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from kingdom.core import KingdomBot, load_config


def main() -> None:
    """Main entry point for Gamma bot."""
    # Determine config path
    config_path = Path(__file__).parent / "config.yaml"
    
    # Load configuration
    config = load_config(config_path=config_path, bot_id="gamma")
    
    # Create and run bot
    bot = KingdomBot(
        config=config,
        bot_name="Kingdom Gamma",
        bot_id="gamma",
    )
    
    # Run the bot
    bot.run_bot()


if __name__ == "__main__":
    main()
