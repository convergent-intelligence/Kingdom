"""
Kingdom Bot Base Class
======================

Provides the foundational bot class with async lifecycle management,
logging, health checks, and cog loading capabilities.
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import discord
from discord import app_commands
from discord.ext import commands, tasks

from .config import Config


class KingdomBot(commands.Bot):
    """
    Base class for Kingdom Discord bots.
    
    Provides:
    - Async lifecycle management (startup, shutdown)
    - Structured logging
    - Health check system
    - Automatic cog loading
    - Graceful shutdown handling
    """
    
    def __init__(
        self,
        config: Config,
        *,
        bot_name: str = "kingdom",
        bot_id: str = "unknown",
    ) -> None:
        """
        Initialize the Kingdom bot.
        
        Args:
            config: Bot configuration object
            bot_name: Human-readable bot name
            bot_id: Unique bot identifier (alpha, beta, gamma, delta)
        """
        self.config = config
        self.bot_name = bot_name
        self.bot_id = bot_id
        self.start_time: Optional[datetime] = None
        self._health_status: dict[str, Any] = {}
        self._shutdown_event = asyncio.Event()
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Discord intents
        intents = discord.Intents.default()
        intents.message_content = config.get("intents.message_content", False)
        intents.members = config.get("intents.members", False)
        
        # Initialize the bot
        super().__init__(
            command_prefix=config.get("prefix", "!"),
            intents=intents,
            help_command=None,
        )
        
        # Register signal handlers
        self._register_signals()
        
    def _setup_logging(self) -> logging.Logger:
        """Configure structured logging for the bot."""
        logger = logging.getLogger(f"kingdom.{self.bot_id}")
        logger.setLevel(
            getattr(logging, self.config.get("logging.level", "INFO").upper())
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        
        # Format with bot ID for multi-bot environments
        formatter = logging.Formatter(
            f"[%(asctime)s] [{self.bot_id.upper()}] [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(formatter)
        
        # File handler if configured
        log_file = self.config.get("logging.file")
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_path)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        logger.addHandler(console_handler)
        return logger
    
    def _register_signals(self) -> None:
        """Register signal handlers for graceful shutdown."""
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                asyncio.get_event_loop().add_signal_handler(
                    sig,
                    lambda s=sig: asyncio.create_task(self._handle_signal(s))
                )
            except NotImplementedError:
                # Windows doesn't support add_signal_handler
                signal.signal(sig, lambda s, f: asyncio.create_task(self._handle_signal(s)))
    
    async def _handle_signal(self, sig: signal.Signals) -> None:
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {sig.name}, initiating shutdown...")
        self._shutdown_event.set()
        await self.close()
    
    async def setup_hook(self) -> None:
        """
        Called when the bot is starting up.
        Override to add custom setup logic.
        """
        self.logger.info(f"Setting up {self.bot_name} ({self.bot_id})...")
        
        # Load core cogs
        await self._load_core_cogs()
        
        # Load bot-specific cogs
        await self._load_local_cogs()
        
        # Start background tasks
        self.health_check_task.start()
        
        self.logger.info("Setup complete, syncing commands...")
        
        # Sync slash commands
        guild_id = self.config.get("guild_id")
        if guild_id:
            guild = discord.Object(id=int(guild_id))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            self.logger.info(f"Commands synced to guild {guild_id}")
        else:
            await self.tree.sync()
            self.logger.info("Commands synced globally")
    
    async def _load_core_cogs(self) -> None:
        """Load the core framework cogs."""
        core_cogs = [
            "kingdom.core.cogs.monitoring",
            "kingdom.core.cogs.control",
            "kingdom.core.cogs.files",
        ]
        
        for cog in core_cogs:
            try:
                await self.load_extension(cog)
                self.logger.info(f"Loaded core cog: {cog}")
            except Exception as e:
                self.logger.error(f"Failed to load core cog {cog}: {e}")
    
    async def _load_local_cogs(self) -> None:
        """Load bot-specific cogs from the local cogs directory."""
        local_cogs_path = self.config.get("cogs_path")
        if not local_cogs_path:
            return
            
        cogs_dir = Path(local_cogs_path)
        if not cogs_dir.exists():
            self.logger.warning(f"Local cogs directory not found: {cogs_dir}")
            return
        
        for cog_file in cogs_dir.glob("*.py"):
            if cog_file.name.startswith("_"):
                continue
                
            # Convert path to module name
            module_name = f"bots.{self.bot_id}.cogs.{cog_file.stem}"
            try:
                await self.load_extension(module_name)
                self.logger.info(f"Loaded local cog: {module_name}")
            except Exception as e:
                self.logger.error(f"Failed to load local cog {module_name}: {e}")
    
    async def on_ready(self) -> None:
        """Called when the bot is fully connected and ready."""
        self.start_time = datetime.now(timezone.utc)
        self.logger.info(f"{self.bot_name} is ready!")
        self.logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        self.logger.info(f"Connected to {len(self.guilds)} guild(s)")
        
        # Set presence
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"Server {self.bot_id.upper()}"
        )
        await self.change_presence(activity=activity, status=discord.Status.online)
    
    async def on_error(self, event_method: str, *args: Any, **kwargs: Any) -> None:
        """Handle errors in event handlers."""
        self.logger.exception(f"Error in {event_method}")
    
    async def on_command_error(
        self,
        ctx: commands.Context,
        error: commands.CommandError
    ) -> None:
        """Handle command errors."""
        if isinstance(error, commands.CommandNotFound):
            return
        
        self.logger.error(f"Command error: {error}", exc_info=error)
        
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command.")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("❌ I don't have the required permissions.")
        else:
            await ctx.send(f"❌ An error occurred: {error}")
    
    @tasks.loop(minutes=1)
    async def health_check_task(self) -> None:
        """Periodic health check task."""
        self._health_status = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": self.uptime.total_seconds() if self.uptime else 0,
            "latency_ms": round(self.latency * 1000, 2),
            "guilds": len(self.guilds),
            "bot_id": self.bot_id,
        }
    
    @health_check_task.before_loop
    async def before_health_check(self) -> None:
        """Wait for bot to be ready before starting health checks."""
        await self.wait_until_ready()
    
    @property
    def uptime(self) -> Optional[datetime]:
        """Get the bot's uptime as a timedelta."""
        if self.start_time:
            return datetime.now(timezone.utc) - self.start_time
        return None
    
    @property
    def health(self) -> dict[str, Any]:
        """Get the current health status."""
        return self._health_status.copy()
    
    def is_healthy(self) -> bool:
        """Check if the bot is healthy."""
        return self._health_status.get("status") == "healthy"
    
    async def close(self) -> None:
        """Gracefully shut down the bot."""
        self.logger.info("Shutting down...")
        
        # Stop background tasks
        if self.health_check_task.is_running():
            self.health_check_task.cancel()
        
        # Update presence
        try:
            await self.change_presence(status=discord.Status.offline)
        except Exception:
            pass
        
        # Close the connection
        await super().close()
        self.logger.info("Shutdown complete")
    
    async def run_async(self) -> None:
        """Run the bot asynchronously."""
        token = self.config.get("token")
        if not token:
            raise ValueError("Bot token not configured")
        
        try:
            await self.start(token)
        except Exception as e:
            self.logger.exception(f"Fatal error: {e}")
            raise
        finally:
            if not self.is_closed():
                await self.close()
    
    def run_bot(self) -> None:
        """Run the bot (blocking)."""
        token = self.config.get("token")
        if not token:
            raise ValueError("Bot token not configured")
        
        try:
            self.run(token)
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        except Exception as e:
            self.logger.exception(f"Fatal error: {e}")
            raise
