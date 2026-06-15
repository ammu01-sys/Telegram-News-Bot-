# Commands to Run the Telegram News Bot

## Prerequisites
```powershell
cd "c:\Users\home\Desktop\PROJECTS\Telegram News Bot"
.venv\Scripts\activate
pip install -r requirements.txt
```

## Backend (FastAPI)
```powershell
cd "c:\Users\home\Desktop\PROJECTS\Telegram News Bot"
.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000

## Frontend (Streamlit Dashboard)
Open a second terminal:
```powershell
cd "c:\Users\home\Desktop\PROJECTS\Telegram News Bot"
.venv\Scripts\activate
streamlit run dashboard/streamlit_app.py --server.port 8501
```
- Dashboard: http://localhost:8501

> Both terminals must be running simultaneously — the dashboard talks to the FastAPI backend.
