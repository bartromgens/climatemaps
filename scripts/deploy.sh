#!/usr/bin/env bash

# Deployment script client and backend

set -euo pipefail

# Resolve the directory of this script, even when called via symlink\SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

# Deploy client
echo "Deploying client..."
bash "$SCRIPT_DIR/deploy_client.sh"

echo "Client deployment completed."

# Deploy backend
echo "Deploying backend..."
bash "$SCRIPT_DIR/deploy_backend.sh"

echo "Backend deployment completed."

echo "All deployments completed successfully."
