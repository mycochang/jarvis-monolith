#!/bin/bash
# Installation script for Jarvis Monolith
set -e

echo "🚀 Installing Jarvis Monolith (Compose/Menu Dictation)"
echo "---------------------------------------------------"

# 1. Input Group Check
if ! groups | grep -q "\binput\b"; then
    echo "⚠️  Adding user to 'input' group to read keyboard events."
    echo "   (You will be prompted for sudo password)"
    sudo usermod -aG input $USER
    echo "🛑 IMPORTANT: You must LOG OUT and LOG BACK IN for the group change to take effect!"
else
    echo "✅ User is already in the 'input' group."
fi

# 2. System Dependencies
echo "📦 Checking system dependencies (ydotool, libnotify)..."
if ! command -v ydotool &> /dev/null || ! command -v notify-send &> /dev/null; then
    echo "   Installing ydotool and libnotify via pacman..."
    sudo pacman -S --needed --noconfirm ydotool libnotify
else
    echo "✅ System dependencies installed."
fi

echo "⚙️  Ensuring ydotool daemon is running..."
if systemctl --user cat ydotool.service >/dev/null 2>&1; then
    systemctl --user enable --now ydotool.service
else
    sudo systemctl enable --now ydotoold.service
fi

# 3. Python Environment
echo "🐍 Syncing Python dependencies via uv..."
cd "$(dirname "$0")"
uv sync

# 4. Systemd Setup
echo "🛠️  Configuring user background service..."
mkdir -p ~/.config/systemd/user/
cp systemd/jarvis.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now jarvis.service

echo "---------------------------------------------------"
echo "✅ Installation complete! The daemon is running in the background."
echo "🎙️  Hold the Compose/Menu key anywhere to dictate."
