#!/bin/bash
# Kingdom Bot VPS Installation Script
# ====================================
# Installs and configures a Kingdom bot on a fresh VPS
#
# Usage: ./install.sh <bot_id>
# Example: ./install.sh alpha

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
KINGDOM_USER="kingdom"
KINGDOM_HOME="/opt/kingdom"
KINGDOM_REPO="https://github.com/your-org/kingdom-bots.git"
PYTHON_VERSION="3.11"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
    fi
}

# Validate bot ID
validate_bot_id() {
    local bot_id="$1"
    case "$bot_id" in
        alpha|beta|gamma|delta)
            log_info "Installing bot: $bot_id"
            ;;
        *)
            log_error "Invalid bot ID. Must be one of: alpha, beta, gamma, delta"
            ;;
    esac
}

# Install system dependencies
install_dependencies() {
    log_info "Updating system packages..."
    apt-get update -qq
    
    log_info "Installing system dependencies..."
    apt-get install -y -qq \
        python${PYTHON_VERSION} \
        python${PYTHON_VERSION}-venv \
        python${PYTHON_VERSION}-dev \
        python3-pip \
        git \
        curl \
        wget \
        htop \
        vim \
        sudo \
        systemd \
        ca-certificates \
        gnupg \
        lsb-release
    
    log_success "System dependencies installed"
}

# Install Tailscale
install_tailscale() {
    log_info "Installing Tailscale..."
    
    if command -v tailscale &> /dev/null; then
        log_warning "Tailscale already installed"
        return
    fi
    
    curl -fsSL https://tailscale.com/install.sh | sh
    
    log_success "Tailscale installed"
    log_warning "Run 'sudo tailscale up' to authenticate"
}

# Create kingdom user
create_user() {
    log_info "Creating kingdom user..."
    
    if id "$KINGDOM_USER" &>/dev/null; then
        log_warning "User $KINGDOM_USER already exists"
    else
        useradd -r -m -d "$KINGDOM_HOME" -s /bin/bash "$KINGDOM_USER"
        log_success "User $KINGDOM_USER created"
    fi
    
    # Add to sudo group for service management
    usermod -aG sudo "$KINGDOM_USER"
    
    # Allow passwordless sudo for specific commands
    cat > /etc/sudoers.d/kingdom << 'EOF'
# Kingdom bot sudo permissions
kingdom ALL=(ALL) NOPASSWD: /bin/systemctl status *
kingdom ALL=(ALL) NOPASSWD: /bin/systemctl start *
kingdom ALL=(ALL) NOPASSWD: /bin/systemctl stop *
kingdom ALL=(ALL) NOPASSWD: /bin/systemctl restart *
kingdom ALL=(ALL) NOPASSWD: /bin/systemctl enable *
kingdom ALL=(ALL) NOPASSWD: /bin/systemctl disable *
kingdom ALL=(ALL) NOPASSWD: /sbin/shutdown
kingdom ALL=(ALL) NOPASSWD: /sbin/reboot
kingdom ALL=(ALL) NOPASSWD: /bin/journalctl
EOF
    
    chmod 440 /etc/sudoers.d/kingdom
    log_success "Sudo permissions configured"
}

# Setup directory structure
setup_directories() {
    log_info "Setting up directory structure..."
    
    mkdir -p "$KINGDOM_HOME"
    mkdir -p /var/log/kingdom
    mkdir -p /etc/kingdom
    
    chown -R "$KINGDOM_USER:$KINGDOM_USER" "$KINGDOM_HOME"
    chown -R "$KINGDOM_USER:$KINGDOM_USER" /var/log/kingdom
    chown -R "$KINGDOM_USER:$KINGDOM_USER" /etc/kingdom
    
    log_success "Directories created"
}

# Clone repository
clone_repo() {
    log_info "Cloning Kingdom repository..."
    
    if [[ -d "$KINGDOM_HOME/kingdom-bots" ]]; then
        log_warning "Repository already exists, pulling latest..."
        cd "$KINGDOM_HOME/kingdom-bots"
        sudo -u "$KINGDOM_USER" git pull
    else
        sudo -u "$KINGDOM_USER" git clone "$KINGDOM_REPO" "$KINGDOM_HOME/kingdom-bots"
    fi
    
    log_success "Repository cloned"
}

