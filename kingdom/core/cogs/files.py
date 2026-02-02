"""
Files Cog
=========

Discord slash commands for file system operations.
Provides /ls, /cat, /tail, /logs commands.
"""

import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import discord
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from ..bot_base import KingdomBot


class FilesCog(commands.Cog, name="Files"):
    """File system browsing and log viewing commands."""
    
    # Directories that are always blocked
    BLOCKED_PATHS = [
        "/etc/shadow",
        "/etc/passwd",
        "/etc/sudoers",
        "/root/.ssh",
        "/home/*/.ssh",
    ]
    
    # Default allowed directories (can be overridden in config)
    DEFAULT_ALLOWED_DIRS = [
        "/var/log",
        "/tmp",
        "/home",
        "/opt",
    ]
    
    def __init__(self, bot: "KingdomBot") -> None:
        self.bot = bot
        self._max_file_size = bot.config.get("files.max_file_size", 50000)  # 50KB
        self._max_lines = bot.config.get("files.max_lines", 100)
        self._allowed_dirs = bot.config.get("files.allowed_dirs", self.DEFAULT_ALLOWED_DIRS)
    
    def _check_permissions(self, interaction: discord.Interaction) -> bool:
        """Check if user has permission to use file commands."""
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
    
    def _is_path_allowed(self, path: str) -> tuple[bool, Optional[str]]:
        """
        Check if a path is allowed to be accessed.
        
        Returns:
            Tuple of (is_allowed, reason_if_blocked)
        """
        # Resolve the path to handle .. and symlinks
        try:
            resolved = Path(path).resolve()
            resolved_str = str(resolved)
        except Exception as e:
            return False, f"Invalid path: {e}"
        
        # Check blocked paths
        for blocked in self.BLOCKED_PATHS:
            if "*" in blocked:
                # Simple glob matching
                pattern = blocked.replace("*", "")
                if pattern in resolved_str:
                    return False, "Access to this path is blocked"
            elif resolved_str.startswith(blocked) or resolved_str == blocked:
                return False, "Access to this path is blocked"
        
        # Check if path is in allowed directories
        for allowed in self._allowed_dirs:
            if resolved_str.startswith(allowed):
                return True, None
        
        # Also allow current working directory
        cwd = os.getcwd()
        if resolved_str.startswith(cwd):
            return True, None
        
        return False, f"Path not in allowed directories: {', '.join(self._allowed_dirs)}"
    
    def _format_size(self, size: int) -> str:
        """Format file size to human-readable string."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    def _format_permissions(self, mode: int) -> str:
        """Format file permissions to rwx string."""
        perms = ""
        for who in range(2, -1, -1):
            for what, char in enumerate(["r", "w", "x"]):
                if mode & (1 << (who * 3 + (2 - what))):
                    perms += char
                else:
                    perms += "-"
        return perms
    
    @app_commands.command(name="ls", description="List directory contents")
    @app_commands.describe(
        path="Directory path to list",
        all_files="Show hidden files",
        long_format="Show detailed information"
    )
    async def ls_command(
        self,
        interaction: discord.Interaction,
        path: str = ".",
        all_files: bool = False,
        long_format: bool = False
    ) -> None:
        """List directory contents."""
        if not self._check_permissions(interaction):
            await interaction.response.send_message(
                "❌ You don't have permission to browse files.",
                ephemeral=True
            )
            return
        
        # Check path access
        is_allowed, reason = self._is_path_allowed(path)
        if not is_allowed:
            await interaction.response.send_message(
                f"❌ {reason}",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            dir_path = Path(path).resolve()
            
            if not dir_path.exists():
                await interaction.followup.send(f"❌ Path not found: {path}")
                return
            
            if not dir_path.is_dir():
                await interaction.followup.send(f"❌ Not a directory: {path}")
                return
            
            # List directory contents
            entries = []
            for entry in sorted(dir_path.iterdir()):
                # Skip hidden files unless requested
                if not all_files and entry.name.startswith("."):
                    continue
                
                try:
                    stat = entry.stat()
                    
                    if long_format:
                        # Format: drwxr-xr-x  4096  2024-01-01 12:00  filename
                        is_dir = "d" if entry.is_dir() else "-"
                        perms = self._format_permissions(stat.st_mode)
                        size = self._format_size(stat.st_size)
                        mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                        
                        entries.append(
                            f"`{is_dir}{perms}` {size:>8} {mtime} {entry.name}"
                        )
                    else:
                        # Simple format
                        suffix = "/" if entry.is_dir() else ""
                        entries.append(f"`{entry.name}{suffix}`")
                        
                except PermissionError:
                    entries.append(f"`{entry.name}` (permission denied)")
                except Exception:
                    entries.append(f"`{entry.name}` (error)")
            
            if not entries:
                await interaction.followup.send(f"📁 Directory is empty: `{dir_path}`")
                return
            
            # Build embed
            embed = discord.Embed(
                title=f"📁 {dir_path}",
                color=discord.Color.blue()
            )
            
            # Split entries into chunks to fit Discord limits
            content = "\n".join(entries)
            if len(content) > 4000:
                content = "\n".join(entries[:50])
                content += f"\n\n... and {len(entries) - 50} more items"
            
            embed.description = content
            embed.set_footer(
                text=f"Server: {self.bot.bot_id.upper()} | {len(entries)} items"
            )
            
            await interaction.followup.send(embed=embed)
            
        except PermissionError:
            await interaction.followup.send(f"❌ Permission denied: {path}")
        except Exception as e:
            self.bot.logger.error(f"Error in ls command: {e}", exc_info=True)
            await interaction.followup.send(f"❌ Error: {e}")
    
    @app_commands.command(name="cat", description="Display file contents")
    @app_commands.describe(
        path="File path to display",
        lines="Number of lines to show (default: all, max: 100)"
    )
    async def cat_command(
        self,
        interaction: discord.Interaction,
        path: str,
        lines: Optional[int] = None
    ) -> None:
        """Display file contents."""
        if not self._check_permissions(interaction):
            await interaction.response.send_message(
                "❌ You don't have permission to read files.",
                ephemeral=True
            )
            return
        
        # Check path access
        is_allowed, reason = self._is_path_allowed(path)
        if not is_allowed:
            await interaction.response.send_message(
                f"❌ {reason}",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            file_path = Path(path).resolve()
            
            if not file_path.exists():
                await interaction.followup.send(f"❌ File not found: {path}")
                return
            
            if not file_path.is_file():
                await interaction.followup.send(f"❌ Not a file: {path}")
                return
            
            # Check file size
            file_size = file_path.stat().st_size
            if file_size > self._max_file_size:
                await interaction.followup.send(
                    f"❌ File too large ({self._format_size(file_size)}). "
                    f"Max: {self._format_size(self._max_file_size)}. Use /tail instead."
                )
                return
            
            # Read file
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
            except UnicodeDecodeError:
                await interaction.followup.send("❌ Cannot read binary file")
                return
            
            # Limit lines if specified
            if lines:
                content_lines = content.split("\n")
                lines = min(lines, self._max_lines)
                content = "\n".join(content_lines[:lines])
                if len(content_lines) > lines:
                    content += f"\n\n... ({len(content_lines) - lines} more lines)"
            
            # Truncate if too long for Discord
            if len(content) > 1900:
                content = content[:1900] + "\n\n... (truncated)"
            
            # Detect file type for syntax highlighting
            suffix = file_path.suffix.lower()
            lang_map = {
                ".py": "python",
                ".js": "javascript",
                ".ts": "typescript",
                ".json": "json",
                ".yaml": "yaml",
                ".yml": "yaml",
                ".sh": "bash",
                ".bash": "bash",
                ".conf": "ini",
                ".ini": "ini",
                ".toml": "toml",
                ".md": "markdown",
                ".sql": "sql",
                ".xml": "xml",
                ".html": "html",
                ".css": "css",
            }
            lang = lang_map.get(suffix, "")
            
            embed = discord.Embed(
                title=f"📄 {file_path.name}",
                color=discord.Color.blue()
            )
            
            embed.description = f"```{lang}\n{content}\n```"
            embed.set_footer(
                text=f"Server: {self.bot.bot_id.upper()} | Size: {self._format_size(file_size)}"
            )
            
            await interaction.followup.send(embed=embed)
            
        except PermissionError:
            await interaction.followup.send(f"❌ Permission denied: {path}")
        except Exception as e:
            self.bot.logger.error(f"Error in cat command: {e}", exc_info=True)
            await interaction.followup.send(f"❌ Error: {e}")
    
    @app_commands.command(name="tail", description="Display last lines of a file")
    @app_commands.describe(
        path="File path to tail",
        lines="Number of lines to show (default: 20, max: 100)",
        follow="Follow file for new content (10 second timeout)"
    )
    async def tail_command(
        self,
        interaction: discord.Interaction,
        path: str,
        lines: int = 20,
        follow: bool = False
    ) -> None:
        """Display last lines of a file."""
        if not self._check_permissions(interaction):
            await interaction.response.send_message(
                "❌ You don't have permission to read files.",
                ephemeral=True
            )
            return
        
        # Check path access
        is_allowed, reason = self._is_path_allowed(path)
        if not is_allowed:
            await interaction.response.send_message(
                f"❌ {reason}",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            file_path = Path(path).resolve()
            
            if not file_path.exists():
                await interaction.followup.send(f"❌ File not found: {path}")
                return
            
            if not file_path.is_file():
                await interaction.followup.send(f"❌ Not a file: {path}")
                return
            
            # Limit lines
            lines = min(max(1, lines), self._max_lines)
            
            if follow:
                # Use tail -f with timeout
                cmd = f"timeout 10 tail -n {lines} -f {file_path}"
            else:
                cmd = f"tail -n {lines} {file_path}"
            
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=15 if follow else 10
            )
            
            content = stdout.decode(errors="replace")
            
            if not content.strip():
                content = "(empty)"
            
            # Truncate if too long
            if len(content) > 1900:
                content = content[-1900:]
                content = "...(truncated)\n" + content
            
            embed = discord.Embed(
                title=f"📜 tail: {file_path.name}",
                color=discord.Color.blue()
            )
            
            embed.description = f"```\n{content}\n```"
            embed.set_footer(
                text=f"Server: {self.bot.bot_id.upper()} | Last {lines} lines"
            )
            
            await interaction.followup.send(embed=embed)
            
        except asyncio.TimeoutError:
            await interaction.followup.send("❌ Command timed out")
        except PermissionError:
            await interaction.followup.send(f"❌ Permission denied: {path}")
        except Exception as e:
            self.bot.logger.error(f"Error in tail command: {e}", exc_info=True)
            await interaction.followup.send(f"❌ Error: {e}")
    
    @app_commands.command(name="logs", description="View system or service logs")
    @app_commands.describe(
        service="Service name (or 'system' for syslog)",
        lines="Number of lines to show (default: 50)",
        since="Time filter (e.g., '1h', '30m', '1d')"
    )
    async def logs_command(
        self,
        interaction: discord.Interaction,
        service: str = "system",
        lines: int = 50,
        since: Optional[str] = None
    ) -> None:
        """View system or service logs."""
        if not self._check_permissions(interaction):
            await interaction.response.send_message(
                "❌ You don't have permission to view logs.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            # Limit lines
            lines = min(max(1, lines), self._max_lines)
            
            # Build journalctl command
            if service.lower() == "system":
                cmd = f"journalctl -n {lines} --no-pager"
            else:
                # Sanitize service name
                safe_service = "".join(c for c in service if c.isalnum() or c in "-_.")
                cmd = f"journalctl -u {safe_service} -n {lines} --no-pager"
            
            # Add time filter
            if since:
                # Validate since format
                valid_since = "".join(c for c in since if c.isalnum())
                cmd += f" --since='{valid_since} ago'"
            
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=30
            )
            
            content = stdout.decode(errors="replace")
            
            if not content.strip():
                if stderr:
                    content = f"No logs found. Error: {stderr.decode()}"
                else:
                    content = "No logs found."
            
            # Truncate if too long
            if len(content) > 1900:
                content = content[-1900:]
                content = "...(truncated)\n" + content
            
            embed = discord.Embed(
                title=f"📋 Logs: {service}",
                color=discord.Color.blue()
            )
            
            embed.description = f"```\n{content}\n```"
            
            footer_text = f"Server: {self.bot.bot_id.upper()} | Last {lines} entries"
            if since:
                footer_text += f" | Since: {since} ago"
            embed.set_footer(text=footer_text)
            
            await interaction.followup.send(embed=embed)
            
        except asyncio.TimeoutError:
            await interaction.followup.send("❌ Command timed out")
        except Exception as e:
            self.bot.logger.error(f"Error in logs command: {e}", exc_info=True)
            await interaction.followup.send(f"❌ Error: {e}")
    
    @app_commands.command(name="find", description="Search for files")
    @app_commands.describe(
        path="Directory to search in",
        name="File name pattern (supports wildcards)",
        type_filter="Filter by type: f=file, d=directory"
    )
    async def find_command(
        self,
        interaction: discord.Interaction,
        path: str,
        name: str,
        type_filter: Optional[str] = None
    ) -> None:
        """Search for files in a directory."""
        if not self._check_permissions(interaction):
            await interaction.response.send_message(
                "❌ You don't have permission to search files.",
                ephemeral=True
            )
            return
        
        # Check path access
        is_allowed, reason = self._is_path_allowed(path)
        if not is_allowed:
            await interaction.response.send_message(
                f"❌ {reason}",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            # Sanitize inputs
            safe_path = Path(path).resolve()
            safe_name = "".join(c for c in name if c.isalnum() or c in "-_.*?")
            
            # Build find command
            cmd = f"find {safe_path} -name '{safe_name}' -maxdepth 5"
            
            if type_filter:
                if type_filter.lower() in ["f", "file"]:
                    cmd += " -type f"
                elif type_filter.lower() in ["d", "dir", "directory"]:
                    cmd += " -type d"
            
            cmd += " 2>/dev/null | head -50"
            
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=30
            )
            
            results = stdout.decode().strip().split("\n")
            results = [r for r in results if r]
            
            if not results:
                await interaction.followup.send(
                    f"🔍 No files found matching `{name}` in `{path}`"
                )
                return
            
            embed = discord.Embed(
                title=f"🔍 Search Results: {name}",
                color=discord.Color.blue()
            )
            
            # Format results
            result_text = "\n".join([f"`{r}`" for r in results[:30]])
            if len(results) > 30:
                result_text += f"\n\n... and {len(results) - 30} more"
            
            embed.description = result_text
            embed.set_footer(
                text=f"Server: {self.bot.bot_id.upper()} | {len(results)} results"
            )
            
            await interaction.followup.send(embed=embed)
            
        except asyncio.TimeoutError:
            await interaction.followup.send("❌ Search timed out")
        except Exception as e:
            self.bot.logger.error(f"Error in find command: {e}", exc_info=True)
            await interaction.followup.send(f"❌ Error: {e}")


async def setup(bot: "KingdomBot") -> None:
    """Setup function for loading the cog."""
    await bot.add_cog(FilesCog(bot))
