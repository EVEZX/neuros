#!/bin/bash
set -e
echo "🚀 Starting EVEZ Ecosystem on Codespace..."

# Install deps
pip install -q aiohttp numpy scipy 2>/dev/null || pip3 install -q aiohttp numpy scipy 2>/dev/null

# Set env
export VULTR_API_KEY="R55BTKKXN5Y7U4ICAV2YCV2FW2A"
export OPENROUTER_API_KEY="sk-or-…4760"  
export GROQ_API_KEY="gsk_Mr…gNGc"
export GEMINI_API_KEY="AIzaSy…gJfM"
export PROVIDER_PORT=9100

# Get the evez-ai repo if not present
if [ ! -d "evez-ai" ]; then
  git clone https://github.com/EVEZX/evez-ai.git evez-ai
fi

cd evez-ai

# Start services in background
echo "Starting Provider (9100)..."
nohup python3 provider/gateway-v2.py > /tmp/provider.log 2>&1 &
PROVIDER_PID=$!

echo "Starting Arena (9800)..."
nohup python3 arena/arena.py > /tmp/arena.log 2>&1 &
ARENA_PID=$!

echo "Starting Commerce (9700)..."
nohup python3 commerce/commerce.py > /tmp/commerce.log 2>&1 &
COMMERCE_PID=$!

sleep 5

# Health checks
echo ""
echo "=== HEALTH CHECKS ==="
curl -s http://localhost:9100/health 2>/dev/null && echo "" || echo "Provider: starting..."
curl -s http://localhost:9800/health 2>/dev/null && echo "" || echo "Arena: starting..."
curl -s http://localhost:9700/health 2>/dev/null && echo "" || echo "Commerce: starting..."

echo ""
echo "🟢 EVEZ running on codespace!"
echo "PIDs: Provider=$PROVIDER_PID Arena=$ARENA_PID Commerce=$COMMERCE_PID"
