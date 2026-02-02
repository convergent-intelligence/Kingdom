# 👑 Kingdom Discord Bot Infrastructure

A fleet of autonomous Discord bots managing Tailscale-connected VPS servers. Each bot (Alpha, Beta, Gamma, Delta) operates independently on its designated server, providing remote monitoring, control, and file management capabilities through Discord slash commands.

## 🏗️ Architecture

```
                              ┌─────────────────────────────────────────────────────────────┐
                              │                     DISCORD                                  │
                              │                                                              │
                              │    ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
                              │    │  /status │  │  /exec   │  │  /logs   │  │  /health │  │
                              │    └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
                              └─────────┼─────────────┼─────────────┼─────────────┼────────┘
                                        │             │             │             │
                    ┌───────────────────┴─────────────┴─────────────┴─────────────┴───────────────────┐
                    │                              TAILSCALE MESH                                      │
                    │                           (Encrypted WireGuard)                                  │
                    └───────────────────┬─────────────┬─────────────┬─────────────┬───────────────────┘
                                        │             │             │             │
              ┌─────────────────────────┼─────────────┼─────────────┼─────────────┼─────────────────────────┐
              │                         │             │             │             │                         │
    ┌─────────▼─────────┐     ┌─────────▼─────────┐  ┌▼─────────────▼┐  ┌─────────▼─────────┐              │
    │   VPS 1 (Alpha)   │     │   VPS 2 (Beta)    │  │  VPS 3 (Gamma) │  │   VPS 4 (Delta)   │              │
    │   ═══════════     │     │   ═══════════     │  │  ═══════════   │  │   ═══════════     │              │
    │                   │     │                   │  │                │  │                   │              │
    │  ┌─────────────┐  │     │  ┌─────────────┐  │  │ ┌─────────────┐│  │  ┌─────────────┐  │              │
    │  │ Kingdom Bot │  │     │  │ Kingdom Bot │  │  │ │ Kingdom Bot ││  │  │ Kingdom Bot │  │              │
    │  │   (Alpha)   │  │     │  │   (Beta)    │  │  │ │   (Gamma)   ││  │  │   (Delta)   │  │              │
    │  └──────┬──────┘  │     │  └──────┬──────┘  │  │ └──────┬──────┘│  │  └──────┬──────┘  │              │
    │         │         │     │         │         │  │        │       │  │         │         │              │
    │  ┌──────▼──────┐  │     │  ┌──────▼──────┐  │  │ ┌──────▼──────┐│  │  ┌──────▼──────┐  │              │
    │  │   System    │  │     │  │   System    │  │  │ │   System    ││  │  │   System    │  │              │
    │  │  Services   │  │     │  │  Services   │  │  │ │  Services   ││  │  │  Services   │  │              │
    │  └─────────────┘  │     │  └─────────────┘  │  │ └─────────────┘│  │  └─────────────┘  │              │
    │                   │     │                   │  │                │  │                   │              │
    │   US-EAST         │     │   US-WEST         │  │   EU-WEST      │  │   AP-SOUTHEAST    │              │
    └───────────────────┘     └───────────────────┘  └────────────────┘  └───────────────────┘              │
              │                                                                                             │
              └─────────────────────────────────────────────────────────────────────────────────────────────┘
```

## ✨ Features

### 🔍 Monitoring Commands
- `/status` - Full system status (CPU, memory, disk, network, Tailscale)
- `/health` - Quick health check with latency and uptime
- `/metrics` - Detailed system metrics and top processes
- `/tailscale` - Tailscale network status and peer list
- `/ping <host>` - Network connectivity test

### 🎮 Control Commands
- `/exec <command>` - Execute shell commands (with safety checks)
- `/service <name> <action>` - Manage systemd services
- `/reboot [delay]` - Reboot server with confirmation
- `/shutdown [delay]` - Shutdown server with confirmation
- `/cancel-shutdown` - Cancel scheduled shutdown/reboot

### 📁 File Commands
- `/ls <path>` - List directory contents
- `/cat <file>` - Display file contents
- `/tail <file> [lines]` - Show last lines of a file
- `/logs [service]` - View system or service logs
- `/find <path> <pattern>` - Search for files

## 📦 Project Structure

