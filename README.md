# SHL Assessment Recommendation Agent

A conversational agent that recommends SHL assessments based on hiring needs.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and add your OpenAI API key

3. Run the service:
```bash
python main.py
```

The service will be available at `http://localhost:8000`

## API Endpoints

- `GET /health` - Health check
- `POST /chat` - Conversational agent endpoint

## Project Structure

- `main.py` - FastAPI application
- `catalog.py` - SHL catalog scraping and parsing
- `retrieval.py` - Assessment retrieval system
- `agent.py` - Conversational agent logic
- `models.py` - Pydantic models for API
