import requests
import os

def upload_csv(csv_path, api_url, api_key):
    with open(csv_path, 'rb') as f:
        files = {'file': (os.path.basename(csv_path), f, 'text/csv')}
        headers = {'X-Traditional-API-Key': api_key}
        response = requests.post(
            f"{api_url}/traditional/transaction/upload", files=files, headers=headers)
        print("Upload response:", response.json())

if __name__ == "__main__":
    # Example usage
    csv_path = "data/Car_SupplyChainManagementDataSet.csv"  # Updated path
    api_url = "http://127.0.0.1:8002"  # Update if your server is running elsewhere
    api_key = "trad-API-KEY-1234"  # Replace with your actual API key
    upload_csv(csv_path, api_url, api_key)
