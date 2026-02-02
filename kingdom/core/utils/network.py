"""
Network Utilities
=================

Tailscale and network utilities for Kingdom bots.
Provides network status, connectivity checks, and Tailscale management.
"""

import asyncio
import json
import socket
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

import psutil


@dataclass
class NetworkInterface:
    """Network interface information."""
    
    name: str
    addresses: list[dict[str, Any]]
    is_up: bool
    speed: Optional[int]
    mtu: int
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "addresses": self.addresses,
            "is_up": self.is_up,
            "speed_mbps": self.speed,
            "mtu": self.mtu,
        }


@dataclass
class TailscaleStatus:
    """Tailscale status information."""
    
    is_running: bool
    is_connected: bool
    tailscale_ip: Optional[str]
    hostname: Optional[str]
    dns_name: Optional[str]
    tailnet: Optional[str]
    version: Optional[str]
    backend_state: Optional[str]
    peers: list[dict[str, Any]]
    exit_node: Optional[str]
    exit_node_ip: Optional[str]
    timestamp: datetime
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_running": self.is_running,
            "is_connected": self.is_connected,
            "tailscale_ip": self.tailscale_ip,
            "hostname": self.hostname,
            "dns_name": self.dns_name,
            "tailnet": self.tailnet,
            "version": self.version,
            "backend_state": self.backend_state,
            "peers_count": len(self.peers),
            "peers": self.peers,
            "exit_node": self.exit_node,
            "exit_node_ip": self.exit_node_ip,
            "timestamp": self.timestamp.isoformat(),
        }
    
    def format_summary(self) -> str:
        """Format a human-readable summary."""
        status_emoji = "🟢" if self.is_connected else "🔴"
        
        summary = f"""**Tailscale Status** {status_emoji}
State: {self.backend_state or 'Unknown'}
IP: {self.tailscale_ip or 'N/A'}
Hostname: {self.hostname or 'N/A'}
DNS: {self.dns_name or 'N/A'}
Tailnet: {self.tailnet or 'N/A'}
Version: {self.version or 'N/A'}
Peers: {len(self.peers)} connected"""
        
        if self.exit_node:
            summary += f"\nExit Node: {self.exit_node}"
        
        return summary


