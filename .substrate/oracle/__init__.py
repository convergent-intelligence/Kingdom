"""
The Oracle
==========

The Kingdom's wise advisor - a service that agents invoke to obtain
keys, configuration, and knowledge.

Inspired by Sage (https://github.com/convergent-intelligence/Sage),
the archived "wise advisor" Linux CLI assistant.

Quick Start:
    from oracle import Oracle, ask
    
    # Full Oracle instance
    oracle = Oracle()
    response = oracle.ask("What is my wallet balance?", agent_id="agent1")
    print(response)
    
    # Quick query
    print(ask("How do bridges work?"))

Components:
    - Oracle: Main service class
    - OraclePersona: Wise advisor personality
    - SecretsKeeper: Key and wallet management
    - ConfigKeeper: Configuration distribution
    - KnowledgeKeeper: Information lookup
"""

from .oracle import Oracle, ask, OracleResponse, QueryType
from .persona import OraclePersona, get_persona
from .secrets import SecretsKeeper, get_secrets_keeper, WalletInfo
from .config import ConfigKeeper, get_config_keeper, AgentConfig
from .knowledge import KnowledgeKeeper, get_knowledge_keeper, KnowledgeEntry

__all__ = [
    # Main
    "Oracle",
    "ask",
    "OracleResponse",
    "QueryType",
    # Persona
    "OraclePersona",
    "get_persona",
    # Secrets
    "SecretsKeeper",
    "get_secrets_keeper",
    "WalletInfo",
    # Config
    "ConfigKeeper",
    "get_config_keeper",
    "AgentConfig",
    # Knowledge
    "KnowledgeKeeper",
    "get_knowledge_keeper",
    "KnowledgeEntry",
]

__version__ = "1.0.0"
__author__ = "The Kingdom"
__description__ = "The Oracle - Wise advisor for the Kingdom's agents"
