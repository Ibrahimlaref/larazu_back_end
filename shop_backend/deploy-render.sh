#!/bin/bash
# Render.com Deployment Script for LAZULI Backend
# Run this from the shop_backend directory

echo "🚀 Deploying LAZULI Backend to Render.com"
echo "=========================================="

# Check if render CLI is installed
if ! command -v render &> /dev/null; then
    echo "❌ Render CLI not found. Install it from: https://docs.render.com/docs/cli"
    exit 1
fi

# Check if logged in
if ! render whoami &> /dev/null; then
    echo "❌ Not logged in to Render. Run: render login"
    exit 1
fi

echo "✅ Render CLI ready"

# Deploy using render.yaml from shop_backend directory
echo "📦 Deploying backend service..."
render deploy render.yaml

echo "🎉 Deployment initiated!"
echo ""
echo "Next steps:"
echo "1. Go to https://dashboard.render.com"
echo "2. Check your service: lazuli-backend"
echo "3. Update CORS_ALLOWED_ORIGINS in backend environment variables"
echo "4. The post-deploy script will run automatically"
echo ""
echo "Admin login: admin@lazuli.dz / admin123"