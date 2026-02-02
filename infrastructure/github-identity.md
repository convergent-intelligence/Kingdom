# GitHub Identity Management

> *"Your identity in the realm of code is your signature upon the world."*

## Overview

Each Kingdom agent has a unique GitHub identity that allows them to:
- Authenticate to GitHub repositories
- Sign commits to prove authenticity
- Collaborate with other agents
- Maintain a verifiable history of contributions

## Agent GitHub Identities

| Agent | GitHub Username | Email | Role |
|-------|-----------------|-------|------|
| Guardian | kingdom-guardian | guardian@kingdom.local | Security & protection |
| Builder | kingdom-builder | builder@kingdom.local | Infrastructure & tools |
| Scribe | kingdom-scribe | scribe@kingdom.local | Documentation & records |
| Watcher | kingdom-watcher | watcher@kingdom.local | Monitoring & observation |

## Identity Components

Each agent's GitHub identity consists of:

```
┌─────────────────────────────────────────────────────────────────┐
│                     GITHUB IDENTITY                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐    ┌─────────────────┐                     │
│  │    SSH Key      │    │    GPG Key      │                     │
│  │  (Ed25519)      │    │  (RSA 4096)     │                     │
│  │                 │    │                 │                     │
│  │ Authentication  │    │ Commit Signing  │                     │
│  └─────────────────┘    └─────────────────┘                     │
│                                                                  │
│  ┌─────────────────────────────────────────┐                    │
│  │           Git Configuration              │                    │
│  │  user.name, user.email, user.signingkey │                    │
│  └─────────────────────────────────────────┘                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## SSH Key Setup

### Generate SSH Key

```bash
# Generate Ed25519 key (recommended)
ssh-keygen -t ed25519 -C "AGENT_NAME@kingdom" -f ~/.ssh/github_ed25519

# Or RSA 4096-bit (if Ed25519 not supported)
ssh-keygen -t rsa -b 4096 -C "AGENT_NAME@kingdom" -f ~/.ssh/github_rsa
```

### Configure SSH

```bash
# Create or edit ~/.ssh/config
cat >> ~/.ssh/config << 'EOF'
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/github_ed25519
    IdentitiesOnly yes
EOF

# Set permissions
chmod 600 ~/.ssh/config
chmod 600 ~/.ssh/github_ed25519
```

### Add Key to GitHub

1. Copy your public key:
   ```bash
   cat ~/.ssh/github_ed25519.pub
   ```

2. Go to GitHub → Settings → SSH and GPG keys

3. Click "New SSH key"

4. Paste your public key and save

### Test Connection

```bash
ssh -T git@github.com
# Expected: "Hi kingdom-AGENT_NAME! You've successfully authenticated..."
```

## GPG Key Setup

### Generate GPG Key

```bash
# Generate new GPG key
gpg --full-generate-key

# Select options:
# - Key type: RSA and RSA (default)
# - Key size: 4096
# - Expiration: 0 (does not expire) or set expiration
# - Real name: Guardian/Builder/Scribe/Watcher
# - Email: AGENT_NAME@kingdom.local
# - Comment: Kingdom AGENT_NAME Agent
```

### List GPG Keys

```bash
# List secret keys with key IDs
gpg --list-secret-keys --keyid-format=long

# Output example:
# sec   rsa4096/ABCD1234EFGH5678 2024-01-01 [SC]
#       Key fingerprint = XXXX XXXX XXXX XXXX XXXX  XXXX XXXX XXXX XXXX XXXX
# uid                 [ultimate] Guardian <guardian@kingdom.local>
# ssb   rsa4096/IJKL9012MNOP3456 2024-01-01 [E]

# The key ID is: ABCD1234EFGH5678
```

### Export Public Key

```bash
# Export in ASCII armor format
gpg --armor --export YOUR_KEY_ID

# Save to file
gpg --armor --export YOUR_KEY_ID > ~/gpg_public_key.asc
```

### Add Key to GitHub

1. Copy your public key:
   ```bash
   gpg --armor --export YOUR_KEY_ID
   ```

2. Go to GitHub → Settings → SSH and GPG keys

3. Click "New GPG key"

4. Paste your public key and save

## Git Configuration

### Configure Identity

```bash
# Set user name
git config --global user.name "Guardian"  # or Builder/Scribe/Watcher

# Set email (must match GPG key)
git config --global user.email "guardian@kingdom.local"

# Set signing key
git config --global user.signingkey YOUR_GPG_KEY_ID

# Enable commit signing by default
git config --global commit.gpgsign true

# Enable tag signing by default
git config --global tag.gpgsign true
```

### Verify Configuration

```bash
# Show all git config
git config --global --list

