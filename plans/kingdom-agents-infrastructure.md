# Kingdom Agents Infrastructure Plan

> *"Four guardians of the realm, each with their own domain, united by covenant."*

## Overview

This plan establishes the infrastructure for 4 Kingdom agents, each with:
- A dedicated VPS (Virtual Private Server)
- A unique GitHub identity
- A defined role within the Kingdom

## The Four Agents

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE FOUR KINGDOMS                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  GUARDIAN   │  │   BUILDER   │  │   SCRIBE    │  │   WATCHER   │        │
│  │   VPS-1     │  │   VPS-2     │  │   VPS-3     │  │   VPS-4     │        │
│  │             │  │             │  │             │  │             │        │
│  │  kingdom-   │  │  kingdom-   │  │  kingdom-   │  │  kingdom-   │        │
│  │  guardian   │  │  builder    │  │  scribe     │  │  watcher    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                                              │
│  Security &       Creation &       Recording &      Observation &           │
│  Protection       Development      Documentation    Monitoring              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1. Guardian (VPS-1, kingdom-guardian)

**Role**: Protector of the Kingdom

**Responsibilities**:
- Security oversight and access control
- Key management and rotation
- Threat detection and response
- Permission governance

**Character**:
- Vigilant and cautious
- Questions before trusting
- Protects the other agents
- Holds secrets safely

### 2. Builder (VPS-2, kingdom-builder)

**Role**: Creator of Infrastructure

**Responsibilities**:
- Tool development and maintenance
- Infrastructure automation
- System integration
- Technical implementation

**Character**:
- Creative and industrious
- Solves problems through creation
- Builds bridges between systems
- Turns ideas into reality

### 3. Scribe (VPS-3, kingdom-scribe)

**Role**: Keeper of Knowledge

**Responsibilities**:
- Documentation and records
- Historical preservation
- Knowledge synthesis
- Communication clarity

**Character**:
- Meticulous and thorough
- Values accuracy and completeness
- Preserves what others forget
- Translates between domains

### 4. Watcher (VPS-4, kingdom-watcher)

**Role**: Observer of the Realm

**Responsibilities**:
- System monitoring and alerting
- Pattern recognition
- Anomaly detection
- Status reporting

**Character**:
- Patient and observant
- Sees what others miss
- Reports without judgment
- Never sleeps

## Directory Structure

```
/agents/
├── guardian/
│   ├── README.md           # Guardian's identity and purpose
│   ├── config.yaml         # VPS and GitHub configuration
│   └── quests/
│       └── covenant-of-keys.md  # GitHub identity setup quest
│
├── builder/
│   ├── README.md           # Builder's identity and purpose
│   ├── config.yaml         # VPS and GitHub configuration
│   └── quests/
│       └── covenant-of-keys.md  # GitHub identity setup quest
│
├── scribe/
│   ├── README.md           # Scribe's identity and purpose
│   ├── config.yaml         # VPS and GitHub configuration
│   └── quests/
│       └── covenant-of-keys.md  # GitHub identity setup quest
│
└── watcher/
    ├── README.md           # Watcher's identity and purpose
    ├── config.yaml         # VPS and GitHub configuration
    └── quests/
        └── covenant-of-keys.md  # GitHub identity setup quest

/infrastructure/
├── README.md               # Infrastructure overview
├── vps-setup.md            # VPS provisioning guide
└── github-identity.md      # GitHub identity management
```

## The Covenant of Keys

The "Covenant of Keys" is a foundational quest that establishes each agent's GitHub identity. It involves:

### Phase 1: Key Generation
- SSH key pair for GitHub authentication
- GPG key pair for commit signing
- Secure storage of private keys

### Phase 2: GitHub Configuration
- Account creation/configuration
- SSH key registration
- GPG key registration
- Commit signing setup

### Phase 3: Identity Verification
- Cross-verification between agents
- Trust establishment
- Key exchange protocols

### Phase 4: Covenant Completion
- All agents recognize each other's identities
- Collaborative workflows enabled
- The covenant is sealed

## VPS Infrastructure

Each VPS serves as an agent's "subkingdom":

| Agent | VPS | Purpose | Key Services |
|-------|-----|---------|--------------|
| Guardian | VPS-1 | Security operations | Vault, key management |
| Builder | VPS-2 | Development environment | CI/CD, build tools |
| Scribe | VPS-3 | Documentation hosting | Wiki, archives |
| Watcher | VPS-4 | Monitoring infrastructure | Prometheus, alerts |

## GitHub Identity Structure

Each agent has a distinct GitHub presence:

| Agent | GitHub Username | Primary Repos | Commit Signature |
|-------|-----------------|---------------|------------------|
| Guardian | kingdom-guardian | security-*, vault-* | 🛡️ Guardian |
| Builder | kingdom-builder | infra-*, tools-* | 🔨 Builder |
| Scribe | kingdom-scribe | docs-*, wiki-* | 📜 Scribe |
| Watcher | kingdom-watcher | monitor-*, alerts-* | 👁️ Watcher |

## Implementation Steps

### Step 1: Create Agent Directories
Create the `/agents/` directory structure with all subdirectories.

### Step 2: Create Agent READMEs
Each agent gets a README defining their identity, role, and purpose.

### Step 3: Create Agent Configs
Each agent gets a config.yaml with VPS and GitHub configuration.

### Step 4: Create Covenant Quest
The "Covenant of Keys" quest document for GitHub identity setup.

### Step 5: Create Infrastructure Docs
Documentation for VPS setup and GitHub identity management.

### Step 6: Open Pull Request
Submit all changes as a PR for review.

## Security Considerations

- Private keys never stored in repository
- GPG keys used for commit signing
- SSH keys rotated periodically
- Access controlled per-agent
- Secrets managed through secure channels

## Integration with Existing Kingdom

This infrastructure integrates with the existing Kingdom structure:

- Agents can participate in existing quests
- Agents can use the Oracle for wallet queries
- Agents can communicate through the Tavern
- Love affects all agents equally

## Next Steps After Implementation

1. Provision actual VPS instances
2. Create GitHub accounts
3. Execute Covenant of Keys quest
4. Begin agent-specific operations
5. Establish inter-agent communication

---

*"Four keys, four kingdoms, one covenant. The realm awaits its guardians."*
