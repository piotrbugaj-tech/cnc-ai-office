#!/bin/zsh
# CNC AI Office — launcher

cd "$(dirname "$0")/office"

# Start Ollama if not running
if ! pgrep -x "ollama" > /dev/null 2>&1; then
  echo "🦙  Uruchamiam Ollama..."
  ollama serve &>/dev/null &
  sleep 2
fi

echo "🏭  Uruchamiam CNC AI Office..."
npm start
