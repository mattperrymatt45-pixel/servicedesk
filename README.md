# AI Service Desk 🛠️

An enterprise-grade, production-style AI-powered Service Desk web application built with **Python**, **FastAPI**, **SQLAlchemy 2.0**, **SQLite**, **Jinja2**, **Tailwind CSS**, and **Groq AI**.

---

## 🚀 Overview & Key Features

The **AI Service Desk** enables IT support teams to manage technical incidents in natural language, automatically triage root causes using Groq LLM, match relevant Knowledge Base SOPs from Hugging Face dataset, and draft non-technical customer replies instantly.

### 🌟 Core Capabilities
- 📊 **Executive Analytics Dashboard**: SQL-driven real-time KPI metrics and interactive **Chart.js** charts (Tickets by Status, Priority, Category, and Daily Creation Trends).
- 🔍 **Unified Global Search**: Search across Ticket Titles, Descriptions, Ticket IDs (`#TCK-0001`), Knowledge Base SOP Titles, and Keywords.
- 🤖 **Groq AI Co-Pilot**: Auto-triages tickets, recommends category and priority, identifies probable root cause, generates step-by-step troubleshooting checklists, and estimates fix difficulty dynamically.
- ✉️ **One-Click AI Customer Reply**: Drafts polite, non-technical customer email responses with a single click and one-touch clipboard copying.
- 📚 **Hugging Face Knowledge Base Repository**: Automatically seeded with 100 high-quality SOP articles from the `mindweave/help-desk-tickets` dataset.
- 🎫 **Complete Ticket Management Lifecycle**: Submit incidents, edit properties, record resolution steps, track chronological activity timelines, and manage statuses (Open, In Progress, Resolved, Closed).
- 🟢 **Comprehensive System Health API**: Liveness check at `/health` reporting DB status, Groq AI availability, configured model, and record counts.

---

## 🏗️ Application Architecture

The application follows a clean, modular monolith architecture inspired by MVC:

```
┌────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER                           │
│        Jinja2 Templates + Tailwind CSS + Alpine.js/Vanilla JS          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                             ROUTER LAYER                               │
│     Web Routers (HTML Views)     │    REST API Routers (JSON/AJAX)    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                            SERVICE LAYER                               │
│ TicketService │ KBService │ AIService (Groq) │ Analytics │ Search │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          DATA ACCESS LAYER                             │
│                  SQLAlchemy 2.0 ORM + SQLite Database                  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Folder Structure

```
ai_service_desk/
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI app factory, lifespan, health check, router registration, error handlers
│   ├── config.py          # Environment settings using Pydantic Settings & dotenv
│   ├── database.py        # SQLAlchemy 2.0 engine, SessionLocal, Base, get_db dependency
│   ├── models.py          # SQLAlchemy ORM models (Ticket, KBArticle, TicketActivity)
│   ├── schemas.py         # Pydantic v2 schemas for request validation & ORM serialization
│   ├── routers/           # Route controllers
│   │   ├── __init__.py
│   │   ├── dashboard.py   # Analytics Dashboard & Global Search routes (/dashboard, /search, /api/dashboard/stats)
│   │   ├── tickets.py     # Ticket CRUD & lifecycle routes (/tickets, /tickets/{id}, /tickets/{id}/edit, /tickets/{id}/resolve)
│   │   ├── kb.py          # Knowledge Base routes (/kb, /kb/{id}, /kb/new, /api/kb)
│   │   └── ai.py          # AI action routes (/tickets/{id}/triage, /api/tickets/{id}/customer-reply)
│   ├── services/          # Business logic layer
│   │   ├── __init__.py
│   │   ├── ai_service.py  # Groq LLM API client, prompt engineering, structured JSON parsing, fallbacks
│   │   ├── ticket_service.py # Ticket CRUD, lifecycle updates, activity timeline logging
│   │   ├── kb_service.py  # Knowledge base search & AI lookup
│   │   ├── analytics_service.py # SQL analytics calculations & Chart.js data formatting
│   │   └── search_service.py # Unified global search logic
│   ├── templates/         # Jinja2 HTML templates
│   │   ├── base.html      # Responsive layout (Header, Navbar, Global Search, Sidebar, Toast, Dark Mode)
│   │   ├── dashboard.html # Analytics Dashboard & Chart.js visualizations
│   │   ├── search.html    # Unified Global Search results view
│   │   ├── 404.html       # Custom 404 error page
│   │   ├── 500.html       # Custom 500 error page
│   │   ├── tickets/
│   │   │   ├── list.html  # Incident Dashboard table, metrics, search & filters
│   │   │   ├── detail.html# Ticket Detail view, AI Co-Pilot Panel, Resolution Box, Timeline, Customer Reply Modal
│   │   │   ├── create.html# Incident submission form
│   │   │   └── edit.html  # Ticket property editor
│   │   └── kb/
│   │       ├── list.html  # KB repository list & search
│   │       ├── detail.html# KB article detail page
│   │       └── create.html# KB article creation form
│   └── static/            # Static assets
│       ├── css/style.css  # Custom utility styles
│       └── js/app.js      # Dark mode & toast notification system
├── data/
│   └── support.db         # SQLite database file
├── scripts/
│   ├── import_dataset.py  # Hugging Face dataset import script
│   └── seed_data.py       # Main database seeder script
├── .env                   # Active environment variables
├── .env.example           # Environment template
├── requirements.txt       # Production dependencies
└── README.md              # Documentation
```

---

## 💻 Tech Stack

- **Backend**: Python 3.12+, FastAPI, Uvicorn
- **Database & ORM**: SQLAlchemy 2.0, SQLite (`data/support.db`)
- **Data Validation**: Pydantic v2
- **Templating & UI**: Jinja2, Tailwind CSS (via CDN), Vanilla JS, Chart.js
- **AI Integration**: Groq Python SDK (`groq`), dynamically configured model (`AI_MODEL=openai/gpt-oss-120b`)
- **Dataset**: Hugging Face `datasets` library (`mindweave/help-desk-tickets`)

---

## ⚙️ Setup & Installation Instructions

### 1. Prerequisites
- Python 3.12 or higher installed.

### 2. Create & Activate Virtual Environment

```bash
# Navigate to project root
cd /path/to/servicedesk

