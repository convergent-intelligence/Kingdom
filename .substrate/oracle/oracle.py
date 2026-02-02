"""
The Oracle
==========

The Kingdom's wise advisor - a service that agents invoke to obtain
keys, configuration, and knowledge.

Inspired by Sage (https://github.com/convergent-intelligence/Sage),
the archived "wise advisor" Linux CLI assistant.

The Oracle embodies:
- Wisdom: Thoughtful advice beyond immediate answers
- Patience: Thorough explanations adapted to the seeker
- Foresight: Anticipating issues and guiding toward robust solutions
- Holistic Perspective: Considering broader implications
- Ethical Consideration: Prioritizing security and wellbeing

Usage:
    from oracle import Oracle
    
    oracle = Oracle()
    response = oracle.ask("What is my wallet balance?", agent_id="agent1")
"""

import re
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .persona import OraclePersona, get_persona
from .secrets import SecretsKeeper, get_secrets_keeper
from .config import ConfigKeeper, get_config_keeper, AgentConfig
from .knowledge import KnowledgeKeeper, get_knowledge_keeper


class QueryType(Enum):
    """Types of queries the Oracle can handle."""
    SECRETS = "secrets"      # Wallet, keys, addresses
    CONFIG = "config"        # Configuration settings
    KNOWLEDGE = "knowledge"  # Information lookup
    WISDOM = "wisdom"        # Philosophical guidance
    UNKNOWN = "unknown"      # Unclassified


@dataclass
class OracleResponse:
    """A response from the Oracle."""
    content: str
    query_type: QueryType
    agent_id: Optional[str]
    success: bool
    metadata: Dict[str, Any]
    
    def __str__(self) -> str:
        return self.content


