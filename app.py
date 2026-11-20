"""
Project Portfolio Website - Backend (Flask + SQLAlchemy)

- Serves the HTML/CSS/JS frontend from /static
- REST API under /api/projects to store and manage project details
- Database: PostgreSQL (or MySQL) via DATABASE_URL; falls back to SQLite for local dev
"""
import os
from datetime import datetime, timezone

from flask import Flask, jsonify, request, send_from_directory, abort
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if url:
        # Heroku / some hosts still hand out the old "postgres://" scheme
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url
    # Local fallback (Vercel only allows writing to /tmp)
    folder = "/tmp" if os.environ.get("VERCEL") else BASE_DIR
    return f"sqlite:///{os.path.join(folder, 'projects.db')}"


app = Flask(__name__, static_folder=os.path.join(BASE_DIR, "static"), static_url_path="/static")
app.config["SQLALCHEMY_DATABASE_URI"] = database_url()
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
CORS(app)
db = SQLAlchemy(app)

ADMIN_KEY = os.environ.get("ADMIN_KEY")  # optional: protects create/update/delete


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    tech_stack = db.Column(db.String(255), default="")  # comma separated
    category = db.Column(db.String(60), default="Web")
    status = db.Column(db.String(30), default="Completed")
    github_url = db.Column(db.String(255), default="")
    live_url = db.Column(db.String(255), default="")
    image_url = db.Column(db.String(500), default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "tech_stack": [t.strip() for t in (self.tech_stack or "").split(",") if t.strip()],
            "category": self.category,
            "status": self.status,
            "github_url": self.github_url,
            "live_url": self.live_url,
            "image_url": self.image_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


FIELDS = ("title", "description", "tech_stack", "category", "status", "github_url", "live_url", "image_url")
STATUSES = {"Completed", "In Progress", "Planned"}

SAMPLE_PROJECTS = [
    {
        "title": "Project Portfolio Website",
        "description": "Full-stack portfolio that stores project details in a SQL database and shows them through a REST API.",
        "tech_stack": "HTML, CSS, JavaScript, Flask, PostgreSQL",
        "category": "Full Stack",
        "status": "Completed",
    },
    {
        "title": "Task Manager API",
        "description": "RESTful API for creating, assigning and tracking tasks with filtering and pagination.",
        "tech_stack": "Python, Flask, SQLAlchemy",
        "category": "Backend",
        "status": "In Progress",
    },
    {
        "title": "Weather Dashboard",
        "description": "Responsive dashboard that shows live weather and a 5-day forecast for any city.",
        "tech_stack": "JavaScript, CSS Grid, REST API",
        "category": "Frontend",
        "status": "Planned",
    },
]


def require_admin():
    if ADMIN_KEY and request.headers.get("X-Admin-Key") != ADMIN_KEY:
        abort(401, description="Invalid or missing admin key")


def clean_payload(data: dict, partial: bool = False) -> dict:
    out = {}
    for f in FIELDS:
        if f in data:
            value = data[f]
            if f == "tech_stack" and isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            out[f] = str(value or "").strip()
    if not partial:
        if not out.get("title"):
            abort(400, description="title is required")
        if not out.get("description"):
            abort(400, description="description is required")
    if "status" in out and out["status"] not in STATUSES:
        abort(400, description=f"status must be one of {sorted(STATUSES)}")
    for f in ("github_url", "live_url", "image_url"):
        if out.get(f) and not out[f].startswith(("http://", "https://")):
            abort(400, description=f"{f} must start with http:// or https://")
    return out


def init_db():
    with app.app_context():
        db.create_all()
        if Project.query.count() == 0:
            db.session.add_all(Project(**p) for p in SAMPLE_PROJECTS)
            db.session.commit()


# ---------------- Frontend ----------------
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


# ---------------- API ----------------
@app.get("/api/health")
def health():
    return jsonify(status="ok", database=db.engine.url.get_backend_name())


@app.get("/api/projects")
def list_projects():
    query = Project.query
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(Project.title.ilike(like), Project.description.ilike(like), Project.tech_stack.ilike(like))
        )
    if category:
        query = query.filter(Project.category == category)
    projects = query.order_by(Project.created_at.desc(), Project.id.desc()).all()
    return jsonify([p.to_dict() for p in projects])


@app.get("/api/projects/<int:project_id>")
def get_project(project_id):
    return jsonify(db.get_or_404(Project, project_id).to_dict())


@app.post("/api/projects")
def create_project():
    require_admin()
    project = Project(**clean_payload(request.get_json(silent=True) or {}))
    db.session.add(project)
    db.session.commit()
    return jsonify(project.to_dict()), 201


@app.put("/api/projects/<int:project_id>")
def update_project(project_id):
    require_admin()
    project = db.get_or_404(Project, project_id)
    for key, value in clean_payload(request.get_json(silent=True) or {}, partial=True).items():
        setattr(project, key, value)
    db.session.commit()
    return jsonify(project.to_dict())


@app.delete("/api/projects/<int:project_id>")
def delete_project(project_id):
    require_admin()
    project = db.get_or_404(Project, project_id)
    db.session.delete(project)
    db.session.commit()
    return jsonify(message="Project deleted", id=project_id)


@app.errorhandler(400)
@app.errorhandler(401)
@app.errorhandler(404)
def handle_error(err):
    return jsonify(error=getattr(err, "description", str(err))), err.code


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