# Setup Python virtual environment
setup_venv() {
    log_info "Setting up Python virtual environment..."
    
    cd "$KINGDOM_HOME/kingdom-bots"
    
    if [[ ! -d "venv" ]]; then
        sudo -u "$KINGDOM_USER" python${PYTHON_VERSION} -m venv venv
    fi
    
    sudo -u "$KINGDOM_USER" ./venv/bin/pip install --upgrade pip
    sudo -u "$KINGDOM_USER" ./venv/bin/pip install -r requirements.txt
    
    log_success "Virtual environment configured"
}

# Setup systemd service
setup_service() {
    local bot_id="$1"
    
    log_info "Setting up systemd service for $bot_id..."
    
    # Copy service template
    cp "$KINGDOM_HOME/kingdom-bots/kingdom/deploy/systemd/kingdom-bot.service" \
       "/etc/systemd/system/kingdom-${bot_id}.service"
    
    # Replace placeholders
    sed -i "s/{{BOT_ID}}/${bot_id}/g" "/etc/systemd/system/kingdom-${bot_id}.service"
    sed -i "s|{{KINGDOM_HOME}}|${KINGDOM_HOME}|g" "/etc/systemd/system/kingdom-${bot_id}.service"
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable service
    systemctl enable "kingdom-${bot_id}.service"
    
    log_success "Systemd service configured"
}

# Create environment file
create_env_file() {
    local bot_id="$1"
    
    log_info "Creating environment file..."
    
    local env_file="/etc/kingdom/${bot_id}.env"
    
    if [[ -f "$env_file" ]]; then
        log_warning "Environment file already exists at $env_file"
        return
    fi
    
    cat > "$env_file" << EOF
# Kingdom Bot ${bot_id^} Environment Configuration
# Generated by install.sh on $(date)

# Discord Bot Token (REQUIRED)
KINGDOM_${bot_id^^}_TOKEN=your_discord_bot_token_here

# Discord Guild ID (optional, for faster command sync)
KINGDOM_${bot_id^^}_GUILD_ID=

# Admin User IDs (comma-separated)
KINGDOM_ADMIN_USER_1=
KINGDOM_ADMIN_USER_2=

# Admin Role ID
KINGDOM_ADMIN_ROLE=
EOF
    
    chmod 600 "$env_file"
    chown "$KINGDOM_USER:$KINGDOM_USER" "$env_file"
    
    log_success "Environment file created at $env_file"
    log_warning "Edit $env_file to add your Discord bot token"
}

# Print completion message
print_completion() {
    local bot_id="$1"
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Kingdom Bot ${bot_id^} Installation Complete${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Configure Tailscale:"
    echo "   sudo tailscale up --hostname=${bot_id}"
    echo ""
    echo "2. Edit the environment file:"
    echo "   sudo nano /etc/kingdom/${bot_id}.env"
    echo ""
    echo "3. Start the bot:"
    echo "   sudo systemctl start kingdom-${bot_id}"
    echo ""
    echo "4. Check status:"
    echo "   sudo systemctl status kingdom-${bot_id}"
    echo ""
    echo "5. View logs:"
    echo "   sudo journalctl -u kingdom-${bot_id} -f"
    echo ""
}

# Main installation function
main() {
    if [[ $# -lt 1 ]]; then
        echo "Usage: $0 <bot_id>"
        echo "Bot IDs: alpha, beta, gamma, delta"
        exit 1
    fi
    
    local bot_id="$1"
    
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  Kingdom Bot Installation Script${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    check_root
    validate_bot_id "$bot_id"
    install_dependencies
    install_tailscale
    create_user
    setup_directories
    clone_repo
    setup_venv
    setup_service "$bot_id"
    create_env_file "$bot_id"
    print_completion "$bot_id"
}

# Run main function
main "$@"
