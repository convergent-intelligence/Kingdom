"""
Kingdom Discord Bot Framework
=============================

A shared framework for autonomous Discord bots managing Tailscale VPS servers.
"""

from .bot_base import KingdomBot
from .config import Config, load_config

__version__ = "1.0.0"
__all__ = ["KingdomBot", "Config", "load_config"]
