# AI Service Desk 🛠️

A modern, production-style AI-powered Service Desk web application built with **FastAPI**, **SQLAlchemy 2.0**, **SQLite**, **Jinja2**, **Tailwind CSS**, and **Google Gemini 2.5 Flash API**.

---

## 🚀 Overview

The **AI Service Desk** is designed to assist support teams in managing, triaging, investigating, and resolving technical issues efficiently. It leverages Google Gemini 2.5 Flash API to automatically analyze natural language tickets, determine root cause, suggest troubleshooting steps, and match relevant knowledge base articles.

### Tech Stack
- **Backend Framework**: Python 3.12+, FastAPI, Uvicorn
- **ORM & Database**: SQLAlchemy 2.0, SQLite (`data/support.db`)
- **Data Validation**: Pydantic v2
- **Templates & UI**: Jinja2, Tailwind CSS (via CDN), Vanilla JS
- **AI Engine**: Google Gemini 2.5 Flash API (`google-genai`)
- **Environment Management**: `python-dotenv`, `pydantic-settings`

---

## 📁 Project Structure

```
ai_service_desk/
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI app factory, lifespan, health check, Jinja2 setup, error handlers
│   ├── config.py          # Environment settings using Pydantic Settings & dotenv
│   ├── database.py        # SQLAlchemy 2.0 engine, SessionLocal, Base, get_db dependency
│   ├── models.py          # SQLAlchemy ORM models (Ticket, KBArticle, TicketActivity)
│   ├── schemas.py         # Pydantic v2 schemas for request validation & ORM serialization
│   ├── routers/           # Route controllers (Web views & REST APIs - Phase 2+)
│   ├── services/          # Decoupled business logic & AI integration services (Phase 2+)
│   ├── templates/         # Jinja2 HTML templates
│   │   ├── base.html      # Responsive enterprise layout (Navbar, Sidebar, Toast, Footer, Dark Mode)
│   │   ├── index.html     # Dashboard landing page
│   │   ├── 404.html       # Custom 404 error page
│   │   └── 500.html       # Custom 500 error page
│   └── static/            # Static assets
│       ├── css/
│       │   └── style.css  # Custom utility styles & animations
│       └── js/
│           └── app.js     # Dark mode toggle & toast notification system
├── data/                  # SQLite database directory (support.db)
├── requirements.txt       # Production dependencies
├── .env.example           # Environment variables template
├── .env                   # Local environment file
└── README.md              # Documentation & setup guide
```

---

## ⚙️ Setup & Installation Instructions

### 1. Prerequisites
- Python 3.12 or higher installed.

### 2. Create & Activate Virtual Environment

```bash
# Navigate to project directory
cd /path/to/project

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

Copy `.env.example` to `.env` and set your configuration:

```bash
cp .env.example .env
```

`.env` configuration:
```env
DATABASE_URL=sqlite:///./data/support.db
GEMINI_API_KEY=your_gemini_api_key_here
APP_NAME=AI Service Desk 🛠️
DEBUG=True
```

---

## 🏃 Running the Application

To start the development server with auto-reload:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Once running, access the web interface and API endpoints:
- **Web Interface**: `http://localhost:8000`
- **Health Check Endpoint**: `http://localhost:8000/health`
- **Interactive OpenAPI Documentation**: `http://localhost:8000/docs`
