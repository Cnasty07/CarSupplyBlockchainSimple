import requests
import os

# used to simulate transacations for populating the blockchain


def upload_csv(csv_path, api_url, api_key):
    with open(csv_path, 'rb') as f:
        files = {'file': (os.path.basename(csv_path), f, 'text/csv')}
        headers = {'X-API-Key': api_key}
        response = requests.post(
            f"{api_url}/transaction/upload", files=files, headers=headers)
        print("Upload response:", response.json())

        # Optionally, add all blocks to the blockchain
        add_block_response = requests.post(
            f"{api_url}/add_block", headers=headers)
        print("Add block response:", add_block_response.json())


if __name__ == "__main__":
    # Example usage
    csv_path = "../data/Car_SupplyChainManagementDataSet.csv"  # Updated path for correct relative location
    api_url = "http://127.0.0.1:8000"  # Update if your server is running elsewhere
    api_key = "xNnSP-fvk-4hFoABvScRcQ"  # Replace with your actual API key
    upload_csv(csv_path, api_url, api_key)
