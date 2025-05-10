# FastAPI app for traditional database operations (no blockchain)
from fastapi import FastAPI, HTTPException, File, UploadFile, Depends, Security
from pydantic import BaseModel
import pandas as pd  # type: ignore
import tempfile
import os
from fastapi.security import APIKeyHeader
import sqlite3
import json
import shutil
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

# Use a unique app name to avoid FastAPI app conflicts
traditional_app = FastAPI()

# Use a unique database file to avoid DB conflicts
TRADITIONAL_DB_PATH = os.path.join(os.path.dirname(__file__), 'traditional_server.db')

def init_traditional_db():
    with sqlite3.connect(TRADITIONAL_DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            data TEXT
        )''')
        conn.commit()

# Ensure DB and table exist at startup
init_traditional_db()

# Use a unique API key env var to avoid conflicts
TRADITIONAL_API_KEY = os.getenv("TRADITIONAL_API_KEY", "trad-API-KEY-1234")
traditional_api_key_header = APIKeyHeader(name="X-Traditional-API-Key", auto_error=False)

def authorize_traditional_transaction(api_key: str = Security(traditional_api_key_header)):
    if api_key != TRADITIONAL_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

@traditional_app.post("/traditional/transaction/upload")
def upload_traditional_transaction_file(file: UploadFile = File(...), _: None = Depends(authorize_traditional_transaction)):
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded.")
    if not file.filename or not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        try:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {str(e)}") from e
    try:
        df = pd.read_csv(tmp_path)
        if df.empty:
            raise HTTPException(status_code=400, detail="Uploaded CSV is empty.")
        records = df.to_dict(orient="records")
        with sqlite3.connect(TRADITIONAL_DB_PATH) as conn:
            c = conn.cursor()
            for record in records:
                timestamp = pd.Timestamp.now().isoformat()
                c.execute('INSERT INTO transactions (timestamp, data) VALUES (?, ?)', (timestamp, json.dumps(record)))
            conn.commit()
        preview = records[:5] if len(records) > 5 else records
        return JSONResponse(content={
            "message": f"{len(records)} transactions uploaded and saved to the traditional database.",
            "preview": preview
        })
    except pd.errors.EmptyDataError as exc:
        raise HTTPException(status_code=400, detail="Uploaded CSV file contains no data.") from exc
    except pd.errors.ParserError as e:
        raise HTTPException(status_code=400, detail=f"CSV parsing error: {str(e)}") from e
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process file: {str(e)}") from e
    finally:
        os.remove(tmp_path)

@traditional_app.get("/traditional/transactions")
def get_traditional_transactions():
    with sqlite3.connect(TRADITIONAL_DB_PATH) as conn:
        c = conn.cursor()
        c.execute('SELECT id, timestamp, data FROM transactions ORDER BY id ASC')
        rows = c.fetchall()
        transactions = [
            {
                "id": row[0],
                "timestamp": row[1],
                "data": json.loads(row[2]) if row[2] else None
            }
            for row in rows
        ]
    preview = transactions[:5] if len(transactions) > 5 else transactions
    return JSONResponse(content={
        "message": f"{len(transactions)} transactions in the traditional database.",
        "preview": preview
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("traditional_db_server.traditional_api:traditional_app", host="127.0.0.1", port=8002, reload=True)
