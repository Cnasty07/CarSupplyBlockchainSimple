import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import io
import pandas as pd

import time
from fastapi.testclient import TestClient
from traditional_api import traditional_app, TRADITIONAL_API_KEY

client = TestClient(traditional_app)


def test_upload_transaction_file():
    df = pd.DataFrame([{"foo": "bar", "amount": 123}, {"foo": "baz", "amount": 456}])
    csv_bytes = df.to_csv(index=False).encode()
    files = {"file": ("test.csv", io.BytesIO(csv_bytes), "text/csv")}
    headers = {"X-Traditional-API-Key": TRADITIONAL_API_KEY}
    start = time.time()
    response = client.post("/traditional/transaction/upload", files=files, headers=headers)
    end = time.time()
    print(f"[PERF] /traditional/transaction/upload: start={start:.6f}, end={end:.6f}, elapsed={end-start:.6f}s")
    assert response.status_code == 200
    data = response.json()
    assert "transactions uploaded" in data["message"]
    assert "preview" in data
    assert len(data["preview"]) > 0

def test_get_transactions():
    start = time.time()
    response = client.get("/traditional/transactions")
    end = time.time()
    print(f"[PERF] /traditional/transactions: start={start:.6f}, end={end:.6f}, elapsed={end-start:.6f}s")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "preview" in data
    assert isinstance(data["preview"], list)
