#!/bin/bash
# Post-deployment setup script for Render.com

echo "🔧 Running post-deployment setup for LAZULI Backend"
echo "==================================================="

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 30

# Run migrations
echo "📦 Running database migrations..."
python manage.py migrate --noinput

# Seed initial data
echo "🌱 Seeding initial data..."
python manage.py seed_lazuli

# Collect static files (in case they weren't collected during build)
echo "📂 Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "✅ Post-deployment setup complete!"
echo ""
echo "Your LAZULI backend is ready at: $RENDER_EXTERNAL_URL"
echo "Admin login: admin@lazuli.dz / admin123"
echo "API docs: $RENDER_EXTERNAL_URL/api/docs/"