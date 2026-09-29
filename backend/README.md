# Backend API

Currently, this backend provides a skeleton structure for the Qoneqt x CTRL FREAK AI Challenge.

## Status
**AI and Video Generation are NOT implemented yet.** 
The `/api/v1/generate` endpoint currently acts as a placeholder that queues a job, and `/api/v1/status` returns the mocked queued state.

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```

2. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - Mac/Linux: `source .venv/bin/activate`

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create configuration:
   ```bash
   cp .env.example .env
   ```

## Running the Server

Start the FastAPI server:
```bash
uvicorn app.main:app --reload
```
The server will be available at `http://127.0.0.1:8000`.

## Testing

Run tests with pytest:
```bash
pytest
```

## API Endpoints

- `GET /health` - Health check.
- `POST /api/v1/generate` - Queue a generation job.
- `GET /api/v1/status/{job_id}` - Check the status of a job.
- `GET /api/v1/result/{job_id}` - Get the final result of a job.
- `POST /api/v1/regenerate-scene` - Request regeneration of a specific scene.
