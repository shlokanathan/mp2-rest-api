import io
import json
import logging
from pathlib import Path
import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from src import DatasetInfo, DatasetStorage, HealthResponse, setup_logging

setup_logging(verbose=True)
logger = logging.getLogger(__name__)

app = FastAPI(title="Data Processing API", version="1.0.0")
storage = DatasetStorage()

@app.get("/health", response_model=HealthResponse)
def health_check():
    """Return the application status and version."""
    return {"status": "ok", "version": app.version}

@app.post("/upload", response_model=DatasetInfo)
async def upload_dataset(file: UploadFile = File(...)):
    """Read and store a CSV upload."""
    suffix = Path(file.filename or "").suffix.lower()
    if suffix != ".csv":
        logger.warning(f"Unsupported file format: {suffix or '(none)'}")
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{suffix or '(none)'}'. Please upload a .csv file.",
        )

    contents = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except pd.errors.EmptyDataError:
        logger.warning(f"Empty CSV upload: {file.filename}")
        raise HTTPException(status_code=400, detail="The uploaded CSV file is empty.")
    except pd.errors.ParserError as e:
        logger.warning(f"Could not parse CSV {file.filename}: {e}")
        raise HTTPException(status_code=400, detail="The uploaded file could not be parsed as CSV.")
    except UnicodeDecodeError:
        logger.warning(f"Could not decode CSV {file.filename}")
        raise HTTPException(status_code=400, detail="The uploaded file is not valid UTF-8 text.")

    dataset_id = storage.save(df, file.filename)
    logger.info(f"Uploaded dataset: id={dataset_id}, filename={file.filename}, rows={len(df)}")
    return storage.get_metadata(dataset_id)

@app.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: int, limit: int = Query(default=100, ge=1)):
    """Return up to limit rows from a stored dataset."""
    df = storage.get(dataset_id)
    if df is None:
        logger.warning(f"Dataset not found: {dataset_id}")
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found.")

    records = json.loads(df.head(limit).to_json(orient="records"))
    logger.info(f"Retrieved dataset: id={dataset_id}, returned_rows={len(records)}")
    return {"id": dataset_id, "data": records, "total_rows": len(df)}
