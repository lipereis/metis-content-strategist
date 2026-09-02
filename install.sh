#!/bin/bash
# install.sh — Content Strategist Agent Installer
# Run: ./install.sh

set -e  # Exit on error

echo "📦 Content Strategist Agent — Installer"
echo "======================================="
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "🐍 Python version: $PYTHON_VERSION"

# Check if version >= 3.10
MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 10 ]); then
    echo "❌ Python 3.10+ required. Found $PYTHON_VERSION"
    exit 1
fi

# Create virtual environment
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv $VENV_DIR
else
    echo "✅ Virtual environment exists"
fi

# Activate
source $VENV_DIR/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Create config directory
mkdir -p config state output transcripts

# Copy templates to config if not exists
if [ ! -f "config/tone_of_voice.yaml" ]; then
    echo "📝 Creating config from templates..."
    cp templates/tone_of_voice.yaml config/tone_of_voice.yaml
    cp templates/feeds.yaml config/feeds.yaml
fi

# Create .env template if not exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env template..."
    cat > .env << 'EOF'
# Content Strategist Agent — Environment Variables
# Copy this file to .env and fill in your values

# Required for Module 2 (Radar)
YOUTUBE_API_KEY=your_youtube_data_api_v3_key_here
TWITTER_BEARER_TOKEN=your_twitter_api_v2_bearer_token_here

# Webhooks (choose one)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXX/XXX/XXX
# TELEGRAM_BOT_TOKEN=123456:ABC-DEF
# TELEGRAM_CHAT_ID=-1001234567890

# License (required)
CONTENT_STRATEGIST_LICENSE=your_license_key_here

# Optional: License server (for custom deployments)
# LICENSE_GIST_URL=https://gist.githubusercontent.com/USER/GIST_ID/raw/licenses.json
# LICENSE_CACHE_TTL=86400
# LICENSE_FAIL_OPEN=false
EOF
    echo "✅ Created .env template — edit it with your keys!"
fi

# Create .gitignore if not exists
if [ ! -f ".gitignore" ]; then
    cat > .gitignore << 'EOF'
# Virtual environment
.venv/
venv/
env/

# Environment files
.env
.env.local

# State & runtime
state/
output/
*.log

# Python
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# License cache
~/.content_strategist/
EOF
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "📋 Next steps:"
echo "  1. Edit .env with your API keys and license"
echo "  2. Activate environment: source .venv/bin/activate"
echo "  3. Test: python scripts/validate_tone.py config/tone_of_voice.yaml"
echo "  4. Run pipeline: python scripts/module1_pipeline.py --input transcripts/sample.txt --tone b2b_corporate --platforms instagram,linkedin,twitter,youtube,tiktok_enhanced,threads,newsletter"
echo ""
echo "📖 Full guide: QUICKSTART.md"
echo "📖 License setup: LICENSE_GIST_TEMPLATE.json"
echo ""
echo "🚀 Ready to create viral content!"