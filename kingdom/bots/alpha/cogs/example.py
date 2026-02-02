"""
Example Local Cog
=================

Template for creating bot-specific cogs.
This file demonstrates how to add custom functionality to a specific bot.
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kingdom.core.bot_base import KingdomBot


class AlphaExampleCog(commands.Cog, name="AlphaExample"):
    """Example cog specific to the Alpha bot."""
    
    def __init__(self, bot: "KingdomBot") -> None:
        self.bot = bot
    
    @app_commands.command(name="alpha-info", description="Show Alpha server information")
    async def alpha_info(self, interaction: discord.Interaction) -> None:
        """Display Alpha-specific server information."""
        embed = discord.Embed(
            title="🅰️ Alpha Server Info",
            description="Primary server in the Kingdom infrastructure.",
            color=discord.Color.blue()
        )
        
        # Get server-specific config
        server_config = self.bot.config.get("server", {})
        
        embed.add_field(
            name="Role",
            value=server_config.get("role", "N/A"),
            inline=True
        )
        
        embed.add_field(
            name="Region",
            value=server_config.get("region", "N/A"),
            inline=True
        )
        
        embed.add_field(
            name="Tailscale Host",
            value=server_config.get("tailscale_hostname", "N/A"),
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)


async def setup(bot: "KingdomBot") -> None:
    """Setup function for loading the cog."""
    await bot.add_cog(AlphaExampleCog(bot))