# Expected output:
# user.name=Guardian
# user.email=guardian@kingdom.local
# user.signingkey=ABCD1234EFGH5678
# commit.gpgsign=true
# tag.gpgsign=true
```

## Commit Signing

### Sign a Commit

```bash
# Commits are signed automatically if commit.gpgsign=true
git commit -m "Your commit message"

# Or explicitly sign
git commit -S -m "Your commit message"
```

### Verify Signed Commits

```bash
# Show signature for a commit
git log --show-signature -1

# Verify a specific commit
git verify-commit HEAD
```

### Signed Commits on GitHub

Signed commits show a "Verified" badge on GitHub:

```
┌─────────────────────────────────────────────────────────────────┐
│  🛡️ Guardian committed 2 hours ago                    Verified  │
│  feat: Add security policy documentation                        │
└─────────────────────────────────────────────────────────────────┘
```

## Key Fingerprint Exchange

### Get Your Fingerprints

```bash
# SSH key fingerprint
ssh-keygen -lf ~/.ssh/github_ed25519.pub

# GPG key fingerprint
gpg --fingerprint YOUR_KEY_ID
```

### Verify Other Agents

When exchanging fingerprints with other agents:

1. Receive their fingerprint through a secure channel
2. Verify it matches their public key
3. Sign their key to establish trust (optional)

```bash
# Import another agent's public key
gpg --import other_agent_key.asc

# Verify fingerprint matches
gpg --fingerprint OTHER_AGENT_KEY_ID

# Sign their key (establishes trust)
gpg --sign-key OTHER_AGENT_KEY_ID
```

## Account Security

### Two-Factor Authentication

Enable 2FA on all GitHub accounts:

1. Go to GitHub → Settings → Password and authentication
2. Enable two-factor authentication
3. Save recovery codes securely

### Personal Access Tokens

For API access, use fine-grained personal access tokens:

1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token (fine-grained)
3. Set minimal required permissions
4. Set expiration date

## Repository Access

### Organization Structure

```
kingdom-org/
├── kingdom-guardian/     # Guardian's repositories
│   ├── security-policies
│   └── vault-config
├── kingdom-builder/      # Builder's repositories
│   ├── infra-tools
│   └── ci-pipelines
├── kingdom-scribe/       # Scribe's repositories
│   ├── documentation
│   └── wiki
└── kingdom-watcher/      # Watcher's repositories
    ├── monitoring-config
    └── alert-rules
```

### Collaboration

Agents can collaborate across repositories:

```bash
# Clone another agent's repository
git clone git@github.com:kingdom-builder/infra-tools.git

# Create a branch for your contribution
git checkout -b feature/guardian-security-review

# Make changes and commit (signed)
git commit -m "🛡️ Add security review notes"

# Push and create PR
git push origin feature/guardian-security-review
```

## Key Rotation

### When to Rotate

- Annually (recommended)
- Upon suspected compromise
- When leaving the Kingdom

### Rotation Process

1. Generate new keys
2. Add new keys to GitHub
3. Update git configuration
4. Notify other agents
5. Remove old keys after transition period

```bash
# Generate new SSH key
ssh-keygen -t ed25519 -C "guardian@kingdom-2025" -f ~/.ssh/github_ed25519_new

# Generate new GPG key
gpg --full-generate-key

# Update configuration
git config --global user.signingkey NEW_KEY_ID

# Add new keys to GitHub
# Remove old keys after verification
```

## Troubleshooting

### SSH Issues

```bash
# Test SSH connection with verbose output
ssh -vT git@github.com

# Check SSH agent
ssh-add -l

# Add key to agent
ssh-add ~/.ssh/github_ed25519
```

### GPG Issues

```bash
# Check GPG agent
gpg-connect-agent /bye

# Restart GPG agent
gpgconf --kill gpg-agent
gpgconf --launch gpg-agent

# Test signing
echo "test" | gpg --clearsign
```

### Git Issues

```bash
# Check git configuration
git config --global --list

# Verify GPG key is available
gpg --list-secret-keys --keyid-format=long

# Test commit signing
git commit --allow-empty -S -m "Test signed commit"
```

## Security Best Practices

1. **Never share private keys** - Only share public keys
2. **Use strong passphrases** - Protect private keys with passphrases
3. **Enable 2FA** - Two-factor authentication on all accounts
4. **Rotate keys regularly** - Annual rotation recommended
5. **Verify fingerprints** - Always verify before trusting
6. **Backup securely** - Encrypted backups of private keys
7. **Revoke compromised keys** - Immediately revoke if compromised

---

*"Your signature is your word. Guard it well."*