class NetworkUtils:
    """
    Network utility functions.
    
    Provides methods for network status, connectivity checks,
    and interface information.
    """
    
    @staticmethod
    def get_interfaces() -> list[NetworkInterface]:
        """
        Get all network interfaces.
        
        Returns:
            List of NetworkInterface objects
        """
        interfaces = []
        
        # Get interface addresses
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        
        for name, addr_list in addrs.items():
            addresses = []
            for addr in addr_list:
                addresses.append({
                    "family": str(addr.family.name),
                    "address": addr.address,
                    "netmask": addr.netmask,
                    "broadcast": addr.broadcast,
                })
            
            stat = stats.get(name)
            interfaces.append(NetworkInterface(
                name=name,
                addresses=addresses,
                is_up=stat.isup if stat else False,
                speed=stat.speed if stat else None,
                mtu=stat.mtu if stat else 0,
            ))
        
        return interfaces
    
    @staticmethod
    def get_connections(kind: str = "inet") -> list[dict[str, Any]]:
        """
        Get network connections.
        
        Args:
            kind: Connection type (inet, inet4, inet6, tcp, udp, etc.)
            
        Returns:
            List of connection dictionaries
        """
        connections = []
        
        for conn in psutil.net_connections(kind=kind):
            connections.append({
                "fd": conn.fd,
                "family": str(conn.family.name),
                "type": str(conn.type.name),
                "local_addr": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                "remote_addr": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                "status": conn.status,
                "pid": conn.pid,
            })
        
        return connections
    
    @staticmethod
    async def check_connectivity(
        host: str = "8.8.8.8",
        port: int = 53,
        timeout: float = 3.0
    ) -> bool:
        """
        Check network connectivity.
        
        Args:
            host: Host to connect to
            port: Port to connect to
            timeout: Connection timeout in seconds
            
        Returns:
            True if connection successful
        """
        try:
            loop = asyncio.get_event_loop()
            
            def _check():
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                try:
                    sock.connect((host, port))
                    return True
                except (socket.timeout, socket.error):
                    return False
                finally:
                    sock.close()
            
            return await loop.run_in_executor(None, _check)
        except Exception:
            return False
    
    @staticmethod
    async def ping(host: str, count: int = 3, timeout: float = 5.0) -> dict[str, Any]:
        """
        Ping a host.
        
        Args:
            host: Host to ping
            count: Number of ping packets
            timeout: Timeout in seconds
            
        Returns:
            Ping results dictionary
        """
        try:
            # Use system ping command
            cmd = ["ping", "-c", str(count), "-W", str(int(timeout)), host]
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout * count + 5
            )
            
            output = stdout.decode()
            
            # Parse ping output
            result = {
                "host": host,
                "success": proc.returncode == 0,
                "packets_sent": count,
                "packets_received": 0,
                "packet_loss": 100.0,
                "rtt_min": None,
                "rtt_avg": None,
                "rtt_max": None,
                "raw_output": output,
            }
            
            # Try to parse statistics
            for line in output.split("\n"):
                if "packets transmitted" in line:
                    parts = line.split(",")
                    for part in parts:
                        if "received" in part:
                            try:
                                result["packets_received"] = int(part.strip().split()[0])
                            except (ValueError, IndexError):
                                pass
                        if "packet loss" in part:
                            try:
                                result["packet_loss"] = float(part.strip().split("%")[0].split()[-1])
                            except (ValueError, IndexError):
                                pass
                
                if "rtt" in line.lower() or "round-trip" in line.lower():
                    try:
                        # Format: rtt min/avg/max/mdev = 1.234/2.345/3.456/0.123 ms
                        stats = line.split("=")[1].strip().split()[0].split("/")
                        result["rtt_min"] = float(stats[0])
                        result["rtt_avg"] = float(stats[1])
                        result["rtt_max"] = float(stats[2])
                    except (ValueError, IndexError):
                        pass
            
            return result
            
        except asyncio.TimeoutError:
            return {
                "host": host,
                "success": False,
                "error": "Timeout",
            }
        except Exception as e:
            return {
                "host": host,
                "success": False,
                "error": str(e),
            }
    
    @staticmethod
    def get_public_ip() -> Optional[str]:
        """
        Get the public IP address.
        
        Returns:
            Public IP address or None
        """
        try:
            # Try to get from a socket connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(("8.8.8.8", 80))
            ip = sock.getsockname()[0]
            sock.close()
            return ip
        except Exception:
            return None


