# VPS Setup Guide

> *"A subkingdom must be built on solid ground."*

## Overview

This guide covers provisioning and configuring VPS instances for the four Kingdom agents. Each agent requires a dedicated VPS that serves as their subkingdom.

## VPS Requirements

### Minimum Specifications

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 1 vCPU | 2 vCPU |
| RAM | 1 GB | 2 GB |
| Storage | 20 GB SSD | 40 GB SSD |
| Network | 1 Gbps | 1 Gbps |
| OS | Debian 12 | Debian 12 |

### Agent-Specific Requirements

| Agent | Additional Requirements |
|-------|------------------------|
| Guardian | Extra storage for logs, security tools |
| Builder | More CPU/RAM for builds, Docker storage |
| Scribe | Storage for documentation archives |
| Watcher | Storage for metrics, time-series database |

## VPS Allocation

| Agent | VPS ID | Hostname | Purpose |
|-------|--------|----------|---------|
| Guardian | VPS-1 | guardian.kingdom.local | Security operations |
| Builder | VPS-2 | builder.kingdom.local | Development environment |
| Scribe | VPS-3 | scribe.kingdom.local | Documentation hosting |
| Watcher | VPS-4 | watcher.kingdom.local | Monitoring infrastructure |

## Provisioning Steps

### Step 1: Create VPS Instance

Using your preferred cloud provider, create a VPS with:
- Debian 12 (Bookworm)
- SSH key authentication enabled
- Firewall allowing SSH (port 22)

### Step 2: Initial Access

```bash
# SSH into the new VPS as root
ssh root@VPS_IP_ADDRESS

# Update system packages
apt update && apt upgrade -y

# Install essential packages
apt install -y \
    git \
    curl \
    wget \
    vim \
    htop \
    ufw \
    fail2ban \
    gnupg \
    sudo
```

### Step 3: Create Agent User

```bash
# Create the agent user (replace AGENT_NAME with guardian/builder/scribe/watcher)
useradd -m -s /bin/bash AGENT_NAME

# Add to sudo group
usermod -aG sudo AGENT_NAME

# Set up SSH directory
mkdir -p /home/AGENT_NAME/.ssh
chmod 700 /home/AGENT_NAME/.ssh
chown AGENT_NAME:AGENT_NAME /home/AGENT_NAME/.ssh
```

### Step 4: Configure SSH

```bash
# Edit SSH configuration
vim /etc/ssh/sshd_config

# Recommended settings:
# PermitRootLogin no
# PasswordAuthentication no
# PubkeyAuthentication yes
# AllowUsers AGENT_NAME

# Restart SSH
systemctl restart sshd
```

### Step 5: Configure Firewall

```bash
# Enable UFW
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw enable

# Agent-specific ports (add as needed)
# Guardian: none additional
# Builder: 8080 (CI/CD), 2375 (Docker)
# Scribe: 80, 443 (web server)
# Watcher: 9090 (Prometheus), 3000 (Grafana)
```

### Step 6: Configure Fail2ban

```bash
# Create local configuration
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 1h
findtime = 10m
maxretry = 5

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
EOF

# Restart fail2ban
systemctl restart fail2ban
```

## Agent-Specific Setup

### Guardian (VPS-1)

```bash
# Install security tools
apt install -y \
    ossec-hids \
    rkhunter \
    lynis \
    auditd

# Create security directories
mkdir -p /home/guardian/{vault,logs,policies}
chown -R guardian:guardian /home/guardian/
```

### Builder (VPS-2)

```bash
# Install development tools
apt install -y \
    docker.io \
    docker-compose \
    build-essential \
    python3-pip \
    nodejs \
    npm

# Add builder to docker group
usermod -aG docker builder

# Create development directories
mkdir -p /home/builder/{projects,tools,templates}
chown -R builder:builder /home/builder/
```

### Scribe (VPS-3)

