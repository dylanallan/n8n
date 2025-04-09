#!/bin/bash

# Generate secure credentials
N8N_PASSWORD=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 16)
N8N_ENCRYPTION_KEY=$(openssl rand -hex 32)

# Create environment variables file
cat > .env << EOL
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}
N8N_USER_MANAGEMENT_DISABLED=true
N8N_PROTOCOL=https
NODE_ENV=production
PORT=5678
EOL

# Install Railway CLI
curl -fsSL https://railway.app/install.sh | sh

# Set Railway token
export RAILWAY_TOKEN="3f4a9925-9125-456e-ad12-c9e2a83a072c"

# Initialize Railway project
railway init

# Link to existing project
railway link

# Add PostgreSQL
railway add

# Deploy
railway up

echo "Deployment initiated!"
echo "Your n8n credentials:"
echo "Username: admin"
echo "Password: ${N8N_PASSWORD}"
echo "Encryption Key: ${N8N_ENCRYPTION_KEY}" 