class TailscaleClient:
    """
    Tailscale CLI client wrapper.
    
    Provides methods to interact with Tailscale via the CLI.
    """
    
    def __init__(self, tailscale_path: str = "tailscale") -> None:
        """
        Initialize the Tailscale client.
        
        Args:
            tailscale_path: Path to tailscale binary
        """
        self.tailscale_path = tailscale_path
    
    async def _run_command(
        self,
        *args: str,
        timeout: float = 30.0
    ) -> tuple[int, str, str]:
        """
        Run a tailscale command.
        
        Args:
            *args: Command arguments
            timeout: Command timeout
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        cmd = [self.tailscale_path] + list(args)
        
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout
            )
            
            return proc.returncode or 0, stdout.decode(), stderr.decode()
            
        except asyncio.TimeoutError:
            return -1, "", "Command timed out"
        except FileNotFoundError:
            return -1, "", f"Tailscale not found at {self.tailscale_path}"
        except Exception as e:
            return -1, "", str(e)
    
    async def get_status(self) -> TailscaleStatus:
        """
        Get Tailscale status.
        
        Returns:
            TailscaleStatus object
        """
        now = datetime.now(timezone.utc)
        
        # Get JSON status
        returncode, stdout, stderr = await self._run_command("status", "--json")
        
        if returncode != 0:
            return TailscaleStatus(
                is_running=False,
                is_connected=False,
                tailscale_ip=None,
                hostname=None,
                dns_name=None,
                tailnet=None,
                version=None,
                backend_state=None,
                peers=[],
                exit_node=None,
                exit_node_ip=None,
                timestamp=now,
            )
        
        try:
            data = json.loads(stdout)
        except json.JSONDecodeError:
            return TailscaleStatus(
                is_running=True,
                is_connected=False,
                tailscale_ip=None,
                hostname=None,
                dns_name=None,
                tailnet=None,
                version=None,
                backend_state="Unknown",
                peers=[],
                exit_node=None,
                exit_node_ip=None,
                timestamp=now,
            )
        
        # Parse self info
        self_info = data.get("Self", {})
        tailscale_ips = self_info.get("TailscaleIPs", [])
        
        # Parse peers
        peers = []
        peer_data = data.get("Peer", {})
        for peer_id, peer_info in peer_data.items():
            peers.append({
                "id": peer_id,
                "hostname": peer_info.get("HostName"),
                "dns_name": peer_info.get("DNSName"),
                "tailscale_ips": peer_info.get("TailscaleIPs", []),
                "online": peer_info.get("Online", False),
                "os": peer_info.get("OS"),
                "relay": peer_info.get("Relay"),
                "exit_node": peer_info.get("ExitNode", False),
            })
        
        # Find exit node
        exit_node = None
        exit_node_ip = None
        for peer in peers:
            if peer.get("exit_node"):
                exit_node = peer.get("hostname")
                ips = peer.get("tailscale_ips", [])
                exit_node_ip = ips[0] if ips else None
                break
        
        return TailscaleStatus(
            is_running=True,
            is_connected=data.get("BackendState") == "Running",
            tailscale_ip=tailscale_ips[0] if tailscale_ips else None,
            hostname=self_info.get("HostName"),
            dns_name=self_info.get("DNSName"),
            tailnet=data.get("CurrentTailnet", {}).get("Name"),
            version=data.get("Version"),
            backend_state=data.get("BackendState"),
            peers=peers,
            exit_node=exit_node,
            exit_node_ip=exit_node_ip,
            timestamp=now,
        )
    
    async def get_ip(self) -> Optional[str]:
        """
        Get the Tailscale IP address.
        
        Returns:
            Tailscale IP or None
        """
        returncode, stdout, stderr = await self._run_command("ip")
        
        if returncode == 0 and stdout.strip():
            # May return multiple IPs, get the first IPv4
            for ip in stdout.strip().split("\n"):
                ip = ip.strip()
                if ip and ":" not in ip:  # Skip IPv6
                    return ip
            return stdout.strip().split("\n")[0].strip()
        
        return None
    
    async def ping_peer(
        self,
        target: str,
        count: int = 3,
        timeout: float = 10.0
    ) -> dict[str, Any]:
        """
        Ping a Tailscale peer.
        
        Args:
            target: Peer hostname or IP
            count: Number of pings
            timeout: Timeout in seconds
            
        Returns:
            Ping results
        """
        returncode, stdout, stderr = await self._run_command(
            "ping",
            "--c", str(count),
            "--timeout", f"{timeout}s",
            target,
            timeout=timeout + 5
        )
        
        return {
            "target": target,
            "success": returncode == 0,
            "output": stdout,
            "error": stderr if returncode != 0 else None,
        }
    
    async def up(self, **kwargs: Any) -> tuple[bool, str]:
        """
        Bring Tailscale up.
        
        Args:
            **kwargs: Additional arguments (authkey, hostname, etc.)
            
        Returns:
            Tuple of (success, message)
        """
        args = ["up"]
        
        for key, value in kwargs.items():
            if value is True:
                args.append(f"--{key}")
            elif value is not False and value is not None:
                args.append(f"--{key}={value}")
        
        returncode, stdout, stderr = await self._run_command(*args, timeout=60.0)
        
        if returncode == 0:
            return True, stdout or "Tailscale is up"
        return False, stderr or "Failed to bring Tailscale up"
    
    async def down(self) -> tuple[bool, str]:
        """
        Bring Tailscale down.
        
        Returns:
            Tuple of (success, message)
        """
        returncode, stdout, stderr = await self._run_command("down")
        
        if returncode == 0:
            return True, "Tailscale is down"
        return False, stderr or "Failed to bring Tailscale down"
    
    async def set_exit_node(self, node: Optional[str] = None) -> tuple[bool, str]:
        """
        Set or clear the exit node.
        
        Args:
            node: Exit node hostname/IP, or None to clear
            
        Returns:
            Tuple of (success, message)
        """
        if node:
            args = ["set", f"--exit-node={node}"]
        else:
            args = ["set", "--exit-node="]
        
        returncode, stdout, stderr = await self._run_command(*args)
        
        if returncode == 0:
            if node:
                return True, f"Exit node set to {node}"
            return True, "Exit node cleared"
        return False, stderr or "Failed to set exit node"
    
    async def get_version(self) -> Optional[str]:
        """
        Get Tailscale version.
        
        Returns:
            Version string or None
        """
        returncode, stdout, stderr = await self._run_command("version")
        
        if returncode == 0:
            return stdout.strip().split("\n")[0]
        return None
