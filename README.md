# Project Portfolio Website

A full-stack portfolio website that stores **project details** in a SQL database and shows them through a REST API.

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript (`static/`) |
| Backend | Python, Flask REST API (`app.py`) |
| Database | PostgreSQL or MySQL via SQLAlchemy (`DATABASE_URL`), SQLite fallback for local dev |
| Deploy | Vercel (`vercel.json`) or Heroku (`Procfile`) |

## Features
- Project cards with title, description, tech stack, category, status, GitHub and live links
- Search and category filters
- Add and delete projects from the UI (optional `ADMIN_KEY` protection)
- Sample projects are seeded on first run

## Run locally
```bash
pip install -r requirements.txt
python app.py
```
Open http://localhost:5000

## Google Colab
Open `colab/Project_Portfolio_Generator.ipynb` in Colab and choose **Runtime → Run all**.
It writes every project file, installs the packages, tests the API and downloads the folder as a zip.

## API
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Health check + active database |
| GET | `/api/projects?q=&category=` | List / search projects |
| GET | `/api/projects/<id>` | One project |
| POST | `/api/projects` | Create (`title`, `description` required) |
| PUT | `/api/projects/<id>` | Update |
| DELETE | `/api/projects/<id>` | Delete |

## Database
Set `DATABASE_URL` (see `.env.example`):
- PostgreSQL: `postgresql://user:pass@host:5432/portfolio` (Neon, Supabase, Heroku Postgres)
- MySQL: `mysql+pymysql://user:pass@host:3306/portfolio` (add `PyMySQL` to requirements)

Tables are created automatically on start.

## Deploy
**Vercel:** import the GitHub repo at vercel.com → add `DATABASE_URL` env variable → Deploy.

**Heroku:**
```bash
heroku create
heroku addons:create heroku-postgresql:essential-0
git push heroku main
```
