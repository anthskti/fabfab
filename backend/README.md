# Backend README

## File Structure

```
backend/
├── app/
│   ├── models/
│   │   └── schemas.py          # Pydantic models
│   ├── services/
│   │   ├── gemini_service.py   # AI generation logic
│   │   └── obj_service.py      # OBJ manipulation
│   ├── routers/
│   │   └── generate.py         # API endpoints
│   └── utils/
│       └── cache.py            # Model caching
├── main.py                     # FastAPI app entry
├── requirements.txt
├── .env.example
└── README.md
```

## Running
Virtual Environment
```bash
python3 -m venv .venv 
source venv/bin/activate
```

Download Requirements
```bash
pip install -r req.txt
```

For .env file, copy ".env.example" then rename to ".env", have your Gemini API Key available.