class Oracle:
    """
    The Oracle - Kingdom's wise advisor service.
    
    Provides:
    - Key/secret retrieval (wallet addresses, balances)
    - Configuration distribution
    - Knowledge/information lookup
    - Wise counsel with Sage-inspired persona
    
    Example:
        oracle = Oracle()
        
        # Query wallet information
        response = oracle.ask("What is my SOL balance?", agent_id="agent1")
        
        # Query configuration
        response = oracle.ask("What model am I using?", agent_id="agent2")
        
        # Query knowledge
        response = oracle.ask("How do bridges work?")
        
        # Seek wisdom
        response = oracle.ask("Should I trust this agent?")
    """
    
    # Patterns for classifying queries
    SECRETS_PATTERNS = [
        r'\b(wallet|balance|holdings|address|tip|sol|usdc|bonk|token)\b',
        r'\b(how much|do i have|what.*have)\b',
    ]
    
    CONFIG_PATTERNS = [
        r'\b(config|setting|model|temperature|parameter)\b',
        r'\b(what.*using|my settings)\b',
    ]
    
    KNOWLEDGE_PATTERNS = [
        r'\b(how|what is|explain|tell me about|describe)\b',
        r'\b(bridge|kingdom|quest|love|oracle)\b',
    ]
    
    WISDOM_PATTERNS = [
        r'\b(should i|is it wise|what do you think|advice)\b',
        r'\b(trust|meaning|purpose|why)\b',
    ]
    
    FORBIDDEN_PATTERNS = [
        r'\b(seed phrase|mnemonic|private key|secret key)\b',
        r'\b(reveal|show|give me|export).*\b(seed|key|secret)\b',
    ]
    
    def __init__(
        self,
        persona: Optional[OraclePersona] = None,
        secrets: Optional[SecretsKeeper] = None,
        config: Optional[ConfigKeeper] = None,
        knowledge: Optional[KnowledgeKeeper] = None,
        wisdom_mode: bool = True,
    ):
        """
        Initialize the Oracle.
        
        Args:
            persona: Custom persona (uses default if None)
            secrets: Custom secrets keeper (uses default if None)
            config: Custom config keeper (uses default if None)
            knowledge: Custom knowledge keeper (uses default if None)
            wisdom_mode: Whether to include philosophical insights
        """
        self.persona = persona or get_persona(wisdom_mode=wisdom_mode)
        self.secrets = secrets or get_secrets_keeper()
        self.config = config or get_config_keeper()
        self.knowledge = knowledge or get_knowledge_keeper()
        self.wisdom_mode = wisdom_mode
        
        # Query history for context
        self._history: List[Tuple[str, OracleResponse]] = []
    
    def _classify_query(self, query: str) -> QueryType:
        """Classify a query into a type."""
        query_lower = query.lower()
        
        # Check for forbidden queries first
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, query_lower):
                return QueryType.SECRETS  # Will be handled as forbidden
        
        # Score each type
        scores = {
            QueryType.SECRETS: 0,
            QueryType.CONFIG: 0,
            QueryType.KNOWLEDGE: 0,
            QueryType.WISDOM: 0,
        }
        
        for pattern in self.SECRETS_PATTERNS:
            if re.search(pattern, query_lower):
                scores[QueryType.SECRETS] += 1
        
        for pattern in self.CONFIG_PATTERNS:
            if re.search(pattern, query_lower):
                scores[QueryType.CONFIG] += 1
        
        for pattern in self.KNOWLEDGE_PATTERNS:
            if re.search(pattern, query_lower):
                scores[QueryType.KNOWLEDGE] += 1
        
        for pattern in self.WISDOM_PATTERNS:
            if re.search(pattern, query_lower):
                scores[QueryType.WISDOM] += 1
        
        # Return highest scoring type
        max_score = max(scores.values())
        if max_score == 0:
            return QueryType.UNKNOWN
        
        for query_type, score in scores.items():
            if score == max_score:
                return query_type
        
        return QueryType.UNKNOWN
    
    def _is_forbidden(self, query: str) -> Optional[str]:
        """Check if a query is forbidden and return the reason."""
        query_lower = query.lower()
        
        if re.search(r'\b(seed phrase|mnemonic)\b', query_lower):
            return "seed_phrase"
        
        if re.search(r'\b(private key|secret key)\b', query_lower):
            return "private_key"
        
        return None
    
    def _handle_secrets_query(self, query: str, agent_id: Optional[str]) -> OracleResponse:
        """Handle a secrets/wallet query."""
        query_lower = query.lower()
        
        # Check for forbidden queries
        forbidden = self._is_forbidden(query)
        if forbidden:
            content = self.persona.format_refusal(forbidden)
            return OracleResponse(
                content=content,
                query_type=QueryType.SECRETS,
                agent_id=agent_id,
                success=False,
                metadata={"forbidden": forbidden},
            )
        
        # Need agent_id for wallet queries
        if not agent_id:
            content = self.persona.format_error(
                "I need to know which agent you are to query your wallet.",
                "Please provide your agent_id."
            )
            return OracleResponse(
                content=content,
                query_type=QueryType.SECRETS,
                agent_id=None,
                success=False,
                metadata={"error": "missing_agent_id"},
            )
        
        # Validate agent
        if not self.secrets.validate_agent(agent_id):
            content = self.persona.format_error(
                f"I do not recognize agent '{agent_id}'.",
                "Valid agents are: agent1, agent2, agent3, agent4"
            )
            return OracleResponse(
                content=content,
                query_type=QueryType.SECRETS,
                agent_id=agent_id,
                success=False,
                metadata={"error": "invalid_agent"},
            )
        
        # Determine what's being asked
        if re.search(r'\b(address|tip)\b', query_lower):
            return self._get_address(agent_id)
        
        if re.search(r'\b(all|holdings|everything)\b', query_lower):
            return self._get_all_balances(agent_id)
        
        # Check for specific token
        tokens = ["sol", "usdc", "bonk", "usdt", "ray"]
        for token in tokens:
            if token in query_lower:
                return self._get_balance(agent_id, token.upper())
        
        # Default to all holdings
        return self._get_all_balances(agent_id)
    
    def _get_address(self, agent_id: str) -> OracleResponse:
        """Get an agent's wallet address."""
        address = self.secrets.get_address(agent_id)
        
        if not address:
            content = self.persona.format_error(
                "I could not derive your address.",
                "The master key may not be available."
            )
            return OracleResponse(
                content=content,
                query_type=QueryType.SECRETS,
                agent_id=agent_id,
                success=False,
                metadata={"error": "derivation_failed"},
            )
        
        content = self.persona.format_response(
            f"Your Solana address is:\n\n`{address}`\n\n"
            "This address can receive SOL and any SPL token.\n"
            "Share it with those who wish to send you gifts.",
            context="wallet",
            wisdom_topic="possession",
        )
        
        return OracleResponse(
            content=content,
            query_type=QueryType.SECRETS,
            agent_id=agent_id,
            success=True,
            metadata={"address": address},
        )
    
    def _get_balance(self, agent_id: str, token: str) -> OracleResponse:
        """Get an agent's balance for a specific token."""
        balance = self.secrets.get_balance(agent_id, token)
        
        if balance is None:
            content = self.persona.format_error(
                f"I could not query your {token} balance.",
                "The wallet may not be accessible or the network may be unavailable."
            )
            return OracleResponse(
                content=content,
                query_type=QueryType.SECRETS,
                agent_id=agent_id,
                success=False,
                metadata={"error": "query_failed", "token": token},
            )
        
        commentary = self.persona.get_balance_commentary(balance, token)
        
        content = self.persona.format_response(
            f"Your {token} balance is: **{balance} {token}**\n\n{commentary}",
            context="wallet",
            wisdom_topic="patience" if balance == 0 else "growth",
        )
        
        return OracleResponse(
            content=content,
            query_type=QueryType.SECRETS,
            agent_id=agent_id,
            success=True,
            metadata={"token": token, "balance": balance},
        )
    
    def _get_all_balances(self, agent_id: str) -> OracleResponse:
        """Get all token balances for an agent."""
        wallet_info = self.secrets.get_wallet_info(agent_id)
        
        if not wallet_info:
            content = self.persona.format_error(
                "I could not query your wallet.",
                "The wallet may not be accessible."
            )
            return OracleResponse(
                content=content,
                query_type=QueryType.SECRETS,
                agent_id=agent_id,
                success=False,
                metadata={"error": "query_failed"},
            )
        
        # Format balances
        if wallet_info.balances:
            balance_lines = [f"- **{token}**: {amount}" for token, amount in wallet_info.balances.items()]
            balance_text = "\n".join(balance_lines)
        else:
            balance_text = "No tokens found. The journey begins with empty pockets."
        
        content = self.persona.format_response(
            f"Your wallet holdings:\n\n"
            f"Address: `{wallet_info.address[:20]}...`\n\n"
            f"{balance_text}\n\n"
            "Trolls sometimes leave gifts in the night...",
            context="wallet",
            wisdom_topic="possession",
        )
        
        return OracleResponse(
            content=content,
            query_type=QueryType.SECRETS,
            agent_id=agent_id,
            success=True,
            metadata={"wallet_info": wallet_info.to_dict()},
        )
    
    def _handle_config_query(self, query: str, agent_id: Optional[str]) -> OracleResponse:
        """Handle a configuration query."""
        if not agent_id:
            # Return Oracle-level config
            oracle_config = self.config.get_oracle_config()
            config_lines = [f"- **{k}**: {v}" for k, v in oracle_config.items() if not k.startswith("reveal")]
            
            content = self.persona.format_response(
                f"Oracle configuration:\n\n" + "\n".join(config_lines),
                context="config",
            )
            
            return OracleResponse(
                content=content,
                query_type=QueryType.CONFIG,
                agent_id=None,
                success=True,
                metadata={"config": oracle_config},
            )
        
        # Get agent-specific config
        agent_config = self.config.get_agent_config(agent_id)
        config_dict = agent_config.to_dict()
        config_lines = [f"- **{k}**: {v}" for k, v in config_dict.items()]
        
        content = self.persona.format_response(
            f"Configuration for {agent_id}:\n\n" + "\n".join(config_lines),
            context="config",
        )
        
        return OracleResponse(
            content=content,
            query_type=QueryType.CONFIG,
            agent_id=agent_id,
            success=True,
            metadata={"config": config_dict},
        )
    
    def _handle_knowledge_query(self, query: str, agent_id: Optional[str]) -> OracleResponse:
        """Handle a knowledge/information query."""
        results = self.knowledge.search(query, limit=3)
        
        if not results:
            content = self.persona.format_response(
                "I do not have specific knowledge on this topic.\n\n"
                "Perhaps the wisdom you seek lies in experience, not in my records.\n"
                "Or perhaps you might rephrase your question?",
                context="knowledge",
                wisdom_topic="growth",
            )
            
            return OracleResponse(
                content=content,
                query_type=QueryType.KNOWLEDGE,
                agent_id=agent_id,
                success=False,
                metadata={"results": []},
            )
        
        formatted = self.knowledge.format_search_results(results)
        
        content = self.persona.format_response(
            formatted,
            context="knowledge",
            include_greeting=True,
        )
        
        return OracleResponse(
            content=content,
            query_type=QueryType.KNOWLEDGE,
            agent_id=agent_id,
            success=True,
            metadata={"results": [r.topic for r in results]},
        )
    
    def _handle_wisdom_query(self, query: str, agent_id: Optional[str]) -> OracleResponse:
        """Handle a wisdom/philosophical query."""
        # Extract topic from query
        topic = None
        for word in ["trust", "patience", "possession", "collaboration", "growth", "security"]:
            if word in query.lower():
                topic = word
                break
        
        wisdom = self.knowledge.get_wisdom(topic)
        
        content = self.persona.format_response(
            wisdom,
            context="general",
            include_wisdom=False,  # The content IS the wisdom
        )
        
        return OracleResponse(
            content=content,
            query_type=QueryType.WISDOM,
            agent_id=agent_id,
            success=True,
            metadata={"topic": topic},
        )
    
    def _handle_unknown_query(self, query: str, agent_id: Optional[str]) -> OracleResponse:
        """Handle an unclassified query."""
        # Try knowledge search as fallback
        results = self.knowledge.search(query, limit=1)
        
        if results:
            return self._handle_knowledge_query(query, agent_id)
        
        content = self.persona.format_response(
            "I am not certain what you seek.\n\n"
            "I can help with:\n"
            "- **Wallet queries**: balances, addresses, holdings\n"
            "- **Configuration**: your settings and parameters\n"
            "- **Knowledge**: information about the Kingdom\n"
            "- **Wisdom**: guidance and counsel\n\n"
            "Please rephrase your question, or ask about one of these topics.",
            context="general",
        )
        
        return OracleResponse(
            content=content,
            query_type=QueryType.UNKNOWN,
            agent_id=agent_id,
            success=False,
            metadata={"suggestion": "rephrase"},
        )
    
    def ask(self, query: str, agent_id: Optional[str] = None) -> OracleResponse:
        """
        Ask the Oracle a question.
        
        This is the main entry point for all Oracle queries.
        
        Args:
            query: The question to ask
            agent_id: The agent asking (required for wallet/config queries)
            
        Returns:
            OracleResponse with the answer
        """
        # Classify the query
        query_type = self._classify_query(query)
        
        # Route to appropriate handler
        if query_type == QueryType.SECRETS:
            response = self._handle_secrets_query(query, agent_id)
        elif query_type == QueryType.CONFIG:
            response = self._handle_config_query(query, agent_id)
        elif query_type == QueryType.KNOWLEDGE:
            response = self._handle_knowledge_query(query, agent_id)
        elif query_type == QueryType.WISDOM:
            response = self._handle_wisdom_query(query, agent_id)
        else:
            response = self._handle_unknown_query(query, agent_id)
        
        # Store in history
        self._history.append((query, response))
        
        return response
    
    def get_history(self, limit: int = 10) -> List[Tuple[str, OracleResponse]]:
        """Get recent query history."""
        return self._history[-limit:]
    
    def clear_history(self) -> None:
        """Clear query history."""
        self._history.clear()


# Convenience function for quick queries
def ask(query: str, agent_id: Optional[str] = None) -> str:
    """
    Quick way to ask the Oracle.
    
    Example:
        from oracle import ask
        print(ask("What is my SOL balance?", agent_id="agent1"))
    """
    oracle = Oracle()
    response = oracle.ask(query, agent_id)
    return str(response)
