# Vision Module - API

FastAPI deployment for trained vision models.

## Usage

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn main:app --host 0.0.0.0 --port 8100

# Test
curl -X POST http://localhost:8100/analyze \
  -F "image=@test_image.jpg"
```

## Endpoints

- `POST /analyze` — Analyze image, return observations
- `GET /health` — Health check

## Response Format

```json
{
  "observations": [
    {
      "condition": "possible_skin_irritation",
      "confidence": 0.82,
      "location": "left_ear"
    }
  ],
  "disclaimer": "This is AI-assisted observation only. Please consult a licensed veterinarian.",
  "model_version": "clip_vet_v1"
}
```
