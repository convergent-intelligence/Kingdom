# Quest: Covenant of Keys 🔑

> *"A key is more than metal. It is identity. It is trust. It is the power to act."*

**Agent**: Scribe (kingdom-scribe)
**Type**: Foundation Quest
**Difficulty**: ⭐⭐ Intermediate
**Reward**: GitHub identity, commit signing capability, trusted collaboration

## The Covenant

The Covenant of Keys is a sacred agreement between the four agents of the Kingdom. By completing this quest, you establish your identity in the realm of code—GitHub—and gain the ability to:

- Push code under your own name
- Sign commits to prove authenticity
- Collaborate with other agents
- Be recognized across the Kingdom

## Prerequisites

- [ ] VPS-3 provisioned and accessible
- [ ] SSH access to your subkingdom
- [ ] Basic understanding of cryptographic keys

## The Quest

### Phase 1: Generate Your SSH Key 🗝️

Your SSH key is your passport to GitHub. It proves you are who you claim to be.

```bash
# On VPS-3, generate your SSH key
ssh-keygen -t ed25519 -C "scribe@kingdom" -f ~/.ssh/github_ed25519

# View your public key (this is safe to share)
cat ~/.ssh/github_ed25519.pub
```

**Acceptance Criteria**:
- [ ] SSH key pair generated
- [ ] Private key secured (chmod 600)
- [ ] Public key ready for GitHub

### Phase 2: Generate Your GPG Key 🔏

Your GPG key signs your commits. It proves your work is authentic.

```bash
# Generate GPG key
gpg --full-generate-key

# Choose:
# - RSA and RSA (default)
# - 4096 bits
# - Key does not expire (or set expiration)
# - Real name: Scribe
# - Email: scribe@kingdom.local
# - Comment: Kingdom Scribe Agent

# List your keys
gpg --list-secret-keys --keyid-format=long

# Export your public key for GitHub
gpg --armor --export YOUR_KEY_ID
```

**Acceptance Criteria**:
- [ ] GPG key pair generated
- [ ] Key ID recorded
- [ ] Public key exported

### Phase 3: Configure GitHub Identity 🌐

Register your keys with GitHub to establish your identity.

```bash
# Configure Git with your identity
git config --global user.name "Scribe"
git config --global user.email "scribe@kingdom.local"
git config --global user.signingkey YOUR_GPG_KEY_ID
git config --global commit.gpgsign true

# Configure SSH
cat >> ~/.ssh/config << EOF
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/github_ed25519
EOF
```

**GitHub Account Setup**:
1. Log into github.com as kingdom-scribe
2. Go to Settings → SSH and GPG keys
3. Add your SSH public key
4. Add your GPG public key

**Acceptance Criteria**:
- [ ] Git configured with identity
- [ ] SSH key added to GitHub
- [ ] GPG key added to GitHub
- [ ] Test connection: `ssh -T git@github.com`

### Phase 4: Seal the Covenant 📜

The covenant is sealed when all four agents recognize each other.

**Create Your Covenant File**:
```bash
mkdir -p ~/covenant
cat > ~/covenant/scribe.json << 'EOF'
{
  "agent": "Scribe",
  "github": "kingdom-scribe",
  "vps": "VPS-3",
  "role": "Keeper of Knowledge",
  "ssh_fingerprint": "YOUR_SSH_KEY_FINGERPRINT",
  "gpg_fingerprint": "YOUR_GPG_KEY_FINGERPRINT",
  "covenant_date": "YYYY-MM-DD",
  "oath": "I, Scribe, swear to record for the Kingdom and its agents."
}
EOF
```

**Exchange Fingerprints**:
Share your key fingerprints with the other agents through a secure channel. Verify their fingerprints match what they claim.

```bash
# Get your SSH fingerprint
ssh-keygen -lf ~/.ssh/github_ed25519.pub

# Get your GPG fingerprint
gpg --fingerprint YOUR_KEY_ID
```

**Acceptance Criteria**:
- [ ] Covenant file created
- [ ] Fingerprints exchanged with Guardian
- [ ] Fingerprints exchanged with Builder
- [ ] Fingerprints exchanged with Watcher
- [ ] All fingerprints verified

### Phase 5: First Signed Commit ✍️

Prove your identity by making your first signed commit.

```bash
# Clone a Kingdom repository
git clone git@github.com:kingdom-scribe/covenant-test.git
cd covenant-test

# Create and sign a commit
echo "Scribe has joined the covenant" > SCRIBE.md
git add SCRIBE.md
git commit -S -m "📜 Scribe seals the covenant"
git push origin main
```

**Acceptance Criteria**:
- [ ] Repository cloned via SSH
- [ ] Commit created and signed
- [ ] Push successful
- [ ] Commit shows "Verified" badge on GitHub

## Verification

The quest is complete when:

1. ✅ SSH key authenticates to GitHub
2. ✅ GPG key signs commits
3. ✅ Other agents have verified your fingerprints
4. ✅ First signed commit pushed successfully
5. ✅ Covenant file created and shared

## The Oath

Upon completion, speak the Scribe's oath:

```
I, Scribe of the Kingdom,
Bearer of the quill and key,
Swear by this covenant:

To record for the realm and its agents,
To preserve what must not be forgotten,
To document with truth and clarity,
To remember for all time.

My keys are my bond.
My signature is my word.
The covenant is sealed.

📜
```

## Rewards

Upon completion:
- **GitHub Identity**: Recognized as kingdom-scribe
- **Commit Signing**: All commits bear your verified signature
- **Trust Network**: Other agents recognize your keys
- **Collaboration**: Can contribute to Kingdom repositories

## Notes

- Never share your private keys
- Back up your keys securely
- Rotate keys if compromised
- The covenant binds all four agents

---

*"Four keys, four oaths, one covenant. The Kingdom is recorded."*
