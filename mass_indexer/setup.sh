#!/bin/bash
# ============================================================
# 🎵 GROOVIA MASS INDEXER — Server Setup Script
# Run this ONCE on a fresh Ubuntu 22.04 VPS/DigitalOcean Droplet
# 
# Usage:
#   chmod +x setup.sh && sudo ./setup.sh
# ============================================================

set -e  # Exit on any error
echo ""
echo "╔═══════════════════════════════════════════╗"
echo "║   🎵 GROOVIA MASS INDEXER SETUP           ║"
echo "╚═══════════════════════════════════════════╝"
echo ""

# ── Step 1: System update ─────────────────────────────────────────────────────
echo "📦 [1/7] Updating system packages..."
apt-get update -qq
apt-get upgrade -y -qq

# ── Step 2: Install system dependencies ──────────────────────────────────────
echo "🔧 [2/7] Installing system dependencies..."
apt-get install -y -qq \
    python3 \
    python3-pip \
    python3-venv \
    ffmpeg \
    git \
    tmux \
    htop \
    wget \
    curl \
    unzip

echo "   ✅ ffmpeg: $(ffmpeg -version 2>&1 | head -1)"
echo "   ✅ Python: $(python3 --version)"

# ── Step 3: Create project directory ─────────────────────────────────────────
echo "📁 [3/7] Setting up project directory..."
PROJECT_DIR="/root/groovia_indexer"
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# ── Step 4: Create Python virtual environment ─────────────────────────────────
echo "🐍 [4/7] Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip -q

# ── Step 5: Install Python dependencies ──────────────────────────────────────
echo "📦 [5/7] Installing Python packages..."
pip install -q \
    "yt-dlp>=2024.1.0" \
    "ytmusicapi>=1.7.0" \
    "pymongo[srv]>=4.6.0" \
    "dnspython>=2.4.0" \
    "requests>=2.31.0" \
    "rich>=13.7.0" \
    "python-dotenv>=1.0.1"

echo "   ✅ yt-dlp: $(yt-dlp --version)"

# ── Step 6: Create temp directory ─────────────────────────────────────────────
echo "📂 [6/7] Creating temp directory..."
mkdir -p /tmp/groovia_dl
chmod 777 /tmp/groovia_dl

# ── Step 7: Copy files ────────────────────────────────────────────────────────
echo "📋 [7/7] Setup complete!"
echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║   ✅ SETUP COMPLETE — Next Steps:                             ║"
echo "╠═══════════════════════════════════════════════════════════════╣"
echo "║                                                               ║"
echo "║  1. Upload your mass_indexer/ folder to: /root/groovia_indexer║"
echo "║     (use SCP, SFTP, or git clone)                             ║"
echo "║                                                               ║"
echo "║  2. Activate virtual environment:                             ║"
echo "║     source /root/groovia_indexer/venv/bin/activate            ║"
echo "║                                                               ║"
echo "║  3. Test all connections:                                     ║"
echo "║     cd /root/groovia_indexer && python run.py test            ║"
echo "║                                                               ║"
echo "║  4. Start the indexer in background (tmux):                   ║"
echo "║     tmux new-session -d -s groovia 'python run.py run'        ║"
echo "║                                                               ║"
echo "║  5. Watch progress:                                           ║"
echo "║     tmux attach -t groovia                                    ║"
echo "║     (Press Ctrl+B then D to detach — keeps running!)          ║"
echo "║                                                               ║"
echo "║  6. Check stats anytime:                                      ║"
echo "║     python run.py stats                                       ║"
echo "║                                                               ║"
echo "║  7. If server reboots, restart with:                          ║"
echo "║     tmux new-session -d -s groovia 'python run.py retry'      ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
