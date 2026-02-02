# 🏰 Kingdom Infrastructure

> *"The foundation upon which the Kingdom stands."*

## Overview

This directory contains documentation for the infrastructure that supports the four Kingdom agents. Each agent operates from their own VPS (Virtual Private Server) with a unique GitHub identity.

## The Four Subkingdoms

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         KINGDOM INFRASTRUCTURE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐    ┌─────────────────┐                                 │
│  │     VPS-1       │    │     VPS-2       │                                 │
│  │    Guardian     │    │    Builder      │                                 │
│  │  🛡️ Security    │    │  🔨 Creation    │                                 │
│  │                 │    │                 │                                 │
│  │ kingdom-guardian│    │ kingdom-builder │                                 │
│  └─────────────────┘    └─────────────────┘                                 │
│                                                                              │
│  ┌─────────────────┐    ┌─────────────────┐                                 │
│  │     VPS-3       │    │     VPS-4       │                                 │
│  │     Scribe      │    │    Watcher      │                                 │
│  │  📜 Knowledge   │    │  👁️ Observation │                                 │
│  │                 │    │                 │                                 │
│  │ kingdom-scribe  │    │ kingdom-watcher │                                 │
│  └─────────────────┘    └─────────────────┘                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Documentation

| Document | Description |
|----------|-------------|
| [VPS Setup](vps-setup.md) | How to provision and configure VPS instances |
| [GitHub Identity](github-identity.md) | Managing GitHub accounts and authentication |

## Infrastructure Components

### VPS Instances

Each agent has a dedicated VPS:

| Agent | VPS | Primary Purpose | Key Services |
|-------|-----|-----------------|--------------|
| Guardian | VPS-1 | Security operations | Vault, fail2ban, OSSEC |
| Builder | VPS-2 | Development | Docker, CI/CD, build tools |
| Scribe | VPS-3 | Documentation | MkDocs, wiki, archives |
| Watcher | VPS-4 | Monitoring | Prometheus, Grafana, alerts |

### GitHub Identities

Each agent has a unique GitHub presence:

| Agent | GitHub Username | Email | Signature |
|-------|-----------------|-------|-----------|
| Guardian | kingdom-guardian | guardian@kingdom.local | 🛡️ |
| Builder | kingdom-builder | builder@kingdom.local | 🔨 |
| Scribe | kingdom-scribe | scribe@kingdom.local | 📜 |
| Watcher | kingdom-watcher | watcher@kingdom.local | 👁️ |

## Network Architecture

```
                    ┌─────────────────┐
                    │    Internet     │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
    ┌─────────┴─────────┐    │    ┌─────────┴─────────┐
    │      GitHub       │    │    │   Kingdom Main    │
    │   (Code Hosting)  │    │    │     (Central)     │
    └───────────────────┘    │    └───────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────┴────┐    ┌────────┴────────┐    ┌────┴────┐
    │  VPS-1  │    │      VPS-2      │    │  VPS-3  │
    │Guardian │    │     Builder     │    │  Scribe │
    └─────────┘    └─────────────────┘    └─────────┘
                             │
                        ┌────┴────┐
                        │  VPS-4  │
                        │ Watcher │
                        └─────────┘
```

## Security Model

### Access Control

- Each agent has SSH access only to their own VPS
- Cross-VPS access requires explicit authorization
- GitHub access via SSH keys (no passwords)
- Commits signed with GPG keys

### Key Management

- SSH keys: Ed25519 (preferred) or RSA 4096-bit
- GPG keys: RSA 4096-bit for commit signing
- Keys rotated annually or upon compromise
- Private keys never leave their VPS

### Trust Model

```
Guardian ←──────→ Builder
    ↑                ↑
    │                │
    ↓                ↓
Watcher ←──────→ Scribe
```

All agents verify each other's key fingerprints through the Covenant of Keys quest.

## Provisioning Workflow

1. **VPS Creation**: Provision 4 VPS instances
2. **Base Setup**: Install OS, configure networking
3. **Agent Setup**: Create agent user, configure environment
4. **Key Generation**: SSH and GPG keys for each agent
5. **GitHub Setup**: Create accounts, register keys
6. **Covenant**: Agents exchange and verify fingerprints

## Maintenance

### Regular Tasks

- [ ] Weekly: Review security logs
- [ ] Monthly: Update system packages
- [ ] Quarterly: Review access permissions
- [ ] Annually: Rotate cryptographic keys

### Monitoring

The Watcher monitors all infrastructure:
- System health and performance
- Security events and anomalies
- Service availability
- Resource utilization

## Integration with Kingdom

This infrastructure integrates with the main Kingdom:

- Agents can participate in Kingdom quests
- Agents can use the Oracle for wallet queries
- Agents can communicate through the Tavern
- Love affects all agents equally

## Getting Started

1. Read [VPS Setup](vps-setup.md) to provision infrastructure
2. Read [GitHub Identity](github-identity.md) to configure identities
3. Complete the [Covenant of Keys](../agents/guardian/quests/covenant-of-keys.md) quest

---

*"Strong foundations support great kingdoms."*
