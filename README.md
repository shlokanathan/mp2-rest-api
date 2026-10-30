# MP2: Data Processing REST API

This project is a FastAPI application that turns the MP1 data pipeline into a REST API. `GET /health` reports the API status and version. `POST /upload` accepts a CSV file, stores it in memory, and returns its ID, row and column counts, and column names. `GET /datasets/{dataset_id}` returns up to `limit` rows of a stored dataset along with its total row count. `POST /datasets/{dataset_id}/process` takes a JSON configuration, validates the dataset with the reused MP1 `validate_dataframe()`, cleans it with `process_data()` (duplicate removal, missing-value handling, and optional outlier removal), replaces the stored data, and returns a cleaning report. Invalid uploads and processing settings return `400`, unknown dataset IDs return `404`, and invalid parameters return `422`. A logging middleware gives every request an 8-character ID, returned in the `X-Request-ID` header, and logs its method, path, status code, and duration.

## Running

```bash
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Then open http://127.0.0.1:8000/docs.

## Testing

```bash
python -m pytest tests -v
```
