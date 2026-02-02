"""
Monitoring Cog
==============

Discord slash commands for system monitoring and status.
Provides /status, /health, /metrics commands.
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import TYPE_CHECKING

from ..utils.system import SystemMonitor, get_system_info
from ..utils.network import TailscaleClient, NetworkUtils

if TYPE_CHECKING:
    from ..bot_base import KingdomBot


class MonitoringCog(commands.Cog, name="Monitoring"):
    """System monitoring and status commands."""
    
    def __init__(self, bot: "KingdomBot") -> None:
        self.bot = bot
        self.system_monitor = SystemMonitor()
        self.tailscale = TailscaleClient()
    
    def _check_permissions(self, interaction: discord.Interaction) -> bool:
        """Check if user has permission to use monitoring commands."""
        # Get admin users and roles from config
        admin_users = self.bot.config.get("permissions.admin_users", [])
        admin_roles = self.bot.config.get("permissions.admin_roles", [])
        
        # Check user ID
        if str(interaction.user.id) in [str(u) for u in admin_users]:
            return True
        
        # Check roles
        if interaction.guild and hasattr(interaction.user, "roles"):
            user_role_ids = [str(r.id) for r in interaction.user.roles]
            for admin_role in admin_roles:
                if str(admin_role) in user_role_ids:
                    return True
        
        # Allow server administrators
        if interaction.guild:
            member = interaction.guild.get_member(interaction.user.id)
            if member and member.guild_permissions.administrator:
                return True
        
        return False
    
    @app_commands.command(name="status", description="Get bot and server status")
    async def status(self, interaction: discord.Interaction) -> None:
        """Display bot and server status."""
        await interaction.response.defer()
        
        try:
            # Get system info
            sys_info = self.system_monitor.get_info()
            
            # Get Tailscale status
            ts_status = await self.tailscale.get_status()
            
            # Build embed
            embed = discord.Embed(
                title=f"📊 Status: {self.bot.bot_name}",
                color=discord.Color.green() if self.bot.is_healthy() else discord.Color.red(),
                timestamp=sys_info.timestamp
            )
            
            # Bot info
            uptime_str = "N/A"
            if self.bot.uptime:
                total_seconds = self.bot.uptime.total_seconds()
                days = int(total_seconds // 86400)
                hours = int((total_seconds % 86400) // 3600)
                minutes = int((total_seconds % 3600) // 60)
                uptime_str = f"{days}d {hours}h {minutes}m"
            
            embed.add_field(
                name="🤖 Bot",
                value=f"**ID:** {self.bot.bot_id.upper()}\n"
                      f"**Uptime:** {uptime_str}\n"
                      f"**Latency:** {round(self.bot.latency * 1000, 2)}ms\n"
                      f"**Guilds:** {len(self.bot.guilds)}",
                inline=True
            )
            
            # System info
            embed.add_field(
                name="💻 System",
                value=f"**Host:** {sys_info.hostname}\n"
                      f"**OS:** {sys_info.platform} {sys_info.platform_release}\n"
                      f"**CPU:** {sys_info.cpu_percent:.1f}%\n"
                      f"**Memory:** {sys_info.memory_percent:.1f}%",
                inline=True
            )
            
            # Tailscale info
            ts_emoji = "🟢" if ts_status.is_connected else "🔴"
            embed.add_field(
                name=f"🔗 Tailscale {ts_emoji}",
                value=f"**IP:** {ts_status.tailscale_ip or 'N/A'}\n"
                      f"**State:** {ts_status.backend_state or 'N/A'}\n"
                      f"**Peers:** {len(ts_status.peers)}\n"
                      f"**Tailnet:** {ts_status.tailnet or 'N/A'}",
                inline=True
            )
            
            # Disk info
            disk_used_gb = sys_info.disk_used / (1024**3)
            disk_total_gb = sys_info.disk_total / (1024**3)
            embed.add_field(
                name="💾 Disk",
                value=f"**Used:** {disk_used_gb:.1f} GB / {disk_total_gb:.1f} GB\n"
                      f"**Usage:** {sys_info.disk_percent:.1f}%",
                inline=True
            )
            
            # Network info
            bytes_sent_mb = sys_info.bytes_sent / (1024**2)
            bytes_recv_mb = sys_info.bytes_recv / (1024**2)
            embed.add_field(
                name="🌐 Network",
                value=f"**Sent:** {bytes_sent_mb:.1f} MB\n"
                      f"**Received:** {bytes_recv_mb:.1f} MB",
                inline=True
            )
            
            # Load average
            load = self.system_monitor.get_load_average()
            embed.add_field(
                name="📈 Load Average",
                value=f"**1m:** {load[0]:.2f}\n"
                      f"**5m:** {load[1]:.2f}\n"
                      f"**15m:** {load[2]:.2f}",
                inline=True
            )
            
            embed.set_footer(text=f"Server: {self.bot.bot_id.upper()}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self.bot.logger.error(f"Error in status command: {e}", exc_info=True)
            await interaction.followup.send(
                f"❌ Error getting status: {e}",
                ephemeral=True
            )
    
    @app_commands.command(name="health", description="Get bot health check")
    async def health(self, interaction: discord.Interaction) -> None:
        """Display bot health status."""
        health = self.bot.health
        
        if health.get("status") == "healthy":
            color = discord.Color.green()
            emoji = "✅"
        else:
            color = discord.Color.red()
            emoji = "❌"
        
        embed = discord.Embed(
            title=f"{emoji} Health Check: {self.bot.bot_id.upper()}",
            color=color
        )
        
        embed.add_field(
            name="Status",
            value=health.get("status", "unknown").upper(),
            inline=True
        )
        
        embed.add_field(
            name="Latency",
            value=f"{health.get('latency_ms', 'N/A')} ms",
            inline=True
        )
        
        embed.add_field(
            name="Uptime",
            value=f"{int(health.get('uptime_seconds', 0))} seconds",
            inline=True
        )
        
        embed.add_field(
            name="Guilds",
            value=str(health.get("guilds", 0)),
            inline=True
        )
        
        embed.add_field(
            name="Last Check",
            value=health.get("timestamp", "N/A"),
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="metrics", description="Get detailed system metrics")
    async def metrics(self, interaction: discord.Interaction) -> None:
        """Display detailed system metrics."""
        if not self._check_permissions(interaction):
            await interaction.response.send_message(
                "❌ You don't have permission to view detailed metrics.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            sys_info = self.system_monitor.get_info()
            
            # Create detailed metrics embed
            embed = discord.Embed(
                title=f"📈 Metrics: {self.bot.bot_id.upper()}",
                color=discord.Color.blue(),
                timestamp=sys_info.timestamp
            )
            
            # CPU details
            cpu_times = self.system_monitor.get_cpu_times()
            embed.add_field(
                name="🔧 CPU Details",
                value=f"**Physical Cores:** {sys_info.cpu_count_physical}\n"
                      f"**Logical Cores:** {sys_info.cpu_count_logical}\n"
                      f"**Current Freq:** {sys_info.cpu_freq_current:.0f} MHz\n"
                      f"**Max Freq:** {sys_info.cpu_freq_max:.0f} MHz\n"
                      f"**User Time:** {cpu_times['user']:.1f}s\n"
                      f"**System Time:** {cpu_times['system']:.1f}s",
                inline=True
            )
            
            # Memory details
            mem_total_gb = sys_info.memory_total / (1024**3)
            mem_used_gb = sys_info.memory_used / (1024**3)
            mem_avail_gb = sys_info.memory_available / (1024**3)
            embed.add_field(
                name="🧠 Memory Details",
                value=f"**Total:** {mem_total_gb:.2f} GB\n"
                      f"**Used:** {mem_used_gb:.2f} GB\n"
                      f"**Available:** {mem_avail_gb:.2f} GB\n"
                      f"**Usage:** {sys_info.memory_percent:.1f}%",
                inline=True
            )
            
            # Swap details
            swap_total_gb = sys_info.swap_total / (1024**3)
            swap_used_gb = sys_info.swap_used / (1024**3)
            embed.add_field(
                name="💫 Swap",
                value=f"**Total:** {swap_total_gb:.2f} GB\n"
                      f"**Used:** {swap_used_gb:.2f} GB\n"
                      f"**Usage:** {sys_info.swap_percent:.1f}%",
                inline=True
            )
            
            # Top processes
            top_procs = self.system_monitor.get_top_processes(n=5, sort_by="cpu")
            proc_list = "\n".join([
                f"`{p.name[:15]:<15}` CPU: {p.cpu_percent:>5.1f}% MEM: {p.memory_percent:>5.1f}%"
                for p in top_procs
            ])
            embed.add_field(
                name="🔝 Top Processes (by CPU)",
                value=proc_list or "No processes",
                inline=False
            )
            
            # System uptime
            embed.add_field(
                name="⏱️ System Uptime",
                value=sys_info._format_uptime(sys_info.uptime_seconds),
                inline=True
            )
            
            embed.set_footer(text=f"Host: {sys_info.hostname}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self.bot.logger.error(f"Error in metrics command: {e}", exc_info=True)
            await interaction.followup.send(
                f"❌ Error getting metrics: {e}",
                ephemeral=True
            )
    
    @app_commands.command(name="tailscale", description="Get Tailscale network status")
    async def tailscale_status(self, interaction: discord.Interaction) -> None:
        """Display Tailscale network status."""
        if not self._check_permissions(interaction):
            await interaction.response.send_message(
                "❌ You don't have permission to view Tailscale status.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            ts_status = await self.tailscale.get_status()
            
            # Status color
            if ts_status.is_connected:
                color = discord.Color.green()
                status_emoji = "🟢"
            elif ts_status.is_running:
                color = discord.Color.yellow()
                status_emoji = "🟡"
            else:
                color = discord.Color.red()
                status_emoji = "🔴"
            
            embed = discord.Embed(
                title=f"🔗 Tailscale Status {status_emoji}",
                color=color,
                timestamp=ts_status.timestamp
            )
            
            # Connection info
            embed.add_field(
                name="📡 Connection",
                value=f"**State:** {ts_status.backend_state or 'N/A'}\n"
                      f"**IP:** {ts_status.tailscale_ip or 'N/A'}\n"
                      f"**Hostname:** {ts_status.hostname or 'N/A'}\n"
                      f"**DNS:** {ts_status.dns_name or 'N/A'}",
                inline=True
            )
            
            # Network info
            embed.add_field(
                name="🌐 Network",
                value=f"**Tailnet:** {ts_status.tailnet or 'N/A'}\n"
                      f"**Version:** {ts_status.version or 'N/A'}\n"
                      f"**Peers:** {len(ts_status.peers)}",
                inline=True
            )
            
            # Exit node
            if ts_status.exit_node:
                embed.add_field(
                    name="🚪 Exit Node",
                    value=f"**Node:** {ts_status.exit_node}\n"
                          f"**IP:** {ts_status.exit_node_ip or 'N/A'}",
                    inline=True
                )
            
            # Online peers
            online_peers = [p for p in ts_status.peers if p.get("online")]
            if online_peers:
                peer_list = "\n".join([
                    f"• `{p.get('hostname', 'unknown')[:20]}` ({p.get('os', 'unknown')})"
                    for p in online_peers[:10]
                ])
                if len(online_peers) > 10:
                    peer_list += f"\n... and {len(online_peers) - 10} more"
                
                embed.add_field(
                    name=f"👥 Online Peers ({len(online_peers)})",
                    value=peer_list,
                    inline=False
                )
            
            embed.set_footer(text=f"Server: {self.bot.bot_id.upper()}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self.bot.logger.error(f"Error in tailscale command: {e}", exc_info=True)
            await interaction.followup.send(
                f"❌ Error getting Tailscale status: {e}",
                ephemeral=True
            )
    
    @app_commands.command(name="ping", description="Ping a host or Tailscale peer")
    @app_commands.describe(target="Host or IP to ping", count="Number of pings (1-10)")
    async def ping_host(
        self,
        interaction: discord.Interaction,
        target: str,
        count: int = 3
    ) -> None:
        """Ping a host or Tailscale peer."""
        if not self._check_permissions(interaction):
            await interaction.response.send_message(
                "❌ You don't have permission to use ping.",
                ephemeral=True
            )
            return
        
        # Validate count
        count = max(1, min(10, count))
        
        await interaction.response.defer()
        
        try:
            result = await NetworkUtils.ping(target, count=count)
            
            if result.get("success"):
                color = discord.Color.green()
                emoji = "✅"
            else:
                color = discord.Color.red()
                emoji = "❌"
            
            embed = discord.Embed(
                title=f"{emoji} Ping: {target}",
                color=color
            )
            
            if result.get("success"):
                embed.add_field(
                    name="📊 Statistics",
                    value=f"**Packets:** {result.get('packets_received', 0)}/{result.get('packets_sent', count)}\n"
                          f"**Loss:** {result.get('packet_loss', 100):.1f}%",
                    inline=True
                )
                
                if result.get("rtt_avg"):
                    embed.add_field(
                        name="⏱️ Round Trip Time",
                        value=f"**Min:** {result.get('rtt_min', 0):.2f} ms\n"
                              f"**Avg:** {result.get('rtt_avg', 0):.2f} ms\n"
                              f"**Max:** {result.get('rtt_max', 0):.2f} ms",
                        inline=True
                    )
            else:
                embed.add_field(
                    name="Error",
                    value=result.get("error", "Unknown error"),
                    inline=False
                )
            
            embed.set_footer(text=f"From: {self.bot.bot_id.upper()}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self.bot.logger.error(f"Error in ping command: {e}", exc_info=True)
            await interaction.followup.send(
                f"❌ Error pinging {target}: {e}",
                ephemeral=True
            )


async def setup(bot: "KingdomBot") -> None:
    """Setup function for loading the cog."""
    await bot.add_cog(MonitoringCog(bot))
