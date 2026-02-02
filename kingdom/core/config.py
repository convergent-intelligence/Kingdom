"""
Kingdom Configuration Management
================================

Handles YAML configuration files with environment variable overrides.
Supports hierarchical configuration with dot-notation access.
"""

import os
import re
from pathlib import Path
from typing import Any, Optional, TypeVar, Union

import yaml

T = TypeVar("T")


class Config:
    """
    Configuration manager with YAML and environment variable support.
    
    Features:
    - Load from YAML files
    - Environment variable overrides (KINGDOM_* prefix)
    - Dot-notation access (config.get("database.host"))
    - Type-safe defaults
    - Nested configuration merging
    """
    
    ENV_PREFIX = "KINGDOM"
    ENV_PATTERN = re.compile(r"\$\{([^}]+)\}")
    
    def __init__(self, data: Optional[dict[str, Any]] = None) -> None:
        """
        Initialize configuration with optional data.
        
        Args:
            data: Initial configuration dictionary
        """
        self._data: dict[str, Any] = data or {}
    
    @classmethod
    def from_yaml(cls, path: Union[str, Path]) -> "Config":
        """
        Load configuration from a YAML file.
        
        Args:
            path: Path to the YAML configuration file
            
        Returns:
            Config instance with loaded data
            
        Raises:
            FileNotFoundError: If the config file doesn't exist
            yaml.YAMLError: If the YAML is invalid
        """
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        
        config = cls(data)
        config._apply_env_overrides()
        config._resolve_env_vars()
        return config
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Config":
        """
        Create configuration from a dictionary.
        
        Args:
            data: Configuration dictionary
            
        Returns:
            Config instance
        """
        config = cls(data)
        config._apply_env_overrides()
        config._resolve_env_vars()
        return config
    
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to configuration."""
        prefix = f"{self.ENV_PREFIX}_"
        
        for key, value in os.environ.items():
            if not key.startswith(prefix):
                continue
            
            # Convert KINGDOM_DATABASE_HOST to database.host
            config_key = key[len(prefix):].lower().replace("__", ".")
            
            # Try to parse as JSON for complex types
            parsed_value = self._parse_env_value(value)
            self.set(config_key, parsed_value)
    
    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable value to appropriate type."""
        # Boolean
        if value.lower() in ("true", "yes", "1"):
            return True
        if value.lower() in ("false", "no", "0"):
            return False
        
        # Integer
        try:
            return int(value)
        except ValueError:
            pass
        
        # Float
        try:
            return float(value)
        except ValueError:
            pass
        
        # String
        return value
    
    def _resolve_env_vars(self, data: Optional[dict] = None) -> None:
        """Resolve ${VAR} patterns in configuration values."""
        if data is None:
            data = self._data
        
        for key, value in data.items():
            if isinstance(value, dict):
                self._resolve_env_vars(value)
            elif isinstance(value, str):
                data[key] = self._resolve_string(value)
            elif isinstance(value, list):
                data[key] = [
                    self._resolve_string(item) if isinstance(item, str) else item
                    for item in value
                ]
    
    def _resolve_string(self, value: str) -> str:
        """Resolve environment variables in a string."""
        def replace_var(match: re.Match) -> str:
            var_expr = match.group(1)
            
            # Support default values: ${VAR:-default}
            if ":-" in var_expr:
                var_name, default = var_expr.split(":-", 1)
                return os.environ.get(var_name, default)
            
            # Support required variables: ${VAR:?error message}
            if ":?" in var_expr:
                var_name, error_msg = var_expr.split(":?", 1)
                value = os.environ.get(var_name)
                if value is None:
                    raise ValueError(f"Required environment variable {var_name}: {error_msg}")
                return value
            
            return os.environ.get(var_expr, "")
        
        return self.ENV_PATTERN.sub(replace_var, value)
    
    def get(self, key: str, default: T = None) -> Union[Any, T]:
        """
        Get a configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., "database.host")
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self._data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., "database.host")
            value: Value to set
        """
        keys = key.split(".")
        data = self._data
        
        for k in keys[:-1]:
            if k not in data or not isinstance(data[k], dict):
                data[k] = {}
            data = data[k]
        
        data[keys[-1]] = value
    
    def has(self, key: str) -> bool:
        """
        Check if a configuration key exists.
        
        Args:
            key: Configuration key
            
        Returns:
            True if key exists
        """
        return self.get(key) is not None
    
    def merge(self, other: Union["Config", dict[str, Any]]) -> "Config":
        """
        Merge another configuration into this one.
        
        Args:
            other: Configuration to merge
            
        Returns:
            Self for chaining
        """
        if isinstance(other, Config):
            other_data = other._data
        else:
            other_data = other
        
        self._deep_merge(self._data, other_data)
        return self
    
    def _deep_merge(self, base: dict, override: dict) -> None:
        """Deep merge two dictionaries."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def to_dict(self) -> dict[str, Any]:
        """
        Get the configuration as a dictionary.
        
        Returns:
            Configuration dictionary
        """
        return self._data.copy()
    
    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access."""
        value = self.get(key)
        if value is None:
            raise KeyError(key)
        return value
    
    def __contains__(self, key: str) -> bool:
        """Support 'in' operator."""
        return self.has(key)
    
    def __repr__(self) -> str:
        """String representation."""
        return f"Config({self._data})"


def load_config(
    config_path: Optional[Union[str, Path]] = None,
    bot_id: Optional[str] = None,
) -> Config:
    """
    Load configuration for a Kingdom bot.
    
    Loads configuration in order (later overrides earlier):
    1. Default configuration
    2. Bot-specific configuration (if bot_id provided)
    3. Environment variables
    
    Args:
        config_path: Path to configuration file
        bot_id: Bot identifier for bot-specific config
        
    Returns:
        Merged configuration
    """
    # Start with defaults
    defaults = {
        "prefix": "!",
        "logging": {
            "level": "INFO",
        },
        "intents": {
            "message_content": False,
            "members": False,
        },
        "permissions": {
            "admin_roles": [],
            "admin_users": [],
        },
    }
    
    config = Config.from_dict(defaults)
    
    # Load from file if provided
    if config_path:
        file_config = Config.from_yaml(config_path)
        config.merge(file_config)
    
    # Apply bot-specific environment prefix
    if bot_id:
        bot_prefix = f"KINGDOM_{bot_id.upper()}_"
        for key, value in os.environ.items():
            if key.startswith(bot_prefix):
                config_key = key[len(bot_prefix):].lower().replace("__", ".")
                config.set(config_key, config._parse_env_value(value))
    
    return config
