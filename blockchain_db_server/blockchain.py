import hashlib
import json
import os
import pickle
from datetime import datetime
import pandas as pd # type: ignore


class Block:
    def __init__(self, index, timestamp, data, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = f"{self.index}{self.timestamp}{json.dumps(self.data)}{self.previous_hash}"
        return hashlib.sha256(block_string.encode()).hexdigest()


class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]

    def create_genesis_block(self):
        return Block(0, str(datetime.now()), "Genesis Block", "0")

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, data):
        latest_block = self.get_latest_block()
        new_block = Block(len(self.chain), str(
            datetime.now()), data, latest_block.hash)
        self.chain.append(new_block)

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            if current_block.hash != current_block.calculate_hash():
                return False

            if current_block.previous_hash != previous_block.hash:
                return False

        return True

    def save_blockchain(self, file_path="blockchain.pkl"):
        """Saves the blockchain to a file."""
        with open(file_path, "wb") as file:
            pickle.dump(self.chain, file)
        print(f"Blockchain saved to {file_path}")

    def load_blockchain(self, file_path="blockchain.pkl"):
        """Loads the blockchain from a file if it exists."""
        if os.path.exists(file_path):
            with open(file_path, "rb") as file:
                self.chain = pickle.load(file)
            print(f"Blockchain loaded from {file_path}")
        else:
            print(
                f"No existing blockchain found at {file_path}. Initializing a new blockchain.")
            self.chain = [self.create_genesis_block()]


# file:Car_SupplyChainManagementDataSet.csv
if __name__ == "__main__":
    # Initialize blockchain
    blockchain = Blockchain()

    # Load existing blockchain or create a new one
    blockchain.load_blockchain()

    # Load dataset
    dataset_path = "data/Car_SupplyChainManagementDataSet.csv"
    dataset = pd.read_csv(dataset_path).to_dict(orient="records")

    # Add dataset records to blockchain
    for record in dataset:
        blockchain.add_block(record)

    # Save the blockchain
    blockchain.save_blockchain()

    # Validate blockchain
    print("Is blockchain valid?", blockchain.is_chain_valid())

    # Print the blockchain
    for block in blockchain.chain:
        print(f"Index: {block.index}, Timestamp: {block.timestamp}, Data: {block.data}, Hash: {block.hash}, Previous Hash: {block.previous_hash}")
