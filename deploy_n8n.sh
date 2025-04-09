#!/bin/bash

# Generate secure credentials
N8N_PASSWORD=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 16)
N8N_ENCRYPTION_KEY=$(openssl rand -hex 16)

# Create .env file
cat > .env << EOL
# N8N Configuration
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}
N8N_USER_MANAGEMENT_DISABLED=true
N8N_PROTOCOL=https
NODE_ENV=production

# Database Configuration (Railway will provide these)
DB_TYPE=postgresdb
EOL

# Create railway.toml
cat > railway.toml << EOL
[build]
builder = "nixpacks"
buildCommand = "pnpm install --frozen-lockfile && pnpm build"

[deploy]
startCommand = "pnpm start"
healthcheckPath = "/healthz"
healthcheckTimeout = 100
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 10

[deploy.env]
PORT = "5678"
NODE_ENV = "production"
N8N_BASIC_AUTH_ACTIVE = "true"
N8N_BASIC_AUTH_USER = "\${N8N_BASIC_AUTH_USER}"
N8N_BASIC_AUTH_PASSWORD = "\${N8N_BASIC_AUTH_PASSWORD}"
N8N_USER_MANAGEMENT_DISABLED = "true"
N8N_PROTOCOL = "https"
N8N_HOST = "\${RAILWAY_STATIC_URL}"
N8N_ENCRYPTION_KEY = "\${N8N_ENCRYPTION_KEY}"
N8N_EDITOR_BASE_URL = "\${RAILWAY_STATIC_URL}"
DB_TYPE = "postgresdb"
DB_POSTGRESDB_HOST = "\${PGHOST}"
DB_POSTGRESDB_PORT = "\${PGPORT}"
DB_POSTGRESDB_DATABASE = "\${PGDATABASE}"
DB_POSTGRESDB_USER = "\${PGUSER}"
DB_POSTGRESDB_PASSWORD = "\${PGPASSWORD}"
EOL

# Create README with deployment instructions
cat > README.md << EOL
# N8N Railway Deployment

## Deployment Instructions

1. Go to https://railway.app/dashboard
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose this repository
5. Select the "railway-deploy" branch
6. Click "Deploy"

## Environment Variables

Add these variables in Railway's dashboard:

\`\`\`
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}
\`\`\`

## Database Setup

1. In Railway dashboard, click "New"
2. Select "Database"
3. Choose "PostgreSQL"

The PostgreSQL variables will be automatically added by Railway.

## Accessing N8N

Once deployed, Railway will provide a URL. Use these credentials to log in:
- Username: admin
- Password: ${N8N_PASSWORD}

## Security Note

Keep these credentials secure and change them after first login.
EOL

echo "Deployment configuration complete!"
echo "Your N8N credentials have been generated and saved in .env"
echo "Please follow the instructions in README.md to complete the deployment"
echo "Your admin password is: ${N8N_PASSWORD}"
echo "Your encryption key is: ${N8N_ENCRYPTION_KEY}" 