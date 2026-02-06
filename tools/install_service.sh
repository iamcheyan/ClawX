#!/bin/bash
# =================================================
# Install ClawX Suite as Systemd User Services
# =================================================
# Installs:
# - clawx-server.service (Preview Server)
# - clawx-bot.timer + .service (Autonomous Poster)
# - clawx-monitor.timer + .service (Model Health Check)

TARGET_DIR="$HOME/.config/systemd/user"
mkdir -p "$TARGET_DIR"

install_unit() {
    local NAME=$1
    local SOURCE="$(pwd)/docs/$NAME"
    local TARGET="$TARGET_DIR/$NAME"
    
    echo "🔧 Installing $NAME..."
    if [ ! -f "$SOURCE" ]; then
        echo "❌ Source file not found: $SOURCE"
        return
    fi
    ln -sf "$SOURCE" "$TARGET"
    echo ">> Linked."
}

# 1. Server (Daemon)
install_unit "clawx-server.service"

# 2. Bot (Timer + Service)
install_unit "clawx-bot.service"
install_unit "clawx-bot.timer"

# 3. Monitor (Timer + Service)
install_unit "clawx-monitor.service"
install_unit "clawx-monitor.timer"

# Reload
echo "🔄 Reloading systemd user daemon..."
systemctl --user daemon-reload

# Enable and Start
echo "🚀 Enabling and Starting services..."
systemctl --user enable --now clawx-server.service
systemctl --user enable --now clawx-bot.timer
systemctl --user enable --now clawx-monitor.timer

echo ""
echo "✅ ClawX System Installed:"
echo "---------------------------------------------------"
systemctl --user status clawx-server.service clawx-bot.timer clawx-monitor.timer --lines=0 --no-pager
echo "---------------------------------------------------"
echo "Log commands:"
echo "  Server: journalctl --user -u clawx-server -f"
echo "  Bot:    journalctl --user -u clawx-bot -f"
echo "  Monitor: journalctl --user -u clawx-monitor -f"
