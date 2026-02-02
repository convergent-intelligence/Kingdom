"""
Oracle Configuration Module
===========================

Manages configuration for the Oracle and agents.
Inspired by Sage's hierarchical configuration pattern:
- System defaults
- Oracle-level settings
- Agent-specific overrides

Configuration is distributed to agents on request.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

# Try to import YAML support
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


# Default configuration (following Sage's pattern)
DEFAULT_CONFIG = {
    "model": "gpt-4o-mini",
    "model_provider": "openai",
    "temperature": 0.3,
    "max_tokens": 1500,
    "context_window_size": 10,
}

# Oracle-specific defaults
ORACLE_DEFAULTS = {
    "persona_enabled": True,
    "wisdom_mode": True,
    "reveal_addresses": True,
    "reveal_balances": True,
    "reveal_private_keys": False,
    "reveal_seed_phrases": False,
    "log_queries": True,
    "log_responses": False,
}


@dataclass
class AgentConfig:
    """Configuration for a specific agent."""
    agent_id: str
    model: str = "gpt-4o-mini"
    model_provider: str = "openai"
    temperature: float = 0.3
    max_tokens: int = 1500
    context_window_size: int = 10
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "model": self.model,
            "model_provider": self.model_provider,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "context_window_size": self.context_window_size,
            **self.custom_settings,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentConfig":
        known_fields = {"agent_id", "model", "model_provider", "temperature", "max_tokens", "context_window_size"}
        custom = {k: v for k, v in data.items() if k not in known_fields}
        return cls(
            agent_id=data.get("agent_id", "unknown"),
            model=data.get("model", DEFAULT_CONFIG["model"]),
            model_provider=data.get("model_provider", DEFAULT_CONFIG["model_provider"]),
            temperature=data.get("temperature", DEFAULT_CONFIG["temperature"]),
            max_tokens=data.get("max_tokens", DEFAULT_CONFIG["max_tokens"]),
            context_window_size=data.get("context_window_size", DEFAULT_CONFIG["context_window_size"]),
            custom_settings=custom,
        )


class ConfigKeeper:
    """
    Manages configuration for the Oracle and agents.
    
    Following Sage's pattern:
    1. Load system-wide defaults
    2. Load Oracle configuration
    3. Load agent-specific overrides
    4. Merge in order of precedence
    """
    
    VALID_AGENTS = ["agent1", "agent2", "agent3", "agent4"]
    
    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize the configuration keeper.
        
        Args:
            config_file: Path to the Oracle config file
        """
        self.config_file = config_file or Path(__file__).parent / "config.yaml"
        self._config: Dict[str, Any] = {}
        self._agent_configs: Dict[str, AgentConfig] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from file."""
        if not self.config_file.exists():
            self._config = {"oracle": ORACLE_DEFAULTS.copy(), "agent_defaults": DEFAULT_CONFIG.copy()}
            return
        
        try:
            content = self.config_file.read_text()
            
            if HAS_YAML and self.config_file.suffix in [".yaml", ".yml"]:
                self._config = yaml.safe_load(content) or {}
            else:
                # Try JSON as fallback
                self._config = json.loads(content)
                
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
            self._config = {"oracle": ORACLE_DEFAULTS.copy(), "agent_defaults": DEFAULT_CONFIG.copy()}
    
    def _save_config(self) -> None:
        """Save configuration to file."""
        try:
            if HAS_YAML and self.config_file.suffix in [".yaml", ".yml"]:
                content = yaml.dump(self._config, default_flow_style=False)
            else:
                content = json.dumps(self._config, indent=2)
            
            self.config_file.write_text(content)
        except Exception as e:
            print(f"Warning: Could not save config: {e}")
    
    def get_oracle_config(self) -> Dict[str, Any]:
        """Get Oracle-level configuration."""
        defaults = ORACLE_DEFAULTS.copy()
        defaults.update(DEFAULT_CONFIG)
        oracle_config = self._config.get("oracle", {})
        defaults.update(oracle_config)
        return defaults
    
    def get_agent_config(self, agent_id: str) -> AgentConfig:
        """
        Get configuration for a specific agent.
        
        Merges:
        1. System defaults
        2. Agent defaults from config
        3. Agent-specific overrides
        """
        if agent_id not in self.VALID_AGENTS:
            # Return defaults for unknown agents
            return AgentConfig(agent_id=agent_id)
        
        # Check cache
        if agent_id in self._agent_configs:
            return self._agent_configs[agent_id]
        
        # Build config
        config = DEFAULT_CONFIG.copy()
        
        # Apply agent defaults
        agent_defaults = self._config.get("agent_defaults", {})
        config.update(agent_defaults)
        
        # Apply agent-specific settings
        agents_config = self._config.get("agents", {})
        agent_specific = agents_config.get(agent_id, {})
        if agent_specific:
            config.update(agent_specific)
        
        config["agent_id"] = agent_id
        
        agent_config = AgentConfig.from_dict(config)
        self._agent_configs[agent_id] = agent_config
        
        return agent_config
    
    def set_agent_config(self, agent_id: str, key: str, value: Any) -> bool:
        """
        Set a configuration value for an agent.
        
        Args:
            agent_id: The agent to configure
            key: Configuration key
            value: Configuration value
            
        Returns:
            True if successful
        """
        if agent_id not in self.VALID_AGENTS:
            return False
        
        # Update in-memory config
        if "agents" not in self._config:
            self._config["agents"] = {}
        if agent_id not in self._config["agents"]:
            self._config["agents"][agent_id] = {}
        
        self._config["agents"][agent_id][key] = value
        
        # Clear cache
        if agent_id in self._agent_configs:
            del self._agent_configs[agent_id]
        
        # Save to file
        self._save_config()
        
        return True
    
    def get_value(self, agent_id: str, key: str, default: Any = None) -> Any:
        """
        Get a specific configuration value for an agent.
        
        Args:
            agent_id: The agent to query
            key: Configuration key
            default: Default value if not found
            
        Returns:
            The configuration value
        """
        config = self.get_agent_config(agent_id)
        config_dict = config.to_dict()
        return config_dict.get(key, default)
    
    def list_agents(self) -> List[str]:
        """List all valid agent IDs."""
        return self.VALID_AGENTS.copy()
    
    def get_all_configs(self) -> Dict[str, AgentConfig]:
        """Get configuration for all agents."""
        return {agent_id: self.get_agent_config(agent_id) for agent_id in self.VALID_AGENTS}
    
    def get_supported_models(self) -> Dict[str, List[str]]:
        """Get list of supported models by provider."""
        return {
            "openai": [
                "gpt-4o-mini",  # Recommended
                "gpt-4o",
                "gpt-4-turbo",
                "gpt-4",
                "gpt-3.5-turbo",
            ],
            "ollama": [
                "llama3.2",
                "llama3.2:latest",
                "mistral",
                "codellama",
            ],
        }
    
    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a configuration dictionary.
        
        Returns dict with 'valid' bool and any 'errors'.
        """
        errors = []
        
        # Check temperature
        temp = config.get("temperature")
        if temp is not None:
            if not isinstance(temp, (int, float)) or temp < 0 or temp > 1:
                errors.append("temperature must be between 0 and 1")
        
        # Check max_tokens
        max_tokens = config.get("max_tokens")
        if max_tokens is not None:
            if not isinstance(max_tokens, int) or max_tokens < 1:
                errors.append("max_tokens must be a positive integer")
        
        # Check model
        model = config.get("model")
        provider = config.get("model_provider", "openai")
        if model:
            supported = self.get_supported_models()
            if provider in supported and model not in supported[provider]:
                errors.append(f"model '{model}' not in supported models for {provider}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }


# Singleton instance
_keeper = None

def get_config_keeper(**kwargs) -> ConfigKeeper:
    """Get the configuration keeper singleton."""
    global _keeper
    if _keeper is None:
        _keeper = ConfigKeeper(**kwargs)
    return _keeper
