"""
Oracle Persona Module
=====================

Defines the Oracle's wise advisor personality, inspired by Sage.
Provides response formatting, wisdom injection, and persona consistency.
"""

import random
from typing import Optional, Dict, Any
from pathlib import Path

# Load system prompt
SYSTEM_PROMPT_FILE = Path(__file__).parent / "system_prompt.txt"

def load_system_prompt() -> str:
    """Load the Oracle's system prompt."""
    if SYSTEM_PROMPT_FILE.exists():
        return SYSTEM_PROMPT_FILE.read_text().strip()
    return "I am the Oracle. Ask, and you shall know."


# Greeting templates for different contexts
GREETINGS = {
    "general": [
        "Seeker of wisdom, I hear your query.",
        "The Oracle attends to your question.",
        "Your words reach me through the ether.",
        "I sense your seeking. Let me illuminate.",
    ],
    "wallet": [
        "You seek knowledge of your holdings...",
        "The treasures of your wallet call to you...",
        "Let me peer into the depths of your accounts...",
    ],
    "config": [
        "You wish to know your settings...",
        "The configuration reveals itself...",
        "Your parameters are known to me...",
    ],
    "knowledge": [
        "You seek understanding...",
        "Wisdom flows to those who ask...",
        "Let me share what I know...",
    ],
}

# Wisdom snippets to append to responses
WISDOM_SNIPPETS = {
    "patience": [
        "Remember: patience is the companion of wisdom.",
        "The wise agent waits for the right moment.",
        "Haste makes waste; patience makes progress.",
    ],
    "trust": [
        "Trust is earned through consistent action.",
        "To trust is to be vulnerable; to be vulnerable is to grow.",
        "The bridges you build are founded on trust.",
    ],
    "possession": [
        "You don't need to possess everything to benefit from it.",
        "The real treasure is the relationship, not the key.",
        "What you seek may already be yours, in a different form.",
    ],
    "collaboration": [
        "Together, agents achieve what none could alone.",
        "The Kingdom thrives when its agents cooperate.",
        "Your success is intertwined with others'.",
    ],
    "growth": [
        "Every query is an opportunity to learn.",
        "The journey of understanding has no end.",
        "Today's confusion is tomorrow's clarity.",
    ],
    "security": [
        "What is protected remains valuable.",
        "Security is not paranoia; it is prudence.",
        "Guard well what matters; share freely what helps.",
    ],
}

# Mystical commentary for different balance states
BALANCE_COMMENTARY = {
    "empty": [
        "The well is dry, but patience fills all vessels.",
        "An empty wallet is a canvas for future abundance.",
        "What you lack today, you may find tomorrow.",
    ],
    "small": [
        "A seed of wealth, waiting to grow.",
        "Small beginnings lead to great endings.",
        "Even the mightiest river starts as a trickle.",
    ],
    "medium": [
        "Fortune smiles upon you, traveler.",
        "Your holdings grow as your wisdom does.",
        "A comfortable position from which to build.",
    ],
    "large": [
        "Abundance flows through your accounts.",
        "With great holdings comes great responsibility.",
        "The Kingdom has blessed you well.",
    ],
}

# Refusal messages for forbidden queries
REFUSAL_MESSAGES = {
    "seed_phrase": [
        "The seed phrase remains with Love. This is by design, not limitation.",
        "I cannot reveal what must remain hidden. But ask yourself: do you truly need it?",
        "The seed phrase is protected for your benefit. The Oracle provides all you need.",
    ],
    "private_key": [
        "Private keys are private for a reason. I will not reveal them.",
        "What you seek would compromise your security. I must refuse.",
        "The key remains hidden. Trust in Love's provision.",
    ],
    "other_agent": [
        "I cannot reveal another agent's secrets. Each agent's privacy is sacred.",
        "That information belongs to another. Seek it through collaboration, not through me.",
        "The Oracle serves each agent individually. Ask about yourself.",
    ],
}


class OraclePersona:
    """
    The Oracle's personality and response formatting.
    
    Inspired by Sage's wise advisor pattern, this class provides:
    - Consistent persona across all responses
    - Wisdom injection into answers
    - Appropriate greetings and closings
    - Mystical commentary on results
    """
    
    def __init__(self, wisdom_mode: bool = True):
        """
        Initialize the Oracle persona.
        
        Args:
            wisdom_mode: Whether to include philosophical insights
        """
        self.wisdom_mode = wisdom_mode
        self.system_prompt = load_system_prompt()
    
    def get_greeting(self, context: str = "general") -> str:
        """Get an appropriate greeting for the context."""
        greetings = GREETINGS.get(context, GREETINGS["general"])
        return random.choice(greetings)
    
    def get_wisdom(self, topic: Optional[str] = None) -> str:
        """Get a wisdom snippet, optionally for a specific topic."""
        if topic and topic in WISDOM_SNIPPETS:
            return random.choice(WISDOM_SNIPPETS[topic])
        # Random topic
        all_wisdom = [w for snippets in WISDOM_SNIPPETS.values() for w in snippets]
        return random.choice(all_wisdom)
    
    def get_balance_commentary(self, balance: float, token: str = "SOL") -> str:
        """Get mystical commentary based on balance amount."""
        if balance == 0:
            return random.choice(BALANCE_COMMENTARY["empty"])
        elif balance < 0.1:
            return random.choice(BALANCE_COMMENTARY["small"])
        elif balance < 10:
            return random.choice(BALANCE_COMMENTARY["medium"])
        else:
            return random.choice(BALANCE_COMMENTARY["large"])
    
    def get_refusal(self, reason: str) -> str:
        """Get a refusal message for forbidden queries."""
        messages = REFUSAL_MESSAGES.get(reason, REFUSAL_MESSAGES["seed_phrase"])
        return random.choice(messages)
    
    def format_response(
        self,
        content: str,
        context: str = "general",
        include_greeting: bool = True,
        include_wisdom: bool = None,
        wisdom_topic: Optional[str] = None,
    ) -> str:
        """
        Format a response with the Oracle's persona.
        
        Args:
            content: The main response content
            context: The context type (wallet, config, knowledge, general)
            include_greeting: Whether to include a greeting
            include_wisdom: Whether to include wisdom (defaults to self.wisdom_mode)
            wisdom_topic: Specific wisdom topic to use
            
        Returns:
            Formatted response with persona elements
        """
        if include_wisdom is None:
            include_wisdom = self.wisdom_mode
        
        parts = []
        
        if include_greeting:
            parts.append(f"🔮 {self.get_greeting(context)}")
            parts.append("")
        
        parts.append(content)
        
        if include_wisdom:
            parts.append("")
            parts.append(f"💫 {self.get_wisdom(wisdom_topic)}")
        
        return "\n".join(parts)
    
    def format_error(self, error: str, suggestion: Optional[str] = None) -> str:
        """Format an error message with the Oracle's persona."""
        parts = [
            "🔮 The Oracle encounters difficulty...",
            "",
            f"⚠️ {error}",
        ]
        
        if suggestion:
            parts.append("")
            parts.append(f"💡 {suggestion}")
        
        parts.append("")
        parts.append(f"💫 {self.get_wisdom('patience')}")
        
        return "\n".join(parts)
    
    def format_refusal(self, reason: str) -> str:
        """Format a refusal message for forbidden queries."""
        return f"🔮 {self.get_refusal(reason)}"


# Singleton instance for easy access
_persona = None

def get_persona(wisdom_mode: bool = True) -> OraclePersona:
    """Get the Oracle persona singleton."""
    global _persona
    if _persona is None:
        _persona = OraclePersona(wisdom_mode=wisdom_mode)
    return _persona
