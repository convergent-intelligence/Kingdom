"""
System Monitoring Utilities
===========================

psutil-based system monitoring for Kingdom bots.
Provides CPU, memory, disk, and process information.
"""

import os
import platform
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

import psutil


@dataclass
class SystemInfo:
    """System information snapshot."""
    
    hostname: str
    platform: str
    platform_release: str
    platform_version: str
    architecture: str
    processor: str
    python_version: str
    
    # CPU
    cpu_count_physical: int
    cpu_count_logical: int
    cpu_percent: float
    cpu_freq_current: Optional[float]
    cpu_freq_max: Optional[float]
    
    # Memory
    memory_total: int
    memory_available: int
    memory_used: int
    memory_percent: float
    
    # Swap
    swap_total: int
    swap_used: int
    swap_percent: float
    
    # Disk
    disk_total: int
    disk_used: int
    disk_free: int
    disk_percent: float
    
    # Network
    bytes_sent: int
    bytes_recv: int
    
    # System
    boot_time: datetime
    uptime_seconds: float
    
    timestamp: datetime
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "hostname": self.hostname,
            "platform": self.platform,
            "platform_release": self.platform_release,
            "platform_version": self.platform_version,
            "architecture": self.architecture,
            "processor": self.processor,
            "python_version": self.python_version,
            "cpu": {
                "count_physical": self.cpu_count_physical,
                "count_logical": self.cpu_count_logical,
                "percent": self.cpu_percent,
                "freq_current_mhz": self.cpu_freq_current,
                "freq_max_mhz": self.cpu_freq_max,
            },
            "memory": {
                "total_bytes": self.memory_total,
                "available_bytes": self.memory_available,
                "used_bytes": self.memory_used,
                "percent": self.memory_percent,
            },
            "swap": {
                "total_bytes": self.swap_total,
                "used_bytes": self.swap_used,
                "percent": self.swap_percent,
            },
            "disk": {
                "total_bytes": self.disk_total,
                "used_bytes": self.disk_used,
                "free_bytes": self.disk_free,
                "percent": self.disk_percent,
            },
            "network": {
                "bytes_sent": self.bytes_sent,
                "bytes_recv": self.bytes_recv,
            },
            "boot_time": self.boot_time.isoformat(),
            "uptime_seconds": self.uptime_seconds,
            "timestamp": self.timestamp.isoformat(),
        }
    
    def format_summary(self) -> str:
        """Format a human-readable summary."""
        return f"""**System: {self.hostname}**
Platform: {self.platform} {self.platform_release}
Architecture: {self.architecture}

**CPU**
Cores: {self.cpu_count_physical} physical / {self.cpu_count_logical} logical
Usage: {self.cpu_percent:.1f}%
Frequency: {self.cpu_freq_current:.0f} MHz

**Memory**
Total: {self._format_bytes(self.memory_total)}
Used: {self._format_bytes(self.memory_used)} ({self.memory_percent:.1f}%)
Available: {self._format_bytes(self.memory_available)}

**Disk**
Total: {self._format_bytes(self.disk_total)}
Used: {self._format_bytes(self.disk_used)} ({self.disk_percent:.1f}%)
Free: {self._format_bytes(self.disk_free)}

**Network**
Sent: {self._format_bytes(self.bytes_sent)}
Received: {self._format_bytes(self.bytes_recv)}

**Uptime**: {self._format_uptime(self.uptime_seconds)}"""
    
    @staticmethod
    def _format_bytes(bytes_val: int) -> str:
        """Format bytes to human-readable string."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_val < 1024:
                return f"{bytes_val:.2f} {unit}"
            bytes_val /= 1024
        return f"{bytes_val:.2f} PB"
    
    @staticmethod
    def _format_uptime(seconds: float) -> str:
        """Format uptime to human-readable string."""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        
        return " ".join(parts) if parts else "< 1m"


@dataclass
class ProcessInfo:
    """Process information."""
    
    pid: int
    name: str
    status: str
    cpu_percent: float
    memory_percent: float
    memory_rss: int
    memory_vms: int
    num_threads: int
    create_time: datetime
    cmdline: list[str]
    username: str
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pid": self.pid,
            "name": self.name,
            "status": self.status,
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "memory_rss_bytes": self.memory_rss,
            "memory_vms_bytes": self.memory_vms,
            "num_threads": self.num_threads,
            "create_time": self.create_time.isoformat(),
            "cmdline": self.cmdline,
            "username": self.username,
        }


class SystemMonitor:
    """
    System monitoring utility.
    
    Provides methods to collect system metrics and process information.
    """
    
    def __init__(self, disk_path: str = "/") -> None:
        """
        Initialize the system monitor.
        
        Args:
            disk_path: Path to monitor for disk usage
        """
        self.disk_path = disk_path
    
    def get_info(self) -> SystemInfo:
        """
        Get current system information.
        
        Returns:
            SystemInfo with current metrics
        """
        # CPU info
        cpu_freq = psutil.cpu_freq()
        cpu_freq_current = cpu_freq.current if cpu_freq else None
        cpu_freq_max = cpu_freq.max if cpu_freq else None
        
        # Memory info
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # Disk info
        disk = psutil.disk_usage(self.disk_path)
        
        # Network info
        net_io = psutil.net_io_counters()
        
        # Boot time
        boot_time = datetime.fromtimestamp(psutil.boot_time(), tz=timezone.utc)
        now = datetime.now(timezone.utc)
        uptime = (now - boot_time).total_seconds()
        
        return SystemInfo(
            hostname=platform.node(),
            platform=platform.system(),
            platform_release=platform.release(),
            platform_version=platform.version(),
            architecture=platform.machine(),
            processor=platform.processor(),
            python_version=platform.python_version(),
            cpu_count_physical=psutil.cpu_count(logical=False) or 0,
            cpu_count_logical=psutil.cpu_count(logical=True) or 0,
            cpu_percent=psutil.cpu_percent(interval=0.1),
            cpu_freq_current=cpu_freq_current,
            cpu_freq_max=cpu_freq_max,
            memory_total=memory.total,
            memory_available=memory.available,
            memory_used=memory.used,
            memory_percent=memory.percent,
            swap_total=swap.total,
            swap_used=swap.used,
            swap_percent=swap.percent,
            disk_total=disk.total,
            disk_used=disk.used,
            disk_free=disk.free,
            disk_percent=disk.percent,
            bytes_sent=net_io.bytes_sent,
            bytes_recv=net_io.bytes_recv,
            boot_time=boot_time,
            uptime_seconds=uptime,
            timestamp=now,
        )
    
    def get_cpu_times(self) -> dict[str, float]:
        """Get CPU time breakdown."""
        times = psutil.cpu_times()
        return {
            "user": times.user,
            "system": times.system,
            "idle": times.idle,
            "iowait": getattr(times, "iowait", 0),
        }
    
    def get_load_average(self) -> tuple[float, float, float]:
        """Get system load average (1, 5, 15 minutes)."""
        try:
            return os.getloadavg()
        except (OSError, AttributeError):
            # Windows doesn't support getloadavg
            return (0.0, 0.0, 0.0)
    
    def get_top_processes(
        self,
        n: int = 10,
        sort_by: str = "cpu"
    ) -> list[ProcessInfo]:
        """
        Get top N processes by resource usage.
        
        Args:
            n: Number of processes to return
            sort_by: Sort by "cpu" or "memory"
            
        Returns:
            List of ProcessInfo objects
        """
        processes = []
        
        for proc in psutil.process_iter([
            "pid", "name", "status", "cpu_percent", "memory_percent",
            "memory_info", "num_threads", "create_time", "cmdline", "username"
        ]):
            try:
                info = proc.info
                memory_info = info.get("memory_info")
                
                processes.append(ProcessInfo(
                    pid=info["pid"],
                    name=info["name"] or "unknown",
                    status=info["status"] or "unknown",
                    cpu_percent=info["cpu_percent"] or 0.0,
                    memory_percent=info["memory_percent"] or 0.0,
                    memory_rss=memory_info.rss if memory_info else 0,
                    memory_vms=memory_info.vms if memory_info else 0,
                    num_threads=info["num_threads"] or 0,
                    create_time=datetime.fromtimestamp(
                        info["create_time"] or 0, tz=timezone.utc
                    ),
                    cmdline=info["cmdline"] or [],
                    username=info["username"] or "unknown",
                ))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        # Sort by requested metric
        if sort_by == "memory":
            processes.sort(key=lambda p: p.memory_percent, reverse=True)
        else:
            processes.sort(key=lambda p: p.cpu_percent, reverse=True)
        
        return processes[:n]


def get_system_info(disk_path: str = "/") -> SystemInfo:
    """
    Convenience function to get system information.
    
    Args:
        disk_path: Path to monitor for disk usage
        
    Returns:
        SystemInfo with current metrics
    """
    monitor = SystemMonitor(disk_path)
    return monitor.get_info()


def get_process_info(pid: int) -> Optional[ProcessInfo]:
    """
    Get information about a specific process.
    
    Args:
        pid: Process ID
        
    Returns:
        ProcessInfo or None if process not found
    """
    try:
        proc = psutil.Process(pid)
        info = proc.as_dict(attrs=[
            "pid", "name", "status", "cpu_percent", "memory_percent",
            "memory_info", "num_threads", "create_time", "cmdline", "username"
        ])
        memory_info = info.get("memory_info")
        
        return ProcessInfo(
            pid=info["pid"],
            name=info["name"] or "unknown",
            status=info["status"] or "unknown",
            cpu_percent=info["cpu_percent"] or 0.0,
            memory_percent=info["memory_percent"] or 0.0,
            memory_rss=memory_info.rss if memory_info else 0,
            memory_vms=memory_info.vms if memory_info else 0,
            num_threads=info["num_threads"] or 0,
            create_time=datetime.fromtimestamp(
                info["create_time"] or 0, tz=timezone.utc
            ),
            cmdline=info["cmdline"] or [],
            username=info["username"] or "unknown",
        )
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None