```bash
# Install documentation tools
apt install -y \
    nginx \
    python3-pip \
    pandoc

# Install MkDocs
pip3 install mkdocs mkdocs-material

# Create documentation directories
mkdir -p /home/scribe/{archives,drafts,published}
mkdir -p /var/www/docs
chown -R scribe:scribe /home/scribe/ /var/www/docs/
```

### Watcher (VPS-4)

```bash
# Install monitoring tools
apt install -y \
    prometheus \
    prometheus-node-exporter \
    grafana

# Create monitoring directories
mkdir -p /home/watcher/{dashboards,alerts,reports}
chown -R watcher:watcher /home/watcher/

# Enable services
systemctl enable prometheus grafana-server
systemctl start prometheus grafana-server
```

## SSH Key Setup

Each agent needs SSH keys for:
1. VPS access (from external systems)
2. GitHub authentication

### Generate VPS Access Key

```bash
# On the management system, generate key for VPS access
ssh-keygen -t ed25519 -C "AGENT_NAME@vps" -f ~/.ssh/AGENT_NAME_vps

# Copy public key to VPS
ssh-copy-id -i ~/.ssh/AGENT_NAME_vps.pub AGENT_NAME@VPS_IP
```

### Generate GitHub Key (on VPS)

```bash
# SSH into VPS as agent
ssh AGENT_NAME@VPS_IP

# Generate GitHub key
ssh-keygen -t ed25519 -C "AGENT_NAME@kingdom" -f ~/.ssh/github_ed25519

# Configure SSH for GitHub
cat >> ~/.ssh/config << 'EOF'
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/github_ed25519
EOF

chmod 600 ~/.ssh/config
```

## Verification Checklist

After setup, verify each VPS:

- [ ] SSH access works with key authentication
- [ ] Root login is disabled
- [ ] Password authentication is disabled
- [ ] Firewall is active and configured
- [ ] Fail2ban is running
- [ ] Agent user has sudo access
- [ ] Agent-specific tools are installed
- [ ] GitHub SSH key is generated

## Maintenance

### Regular Updates

```bash
# Weekly update script
apt update && apt upgrade -y
apt autoremove -y
```

### Log Rotation

```bash
# Ensure logrotate is configured
cat > /etc/logrotate.d/kingdom << 'EOF'
/home/*/logs/*.log {
    weekly
    rotate 4
    compress
    delaycompress
    missingok
    notifempty
}
EOF
```

### Backup

```bash
# Backup agent home directories
tar -czf /backup/AGENT_NAME-$(date +%Y%m%d).tar.gz /home/AGENT_NAME/
```

## Troubleshooting

### SSH Connection Issues

```bash
# Check SSH service status
systemctl status sshd

# Check firewall rules
ufw status verbose

# Check fail2ban status
fail2ban-client status sshd
```

### Permission Issues

```bash
# Fix home directory permissions
chown -R AGENT_NAME:AGENT_NAME /home/AGENT_NAME/
chmod 700 /home/AGENT_NAME/
chmod 700 /home/AGENT_NAME/.ssh/
chmod 600 /home/AGENT_NAME/.ssh/*
```

## Security Hardening

### Additional Measures

```bash
# Disable unused services
systemctl disable bluetooth
systemctl disable cups

# Configure automatic security updates
apt install -y unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades

# Set up audit logging
auditctl -e 1
```

## Network Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        INTERNET                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ SSH (22)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         FIREWALL                                 │
│                    (UFW on each VPS)                            │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
   ┌─────────┐          ┌─────────┐          ┌─────────┐
   │  VPS-1  │          │  VPS-2  │          │  VPS-3  │
   │Guardian │          │ Builder │          │  Scribe │
   │  :22    │          │:22,8080 │          │:22,80,  │
   │         │          │  :2375  │          │   443   │
   └─────────┘          └─────────┘          └─────────┘
                              │
                              ▼
                        ┌─────────┐
                        │  VPS-4  │
                        │ Watcher │
                        │:22,9090 │
                        │  :3000  │
                        └─────────┘
```

---

*"A well-built foundation supports all that rises above it."*
