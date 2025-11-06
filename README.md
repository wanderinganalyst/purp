# BecauseImStuck

![Tests](https://github.com/YOUR_USERNAME/becauseImstuck/workflows/Test%20Suite/badge.svg)
![Branch Protection](https://github.com/YOUR_USERNAME/becauseImstuck/workflows/Branch%20Protection/badge.svg)

A Flask application for tracking bills and representatives with comprehensive testing and multi-cloud deployment infrastructure.

Quick start (macOS, zsh):

1. Create a virtual environment and activate it:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

3. Run the app:

```bash
python main.py
```

Open http://127.0.0.1:5000 in your browser to see "Hello, World!".

Alternately, run with the Flask CLI:

```bash
export FLASK_APP=main.py
flask run
```

Notes:
- The app binds to 127.0.0.1:5000 by default. Change `host`/`port` in `main.py` if needed.
- Use a virtualenv to avoid contaminating your system Python.

Docker
------

Build the image and run the container (from the repository root):

```bash
# build the image
docker build -t flask-hello .

# run the container (maps container port 5000 to host 5000)
docker run --rm -p 5000:5000 flask-hello
```

Or use docker-compose:

```bash
docker-compose up --build
```

Then open http://127.0.0.1:5000 in your browser.

Notes about the container:
- The container uses `gunicorn` to serve the Flask app.
- If you need a development container with auto-reload, consider mounting the source and using the Flask CLI or adjusting the Dockerfile for development.

Database initialization (Postgres)
---------------------------------

If you use the included Postgres container (via `docker-compose.yml`) you need to initialize the database schema and seed demo users once. From the repository root:

```bash
# start only the database service
docker-compose up -d db

# run the init_db script using the web service's image and environment
docker-compose run --rm web python init_db.py
```

This creates the tables and inserts two demo users:
- `regular` / `password` (role: regular)
- `power` / `powerpass` (role: power)

If Postgres isn't ready when you run the init command, wait a few seconds and try again. See `docker-compose logs db` for DB startup logs.

## Cloud Deployment

Deploy the application to AWS, Azure, or GCP with automated infrastructure provisioning:

```bash
cd infrastructure/scripts
./deploy.sh
```

Features:
- **Multi-cloud support**: Choose AWS, Azure, or GCP
- **Environment modes**: Production (larger resources) or Demo (minimal resources)
- **Fully automated**: Terraform + Ansible handle everything
- **Production-ready**: Nginx reverse proxy, Systemd service, Gunicorn

See [infrastructure/README.md](infrastructure/README.md) for complete documentation.

Quick links:
- [Quick Start Guide](infrastructure/QUICKSTART.md) - Deploy in 5 minutes
- [Architecture](infrastructure/ARCHITECTURE.md) - Diagrams and design
- [Testing Checklist](infrastructure/TESTING.md) - Verification procedures

## Testing

Comprehensive test suite with 100+ tests:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
pytest tests/docker/
```

See [tests/README.md](tests/README.md) for complete testing documentation.

## Project Structure

```
becauseImstuck/
├── app.py                  # Main Flask application
├── models.py              # Database models
├── routes/                # Route blueprints
│   ├── auth.py           # Authentication routes
│   ├── bills.py          # Bill tracking routes
│   └── reps.py           # Representative routes
├── utils/                 # Utility modules
│   ├── data_fetcher.py   # Production data fetching
│   └── validators.py     # Input validation
├── templates/             # Jinja2 templates
├── static/               # CSS, JS, images
├── tests/                # Test suite (100+ tests)
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   ├── e2e/             # End-to-end tests
│   └── docker/          # Docker tests
├── infrastructure/       # Multi-cloud deployment
│   ├── terraform/       # Infrastructure as code
│   ├── ansible/         # Configuration management
│   ├── scripts/         # Deployment automation
│   └── README.md        # Infrastructure docs
├── Dockerfile           # Container definition
├── docker-compose.yml   # Multi-container setup
└── requirements.txt     # Python dependencies
```
