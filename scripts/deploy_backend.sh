#!/usr/bin/env bash

# Deployment script for API and TileServer on openclimatemap.org

set -euo pipefail

SSH_HOST="openclimatemap.org"

ssh "$SSH_HOST" << 'EOF'
  set -euo pipefail
  # Define and expand project directory on remote
  cd ~/climatemaps

  echo "Pulling latest changes..."
  git pull

  echo "Rebuilding and restarting containers..."
  docker compose up -d --build

  echo "Deployment completed successfully."
EOF