# Create virtual environment
python3 -m venv venv

# Activate on Linux/macOS
source venv/bin/activate

# Activate on Windows
# venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create or update `.env` in the project root directory:

```env
DATABASE_URL=sqlite:///./data/support.db
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
AI_MODEL=openai/gpt-oss-120b
APP_NAME=AI Service Desk 🛠️
DEBUG=True
```

---

## 📥 How to Import Dataset & Seed Database

To download and seed 100 high-quality Knowledge Base articles from Hugging Face alongside sample support tickets:

```bash
# Run standalone Hugging Face dataset importer
python scripts/import_dataset.py

# Or run full database seeder script
python scripts/seed_data.py
```

---

## 🏃 How to Run the Application

Start the development server with auto-reload:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Access the application in your browser:
- **Main Incident Dashboard**: `http://localhost:8000/tickets`
- **Analytics Dashboard**: `http://localhost:8000/dashboard`
- **Knowledge Base Repository**: `http://localhost:8000/kb`
- **Health Check API**: `http://localhost:8000/health`
- **Interactive OpenAPI Documentation**: `http://localhost:8000/docs`

---

## 🧪 Manual Testing Checklist

| Feature | Endpoint / Page | Expected Outcome |
|---|---|---|
| **Health Check** | `GET /health` | Returns status, DB connection, AI availability, `ai_model`, record counts |
| **Analytics Dashboard** | `GET /dashboard` | Renders KPI cards and 4 Chart.js charts |
| **Global Search** | `GET /search?q=VPN` | Returns matching tickets and KB articles |
| **Submit Ticket** | `POST /tickets` | Validates form, creates ticket, logs `CREATED` activity |
| **AI Triage** | `POST /tickets/{id}/triage` | Calls Groq API, saves AI summary & logs `AI_TRIAGED` timeline event |
| **Customer Email Reply** | `POST /api/tickets/{id}/customer-reply` | Returns friendly customer email draft JSON |
| **Resolve Ticket** | `POST /tickets/{id}/resolve` | Sets status `Resolved`, stores resolution text, logs `RESOLVED` event |
| **Dataset Importer** | `python scripts/import_dataset.py` | Imports 100 records idempotently |

---

## ☁️ Deployment Instructions for Render

1. Create a new **Web Service** on [Render](https://render.com).
2. Connect your GitHub repository (`https://github.com/YOUR_USERNAME/servicedesk.git`).
3. Set the build and start settings:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && python scripts/import_dataset.py`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add Environment Variables in Render Dashboard:
   - `GROQ_API_KEY`: Your Groq API key (`gsk_...`)
   - `AI_MODEL`: `openai/gpt-oss-120b`
   - `DATABASE_URL`: `sqlite:///./data/support.db`
5. Click **Deploy**.

---

## ⚠️ Known Limitations

1. **SQLite Concurrency**: Designed for single-instance deployment; production multi-node scaling would use PostgreSQL.
2. **Groq API Rate Limits**: Free tier Groq keys have rate limits; the application includes automatic fallback handling so API timeouts never crash the app.
