# Tests for blockchain_api.py using FastAPI TestClient
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import io
import json
import pandas as pd
import time
from fastapi.testclient import TestClient
from blockchain_api import app, API_KEY

client = TestClient(app)


def test_get_chain():
    start = time.time()
    response = client.get("/chain")
    end = time.time()
    print(f"[PERF] /chain: start={start:.6f}, end={end:.6f}, elapsed={end-start:.6f}s")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "preview" in data


def test_upload_transaction_file_and_add_block():
    df = pd.DataFrame([{"foo": "bar", "amount": 123}, {"foo": "baz", "amount": 456}])
    csv_bytes = df.to_csv(index=False).encode()
    files = {"file": ("test.csv", io.BytesIO(csv_bytes), "text/csv")}
    headers = {"X-API-Key": API_KEY}
    start_upload = time.time()
    upload_resp = client.post("/transaction/upload", files=files, headers=headers)
    end_upload = time.time()
    print(f"[PERF] /transaction/upload: start={start_upload:.6f}, end={end_upload:.6f}, elapsed={end_upload-start_upload:.6f}s")
    assert upload_resp.status_code == 200
    upload_data = upload_resp.json()
    assert "transactions uploaded" in upload_data["message"]
    # Add block
    start_add = time.time()
    add_resp = client.post("/add_block", headers=headers)
    end_add = time.time()
    print(f"[PERF] /add_block: start={start_add:.6f}, end={end_add:.6f}, elapsed={end_add-start_add:.6f}s")
    assert add_resp.status_code == 200
    add_data = add_resp.json()
    assert "blocks added" in add_data["message"]


def test_validate_chain():
    start = time.time()
    response = client.get("/validate")
    end = time.time()
    print(f"[PERF] /validate: start={start:.6f}, end={end:.6f}, elapsed={end-start:.6f}s")
    assert response.status_code == 200
    data = response.json()
    assert "is_valid" in data
    assert "block_count" in data


def test_get_block():
    start = time.time()
    response = client.get("/block/0")
    end = time.time()
    print(f"[PERF] /block/0: start={start:.6f}, end={end:.6f}, elapsed={end-start:.6f}s")
    assert response.status_code == 200
    data = response.json()
    assert "block" in data
    assert data["block"]["index"] == 0


def test_get_all_blocks_for_powerbi():
    start = time.time()
    response = client.get("/powerbi/all_blocks")
    end = time.time()
    print(f"[PERF] /powerbi/all_blocks: start={start:.6f}, end={end:.6f}, elapsed={end-start:.6f}s")
    assert response.status_code == 200
    data = response.json()
    assert "blocks" in data
    assert "count" in data


def test_save_blockchain_to_csv():
    start = time.time()
    response = client.get("/powerbi/save_csv")
    end = time.time()
    print(f"[PERF] /powerbi/save_csv: start={start:.6f}, end={end:.6f}, elapsed={end-start:.6f}s")
    assert response.status_code == 200
    data = response.json()
    assert "blockchain_export.csv" in data["message"]
    assert "count" in data