```
kingdom/
├── core/                       # Shared framework
│   ├── __init__.py
│   ├── bot_base.py            # Base bot class with lifecycle management
│   ├── config.py              # YAML + environment configuration
│   ├── utils/
│   │   ├── system.py          # psutil-based system monitoring
│   │   └── network.py         # Tailscale and network utilities
│   └── cogs/
│       ├── monitoring.py      # /status, /health, /metrics
│       ├── control.py         # /exec, /service, /reboot
│       └── files.py           # /ls, /cat, /tail, /logs
│
├── bots/                       # Bot instances
│   ├── alpha/                  # VPS 1 - Primary
│   │   ├── main.py
│   │   ├── config.yaml
│   │   └── cogs/              # Alpha-specific extensions
│   ├── beta/                   # VPS 2 - Secondary
│   ├── gamma/                  # VPS 3 - Worker
│   └── delta/                  # VPS 4 - Worker
│
├── deploy/                     # Deployment tools
│   ├── install.sh             # VPS installation script
│   ├── systemd/
│   │   └── kingdom-bot.service
│   └── ansible/
│       ├── deploy-bots.yml
│       ├── inventory.yml.example
│       └── templates/
│
├── requirements.txt
├── pyproject.toml
├── .env.example
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Discord Bot Token (create at [Discord Developer Portal](https://discord.com/developers/applications))
- VPS with Tailscale installed

### Local Development

```bash
# Clone the repository
git clone https://github.com/your-org/kingdom-bots.git
cd kingdom-bots

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Discord bot token

# Run a bot locally
python -m kingdom.bots.alpha.main
```

### VPS Deployment

#### Option 1: Installation Script

```bash
# On your VPS (as root)
curl -fsSL https://raw.githubusercontent.com/your-org/kingdom-bots/main/kingdom/deploy/install.sh | bash -s alpha
```

#### Option 2: Ansible

```bash
# On your control machine
cd kingdom/deploy/ansible
cp inventory.yml.example inventory.yml
# Edit inventory.yml with your server details

ansible-playbook -i inventory.yml deploy-bots.yml
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `KINGDOM_ALPHA_TOKEN` | Discord bot token for Alpha | Yes |
| `KINGDOM_ALPHA_GUILD_ID` | Guild ID for fast command sync | No |
| `KINGDOM_ADMIN_USER_1` | Admin user Discord ID | No |
| `KINGDOM_ADMIN_USER_2` | Admin user Discord ID | No |
| `KINGDOM_ADMIN_ROLE` | Admin role Discord ID | No |

### Bot Configuration (config.yaml)

```yaml
bot_id: alpha
bot_name: "Kingdom Alpha"

token: "${KINGDOM_ALPHA_TOKEN}"
guild_id: "${KINGDOM_ALPHA_GUILD_ID:-}"

logging:
  level: INFO
  file: /var/log/kingdom/alpha.log

permissions:
  admin_users:
    - "123456789012345678"
  admin_roles:
    - "987654321098765432"

server:
  tailscale_hostname: alpha
  role: primary
  region: us-east
```

## 🔒 Security

### Permission System
- Commands require admin permissions (configurable user/role IDs)
- Server administrators automatically have access
- Dangerous commands require confirmation

### Command Safety
- Blocked dangerous patterns (rm -rf /, fork bombs, etc.)
- File access restricted to allowed directories
- Command execution timeout limits
- Output truncation for large responses

### Systemd Hardening
- Runs as dedicated `kingdom` user
- Read-only filesystem access
- Private /tmp
- Memory and CPU limits
- No new privileges

## 🛠️ Development

### Adding Custom Cogs

Create a new cog in `bots/<bot_id>/cogs/`:

```python
# bots/alpha/cogs/custom.py
import discord
from discord import app_commands
from discord.ext import commands

class CustomCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="custom", description="Custom command")
    async def custom_command(self, interaction: discord.Interaction):
        await interaction.response.send_message("Hello from Alpha!")

async def setup(bot):
    await bot.add_cog(CustomCog(bot))
```

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=kingdom
```

## 📊 Monitoring

### Systemd Service

```bash
# Check status
sudo systemctl status kingdom-alpha

# View logs
sudo journalctl -u kingdom-alpha -f

# Restart
sudo systemctl restart kingdom-alpha
```

### Health Endpoints

Each bot exposes health status via the `/health` command, returning:
- Bot status (healthy/unhealthy)
- Latency
- Uptime
- Connected guilds

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [discord.py](https://github.com/Rapptz/discord.py) - Discord API wrapper
- [Tailscale](https://tailscale.com/) - Mesh VPN
- [psutil](https://github.com/giampaolo/psutil) - System monitoring

---

**Kingdom** - Autonomous server management through Discord 👑
