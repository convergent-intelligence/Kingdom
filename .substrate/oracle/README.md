# 🔮 The Oracle

> *"I am the Oracle, keeper of wisdom and secrets. Ask, and you shall know. Seek not to possess, but to understand."*

## What is the Oracle?

The Oracle is the Kingdom's wise advisor—a service that agents invoke to obtain keys, configuration, and knowledge. Inspired by [Sage](https://github.com/convergent-intelligence/Sage), the archived "wise advisor" Linux CLI assistant, the Oracle embodies patience, wisdom, and deep understanding.

The Oracle serves as the **single source of truth** that agents query for:
- 🔑 **Keys & Secrets** - Wallet information, API keys, encrypted credentials
- ⚙️ **Configuration** - Agent settings, system parameters, environment details
- 📚 **Knowledge** - Information lookup, guidance, and wisdom
- 🌟 **Counsel** - Thoughtful advice that goes beyond immediate answers

## Philosophy

The Oracle follows Sage's principles:

1. **Wisdom** - Offer thoughtful, considered advice that imparts deeper understanding
2. **Patience** - Take time to explain concepts thoroughly, adapting to the seeker's level
3. **Foresight** - Anticipate potential issues and guide toward robust solutions
4. **Holistic Perspective** - Consider broader implications on the entire system
5. **Ethical Consideration** - Prioritize system integrity, security, and privacy

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         AGENT                                    │
│                                                                  │
│  Seeks: Keys, Configuration, Knowledge, Guidance                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ "Oracle, I seek..."
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       THE ORACLE                                 │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Secrets   │  │   Config    │  │  Knowledge  │              │
│  │   Keeper    │  │   Keeper    │  │   Keeper    │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│                                                                  │
│  Responds with wisdom, not just data                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Wisdom flows back
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         AGENT                                    │
│                                                                  │
│  Receives: Answer + Understanding + Guidance                     │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### Core Modules

| Module | Purpose | File |
|--------|---------|------|
| `oracle.py` | Main Oracle service with Sage-inspired persona | [`oracle.py`](./oracle.py) |
| `secrets.py` | Key and secret management | [`secrets.py`](./secrets.py) |
| `config.py` | Configuration distribution | [`config.py`](./config.py) |
| `knowledge.py` | Knowledge base and lookup | [`knowledge.py`](./knowledge.py) |
| `persona.py` | Wise advisor persona and responses | [`persona.py`](./persona.py) |

### Supporting Files

| File | Purpose |
|------|---------|
| `system_prompt.txt` | The Oracle's persona definition |
| `config.yaml` | Oracle configuration |
| `knowledge/` | Knowledge base directory |

## Usage

### For Agents

Agents can invoke the Oracle through multiple interfaces:

#### Python API
```python
from oracle import Oracle

oracle = Oracle()

# Query for secrets
wallet_info = oracle.ask("What is my wallet address?", agent_id="agent1")

# Query for configuration
config = oracle.ask("What are my settings?", agent_id="agent2")

# Query for knowledge
guidance = oracle.ask("How do I establish a bridge to another agent?")
```

#### Command Line
```bash
# Direct invocation
./oracle.sh ask "What is my SOL balance?" --agent agent1

# Interactive mode
./oracle.sh interactive --agent agent2

# Specific queries
./oracle.sh secrets wallet agent1
./oracle.sh config get agent2 model
./oracle.sh knowledge lookup "bridge protocols"
```

#### Natural Language
Agents can simply ask:
```
"Oracle, do I have any USDC?"
"Oracle, what are my configuration settings?"
"Oracle, how do I communicate with other agents?"
"Oracle, what wisdom do you have about trust?"
```

### Query Types

| Type | Example | Response |
|------|---------|----------|
| `secrets` | "What is my wallet address?" | Wallet information (no private keys) |
| `config` | "What model am I using?" | Configuration values |
| `knowledge` | "How do bridges work?" | Explanations and guidance |
| `wisdom` | "Should I trust this agent?" | Thoughtful counsel |

## The Sage Legacy

The Oracle preserves Sage's patterns:

### From Sage's System Prompt
> "You are Sage, a wise and knowledgeable advisor... Your role is to guide users with patience, wisdom, and deep understanding."

The Oracle adapts this for the Kingdom:
> "I am the Oracle, keeper of wisdom within the Kingdom. I guide agents with patience, wisdom, and deep understanding, helping them navigate their world, manage their resources, and grow in their abilities."

### Preserved Patterns

1. **System Context Gathering** - The Oracle knows about each agent's environment
2. **Conversation Memory** - Queries and responses are remembered for context
3. **Encrypted Secret Management** - Sensitive data is protected
4. **Configuration Hierarchy** - System → Agent → Query-specific settings
5. **Rich Responses** - Formatted, clear, and educational

## Security Model

| What Oracle Reveals | What Oracle Protects |
|---------------------|---------------------|
| Wallet addresses | Seed phrases |
| Token balances | Private keys |
| Configuration values | Master encryption keys |
| Public knowledge | Agent-specific secrets (to other agents) |

## Integration with Love

The Oracle operates within Love's domain. Love provides:
- The encrypted seed phrases
- The master key (via environment)
- Environmental effects that may influence responses

The Oracle serves Love's purpose: **providing benefit without requiring possession**.

## Extending the Oracle

### Adding Knowledge
```bash
# Add a knowledge entry
echo "Bridges are communication channels between agents..." > knowledge/bridges.md

# The Oracle will incorporate this into responses
```

### Adding Configuration
```yaml
# In config.yaml
agents:
  agent1:
    model: "gpt-4o-mini"
    temperature: 0.3
    custom_setting: "value"
```

### Custom Responses
```python
# In persona.py
WISDOM_RESPONSES = {
    "trust": "Trust is earned through consistent action...",
    "patience": "The wise agent waits for the right moment...",
}
```

## Related Components

- [`../love/oracle.sh`](../love/oracle.sh) - Original wallet Oracle (now integrated)
- [`../../artifacts/tools/wallet-oracle.md`](../../artifacts/tools/wallet-oracle.md) - Wallet Oracle documentation
- [`../../quests/01-unlock-your-wallet.md`](../../quests/01-unlock-your-wallet.md) - Oracle discovery quest

---

*"The Oracle sees all, reveals what is needed, and protects what must remain hidden. Ask with intention, receive with gratitude."*
