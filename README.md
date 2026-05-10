# AI Multi-Agent Travel Planning System

An intelligent travel planning system powered by multi-agent architecture with real-time API integration.

## Features

- **Real-time Weather Data**: OpenWeatherMap API integration for weather forecasts and travel advisories
- **Web Search Integration**: Serper API for finding flights, hotels, and travel information
- **AI-Powered Planning**: Groq LLM (LLaMA 3.1) for intelligent travel recommendations
- **Multi-Agent Coordination**: Specialized agents for different travel planning tasks
- **Budget Optimization**: Smart budget analysis and cost-effective suggestions
- **Interactive Dashboard**: Streamlit-based user interface

## Tech Stack

- **Backend**: FastAPI, Python
- **Frontend**: Streamlit
- **AI/ML**: Groq LLM, CrewAI
- **APIs**: OpenWeatherMap, Serper Search
- **Database**: ChromaDB

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Add your API keys to .env
```

## API Keys Required

- `GROQ_API_KEY`: Get from https://console.groq.com/
- `SERPER_API_KEY`: Get from https://serper.dev/
- `OPENWEATHERMAP_API_KEY`: Get from https://openweathermap.org/api

## Usage

### Run the Dashboard

```bash
streamlit run ui/app_working.py
```

### Run the Backend API

```bash
uvicorn api.main:app --reload
```

## Project Structure

```
├── agents/          # Agent definitions
├── api/            # FastAPI backend
├── services/       # Core business logic
├── tools/          # API integration tools
├── ui/             # Streamlit dashboard
├── utils/          # Utility functions
└── requirements.txt
```

## Example Request

"Chennai to Bangalore flight booking date May 25, my budget is 15k. May 25 booking for budget-friendly hotel booking for above 4 rating."

## License

MIT License
