import requests
import json
import os
import urllib3
import subprocess
import time

# Disable SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class DeploymentManager:
    def __init__(self):
        self.railway_token = "3f4a9925-9125-456e-ad12-c9e2a83a072c"
        self.base_url = "https://api.railway.app/v2"
        self.headers = {
            "Authorization": f"Bearer {self.railway_token}",
            "Content-Type": "application/json"
        }

    def create_project(self):
        try:
            response = requests.post(
                f"{self.base_url}/projects",
                headers=self.headers,
                json={"name": "dylan-n8n", "template": "node"},
                verify=False
            )
            if response.status_code == 200:
                return response.json()['id']
            else:
                print(f"Error creating project: {response.text}")
                return None
        except Exception as e:
            print(f"Error in create_project: {str(e)}")
            return None

    def set_environment_variables(self, project_id):
        try:
            variables = {
                "PORT": "5678",
                "N8N_BASIC_AUTH_ACTIVE": "true",
                "N8N_BASIC_AUTH_USER": "admin",
                "N8N_BASIC_AUTH_PASSWORD": os.urandom(16).hex(),
                "N8N_USER_MANAGEMENT_DISABLED": "true",
                "N8N_PROTOCOL": "https",
                "N8N_ENCRYPTION_KEY": os.urandom(32).hex()
            }
            
            response = requests.post(
                f"{self.base_url}/projects/{project_id}/variables",
                headers=self.headers,
                json={"variables": variables},
                verify=False
            )
            
            if response.status_code == 200:
                print("Environment variables set successfully")
                return True
            else:
                print(f"Error setting variables: {response.text}")
                return False
        except Exception as e:
            print(f"Error in set_environment_variables: {str(e)}")
            return False

    def deploy_project(self, project_id):
        try:
            # First, ensure we're in the correct directory
            os.chdir("n8n-deploy")
            
            # Initialize git if not already done
            if not os.path.exists(".git"):
                subprocess.run(["git", "init"], check=True)
                subprocess.run(["git", "add", "."], check=True)
                subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)
            
            # Push to Railway
            response = requests.post(
                f"{self.base_url}/projects/{project_id}/deployments",
                headers=self.headers,
                json={
                    "source": "local",
                    "buildCommand": "pnpm install --frozen-lockfile && pnpm build",
                    "startCommand": "pnpm start"
                },
                verify=False
            )
            
            if response.status_code == 200:
                print("Deployment started successfully")
                return True
            else:
                print(f"Error starting deployment: {response.text}")
                return False
        except Exception as e:
            print(f"Error in deploy_project: {str(e)}")
            return False

    def add_postgres_database(self, project_id):
        try:
            response = requests.post(
                f"{self.base_url}/projects/{project_id}/services",
                headers=self.headers,
                json={
                    "name": "postgres",
                    "type": "postgresql"
                },
                verify=False
            )
            
            if response.status_code == 200:
                print("PostgreSQL database added successfully")
                return True
            else:
                print(f"Error adding database: {response.text}")
                return False
        except Exception as e:
            print(f"Error in add_postgres_database: {str(e)}")
            return False

def main():
    manager = DeploymentManager()
    
    print("Creating Railway project...")
    project_id = manager.create_project()
    if not project_id:
        print("Failed to create project")
        return
    
    print("Setting environment variables...")
    if not manager.set_environment_variables(project_id):
        print("Failed to set environment variables")
        return
    
    print("Adding PostgreSQL database...")
    if not manager.add_postgres_database(project_id):
        print("Failed to add database")
        return
    
    print("Starting deployment...")
    if not manager.deploy_project(project_id):
        print("Failed to start deployment")
        return
    
    print("Deployment process initiated successfully!")
    print("Please check your Railway dashboard for deployment status")

if __name__ == "__main__":
    main() 