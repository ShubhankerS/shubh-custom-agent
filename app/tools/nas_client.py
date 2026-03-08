import os
import requests
from dotenv import load_dotenv
from pathlib import Path

# Advanced Path Finder: Looks for .env in the current folder or parent folders
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class NASClient:
    def __init__(self):
        self.api_key = os.getenv("TRUENAS_API_KEY")
        self.ip = os.getenv("TRUENAS_IP")
        
        if not self.api_key or not self.ip:
            # This will show up in your terminal to tell you exactly what's missing
            raise ValueError(f"CRITICAL_ENV_MISSING: Check {env_path}")
            
        # Ensure we use http or https based on your TrueNAS settings
        self.base_url = f"http://{self.ip}/api/v2.0"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }

    def get_pool_status(self):
        """Fetches the actual ZFS pool data from the TrueNAS API."""
        try:
            # We add a short timeout so the agent doesn't hang if the NAS is down
            response = requests.get(f"{self.base_url}/pool", headers=self.headers, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"PHYSICAL_CONNECTION_FAILED: {str(e)}"}

    def get_disk_health(self):
        """Fetches S.M.A.R.T. and overall disk status."""
        try:
            response = requests.get(f"{self.base_url}/disk", headers=self.headers, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"DISK_QUERY_FAILED: {str(e)}"}

    def get_dataset_quotas(self):
        """Retrieves ZFS dataset usage and quotas."""
        try:
            response = requests.get(f"{self.base_url}/pool/dataset", headers=self.headers, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"QUOTA_QUERY_FAILED: {str(e)}"}

    def get_service_utilization(self):
        """Fetches TrueNAS App (chart release) resource utilization."""
        try:
            # Gets status of installed Apps
            response = requests.get(f"{self.base_url}/chart/release", headers=self.headers, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"APP_QUERY_FAILED: {str(e)}"}