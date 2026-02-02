"""
Control Cog
===========

Discord slash commands for server control operations.
Provides /exec, /service, /reboot commands.

⚠️ WARNING: These commands execute system operations.
Ensure proper permission controls are in place.
"""

import asyncio
import shlex
from typing import TYPE_CHECKING, Optional

import discord
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from ..bot_base import KingdomBot


class ControlCog(commands.Cog, name="Control"):
    """Server control and management commands."""
    
    # Commands that are always blocked for safety
    BLOCKED_COMMANDS = [
        "rm -rf /",
        "rm -rf /*",
        "mkfs",
        "dd if=/dev/zero",
        ":(){ :|:& };:",  # Fork bomb
        "> /dev/sda",
        "chmod -R 777 /",
        "chown -R",
    ]
    
    # Allowed service operations
    ALLOWED_SERVICE_OPS = ["status", "start", "stop", "restart", "enable", "disable"]
    
    def __init__(self, bot: "KingdomBot") -> None:
        self.bot = bot
        self._command_timeout = bot.config.get("control.command_timeout", 30)
        self._max_output_length = bot.config.get("control.max_output_length", 1900)
    
    def _check_admin(self, interaction: discord.Interaction) -> bool:
        """Check if user has admin permissions."""
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
        
        # Check server administrator permission
        if interaction.guild:
            member = interaction.guild.get_member(interaction.user.id)
            if member and member.guild_permissions.administrator:
                return True
        
        return False
    
    def _is_command_safe(self, command: str) -> tuple[bool, Optional[str]]:
        """
        Check if a command is safe to execute.
        
        Returns:
            Tuple of (is_safe, reason_if_blocked)
        """
        command_lower = command.lower().strip()
        
        # Check against blocked commands
        for blocked in self.BLOCKED_COMMANDS:
            if blocked in command_lower:
                return False, f"Command contains blocked pattern: {blocked}"
        
        # Check for dangerous patterns
        dangerous_patterns = [
            ("rm -rf", "Recursive force delete"),
            ("> /dev/", "Direct device write"),
            ("| sh", "Piped shell execution"),
            ("| bash", "Piped bash execution"),
            ("curl | ", "Piped curl execution"),
            ("wget | ", "Piped wget execution"),
            ("eval ", "Eval execution"),
            ("exec ", "Exec execution"),
        ]
        
        for pattern, reason in dangerous_patterns:
            if pattern in command_lower:
                return False, f"Potentially dangerous: {reason}"
        
        return True, None
    
    async def _execute_command(
        self,
        command: str,
        timeout: Optional[float] = None,
        cwd: Optional[str] = None
    ) -> tuple[int, str, str]:
        """
        Execute a shell command.
        
        Args:
            command: Command to execute
            timeout: Command timeout in seconds
            cwd: Working directory
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        timeout = timeout or self._command_timeout
        
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout
            )
            
            return proc.returncode or 0, stdout.decode(), stderr.decode()
            
        except asyncio.TimeoutError:
            # Try to kill the process
            try:
                proc.kill()
                await proc.wait()
            except Exception:
                pass
            return -1, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return -1, "", str(e)
    
    def _truncate_output(self, output: str, max_length: Optional[int] = None) -> str:
        """Truncate output to fit Discord message limits."""
        max_length = max_length or self._max_output_length
        
        if len(output) <= max_length:
            return output
        
        truncated = output[:max_length - 50]
        return f"{truncated}\n\n... (truncated, {len(output) - max_length + 50} chars omitted)"
    
    @app_commands.command(name="exec", description="Execute a shell command")
    @app_commands.describe(
        command="Shell command to execute",
        timeout="Command timeout in seconds (default: 30)"
    )
    async def exec_command(
        self,
        interaction: discord.Interaction,
        command: str,
        timeout: Optional[int] = None
    ) -> None:
        """Execute a shell command on the server."""
        if not self._check_admin(interaction):
            await interaction.response.send_message(
                "❌ You don't have permission to execute commands.",
                ephemeral=True
            )
            return
        
        # Safety check
        is_safe, reason = self._is_command_safe(command)
        if not is_safe:
            await interaction.response.send_message(
                f"❌ Command blocked: {reason}",
                ephemeral=True
            )
            self.bot.logger.warning(
                f"Blocked command from {interaction.user}: {command} - {reason}"
            )
            return
        
        await interaction.response.defer()
        
        self.bot.logger.info(f"Executing command from {interaction.user}: {command}")
        
        try:
            returncode, stdout, stderr = await self._execute_command(
                command,
                timeout=timeout
            )
            
            # Build response embed
            if returncode == 0:
                color = discord.Color.green()
                status = "✅ Success"
            else:
                color = discord.Color.red()
                status = f"❌ Failed (exit code: {returncode})"
            
            embed = discord.Embed(
                title="🖥️ Command Execution",
                color=color
            )
            
            embed.add_field(
                name="Command",
                value=f"```{command[:100]}{'...' if len(command) > 100 else ''}```",
                inline=False
            )
            
            embed.add_field(
                name="Status",
                value=status,
                inline=True
            )
            
            embed.add_field(
                name="Server",
                value=self.bot.bot_id.upper(),
                inline=True
            )
            
            # Add stdout if present
            if stdout.strip():
                truncated_stdout = self._truncate_output(stdout.strip())
                embed.add_field(
                    name="Output",
                    value=f"```\n{truncated_stdout}\n```",
                    inline=False
                )
            
            # Add stderr if present
            if stderr.strip():
                truncated_stderr = self._truncate_output(stderr.strip(), 500)
                embed.add_field(
                    name="Errors",
                    value=f"```\n{truncated_stderr}\n```",
                    inline=False
                )
            
            embed.set_footer(text=f"Executed by {interaction.user}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self.bot.logger.error(f"Error executing command: {e}", exc_info=True)
            await interaction.followup.send(
                f"❌ Error executing command: {e}",
                ephemeral=True
            )
    
    @app_commands.command(name="service", description="Manage systemd services")
    @app_commands.describe(
        name="Service name",
        action="Action to perform"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="status", value="status"),
        app_commands.Choice(name="start", value="start"),
        app_commands.Choice(name="stop", value="stop"),
        app_commands.Choice(name="restart", value="restart"),
        app_commands.Choice(name="enable", value="enable"),
        app_commands.Choice(name="disable", value="disable"),
    ])
    async def service_command(
        self,
        interaction: discord.Interaction,
        name: str,
        action: str
    ) -> None:
        """Manage systemd services."""
        if not self._check_admin(interaction):
            await interaction.response.send_message(
                "❌ You don't have permission to manage services.",
                ephemeral=True
            )
            return
        
        # Validate action
        if action not in self.ALLOWED_SERVICE_OPS:
            await interaction.response.send_message(
                f"❌ Invalid action. Allowed: {', '.join(self.ALLOWED_SERVICE_OPS)}",
                ephemeral=True
            )
            return
        
        # Sanitize service name
        safe_name = shlex.quote(name)
        
        await interaction.response.defer()
        
        self.bot.logger.info(
            f"Service {action} '{name}' requested by {interaction.user}"
        )
        
        try:
            # Build command based on action
            if action == "status":
                command = f"systemctl status {safe_name} --no-pager"
            else:
                command = f"sudo systemctl {action} {safe_name}"
            
            returncode, stdout, stderr = await self._execute_command(command)
            
            # Determine status
            if action == "status":
                # For status, check if service is active
                if "Active: active" in stdout:
                    color = discord.Color.green()
                    status_emoji = "🟢"
                elif "Active: inactive" in stdout:
                    color = discord.Color.yellow()
                    status_emoji = "🟡"
                else:
                    color = discord.Color.red()
                    status_emoji = "🔴"
            else:
                if returncode == 0:
                    color = discord.Color.green()
                    status_emoji = "✅"
                else:
                    color = discord.Color.red()
                    status_emoji = "❌"
            
            embed = discord.Embed(
                title=f"{status_emoji} Service: {name}",
                color=color
            )
            
            embed.add_field(
                name="Action",
                value=action.upper(),
                inline=True
            )
            
            embed.add_field(
                name="Server",
                value=self.bot.bot_id.upper(),
                inline=True
            )
            
            # Add output
            output = stdout.strip() or stderr.strip() or "No output"
            truncated_output = self._truncate_output(output)
            embed.add_field(
                name="Output",
                value=f"```\n{truncated_output}\n```",
                inline=False
            )
            
            embed.set_footer(text=f"Requested by {interaction.user}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self.bot.logger.error(f"Error managing service: {e}", exc_info=True)
            await interaction.followup.send(
                f"❌ Error managing service: {e}",
                ephemeral=True
            )
    
    @app_commands.command(name="reboot", description="Reboot the server")
    @app_commands.describe(
        delay="Delay in minutes before reboot (default: 0)",
        message="Broadcast message before reboot"
    )
    async def reboot_command(
        self,
        interaction: discord.Interaction,
        delay: int = 0,
        message: Optional[str] = None
    ) -> None:
        """Reboot the server."""
        if not self._check_admin(interaction):
            await interaction.response.send_message(
                "❌ You don't have permission to reboot the server.",
                ephemeral=True
            )
            return
        
        # Confirmation view
        class ConfirmReboot(discord.ui.View):
            def __init__(self, cog: "ControlCog"):
                super().__init__(timeout=60)
                self.cog = cog
                self.confirmed = False
            
            @discord.ui.button(label="Confirm Reboot", style=discord.ButtonStyle.danger)
            async def confirm(
                self,
                button_interaction: discord.Interaction,
                button: discord.ui.Button
            ):
                if button_interaction.user.id != interaction.user.id:
                    await button_interaction.response.send_message(
                        "❌ Only the command initiator can confirm.",
                        ephemeral=True
                    )
                    return
                
                self.confirmed = True
                self.stop()
                
                await button_interaction.response.edit_message(
                    content="🔄 Initiating reboot...",
                    view=None
                )
                
                # Execute reboot
                if delay > 0:
                    cmd = f"sudo shutdown -r +{delay}"
                    if message:
                        cmd += f' "{message}"'
                else:
                    cmd = "sudo shutdown -r now"
                
                self.cog.bot.logger.warning(
                    f"Reboot initiated by {interaction.user} with delay {delay}m"
                )
                
                returncode, stdout, stderr = await self.cog._execute_command(cmd)
                
                if returncode == 0:
                    await button_interaction.followup.send(
                        f"✅ Reboot scheduled. Server {self.cog.bot.bot_id.upper()} "
                        f"will reboot in {delay} minute(s)."
                    )
                else:
                    await button_interaction.followup.send(
                        f"❌ Failed to schedule reboot: {stderr or stdout}"
                    )
            
            @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
            async def cancel(
                self,
                button_interaction: discord.Interaction,
                button: discord.ui.Button
            ):
                if button_interaction.user.id != interaction.user.id:
                    await button_interaction.response.send_message(
                        "❌ Only the command initiator can cancel.",
                        ephemeral=True
                    )
                    return
                
                self.stop()
                await button_interaction.response.edit_message(
                    content="❌ Reboot cancelled.",
                    view=None
                )
        
        view = ConfirmReboot(self)
        
        warning_msg = (
            f"⚠️ **Reboot Confirmation Required**\n\n"
            f"Server: **{self.bot.bot_id.upper()}**\n"
            f"Delay: **{delay} minute(s)**\n"
        )
        if message:
            warning_msg += f"Message: {message}\n"
        warning_msg += "\nAre you sure you want to reboot this server?"
        
        await interaction.response.send_message(warning_msg, view=view)
    
    @app_commands.command(name="shutdown", description="Shutdown the server")
    @app_commands.describe(
        delay="Delay in minutes before shutdown (default: 0)",
        message="Broadcast message before shutdown"
    )
    async def shutdown_command(
        self,
        interaction: discord.Interaction,
        delay: int = 0,
        message: Optional[str] = None
    ) -> None:
        """Shutdown the server."""
        if not self._check_admin(interaction):
            await interaction.response.send_message(
                "❌ You don't have permission to shutdown the server.",
                ephemeral=True
            )
            return
        
        # Confirmation view
        class ConfirmShutdown(discord.ui.View):
            def __init__(self, cog: "ControlCog"):
                super().__init__(timeout=60)
                self.cog = cog
            
            @discord.ui.button(label="Confirm Shutdown", style=discord.ButtonStyle.danger)
            async def confirm(
                self,
                button_interaction: discord.Interaction,
                button: discord.ui.Button
            ):
                if button_interaction.user.id != interaction.user.id:
                    await button_interaction.response.send_message(
                        "❌ Only the command initiator can confirm.",
                        ephemeral=True
                    )
                    return
                
                self.stop()
                
                await button_interaction.response.edit_message(
                    content="🔌 Initiating shutdown...",
                    view=None
                )
                
                # Execute shutdown
                if delay > 0:
                    cmd = f"sudo shutdown +{delay}"
                    if message:
                        cmd += f' "{message}"'
                else:
                    cmd = "sudo shutdown now"
                
                self.cog.bot.logger.warning(
                    f"Shutdown initiated by {interaction.user} with delay {delay}m"
                )
                
                returncode, stdout, stderr = await self.cog._execute_command(cmd)
                
                if returncode == 0:
                    await button_interaction.followup.send(
                        f"✅ Shutdown scheduled. Server {self.cog.bot.bot_id.upper()} "
                        f"will shutdown in {delay} minute(s)."
                    )
                else:
                    await button_interaction.followup.send(
                        f"❌ Failed to schedule shutdown: {stderr or stdout}"
                    )
            
            @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
            async def cancel(
                self,
                button_interaction: discord.Interaction,
                button: discord.ui.Button
            ):
                if button_interaction.user.id != interaction.user.id:
                    await button_interaction.response.send_message(
                        "❌ Only the command initiator can cancel.",
                        ephemeral=True
                    )
                    return
                
                self.stop()
                await button_interaction.response.edit_message(
                    content="❌ Shutdown cancelled.",
                    view=None
                )
        
        view = ConfirmShutdown(self)
        
        warning_msg = (
            f"⚠️ **Shutdown Confirmation Required**\n\n"
            f"Server: **{self.bot.bot_id.upper()}**\n"
            f"Delay: **{delay} minute(s)**\n"
        )
        if message:
            warning_msg += f"Message: {message}\n"
        warning_msg += "\n**WARNING:** This will power off the server!"
        
        await interaction.response.send_message(warning_msg, view=view)
    
    @app_commands.command(name="cancel-shutdown", description="Cancel a scheduled shutdown/reboot")
    async def cancel_shutdown_command(self, interaction: discord.Interaction) -> None:
        """Cancel a scheduled shutdown or reboot."""
        if not self._check_admin(interaction):
            await interaction.response.send_message(
                "❌ You don't have permission to cancel shutdowns.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            returncode, stdout, stderr = await self._execute_command(
                "sudo shutdown -c"
            )
            
            if returncode == 0:
                await interaction.followup.send(
                    f"✅ Scheduled shutdown/reboot cancelled on {self.bot.bot_id.upper()}"
                )
            else:
                await interaction.followup.send(
                    f"❌ Failed to cancel: {stderr or 'No scheduled shutdown'}"
                )
                
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}")


async def setup(bot: "KingdomBot") -> None:
    """Setup function for loading the cog."""
    await bot.add_cog(ControlCog(bot))
