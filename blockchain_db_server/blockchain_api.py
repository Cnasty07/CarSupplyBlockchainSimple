# FastAPI app for blockchain operations
from fastapi import FastAPI, HTTPException, File, UploadFile, Depends, Security
from pydantic import BaseModel
from typing import Any, List
from blockchain import Blockchain, Block
import pandas as pd  # type: ignore
import tempfile
import os
from fastapi.security import APIKeyHeader
import sqlite3
import json
import secrets
import shutil
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()


app = FastAPI()

DB_PATH = os.path.join(os.path.dirname(__file__), 'blockchain.db')
SELECT_BLOCKS_QUERY = 'SELECT idx, timestamp, data, previous_hash, hash FROM blocks ORDER BY idx ASC'


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS blocks (
            idx INTEGER PRIMARY KEY,
            timestamp TEXT,
            data TEXT,
            previous_hash TEXT,
            hash TEXT
        )''')
        conn.commit()


# Patch Blockchain to use SQLite
class SQLiteBlockchain(Blockchain):
    def save_blockchain(self, file_path=None):
        init_db()
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute('DELETE FROM blocks')
            for block in self.chain:
                c.execute('''INSERT INTO blocks (idx, timestamp, data, previous_hash, hash) VALUES (?, ?, ?, ?, ?)''',
                          (block.index, block.timestamp, json.dumps(block.data), block.previous_hash, block.hash))
            conn.commit()

    def load_blockchain(self, file_path=None):
        init_db()
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute(SELECT_BLOCKS_QUERY)
            rows = c.fetchall()
            if not rows:
                self.chain = [self.create_genesis_block()]
            else:
                self.chain = [Block(idx, timestamp, json.loads(
                    data), previous_hash) for idx, timestamp, data, previous_hash, hash_ in rows]
                # Fix hash assignment
                for i, (_, _, _, _, hash_) in enumerate(rows):
                    self.chain[i].hash = hash_


# Replace blockchain instance
blockchain = SQLiteBlockchain()
blockchain.load_blockchain()


# Random test key generated at startup
API_KEY = os.getenv("API_KEY", "xNnSP-fvk-4hFoABvScRcQ")
print(f"[TEST] Your API key for testing is: {API_KEY}")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def authorize_transaction(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


class BlockData(BaseModel):
    data: Any


class BlockResponse(BaseModel):
    index: int
    timestamp: str
    data: Any
    previous_hash: str
    hash: str


@app.get("/chain")
def get_chain():
    chain = [BlockResponse(
        index=block.index,
        timestamp=block.timestamp,
        data=block.data,
        previous_hash=block.previous_hash,
        hash=block.hash
    ) for block in blockchain.chain]
    preview = chain[:5] if len(chain) > 5 else chain
    return JSONResponse(content={
        "message": f"{len(chain)} blocks in the blockchain.",
        "preview": [block.model_dump() for block in preview]
    })


# Store uploaded transactions in memory for add_block usage
if not hasattr(app.state, "uploaded_transactions"):
    app.state.uploaded_transactions = []


@app.post("/transaction/upload")
def upload_transaction_file(file: UploadFile = File(...), _: None = Depends(authorize_transaction)):
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded.")
    if not file.filename or not file.filename.lower().endswith('.csv'):
        raise HTTPException(
            status_code=400, detail="Only CSV files are supported.")
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        try:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to save uploaded file: {str(e)}") from e
    # Ensure the temp file is closed before reading
    try:
        df = pd.read_csv(tmp_path)
        print(f"DataFrame loaded: {df.head()}")
        if df.empty:
            raise HTTPException(
                status_code=400, detail="Uploaded CSV is empty.")
        records = df.to_dict(orient="records")
        app.state.uploaded_transactions = records
        # Truncate output for response
        preview = records[:5] if len(records) > 5 else records
        return JSONResponse(content={
            "message": f"{len(records)} transactions uploaded.",
            "preview": preview
        })
    except pd.errors.EmptyDataError as exc:
        raise HTTPException(
            status_code=400, detail="Uploaded CSV file contains no data.") from exc
    except pd.errors.ParserError as e:
        raise HTTPException(
            status_code=400, detail=f"CSV parsing error: {str(e)}") from e
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to process file: {str(e)}") from e
    finally:
        os.remove(tmp_path)


@app.post("/add_block")
def add_block_from_uploaded():
    if not getattr(app.state, "uploaded_transactions", []):
        raise HTTPException(
            status_code=400, detail="No uploaded transactions available. Please upload a transaction file first.")
    responses = []
    for record in app.state.uploaded_transactions:
        blockchain.add_block(record)
        block = blockchain.get_latest_block()
        responses.append(BlockResponse(
            index=block.index,
            timestamp=block.timestamp,
            data=block.data,
            previous_hash=block.previous_hash,
            hash=block.hash
        ))
    blockchain.save_blockchain()
    app.state.uploaded_transactions = []  # Clear after adding
    preview = responses[:5] if len(responses) > 5 else responses
    return JSONResponse(content={
        "message": f"{len(responses)} blocks added to the blockchain.",
        "preview": [block.model_dump() for block in preview]
    })


@app.get("/validate")
def validate_chain():
    valid = blockchain.is_chain_valid()
    count = len(blockchain.chain)
    return {
        "is_valid": valid,
        "block_count": count,
        "message": f"Blockchain is {'valid' if valid else 'invalid'} with {count} blocks."
    }


@app.get("/block/{index}")
def get_block(index: int):
    if index < 0 or index >= len(blockchain.chain):
        raise HTTPException(status_code=404, detail="Block not found")
    block = blockchain.chain[index]
    block_response = BlockResponse(
        index=block.index,
        timestamp=block.timestamp,
        data=block.data,
        previous_hash=block.previous_hash,
        hash=block.hash
    )
    return JSONResponse(content={
        "message": f"Block {index} details.",
        "block": block_response.model_dump()
    })


@app.get("/powerbi/all_blocks")
def get_all_blocks_for_powerbi():
    # Query all blocks directly from the SQLite database for PowerBI
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(SELECT_BLOCKS_QUERY)
        rows = c.fetchall()
        # Convert each row to a dict, parsing JSON data
        blocks = []
        for idx, timestamp, data, previous_hash, hash_ in rows:
            try:
                parsed_data = json.loads(data)
            except (json.JSONDecodeError, TypeError):
                parsed_data = data
            blocks.append({
                "index": idx,
                "timestamp": timestamp,
                "data": parsed_data,
                "previous_hash": previous_hash,
                "hash": hash_
            })
    return {"blocks": blocks, "count": len(blocks)}


@app.get("/powerbi/save_csv")
def save_blockchain_to_csv():
    # Save to the correct path in the current folder
    csv_path = os.path.join(os.path.dirname(__file__), 'blockchain_export.csv')
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(SELECT_BLOCKS_QUERY)
        rows = c.fetchall()
        blocks = []
        for idx, timestamp, data, previous_hash, hash_ in rows:
            try:
                parsed_data = json.loads(data)
            except (json.JSONDecodeError, TypeError):
                parsed_data = data
            blocks.append({
                "index": idx,
                "timestamp": timestamp,
                "data": parsed_data,
                "previous_hash": previous_hash,
                "hash": hash_
            })
    df = pd.DataFrame(blocks)
    df.to_csv(csv_path, index=False)
    return {"message": f"Blockchain exported to {csv_path}", "count": len(blocks)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("blockchain_db_server.blockchain_api:app", host="127.0.0.1", port=8000, reload=True)
