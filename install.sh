#!/bin/bash
# JACK AI - Production Core Installer
# (C) 2026 B. Jaswanth Reddy

echo "🚀 Initializing TITAN Installation Grid..."

# 1. Core Dependencies
echo "📦 Installing Python dependencies..."
pip install -r setup/requirements_production.txt

# 2. Neural Models (Ollama)
echo "🧠 Synchronizing Neural Models via Ollama..."
if command -v ollama &> /dev/null
then
    ollama pull qwen2.5-coder:7b
    ollama pull mistral:latest
else
    echo "❌ ERROR: Ollama not found. Please install Ollama from https://ollama.com first."
    exit 1
fi

# 3. Vision & Web Drivers
echo "🌐 Initializing Web & Vision Drivers..."
playwright install chromium
python -m playwright install-deps

# 4. Vault Initialization
echo "🔒 Initializing Neural Vault..."
mkdir -p vault/memory
mkdir -p logs

echo "✅ JACK is ready for Overdrive. Run 'python api/server.py' to begin mission orchestration."
